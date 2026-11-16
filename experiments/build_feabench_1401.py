#!/usr/bin/env python3
"""Write one runner manifest for all 1,401 FEA-Bench PRs and split them across the five task lists.

Manifest: entries already in batch-100, windows-100, windows-200 or mac-100 are copied unchanged, so
started features keep resuming; every other PR gets an entry built as in build_windows_100.py.
Task lists: each tasks/*.txt keeps the PRs it already lists (never move a started task); the rest,
shuffled with a fixed seed, fill the five lists to equal size. Their union is all 1,401 PRs and no PR
is in two lists.
Output: experiments/feabench-1401/{runner-manifest.json, environment-specs.json}; tasks/*.txt.
"""
import json
from pathlib import Path
import random

import build_windows_100 as builder

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments/feabench-1401"
# mac-100 before windows-200: the seven MONAI PRs moved to mac-100 use its entries.
SOURCES = [builder.BATCH, ROOT / "experiments/windows-100", ROOT / "experiments/mac-100", ROOT / "experiments/windows-200"]
LISTS = ["ghc", "mac", "mac-100", "windows", "windows-200"]
SEED = 20261116


def task_ids(path):
    return [line.split("#")[0].strip() for line in path.read_text().splitlines() if line.split("#")[0].strip()]


def main():
    rows = json.loads((builder.BATCH / "source/manifest-rows.json").read_text())
    batch = json.loads((builder.BATCH / "runner-manifest.json").read_text())
    batch_specs = {spec["id"]: spec for spec in json.loads((builder.BATCH / "environment-specs.json").read_text())}
    templates = {}
    for task in batch:
        templates.setdefault((task["repo"], batch_specs[task["id"]]["version"]), task)
    existing, specs = {}, {}
    for source in SOURCES:
        for task in json.loads((source / "runner-manifest.json").read_text()):
            existing.setdefault(task["id"], task)
        for spec in json.loads((source / "environment-specs.json").read_text()):
            specs.setdefault(spec["id"], spec)
    tasks, environments = [], []
    for row in rows:   # official dataset order
        task, environment = builder.entry(row, templates, batch)
        tasks.append(existing.get(row["instance_id"], task))
        environments.append(specs.get(row["instance_id"], environment))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "runner-manifest.json").write_text(json.dumps(tasks, indent=2) + "\n")
    (OUTPUT / "environment-specs.json").write_text(json.dumps(environments, indent=2) + "\n")

    paths = {name: ROOT / f"tasks/{name}.txt" for name in LISTS}
    assigned = {name: task_ids(path) for name, path in paths.items()}
    taken = {task for ids in assigned.values() for task in ids}
    rest = sorted(row["instance_id"] for row in rows if row["instance_id"] not in taken)
    random.Random(SEED).shuffle(rest)
    added = {name: [] for name in LISTS}
    for task in rest:
        name = min(LISTS, key=lambda n: (len(assigned[n]) + len(added[n]), LISTS.index(n)))
        added[name].append(task)
    for name, path in paths.items():
        if added[name]:
            text = path.read_text().rstrip("\n") + "\n# Added by experiments/build_feabench_1401.py " \
                   "(manifest experiments/feabench-1401/runner-manifest.json):\n" + "\n".join(added[name]) + "\n"
            path.write_text(text)
    final = {name: task_ids(path) for name, path in paths.items()}
    union = [task for ids in final.values() for task in ids]
    assert len(union) == len(set(union)) == len(rows), "task lists must partition FEA-Bench"
    print({name: len(ids) for name, ids in final.items()}, f"{len(tasks)} tasks in {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
