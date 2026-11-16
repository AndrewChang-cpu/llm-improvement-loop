#!/usr/bin/env python3
"""Select the next 100 FEA-Bench PRs not in batch-100, windows-100, or the two pilots.

Selection: a seeded uniform random sample of all FEA-Bench instances outside batch-100, windows-100,
and the two pilots. Repositories batch-100 covers reuse its validated install lists for the same
version (the nearest version when none exists); others get SWE-bench's environment for the
repository and version (its default, Python 3.9 with `pip install -e .` and `pytest -rA`, when it
has none), converted to pip.
Output: experiments/windows-200/{selection.json, runner-manifest.json, environment-specs.json}.
"""
import json
from pathlib import Path
import random
import re
import runpy
import shlex

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / ".experiments/batch-100"
WIN100 = ROOT / "experiments/windows-100"
OUTPUT = ROOT / "experiments/windows-200"
SEED = 20261116
PILOTS = {"mwaskom__seaborn-3063", "sphinx-doc__sphinx-11989"}
SWEBENCH = runpy.run_path(str(BATCH / "source/swebench-python-constants.py"))


def number(version):
    major, minor = (version or "0.0").split(".")[:2]
    return int(major) + int(minor) / 100


def swebench_environment(row):
    """SWE-bench's spec for the row's repository and version, as pip install lists and a check prefix."""
    specs = SWEBENCH["MAP_REPO_VERSION_TO_SPECS_PY"]
    by_version = specs.get(row["repo"], specs["default"])
    spec = by_version[row["version"]] if row["version"] in by_version else by_version[sorted(
        (v for v in by_version if v not in (None, "default")), key=lambda v: abs(number(v) - number(row["version"])))[0]]
    packages = spec.get("packages", "")
    first = shlex.split(packages) if packages not in ("", "requirements.txt", "environment.yml") else []
    install = [first + [shlex.split(p)[0] for p in spec.get("pip_packages", [])]]
    if packages == "requirements.txt":
        install.append(["-r", SWEBENCH["MAP_REPO_TO_REQS_PATHS"][row["repo"]][0]])
    for step in spec["install"].split(";"):
        words = shlex.split(step)
        install.append(words[words.index("install") + 1:])
    test = shlex.split(spec["test_cmd"])
    prefix = ["{python}", "-m"] + test if test[0] == "pytest" else ["{python}", "-m", "pytest", "-rA"]
    return [step for step in install if step], prefix, spec


def django_label(test):
    match = re.fullmatch(r"(\S+) \((\S+)\)", test)
    if not match:
        return test
    name, owner = match.groups()
    return owner if owner.endswith("." + name) else f"{owner}.{name}"


def pytest_id(test):
    return test.split("[")[0] if " " in test or test.count("[") != test.count("]") else test


def main():
    rows = json.loads((BATCH / "source/manifest-rows.json").read_text())
    manifest = json.loads((BATCH / "runner-manifest.json").read_text())
    specs = {spec["id"]: spec for spec in json.loads((BATCH / "environment-specs.json").read_text())}
    win100_ids = {t["id"] for t in json.loads((WIN100 / "runner-manifest.json").read_text())}
    used = {task["id"] for task in manifest} | PILOTS | win100_ids
    templates = {}
    for task in manifest:
        templates.setdefault((task["repo"], specs[task["id"]]["version"]), task)
    pool = sorted((row for row in rows if row["instance_id"] not in used), key=lambda row: row["instance_id"])
    chosen = {row["instance_id"] for row in random.Random(SEED).sample(pool, 100)}
    selected = [row for row in rows if row["instance_id"] in chosen]

    tasks, environments = [], []
    for row in selected:
        tests = list(dict.fromkeys(row["FAIL_TO_PASS"] + row["PASS_TO_PASS"]))
        if any(repo == row["repo"] for repo, _ in templates):
            versions = [version for repo, version in templates if repo == row["repo"]]
            exact = row["version"] in versions
            version = row["version"] if exact else min(versions, key=lambda v: abs(number(v) - number(row["version"])))
            template = templates[(row["repo"], version)]
            prefix, official = template["candidate_check_prefix"], template["official_environment"]
            install, python = template["install"], template["python_version"]
            note = None if exact else f"install list of version {version} (no batch-100 task has {row['version']})"
        else:
            install, prefix, official = swebench_environment(row)
            python = official["python"]
            note = "SWE-bench environment converted to pip" + ("; pre_install steps skipped" if official.get("pre_install") else "")
        if row["repo"] == "django/django":
            labels = [django_label(t) for t in tests]
        elif row["repo"] == "sympy/sympy":
            labels = []
        else:
            labels = [pytest_id(t) for t in tests if "::" in t]
        dropped = [label for label in labels if " " in label]
        if dropped:
            labels = [label for label in labels if " " not in label]
            note = "; ".join(filter(None, [note, f"{len(dropped)} docstring-named tests not run"]))
        task = {"id": row["instance_id"], "repo": row["repo"], "pr": row["pull_number"],
                "base_commit": row["base_commit"], "install": install,
                "checks": [prefix + (["-k", " or ".join(tests), "sympy"] if row["repo"] == "sympy/sympy"
                                     else list(dict.fromkeys(labels)))], "test_files": [],
                "python_version": python, "official_test_command": official["test_cmd"],
                "official_environment": official, "environment_setup_commit": row["environment_setup_commit"],
                "feabench_tests": {"FAIL_TO_PASS": row["FAIL_TO_PASS"], "PASS_TO_PASS": row["PASS_TO_PASS"]},
                "candidate_check_prefix": prefix, "requirements": manifest[0]["requirements"]}
        if row["repo"] == "sympy/sympy":
            note = (note + "; " if note else "") + "tests selected by name with pytest -k (substring match) instead of bin/test"
        if note:
            task["environment_note"] = note
        tasks.append(task)
        environments.append({"id": row["instance_id"], "repo": row["repo"], "version": row["version"],
                             "environment_setup_commit": row["environment_setup_commit"],
                             "official_spec": dict(official, python=python)})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "selection.json").write_text(json.dumps(
        {"seed": SEED, "method": __doc__.split("\n\n")[1], "dataset_revision": "55ee2f78126a3ecdeac6f595fa1ba6ae5c600bad",
         "excluded": "batch-100, windows-100, and the two pilots", "ids": [row["instance_id"] for row in selected]}, indent=2) + "\n")
    (OUTPUT / "runner-manifest.json").write_text(json.dumps(tasks, indent=2) + "\n")
    (OUTPUT / "environment-specs.json").write_text(json.dumps(environments, indent=2) + "\n")
    print(f"{len(tasks)} tasks written to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
