from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import claude_low_queue as queue  # noqa: E402
import run_experiment as runner  # noqa: E402

OLD = "/tmp/aechang/llm-improvement-loop/.experiments/manual-claude-low-ghc/tasks/t1"


def old_task():
    python = OLD + "/venv/bin/python"
    return {"id": "t1", "base": OLD + "/base", "reference": OLD + "/reference",
            "generator_python": OLD + "/generator-venv/bin/python", "description": OLD + " is text",
            "checks": [[python, "-m", "pytest", "x.py"]], "inspection": [[python, "-c", "1"]],
            "candidate_check_prefix": [python, "-m"]}


class PathTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_old_absolute_task_paths_move_to_this_experiment(self):
        task = runner.local_task(old_task(), self.root)
        new = str(self.root / "tasks/t1")
        self.assertEqual(task["base"], new + "/base")
        self.assertEqual(task["generator_python"], new + "/generator-venv/bin/python")
        self.assertEqual(task["checks"], [[new + "/venv/bin/python", "-m", "pytest", "x.py"]])
        self.assertEqual(task["candidate_check_prefix"], [new + "/venv/bin/python", "-m"])
        self.assertEqual(task["description"], OLD + " is text")
        portable = runner.portable_task(task)
        self.assertEqual(portable["reference"], "tasks/t1/reference")
        self.assertEqual(runner.local_task(portable, self.root), task)

    def test_existing_absolute_task_paths_are_kept(self):
        (self.root / "tasks/t1/base").mkdir(parents=True)
        task = runner.relocate_task(old_task(), self.root / "tasks/t1")
        self.assertIs(runner.local_task(task, "/elsewhere"), task)

    def test_copied_experiment_resumes_and_keeps_its_path_style(self):
        settings = {"task": runner.local_task(old_task(), self.root), "model": "m", "backend": "codex", "runner_sha256": "x"}
        runner.write_json(self.root / "settings.json", dict(settings, task=old_task()))
        runner.resume_settings(self.root, settings)
        self.assertEqual(runner.read_json(self.root / "settings.json"), settings)
        with self.assertRaisesRegex(ValueError, "settings changed"):
            runner.resume_settings(self.root, dict(settings, task=dict(settings["task"], id="t2")))

    def test_new_settings_record_paths_relative_to_the_experiment(self):
        settings = {"task": runner.local_task(old_task(), self.root), "backend": "codex", "runner_sha256": "x"}
        runner.resume_settings(self.root / "new", settings)
        saved = runner.read_json(self.root / "new/settings.json")
        self.assertEqual(saved["task"]["base"], "tasks/t1/base")
        runner.resume_settings(self.root / "new", settings)
        self.assertFalse((self.root / "new/settings-history.json").exists())

    def test_recorded_paths_remap_into_this_repo(self):
        self.assertEqual(runner.recorded_path(".experiments/x/results/t"), runner.ROOT / ".experiments/x/results/t")
        self.assertEqual(runner.recorded_path("/tmp/aechang/llm-improvement-loop/.experiments/x/results/t"),
                         runner.ROOT / ".experiments/x/results/t")
        self.assertEqual(runner.record_path(runner.ROOT / ".experiments/x"), ".experiments/x")
        self.assertEqual(runner.record_path(self.root), str(self.root))

    def test_batch_candidates_are_found_next_to_the_batch(self):
        runner.write_json(self.root / "batch.json", {"runs": [{"passed": True, "generated": OLD + "/gone"},
                                                             {"passed": False, "generated": "run-01/generated"}]})
        runs = runner.load_batch(self.root / "batch.json")
        self.assertEqual([r["generated"] for r in runs],
                         [str(self.root / "run-00/generated"), str(self.root / "run-01/generated")])

    def test_task_list_file_allows_comments(self):
        (self.root / "tasks.txt").write_text("# Windows\na  # started\n\nb\n")
        self.assertEqual(queue.task_list(str(self.root / "tasks.txt")), {"a", "b"})
        self.assertEqual(queue.task_list("a,b"), {"a", "b"})

    def test_machine_task_lists_are_disjoint_claude_tasks(self):
        lists = {name: queue.task_list(str(runner.ROOT / f"tasks/{name}.txt")) for name in ("mac", "ghc", "windows")}
        self.assertEqual(sum(map(len, lists.values())), len(set().union(*lists.values())))
        self.assertLessEqual(lists["mac"] | lists["ghc"], set(queue.claude_tasks()))
        windows = runner.read_json(runner.ROOT / "experiments/windows-100/runner-manifest.json")
        self.assertEqual(lists["windows"], {task["id"] for task in windows})
        batch = runner.read_json(runner.ROOT / ".experiments/batch-100/runner-manifest.json")
        self.assertFalse(lists["windows"] & {task["id"] for task in batch})


if __name__ == "__main__":
    unittest.main()
