#!/usr/bin/env python3
"""Reduce judged runs' repository copies to patch.diff, archiving trees their patch cannot rebuild."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import threading

import run_experiment as runner

COPIES = {"generated", "evaluation", "candidate-test-tmp", "rebuild-check", "materializing"}
log_lock = threading.Lock()


def judged_runs(root):
    # Yield (task, run) for runs with a verdict, without walking into repository copies.
    tasks = {}
    for directory, dirs, files in os.walk(root):
        path = Path(directory)
        dirs[:] = sorted(name for name in dirs if name not in COPIES and name != "tasks")
        if "settings.json" in files:
            settings = runner.read_json(path / "settings.json")
            if "task" in settings:
                tasks[path] = settings["task"]
        if path.name.startswith("run-") and "verdict.json" in files and "patch.diff" in files:
            owner = next(p for p in path.parents if p in tasks)
            yield tasks[owner], path


def retire(task, run, log):
    result = {"run": str(run), "generated": runner.retire_workspace(task, run)}
    # checks.json is the durable record of the evaluation copy.
    for name in ("evaluation", "candidate-test-tmp"):
        if (run / name).exists() and (run / "checks.json").exists():
            shutil.rmtree(run / name)
            result[name] = "deleted"
    with log_lock, log.open("a") as out:
        out.write(json.dumps(result) + "\n")
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root = args.root.resolve()
    log = root / "retire-workspaces.jsonl"
    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(lambda item: retire(*item, log), list(judged_runs(root))))


if __name__ == "__main__":
    main()
