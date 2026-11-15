#!/usr/bin/env python3
"""Select 100 FEA-Bench PRs not in batch-100 and write their runner manifest and environment specs.

Selection: every remaining instance of the eight shortlisted repositories (84), plus a seeded random
sample of instances from other repositories that SWE-bench gives its default environment
(Python 3.9, `pip install -e .`, `pytest -rA`). Environments reuse batch-100's validated install
lists for the same repository and version (the nearest version when none exists).
Output: experiments/windows-100/{selection.json, runner-manifest.json, environment-specs.json}.
"""
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / ".experiments/batch-100"
OUTPUT = ROOT / "experiments/windows-100"
SEED = 20261114
PILOTS = {"mwaskom__seaborn-3063", "sphinx-doc__sphinx-11989"}
SHORTLIST = {"scikit-learn/scikit-learn", "matplotlib/matplotlib", "boto/boto3", "scrapy/scrapy",
             "django/django", "mwaskom/seaborn", "pallets/flask", "sphinx-doc/sphinx"}
# The SWE-bench constants FEA-Bench patches; repositories missing from its map use the default.
SPECIFIED = {"astropy/astropy", "dbt-labs/dbt-core", "django/django", "matplotlib/matplotlib",
             "marshmallow-code/marshmallow", "mwaskom/seaborn", "pallets/flask", "psf/requests",
             "pvlib/pvlib-python", "pydata/xarray", "pydicom/pydicom", "pylint-dev/astroid",
             "pylint-dev/pylint", "pytest-dev/pytest", "pyvista/pyvista", "scikit-learn/scikit-learn",
             "sphinx-doc/sphinx", "sqlfluff/sqlfluff", "swe-bench/humaneval", "sympy/sympy",
             "huggingface/datasets", "huggingface/accelerate", "encode/django-rest-framework",
             "twisted/twisted", "Cog-Creators/Red-DiscordBot", "conan-io/conan", "pytorch/vision",
             "gradio-app/gradio", "tensorflow/datasets", "tortoise/tortoise-orm"}
DEFAULT = {"python": "3.9", "install": "pip install -e .", "pip_packages": ["pytest"], "test_cmd": "pytest -rA"}


def number(version):
    major, minor = (version or "0.0").split(".")[:2]
    return int(major) + int(minor) / 100


def django_label(test):
    # "test_x (module.Class)" or "test_x (module.Class.test_x)" -> module.Class.test_x
    match = re.fullmatch(r"(\S+) \((\S+)\)", test)
    if not match:
        return test
    name, owner = match.groups()
    return owner if owner.endswith("." + name) else f"{owner}.{name}"


def pytest_id(test):
    # Parametrized IDs with spaces cannot be passed as one argument; run the whole test function.
    return test.split("[")[0] if " " in test or test.count("[") != test.count("]") else test


def main():
    rows = json.loads((BATCH / "source/manifest-rows.json").read_text())
    manifest = json.loads((BATCH / "runner-manifest.json").read_text())
    specs = {spec["id"]: spec for spec in json.loads((BATCH / "environment-specs.json").read_text())}
    used = {task["id"] for task in manifest} | PILOTS
    templates = {}
    for task in manifest:
        templates.setdefault((task["repo"], specs[task["id"]]["version"]), task)
    pool = [row for row in rows if row["instance_id"] not in used]
    shortlisted = [row for row in pool if row["repo"] in SHORTLIST]
    others = sorted((row for row in pool if row["repo"] not in SPECIFIED | SHORTLIST), key=lambda row: row["instance_id"])
    chosen = {row["instance_id"] for row in shortlisted + random.Random(SEED).sample(others, 100 - len(shortlisted))}
    selected = [row for row in rows if row["instance_id"] in chosen]   # official dataset order

    tasks, environments = [], []
    for row in selected:
        tests = list(dict.fromkeys(row["FAIL_TO_PASS"] + row["PASS_TO_PASS"]))
        if row["repo"] in SHORTLIST:
            versions = [version for repo, version in templates if repo == row["repo"]]
            exact = row["version"] in versions
            version = row["version"] if exact else min(versions, key=lambda v: abs(number(v) - number(row["version"])))
            template = templates[(row["repo"], version)]
            prefix, official = template["candidate_check_prefix"], template["official_environment"]
            install, python = template["install"], template["python_version"]
            note = None if exact else f"install list of version {version} (no batch-100 task has {row['version']})"
        else:
            prefix, official = ["{python}", "-m", "pytest", "-rA"], DEFAULT
            install, python, note = [["pytest"], ["-e", "."]], "3.9", "SWE-bench default environment"
        labels = [django_label(t) if row["repo"] == "django/django" else pytest_id(t) for t in tests]
        # FEA-Bench names some Django tests by their docstring, which runtests.py cannot select.
        dropped = [label for label in labels if " " in label]
        if dropped:
            labels = [label for label in labels if " " not in label]
            note = "; ".join(filter(None, [note, f"{len(dropped)} docstring-named tests not run"]))
        task = {"id": row["instance_id"], "repo": row["repo"], "pr": row["pull_number"],
                "base_commit": row["base_commit"], "install": install,
                "checks": [prefix + list(dict.fromkeys(labels))], "test_files": [],
                "python_version": python, "official_test_command": official["test_cmd"],
                "official_environment": official, "environment_setup_commit": row["environment_setup_commit"],
                "feabench_tests": {"FAIL_TO_PASS": row["FAIL_TO_PASS"], "PASS_TO_PASS": row["PASS_TO_PASS"]},
                "candidate_check_prefix": prefix, "requirements": manifest[0]["requirements"]}
        if note:
            task["environment_note"] = note
        tasks.append(task)
        environments.append({"id": row["instance_id"], "repo": row["repo"], "version": row["version"],
                             "environment_setup_commit": row["environment_setup_commit"],
                             "official_spec": dict(official, python=python)})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "selection.json").write_text(json.dumps(
        {"seed": SEED, "method": __doc__.split("\n\n")[1], "dataset_revision": "55ee2f78126a3ecdeac6f595fa1ba6ae5c600bad",
         "excluded": "batch-100 and the two pilots", "ids": [row["instance_id"] for row in selected]}, indent=2) + "\n")
    (OUTPUT / "runner-manifest.json").write_text(json.dumps(tasks, indent=2) + "\n")
    (OUTPUT / "environment-specs.json").write_text(json.dumps(environments, indent=2) + "\n")
    print(f"{len(tasks)} tasks ({len(shortlisted)} shortlisted) written to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
