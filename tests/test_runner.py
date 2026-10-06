import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


MODULE = Path(__file__).resolve().parents[1] / "run_experiment.py"
spec = importlib.util.spec_from_file_location("runner", MODULE)
runner = importlib.util.module_from_spec(spec) if spec else None
if MODULE.exists():
    spec.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.exists(), "experiment runner has not been implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def verdict(self, failed=None):
        return {"criteria": [
            {"criterion": name, "passed": name != failed,
             "evidence": ["generated/feature.py:1"],
             "deficiency": "missing requirement" if name == failed else ""}
            for name in runner.CRITERIA
        ]}

    def test_missing_duplicate_or_nonboolean_criteria_cannot_pass(self):
        valid = self.verdict()
        self.assertTrue(runner.validate_verdict(valid))
        self.assertFalse(runner.validate_verdict(self.verdict("convention_fit")))
        malformed = [
            {"criteria": valid["criteria"][:-1]},
            {"criteria": valid["criteria"] + [valid["criteria"][0]]},
            {"criteria": [dict(c, passed="true") for c in valid["criteria"]]},
            {"criteria": [dict(c, evidence=[]) for c in valid["criteria"]]},
        ]
        for verdict in malformed:
            with self.subTest(verdict=verdict):
                with self.assertRaises(ValueError):
                    runner.validate_verdict(verdict)

    def test_only_nine_complete_run_passes_converge(self):
        self.assertTrue(runner.converged([True] * 9 + [False]))
        self.assertFalse(runner.converged([True] * 8 + [False] * 2))
        self.assertFalse(runner.converged([True] * 9))

    def test_fresh_snapshot_has_no_reference_or_original_history(self):
        source = self.root / "source"
        source.mkdir()
        (source / "feature.py").write_text("original = True\n")
        runner.initialize_git(source)
        (source / "secret_reference.py").write_text("reference = True\n")
        subprocess.run(["git", "add", "."], cwd=source, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-qm", "reference"], cwd=source, check=True)
        original_commit = runner.command(["git", "rev-parse", "HEAD~1"], source).strip()
        base = self.root / "base"
        runner.export_commit(source, original_commit, base)
        generated = self.root / "generated"
        runner.fresh_workspace(base, generated)
        self.assertFalse((generated / "secret_reference.py").exists())
        self.assertEqual(runner.command(["git", "rev-list", "--count", "HEAD"], generated).strip(), "1")
        self.assertEqual(runner.command(["git", "remote"], generated).strip(), "")

    def test_codex_command_allows_filesystem_access_and_uses_subscription(self):
        cwd = self.root / "generated"
        cwd.mkdir()
        args = runner.codex_command("codex", "gpt-6-luna", cwd,
                                    self.root / "result", True, [])
        joined = " ".join(args)
        self.assertIn('forced_login_method="chatgpt"', joined)
        self.assertIn('":root" = "write"', joined)
        self.assertNotIn('":minimal"', joined)
        self.assertIn('enabled = false', joined)
        self.assertNotIn("dangerously-bypass", joined)
        self.assertIn("--ephemeral", args)
        self.assertIn("--ignore-user-config", args)

    def test_bad_editor_category_is_rejected(self):
        edit = {"category": "Architecture", "subsection": "File placement",
                "operation": "add", "change": "use the existing module",
                "hypothesis": "prevents misplaced code"}
        categories = {"Architecture": ["File placement"]}
        runner.validate_revision({"specification": "new", "edits": [edit]}, categories)
        with self.assertRaises(ValueError):
            runner.validate_revision({"specification": "new", "edits": [dict(edit, category="Invented")]}, categories)

    def test_smoke_requires_tool_evidence_and_direct_filesystem_access(self):
        events = self.root / "events.jsonl"
        events.write_text(json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": "workspace_access true"}}) + "\n")
        with self.assertRaises(RuntimeError):
            runner.validate_smoke_events(events)
        events.write_text(json.dumps({"type": "item.completed", "item": {
            "type": "command_execution", "command": "cat probe.txt", "exit_code": 0,
            "aggregated_output": "repository access works\n"}}) + "\n")
        runner.validate_smoke_events(events)
        runner.validate_sandbox_check({"returncode": 0, "stdout": "repository access works\noutside filesystem access works\n",
                                       "stderr": ""})
        with self.assertRaises(RuntimeError):
            runner.validate_sandbox_check({"returncode": 1, "stdout": "repository access works\n",
                                           "stderr": "Operation not permitted"})

    def test_prepare_resumes_after_bare_repository_created_before_fetch(self):
        source = self.root / "source"
        source.mkdir()
        (source / "feature.py").write_text("value = 0\n")
        runner.initialize_git(source)
        commit = runner.command(["git", "rev-parse", "HEAD"], source).strip()
        (source / "feature.py").write_text("value = 1\n")
        diff = runner.command(["git", "diff"], source)
        task = {"id": "fixture", "repo": "fixture/repo", "pr": 1,
                "base_commit": commit, "install": [], "checks": []}
        directory = self.root / "tasks/fixture"
        directory.mkdir(parents=True)
        runner.write_json(directory / "pull.json", {"merged_at": "2024-01-01", "title": "Feature", "body": "Behavior"})
        runner.write_json(directory / "files.json", [])
        (directory / "reference.diff").write_text(diff)
        runner.command(["git", "init", "--bare", "-q", str(directory / "source.git")])
        real_command = runner.command

        def local_command(args, cwd=None, env=None):
            if args[:2] == ["git", "fetch"]:
                args = args[:-2] + [str(source), args[-1]]
            return real_command(args, cwd, env)

        with patch.object(runner, "command", side_effect=local_command):
            prepared = runner.prepare_task(task, self.root)
        self.assertEqual((Path(prepared["reference"]) / "feature.py").read_text(), "value = 1\n")

    def test_audit_contains_context_for_manual_judgment(self):
        output = self.root / "results/fixture"
        run = output / "revision-00/run-00"
        verdict = self.verdict()
        verdict["generated"] = str(run / "generated")
        task = {"base": "original", "reference": "reference", "requirements": runner.CRITERIA}
        runner.write_json(output / "settings.json", {"task": task})
        runner.write_json(run / "verdict.json", verdict)
        runner.make_audit(self.root)
        case = runner.read_json(self.root / "audit/sample.json")[0]
        self.assertEqual(case["original"], "original")
        self.assertEqual(case["reference"], "reference")
        self.assertEqual(case["requirements"], runner.CRITERIA)
        self.assertNotIn("judge", case)

    def test_codex_subprocess_logs_response_and_reuses_completed_call(self):
        executable = self.root / "fake-codex"
        executable.write_text("#!" + sys.executable + "\n"
                              "import json, pathlib, sys\n"
                              "args = sys.argv\n"
                              "print(json.dumps({'type': 'turn.completed'}))\n"
                              "pathlib.Path(args[args.index('--output-last-message') + 1]).write_text(json.dumps({'specification': sys.stdin.read()}))\n")
        executable.chmod(0o755)
        agent = runner.Codex(executable=str(executable))
        output, cwd = self.root / "session", self.root / "workspace"
        result = agent.run("baseline", "Behavior", cwd, output, runner.SPEC_SCHEMA)
        self.assertEqual(result, {"specification": "Behavior"})
        self.assertIn("turn.completed", (output / "events.jsonl").read_text())
        executable.unlink()
        self.assertEqual(agent.run("baseline", "Behavior", cwd, output, runner.SPEC_SCHEMA), result)

    def test_judge_cannot_pass_a_patch_missing_required_test_changes(self):
        base, reference = self.root / "base", self.root / "reference"
        base.mkdir()
        reference.mkdir()
        (base / "feature.py").write_text("value = 0\n")
        (reference / "feature.py").write_text("value = 1\n")
        task = {"id": "fixture", "base": str(base), "reference": str(reference),
                "test_files": [], "requires_test_changes": True,
                "checks": [[sys.executable, "-c", "from feature import value; assert value == 1"]],
                "requirements": dict(runner.CRITERIA)}
        verdicts = runner.evaluate_batch(task, self.root / "batch", FakeCodex(), "Refined")
        self.assertTrue(all(not verdict["passed"] for verdict in verdicts))
        self.assertTrue(all(not next(row for row in verdict["criteria"]
                                   if row["criterion"] == "convention_fit")["passed"]
                            for verdict in verdicts))

    def test_candidate_test_failure_is_not_hidden_by_reference_overlay(self):
        base = self.root / "base"
        (base / "tests").mkdir(parents=True)
        (base / "feature.py").write_text("value = 0\n")
        (base / "tests/test_feature.py").write_text("from feature import value\n\ndef test_value():\n    assert value == 0\n")
        reference = self.root / "reference"
        runner.fresh_workspace(base, reference)
        (reference / "tests/test_feature.py").write_text("from feature import value\n\ndef test_value():\n    assert value == 1\n")
        generated = self.root / "generated"
        runner.fresh_workspace(base, generated)
        (generated / "feature.py").write_text("value = 1\n")
        (generated / "tests/test_feature.py").write_text("from feature import value\n\ndef test_value():\n    assert value == 2\n")
        runner.command(["git", "add", "-A"], generated, runner.clean_env())
        task = {"base": str(base), "reference": str(reference),
                "test_files": ["tests/test_feature.py"], "generator_python": sys.executable,
                "checks": [[sys.executable, "-m", "pytest", "-q", "tests/test_feature.py"]]}
        checks = runner.check_candidate(task, generated, self.root)
        self.assertEqual([c["phase"] for c in checks["commands"]], ["candidate_tests", "reference_tests"])
        self.assertNotEqual(checks["commands"][0]["returncode"], 0)
        self.assertEqual(checks["commands"][1]["returncode"], 0)

    def test_reference_overlay_does_not_orphan_candidate_only_fixtures(self):
        base = self.root / "base"
        (base / "tests").mkdir(parents=True)
        (base / "feature.py").write_text("value = 0\n")
        (base / "tests/index.txt").write_text("original.txt\n")
        (base / "tests/original.txt").write_text("original")
        test = ("from pathlib import Path\nfrom feature import value\n\n"
                "def test_fixtures():\n    assert value == 1\n"
                "    root = Path('tests')\n"
                "    assert {p.name for p in root.glob('*.txt') if p.name != 'index.txt'} == "
                "set((root / 'index.txt').read_text().splitlines())\n")
        (base / "tests/test_feature.py").write_text(test)
        reference = self.root / "reference"
        runner.fresh_workspace(base, reference)
        (reference / "tests/index.txt").write_text("original.txt\nreference.txt\n")
        (reference / "tests/reference.txt").write_text("reference")
        generated = self.root / "generated"
        runner.fresh_workspace(base, generated)
        (generated / "feature.py").write_text("value = 1\n")
        (generated / "tests/index.txt").write_text("original.txt\ncandidate.txt\n")
        (generated / "tests/candidate.txt").write_text("candidate")
        runner.command(["git", "add", "-A"], generated, runner.clean_env())
        task = {"base": str(base), "reference": str(reference),
                "test_files": ["tests/index.txt", "tests/reference.txt"],
                "generator_python": sys.executable,
                "checks": [[sys.executable, "-m", "pytest", "-q", "tests/test_feature.py"]]}
        checks = runner.check_candidate(task, generated, self.root)
        self.assertEqual([c["returncode"] for c in checks["commands"]], [0, 0])
        self.assertTrue((generated / "tests/candidate.txt").exists())
        self.assertFalse((self.root / "evaluation/tests/candidate.txt").exists())

    def test_codex_rejects_mutation_of_protected_specification(self):
        protected = self.root / "specification.md"
        protected.write_text("original")
        executable = self.root / "fake-codex"
        executable.write_text("#!" + sys.executable + "\n"
                              "import json, pathlib, sys\n"
                              f"pathlib.Path({str(protected)!r}).write_text('mutated')\n"
                              "pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1]).write_text(json.dumps({'specification': 'next'}))\n")
        executable.chmod(0o755)
        output = self.root / "session"
        with self.assertRaisesRegex(RuntimeError, "modified a protected experiment input"):
            runner.Codex(executable=str(executable)).run(
                "edit", "Return JSON only", self.root, output, runner.SPEC_SCHEMA,
                protected=[protected])
        self.assertFalse((output / "complete.json").exists())
        self.assertEqual((output / "protected-inputs/00-specification.md").read_text(), "original")

    def test_loop_refines_once_confirms_and_resumes_without_new_calls(self):
        base = self.root / "base"
        base.mkdir()
        (base / "feature.py").write_text("value = 0\n")
        reference = self.root / "reference"
        reference.mkdir()
        (reference / "feature.py").write_text("value = 1\n")
        task = {"id": "fixture", "base": str(base), "reference": str(reference),
                "description": "Implement the new capability.", "test_files": [],
                "checks": [[sys.executable, "-c", "from feature import value; assert value == 1"]],
                "requirements": {key: key for key in runner.CRITERIA}}
        fake = FakeCodex()
        categories = {"Architecture": ["Responsibilities"]}
        output = self.root / "output"
        result = runner.run_task(task, output, fake, categories)
        self.assertEqual(result["status"], "converged")
        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["baseline_passes"], 0)
        self.assertEqual((output / "baseline.md").read_text(), task["description"])
        self.assertFalse(any(role == "baseline" for role, _, _ in fake.calls))
        self.assertEqual(result["confirmation_passes"], 10)
        calls = len(fake.calls)
        self.assertEqual(runner.run_task(task, output, fake, categories), result)
        self.assertEqual(len(fake.calls), calls)
        for role, prompt, cwd in fake.calls:
            if role == "generate":
                self.assertNotIn(str(reference), prompt)
                self.assertFalse((cwd / "reference").exists())
            if role == "judge":
                self.assertNotIn(task["description"], prompt)
                self.assertNotIn("baseline_behavior", prompt)
                self.assertIn("source of truth", prompt)
            if role == "edit":
                self.assertNotIn("baseline", runner.read_json(cwd / "feedback.json"))
                self.assertIn("correct or remove", prompt)

    def test_nonconvergence_stops_after_ten_revisions(self):
        base = self.root / "base"
        base.mkdir()
        (base / "feature.py").write_text("value = 0\n")
        task = {"id": "fixture", "base": str(base), "reference": str(base),
                "description": "Feature", "test_files": [], "checks": [],
                "requirements": {key: key for key in runner.CRITERIA}}
        fake = FakeCodex(always_fail=True)
        result = runner.run_task(task, self.root / "output", fake,
                                 {"Architecture": ["Responsibilities"]})
        self.assertEqual(result["status"], "non_convergent")
        self.assertEqual(sum(role == "edit" for role, _, _ in fake.calls), 10)
        self.assertEqual(sum(role == "generate" for role, _, _ in fake.calls), 110)


class FakeCodex:
    model = "fake"

    def __init__(self, always_fail=False):
        self.calls = []
        self.always_fail = always_fail

    def run(self, role, prompt, cwd, output, schema, writable=False, readable=(), python=None, protected=()):
        self.calls.append((role, prompt, cwd))
        if role == "baseline":
            return {"specification": "Implement the behavior."}
        if role == "generate":
            (cwd / "feature.py").write_text("value = 1\n" if "Refined" in prompt else "value = 0\n")
            return {"summary": "implemented"}
        if role == "judge":
            passed = not self.always_fail and "value = 1" in (Path(readable[-1]) / "feature.py").read_text()
            return {"criteria": [{"criterion": key, "passed": passed,
                                  "evidence": ["feature.py:1"],
                                  "deficiency": "" if passed else "Missing behavior"}
                                 for key in runner.CRITERIA]}
        if role == "edit":
            return {"specification": "Refined specification.", "edits": [
                {"category": "Architecture", "subsection": "Responsibilities",
                 "operation": "clarify", "change": "implement the behavior",
                 "hypothesis": "resolves missing behavior"}]}
        raise AssertionError(role)


if __name__ == "__main__":
    unittest.main()
