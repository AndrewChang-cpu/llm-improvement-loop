#!/usr/bin/env python3
"""Run the specification-refinement pilot through ChatGPT-authenticated Codex."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request


ROOT = Path(__file__).resolve().parent
CRITERIA = {
    "patch_and_checks": "Patch applies and the recorded executable checks pass.",
    "file_location": "Code is placed in the required existing module or component.",
    "api_contract": "API names, visibility, parameters, types, and return contracts match requirements.",
    "dependency_direction": "Imports and dependency directions respect existing boundaries.",
    "extension_registration": "Required registration and interface implementation are present.",
    "approved_dependencies": "No unapproved dependencies are introduced.",
    "architectural_fit": "Responsibilities belong in the intended layer or component.",
    "extension_point_adherence": "Existing extension mechanisms are used rather than a parallel path.",
    "abstraction_integrity": "Domain, transport, persistence, and framework boundaries are preserved.",
    "convention_fit": "Validation, errors, naming, logging, and tests match analogous local code.",
    "requirement_intent": "The feature satisfies its behavioral intent and constraints.",
}


def command(args, cwd=None, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {args!r}\n{result.stdout[-2000:]}{result.stderr[-2000:]}")
    return result.stdout


def clean_env():
    env = os.environ.copy()
    for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "GH_TOKEN", "GITHUB_TOKEN"):
        env.pop(key, None)
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text())


def initialize_git(directory):
    command(["git", "init", "-q", str(directory)], env=clean_env())
    command(["git", "add", "-A"], directory, clean_env())
    command(["git", "-c", "user.name=Experiment", "-c", "user.email=experiment@example.invalid",
             "-c", "core.hooksPath=" + os.devnull, "commit", "-qm", "Original snapshot"],
            directory, clean_env())


def export_commit(repository, commit, destination):
    data = subprocess.check_output(["git", "archive", commit], cwd=repository, env=clean_env())
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            if Path(member.name).is_absolute() or ".." in Path(member.name).parts:
                raise ValueError("Git archive contains an unsafe path")
            if member.issym() or member.islnk():
                target = (destination / member.name).parent / member.linkname
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError("Git archive links outside the snapshot")
        archive.extractall(destination)


def fresh_workspace(base, destination):
    # Fresh Git history prevents the generator from finding the reference PR in old commits.
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(base, destination, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", ".codex", "__pycache__", ".pytest_cache"))
    initialize_git(destination)


def object_schema(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


TEXT = {"type": "string", "minLength": 1}
SPEC_SCHEMA = object_schema({"specification": TEXT})
GEN_SCHEMA = object_schema({"summary": TEXT})
JUDGE_SCHEMA = object_schema({"criteria": {
    "type": "array", "minItems": len(CRITERIA), "maxItems": len(CRITERIA),
    "items": object_schema({
        "criterion": {"type": "string", "enum": list(CRITERIA)},
        "passed": {"type": "boolean"},
        "evidence": {"type": "array", "items": TEXT, "minItems": 1},
        "deficiency": {"type": "string"},
    }),
}})


def validate_verdict(verdict):
    rows = verdict.get("criteria", [])
    names = [row.get("criterion") for row in rows]
    if len(names) != len(CRITERIA) or set(names) != set(CRITERIA):
        raise ValueError("Judge must report every criterion exactly once")
    for row in rows:
        if type(row.get("passed")) is not bool:
            raise ValueError("Criterion verdicts must be boolean")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
            raise ValueError("Each judgment needs evidence")
        if not row["passed"] and not str(row.get("deficiency", "")).strip():
            raise ValueError("Failed judgments need a deficiency")
    return all(row["passed"] for row in rows)


def converged(passes):
    # A run passes only when every criterion passes; convergence requires nine such runs.
    return len(passes) == 10 and sum(passes) >= 9


def categories_from_docs():
    text = (ROOT / "docs/experimental-methodology.md").read_text()
    section = text.split("## Specification categories\n", 1)[1].split("\n## ", 1)[0]
    return {parts[0]: [item.strip() for item in parts[1].split(";")]
            for line in section.splitlines() if line.startswith("| ")
            for parts in [[p.strip() for p in line.strip("|").split("|")]]
            if parts[0] not in ("Category", "---")}


def validate_revision(revision, categories):
    if not isinstance(revision.get("specification"), str) or not revision["specification"].strip():
        raise ValueError("Editor returned an empty specification")
    if not revision.get("edits"):
        raise ValueError("Editor must explain its changes")
    for edit in revision["edits"]:
        if edit.get("subsection") not in categories.get(edit.get("category"), []):
            raise ValueError("Editor invented a category or subsection")
        if edit.get("operation") not in ("add", "clarify", "reformat", "remove"):
            raise ValueError("Unknown edit operation")
        if not edit.get("change", "").strip() or not edit.get("hypothesis", "").strip():
            raise ValueError("Edits need exact changes and hypotheses")


def codex_command(executable, model, cwd, output, writable, readable):
    # Full filesystem access permits system tools; task-code boundaries are prompt instructions.
    policy = '{ filesystem = { ":root" = "write" }, network = { enabled = false }}'
    return [executable, "--no-daemon", "-a", "never", "exec", "--ignore-user-config",
            "--ignore-rules", "--ephemeral", "--json", "-m", model, "-C", str(cwd),
            "-c", 'model_reasoning_effort="high"',
            "-c", 'forced_login_method="chatgpt"', "-c", 'default_permissions="experiment"',
            "-c", "permissions.experiment=" + policy,
            "-c", 'web_search="disabled"', "-c", "mcp_servers={}",
            "-c", "project_doc_max_bytes=0", "-c", "features.skip_host_skill_discovery=true",
            "--disable", "apps", "--disable", "memories", "--disable", "multi_agent",
            "--disable", "hooks", "--disable", "browser_use", "--disable", "computer_use",
            "--output-schema", str(output / "schema.json"),
            "--output-last-message", str(output / "response.json"), "-"]


class Codex:
    def __init__(self, model="gpt-6-luna", executable="codex"):
        self.model = model
        self.executable = executable

    def run(self, role, prompt, cwd, output, schema, writable=False, readable=(), python=None, protected=()):
        output.mkdir(parents=True, exist_ok=True)
        cwd.mkdir(parents=True, exist_ok=True)
        args = codex_command(self.executable, self.model, cwd, output, writable, readable)
        request = {"role": role, "prompt": prompt, "command": args, "schema": schema}
        if protected:
            request["protected_inputs"] = [str(path) for path in protected]
        env = clean_env()
        if python:
            # Test commands use prepared dependencies and import this candidate's source.
            env.update(PATH=str(Path(python).parent) + os.pathsep + env.get("PATH", ""),
                       VIRTUAL_ENV=str(Path(python).parent.parent), PYTHONPATH=str(cwd),
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", MPLBACKEND="Agg")
            request["python"] = python
        if (output / "request.json").exists() and read_json(output / "request.json") != request:
            raise ValueError(f"Cached request differs: {output}. Use a new output directory.")
        write_json(output / "request.json", request)
        if (output / "complete.json").exists():
            return read_json(output / "complete.json")
        write_json(output / "schema.json", schema)
        # Preserve input evidence even when a role has full filesystem access.
        before = {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in protected}
        if protected:
            snapshots = output / "protected-inputs"
            snapshots.mkdir(exist_ok=True)
            for number, path in enumerate(protected):
                shutil.copy2(path, snapshots / f"{number:02d}-{Path(path).name}")
        print(f"  {role}: {output}", flush=True)
        with (output / "events.jsonl").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
            result = subprocess.run(args, input=prompt, text=True, stdout=stdout, stderr=stderr,
                                    env=env)
        after = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                 if Path(path).is_file() else None for path in before}
        if before:
            write_json(output / "input-integrity.json", {"before": before, "after": after})
        if before != after:
            raise RuntimeError(f"{role} modified a protected experiment input. Logs: {output}")
        if result.returncode:
            raise RuntimeError(f"Codex failed ({result.returncode}); resume after resolving the error. Logs: {output}")
        response = read_json(output / "response.json")
        write_json(output / "complete.json", response)
        return response


def check_candidate(task, generated, output):
    # Evaluate the candidate with the reference PR's tests, preserving the candidate for judging.
    patch = command(["git", "diff", "--cached", "--binary"], generated, clean_env())
    (output / "patch.diff").write_text(patch)
    evaluation = output / "evaluation"
    fresh_workspace(Path(task["base"]), evaluation)
    apply = subprocess.run(["git", "apply", "--binary", "-"], input=patch, cwd=evaluation,
                           text=True, capture_output=True, env=clean_env())
    checks = {"patch_applies": bool(patch) and apply.returncode == 0, "commands": []}
    changed = command(["git", "diff", "--cached", "--name-only"], generated, clean_env()).splitlines()
    checks["candidate_test_changes"] = [path for path in changed if path.startswith("tests/")]
    env = clean_env()
    env.update(PYTHONPATH=str(evaluation), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", MPLBACKEND="Agg",
               PYTHONDONTWRITEBYTECODE="1")
    # Validate candidate-owned tests before reference files can replace them.
    if task.get("generator_python") and task["checks"] and task["checks"][0][1:3] == ["-m", "pytest"]:
        paths = task["checks"][0][4:] + [path for path in checks["candidate_test_changes"]
                if Path(path).name.startswith("test_") and path.endswith(".py")]
        tests = sorted({path for path in paths if (evaluation / path.split("::")[0]).exists()})
        args = [task["generator_python"], "-m", "pytest", "-q", "--basetemp",
                str(output / "candidate-test-tmp")] + tests
        result = subprocess.run(args, cwd=evaluation, env=env, text=True, capture_output=True)
        checks["commands"].append({"phase": "candidate_tests", "command": args,
                                   "returncode": result.returncode,
                                   "output": result.stdout + result.stderr})
    # Reference tests use original-plus-reference fixtures, without candidate-only test data.
    if (evaluation / "tests").exists():
        shutil.rmtree(evaluation / "tests")
    if (Path(task["base"]) / "tests").exists():
        shutil.copytree(Path(task["base"]) / "tests", evaluation / "tests",
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    for filename in task["test_files"]:
        source = Path(task["reference"]) / filename
        target = evaluation / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_file():
            shutil.copy2(source, target)
        elif target.exists():
            target.unlink()
    # Record effective inherited API attributes instead of relying on visual inference.
    checks["api_inspection"] = []
    for label, repository in (("original", task["base"]), ("reference", task["reference"]),
                              ("generated", str(generated))):
        for args in task.get("inspection", []):
            probe_env = dict(env, PYTHONPATH=repository)
            result = subprocess.run(args, cwd=repository, env=probe_env, text=True, capture_output=True)
            checks["api_inspection"].append({"snapshot": label, "command": args,
                                            "returncode": result.returncode,
                                            "output": result.stdout + result.stderr})
    for args in task["checks"]:
        result = subprocess.run(args, cwd=evaluation, env=env, text=True, capture_output=True)
        checks["commands"].append({"phase": "reference_tests", "command": args, "returncode": result.returncode,
                                   "output": result.stdout + result.stderr})
    write_json(output / "checks.json", checks)
    return checks


def judge_prompt(task, generated, checks=None):
    # Neither the PR description nor the current specification defines evaluation requirements.
    facts = []
    for probe in (checks or {}).get("api_inspection", []):
        if probe["returncode"] == 0:
            facts.append({"snapshot": probe["snapshot"], "facts": json.loads(probe["output"])})
    return ("Evaluate this patch against every fixed criterion. Read the original, reference, and generated "
            "code using the supplied paths. The reference implementation is the source of truth for "
            "the feature's behavior, public contracts, and intended architecture. Accept valid alternative "
            "implementations without requiring textual identity or incidental private helper names. "
            "Do not invent requirements from optional implementation choices. Verify each claimed "
            "failure against the actual reference and analogous original code. "
            "Before claiming an option, method, or registration is missing, trace its complete inherited "
            "definitions in both implementations. Distinguish accepting an option from rendering its value. "
            "Determine additions, removals, and regressions against the original snapshot and patch.diff, "
            "not a reference-to-generated diff. Reference-only tests absent from the candidate are not "
            "deleted tests. Distinguish an object nested inside a container from that object allowing "
            "nested contents; verify the actual reference behavior rather than inferring a required flag. "
            "Cite file:line evidence for each criterion and describe each failure. "
            "Use checks.json for executable status and recorded API inspection facts; do not contradict "
            "a successful inspection of an effective inherited attribute. Never invent execution results. "
            "Do not modify files.\n"
            + json.dumps({"verified_api_facts": facts,
                          "candidate_test_changes": (checks or {}).get("candidate_test_changes", []),
                          "requires_test_changes": task.get("requires_test_changes", False),
                          "requirements": task["requirements"], "original": task["base"],
                          "reference": task["reference"], "generated": str(generated)}, indent=2))


def evaluate_batch(task, output, agent, specification, runs=10):
    if runs < 1:
        raise ValueError("Batch size must be positive")
    def evaluate_run(number):
        run = output / f"run-{number:02d}"
        generated = run / "generated"
        if (run / "verdict.json").exists():
            return read_json(run / "verdict.json")
        if not (run / "generation/complete.json").exists():
            fresh_workspace(Path(task["base"]), generated)
        # The generator sees only the specification and its original-code workspace.
        agent.run("generate", "Implement this feature in the repository. Inspect and edit repository files. "
                  "Do not use the network, other repository directories, additional agents, or outside feedback. "
                  "Do not modify tests to conceal failures. Do not commit changes. "
                  + (f"Run tests using {task['generator_python']}. This prepared environment is shared; "
                     "do not install packages or modify it. " if task.get("generator_python") else "")
                  + "\n\nSPECIFICATION:\n" + specification, generated, run / "generation", GEN_SCHEMA,
                  writable=True, python=task.get("generator_python"))
        command(["git", "add", "-A"], generated, clean_env())
        checks = check_candidate(task, generated, run)
        context = run / "judge-context"
        context.mkdir(exist_ok=True)
        shutil.copy2(run / "checks.json", context / "checks.json")
        shutil.copy2(run / "patch.diff", context / "patch.diff")
        readable = [task["base"], task["reference"], str(generated)]
        prompt = judge_prompt(task, generated, checks)
        verdict = agent.run("judge", prompt, context, run / "judgment", JUDGE_SCHEMA, readable=readable,
                            protected=[context / "checks.json", context / "patch.diff"])
        validate_verdict(verdict)
        executable_pass = checks["patch_applies"] and all(c["returncode"] == 0 for c in checks["commands"])
        # A judge cannot override an actual patch or test failure.
        if not executable_pass:
            row = next(c for c in verdict["criteria"] if c["criterion"] == "patch_and_checks")
            row.update(passed=False, deficiency="Patch application or an executable check failed.",
                       evidence=[str(context / "checks.json") + ":1"])
        if task.get("requires_test_changes") and not checks["candidate_test_changes"]:
            row = next(c for c in verdict["criteria"] if c["criterion"] == "convention_fit")
            row.update(passed=False, deficiency="Repository policy requires feature regression tests; "
                       "the candidate patch contains no test changes.",
                       evidence=[str(context / "checks.json") + ":1"])
        verdict["passed"] = validate_verdict(verdict)
        verdict["generated"] = str(generated)
        # The editor needs actual failures and API facts, not only the judge's paraphrase.
        verdict["checks"] = checks
        write_json(run / "verdict.json", verdict)
        return verdict

    # Each lane has its own repository and logs; only the frozen reference is shared read-only.
    with ThreadPoolExecutor(max_workers=min(10, runs)) as pool:
        results = list(pool.map(evaluate_run, range(runs)))
    write_json(output / "batch.json", {"passes": sum(r["passed"] for r in results), "runs": results})
    return results


def run_task(task, output, agent, categories):
    output.mkdir(parents=True, exist_ok=True)
    # Refuse to mix cached results with a changed model, task, rubric, or runner.
    settings = {"task": task, "model": agent.model, "categories": categories,
                "runs": 10, "parallel_runs": 10, "max_revisions": 10,
                "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if (output / "settings.json").exists() and read_json(output / "settings.json") != settings:
        raise ValueError("Experiment settings changed. Use a new output directory.")
    write_json(output / "settings.json", settings)
    if (output / "result.json").exists():
        return read_json(output / "result.json")
    # Preserve the historical request verbatim; only editor-produced revisions prohibit code.
    baseline = task["description"]
    if not isinstance(baseline, str) or not baseline.strip():
        raise ValueError("PR baseline is empty")
    (output / "baseline.md").write_text(baseline)
    specification = baseline
    baseline_passes = None
    edit_schema = object_schema({"specification": TEXT, "edits": {
        "type": "array", "minItems": 1, "items": {"anyOf": [object_schema({
            "category": {"type": "string", "enum": [category]},
            "subsection": {"type": "string", "enum": subsections},
            "operation": {"type": "string", "enum": ["add", "clarify", "reformat", "remove"]},
            "change": TEXT, "hypothesis": TEXT,
        }) for category, subsections in categories.items()]},
    }})
    for revision in range(11):
        # Revision zero is the original PR baseline; revisions one through ten are editor outputs.
        directory = output / f"revision-{revision:02d}"
        directory.mkdir(exist_ok=True)
        (directory / "specification.md").write_text(specification + "\n")
        results = evaluate_batch(task, directory, agent, specification)
        passes = sum(r["passed"] for r in results)
        if baseline_passes is None:
            baseline_passes = passes
        if converged([r["passed"] for r in results]):
            # Confirm a qualifying specification with ten additional independent generations.
            confirmation = evaluate_batch(task, directory / "confirmation", agent, specification)
            if converged([r["passed"] for r in confirmation]):
                (output / "comprehensive-specification.md").write_text(specification + "\n")
                result = {"task": task["id"], "status": "converged", "revision": revision,
                          "baseline_passes": baseline_passes, "final_passes": passes,
                          "confirmation_passes": sum(r["passed"] for r in confirmation)}
                write_json(output / "result.json", result)
                return result
            results += confirmation
        if revision == 10:
            break
        editor_context = directory / "editor-context"
        editor_context.mkdir(exist_ok=True)
        feedback = {"current_specification": specification,
                    "categories": categories, "requirements": task["requirements"], "runs": results}
        write_json(editor_context / "feedback.json", feedback)
        readable = [task["base"], task["reference"]] + [r["generated"] for r in results]
        prompt = ("Read feedback.json and the original, reference, and generated code. Produce ONE next "
                  "specification describing the feature implemented by the reference code. The reference "
                  "implementation is the source of truth for behavior, public contracts, and architecture. "
                  "The current specification is an editable draft, not an independent source of requirements; "
                  "correct or remove any content that conflicts with the reference implementation. "
                  "Introduce or improve sections only within the "
                  "listed categories and subsections. Use the exact listed subsection names as specification "
                  "section headings; parent categories only group the inventory. Include the relevant subset "
                  "and do not invent headings. Explain exact edits and hypotheses. You may add, clarify, "
                  "reformat, or remove content. Focus edits on the failures reported by the judge. "
                  "Verify each diagnosis by reading the complete relevant reference methods, including "
                  "inherited methods. Preserve correct requirements and explain which failed criterion "
                  "each edit addresses. Do not remove a correct constraint because current runs satisfy "
                  "it. Justify removal with reference evidence or redundancy, preserving its protection. "
                  "Address the cause of each distinct reported failure. For runtime "
                  "errors, identify the failing operation and cause before proposing a specification "
                  "change; changing output wording does not resolve an exception. "
                  "The specification must instruct the agent how to implement "
                  "the feature, not supply the implementation. Do not include actual programming-language "
                  "code, implementation bodies, executable examples, or code-form declarations or signatures. "
                  "Do not copy reference code into the specification. Express API contracts, names, types, "
                  "and structural constraints in any format that is not actual code. Pseudocode is allowed; label it as "
                  "pseudocode. Remove any actual code from the current specification. Do not modify any "
                  "code or execute another generator. Return the specification and edit explanations "
                  "only in the requested JSON response. Do not write, edit, or delete any files, "
                  "including specifications, feedback, and experiment artifacts.\n"
                  + json.dumps({"original": task["base"], "reference": task["reference"]}))
        response = agent.run("edit", prompt, editor_context, directory / "editing", edit_schema,
                             readable=readable, protected=[directory / "specification.md",
                                                          editor_context / "feedback.json"])
        validate_revision(response, categories)
        write_json(directory / "revision-edit.json", response)
        specification = response["specification"]
    result = {"task": task["id"], "status": "non_convergent", "revision": 10,
              "baseline_passes": baseline_passes, "final_passes": passes}
    write_json(output / "result.json", result)
    return result


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "specification-refinement-pilot"})
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        request.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(request) as response:
        return response.read()


def prepare_generator_environment(task, directory, base):
    venv = directory / "generator-venv"
    python = str(venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
    marker = venv / "prepared.json"
    configuration = {"base_commit": task["base_commit"], "install": task["install"]}
    if marker.exists() and read_json(marker) == configuration:
        return python
    if not venv.exists():
        command([sys.executable, "-m", "venv", str(venv)])
    # Install the original project, never the merged reference implementation.
    for packages in task["install"]:
        command([python, "-m", "pip", "install"] + packages, base, clean_env())
    command([python, "-m", "pip", "check"], base, clean_env())
    write_json(marker, configuration)
    return python


def prepare_task(task, storage):
    directory = storage / "tasks" / task["id"]
    if (directory / "prepared.json").exists():
        prepared = read_json(directory / "prepared.json")
        if prepared["manifest"] != task:
            raise ValueError("Task manifest changed. Use a new output directory.")
        prepared["task"]["generator_python"] = prepare_generator_environment(
            task, directory, Path(prepared["task"]["base"]))
        write_json(directory / "prepared.json", prepared)
        return prepared["task"]
    directory.mkdir(parents=True, exist_ok=True)
    metadata = directory / "pull.json"
    if not metadata.exists():
        write_json(metadata, json.loads(download(f"https://api.github.com/repos/{task['repo']}/pulls/{task['pr']}")))
    pull = read_json(metadata)
    if not pull.get("merged_at"):
        raise ValueError("Pilot task is not a merged PR")
    patch_file = directory / "reference.diff"
    if not patch_file.exists():
        patch_file.write_bytes(download(pull["diff_url"]))
    file_list = directory / "files.json"
    if not file_list.exists():
        write_json(file_list, json.loads(download(f"https://api.github.com/repos/{task['repo']}/pulls/{task['pr']}/files?per_page=100")))
    repository = directory / "source.git"
    if not repository.exists():
        command(["git", "init", "--bare", "-q", str(repository)])
    # An interrupted fetch may leave a valid but empty bare repository.
    available = subprocess.run(["git", "cat-file", "-e", task["base_commit"] + "^{commit}"],
                               cwd=repository, env=clean_env(), capture_output=True)
    if available.returncode:
        command(["git", "fetch", "--depth=1", "--no-tags", f"https://github.com/{task['repo']}.git", task["base_commit"]], repository)
    base, reference = directory / "base", directory / "reference"
    if base.exists():
        shutil.rmtree(base)
    export_commit(repository, task["base_commit"], base)
    fresh_workspace(base, reference)
    command(["git", "apply", "--binary", str(patch_file)], reference, clean_env())
    venv = directory / "venv"
    if not venv.exists():
        command([sys.executable, "-m", "venv", str(venv)])
    python = str(venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
    for packages in task["install"]:
        command([python, "-m", "pip", "install"] + packages, reference, clean_env())
    checks = [[python if word == "{python}" else word for word in args] for args in task["checks"]]
    inspection = [[python if word == "{python}" else word for word in args]
                  for args in task.get("inspection", [])]
    env = clean_env()
    env.update(PYTHONPATH=str(reference), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", MPLBACKEND="Agg")
    logs = []
    for args in checks:
        logs.append({"command": args, "output": command(args, reference, env)})
    write_json(directory / "reference-validation.json", logs)
    test_files = [f["filename"] for f in read_json(file_list) if f["filename"].startswith("tests/")]
    prepared = {"id": task["id"], "base": str(base), "reference": str(reference),
                "description": (pull["title"] + "\n\n" + (pull.get("body") or "")),
                "test_files": test_files, "checks": checks, "inspection": inspection,
                "generator_python": prepare_generator_environment(task, directory, base),
                "requires_test_changes": task.get("requires_test_changes", False),
                "requirements": {key: task.get("requirements", {}).get(key, description)
                                 for key, description in CRITERIA.items()}}
    write_json(directory / "prepared.json", {"manifest": task, "task": prepared})
    return prepared


def make_audit(storage):
    destination = storage / "audit"
    if (destination / "sample.json").exists():
        return
    paths = sorted((storage / "results").glob("*/revision-*/**/run-*/verdict.json"))
    sample = random.Random(42).sample(paths, min(10, len(paths)))
    cases, key = [], []
    for number, path in enumerate(sample):
        verdict = read_json(path)
        task = read_json(storage / "results" / path.relative_to(storage / "results").parts[0] / "settings.json")["task"]
        cases.append({"id": number, "patch": str(path.parent / "patch.diff"),
                      "generated": verdict["generated"], "original": task["base"],
                      "reference": task["reference"], "requirements": task["requirements"],
                      "checks": str(path.parent / "checks.json"),
                      "manual": {c: None for c in CRITERIA}})
        key.append({"id": number, "judge": verdict["criteria"]})
    write_json(destination / "sample.json", cases)
    write_json(destination / "judge-key.json", key)


def validate_smoke_events(events):
    # Require a recorded tool result rather than accepting the model's access claim.
    commands = [event["item"] for line in events.read_text().splitlines()
                for event in [json.loads(line)] if event.get("type") == "item.completed"
                and event.get("item", {}).get("type") == "command_execution"]
    if not any("probe.txt" in item["command"]
               and "repository access works" in item.get("aggregated_output", "") for item in commands):
        raise RuntimeError("Smoke transcript does not demonstrate repository access")


def validate_sandbox_check(check):
    if (check["returncode"] != 0 or "repository access works" not in check["stdout"]
            or "outside filesystem access works" not in check["stdout"]):
        raise RuntimeError("Filesystem probe did not demonstrate workspace and outside-file access")


def audit_agreement(storage):
    cases = read_json(storage / "audit/sample.json")
    key = {entry["id"]: entry["judge"] for entry in read_json(storage / "audit/judge-key.json")}
    report = {"reviewed": 0, "criterion_agreements": 0, "criterion_total": 0,
              "overall_agreements": 0, "false_passes": 0, "false_failures": 0}
    for case in cases:
        manual = case["manual"]
        if set(manual) != set(CRITERIA) or not all(type(v) is bool for v in manual.values()):
            continue
        judged = {r["criterion"]: r["passed"] for r in key[case["id"]]}
        human_pass, judge_pass = all(manual.values()), all(judged.values())
        report["reviewed"] += 1
        report["criterion_total"] += len(CRITERIA)
        report["criterion_agreements"] += sum(manual[c] == judged[c] for c in CRITERIA)
        report["overall_agreements"] += human_pass == judge_pass
        report["false_passes"] += judge_pass and not human_pass
        report["false_failures"] += human_pass and not judge_pass
    write_json(storage / "audit/agreement.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run", "audit", "smoke"])
    parser.add_argument("--output", type=Path, default=ROOT / ".experiments")
    parser.add_argument("--manifest", type=Path, default=ROOT / "experiments/pilot.json")
    parser.add_argument("--task", help="Run only this task ID")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    storage = args.output.resolve()
    storage.mkdir(parents=True, exist_ok=True)
    agent = Codex(args.model, args.codex)
    if args.action == "audit":
        print(json.dumps(audit_agreement(storage), indent=2))
        return
    if args.action == "smoke":
        cwd = storage / "smoke/workspace"
        cwd.mkdir(parents=True, exist_ok=True)
        (cwd / "probe.txt").write_text("repository access works\n")
        outside = storage / "smoke/outside-probe.txt"
        outside.write_text("outside filesystem access works\n")
        # Test actual filesystem access directly, independently of model testimony.
        configured = codex_command(args.codex, args.model, cwd, storage / "smoke/session", False, [])
        sandbox_args = [args.codex, "sandbox", "-P", "experiment", "-C", str(cwd)]
        for index, value in enumerate(configured):
            if value == "-c" and configured[index + 1].startswith(("default_permissions=", "permissions.experiment=")):
                sandbox_args += ["-c", configured[index + 1]]
        sandbox_args += ["--", "/bin/cat", "probe.txt", str(outside)]
        probe = subprocess.run(sandbox_args, text=True, capture_output=True, env=clean_env())
        check = {"command": sandbox_args, "returncode": probe.returncode,
                 "stdout": probe.stdout, "stderr": probe.stderr}
        write_json(storage / "smoke/sandbox-check.json", check)
        validate_sandbox_check(check)
        schema = object_schema({"message": {"type": "string"}, "workspace_access": {"type": "boolean"}})
        prompt = ("Read probe.txt using the shell tool. Do not change files. Return message OK "
                  "and workspace_access true only if the tool actually read the file.")
        response = agent.run("smoke", prompt, cwd, storage / "smoke/session", schema)
        if response != {"message": "OK", "workspace_access": True}:
            raise RuntimeError(f"Model or filesystem isolation smoke test failed: {response}")
        validate_smoke_events(storage / "smoke/session/events.jsonl")
        print("Model and filesystem-access smoke test passed.")
        return
    tasks = read_json(args.manifest)
    if args.task:
        tasks = [task for task in tasks if task["id"] == args.task]
        if not tasks:
            parser.error("Unknown task ID")
    for task in tasks:
        print(f"Preparing {task['id']}", flush=True)
        prepared = prepare_task(task, storage)
        if args.action == "run":
            print(json.dumps(run_task(prepared, storage / "results" / task["id"], agent, categories_from_docs()), indent=2))
    if args.action == "run":
        make_audit(storage)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
