#!/usr/bin/env python3
"""Run the Claude PRs from experiment-commands.txt at low effort, three features at a time.

Each feature refines its specification and, when it converges, simplifies it. After a feature
finishes simplification, its repository copies are deleted and every result file is kept.
Non-convergent or failed features keep all intermediate files. Rerunning skips finished features
and resumes unfinished ones.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / ".experiments/manual-claude-low-v2"
MANIFEST = ".experiments/batch-100/runner-manifest.json"
SPECS = ROOT / ".experiments/batch-100/environment-specs.json"
MIN_FREE_GB = 30
REPO_COPIES = {"generated", "evaluation", "candidate-test-tmp"}
status_lock = threading.Lock()
API_WAIT_SECONDS = 600


def api_unavailable(output):
    # A Claude call that ended on a usage limit or API/auth error is retried after a wait.
    failure = re.search(r"claude failed \(\d+\); resume after resolving the error\. Logs: (\S+)", output)
    if not failure:
        return False
    logs = Path(failure[1])
    events = (logs / "events.jsonl").read_text(errors="replace").splitlines() if (logs / "events.jsonl").exists() else []
    results = [event for line in events if '"type":"result"' in line for event in [json.loads(line)] if event.get("type") == "result"]
    final = results[-1] if results else {}
    stderr = (logs / "stderr.log").read_text(errors="replace") if (logs / "stderr.log").exists() else ""
    message = (str(final.get("result", "")) if final.get("is_error") else "") + stderr
    return (final.get("terminal_reason") == "api_error"
            or bool(re.search(r"hit your .*limit|\b40[13]\b|log ?in|authenticat", message, re.I)))


def claude_tasks():
    lines = (ROOT / "experiment-commands.txt").read_text().splitlines()
    start = lines.index("# Remaining PRs using Claude")
    return [line.split("--task ")[1].split()[0] for line in lines[start:]
            if line.startswith("python3 run_experiment.py run") and "--backend claude" in line]


def python_for(task):
    # Use the benchmark's Python, or the oldest one available here when that is unavailable.
    spec = next(s for s in json.loads(SPECS.read_text()) if s["id"] == task)
    version = spec["official_spec"]["python"]
    if tuple(map(int, version.split("."))) < (3, 8):
        version = "3.8"
    subprocess.run(["uv", "python", "install", version], capture_output=True)
    return subprocess.run(["uv", "python", "find", version], capture_output=True, text=True,
                          check=True).stdout.strip()


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def update(task, **fields):
    with status_lock:
        path = OUTPUT / "queue-status.json"
        status = read(path) or {}
        status[task] = dict(status.get(task, {}), **fields, updated=datetime.now().isoformat(timespec="seconds"))
        path.write_text(json.dumps(status, indent=2) + "\n")


def clean(task):
    for folder in (OUTPUT / "results" / task, OUTPUT / "simplification" / task):
        for path in sorted(folder.rglob("*"), reverse=True):
            if path.is_dir() and path.name in REPO_COPIES:
                shutil.rmtree(path)
    shutil.rmtree(OUTPUT / "tasks" / task, ignore_errors=True)


def wait_for_disk(task):
    while shutil.disk_usage(OUTPUT).free < MIN_FREE_GB * 1024 ** 3:
        update(task, state="waiting_for_disk")
        time.sleep(300)


def run_feature(task):
    result = OUTPUT / "results" / task / "result.json"
    simplified = OUTPUT / "simplification" / task / "result.json"
    log = OUTPUT / f"{task}.log"
    python = python_for(task)
    env = dict(os.environ)
    if task.startswith("matplotlib__"):
        # Old bundled FreeType builds on macOS only against the system zlib.
        env.update(CFLAGS="-DFT_CONFIG_OPTION_SYSTEM_ZLIB", LDFLAGS="-lz")
    steps = [("refining", [python, "run_experiment.py", "run", "--backend", "claude", "--effort", "low",
                           "--manifest", MANIFEST, "--task", task, "--output", str(OUTPUT)]),
             ("simplifying", [python, "simplify_specifications.py", str(OUTPUT / "results" / task),
                              "--output", str(OUTPUT / "simplification")])]
    for state, command in steps:
        if state == "simplifying" and (read(result) or {}).get("status") != "converged":
            update(task, state=(read(result) or {}).get("status", "failed"), detail="kept intermediate files")
            return
        if state == "simplifying" and simplified.exists():
            break
        wait_for_disk(task)
        while True:
            update(task, state=state, python=python)
            start = log.stat().st_size if log.exists() else 0
            with log.open("a") as out:
                out.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} {state} ===\n")
                out.flush()
                code = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT).returncode
            with log.open() as out:
                out.seek(start)
                if not code or not api_unavailable(out.read()):
                    break
            update(task, state="waiting_for_api", detail=f"Claude unavailable; retrying {state} in {API_WAIT_SECONDS}s")
            time.sleep(API_WAIT_SECONDS)
        if code:
            update(task, state="failed", detail=f"{state} exited {code}; see {log.name}")
            return
    clean(task)
    update(task, state="done", detail=(read(simplified) or {}).get("status", "simplified"))


def task_list(value):
    # A comma-separated list of tasks, or a file with one task per line.
    path = Path(value)
    names = path.read_text().split() if path.is_file() else value.split(",")
    return {name for name in names if name}


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--retry-failed", action="store_true", help="Also resume features that failed before")
    parser.add_argument("--tasks", type=task_list, help="Run only these tasks (comma-separated or a file)")
    parser.add_argument("--exclude", type=task_list, default=set(), help="Skip these tasks (comma-separated or a file)")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    OUTPUT = args.output.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    previous = read(OUTPUT / "queue-status.json") or {}
    skip = {"done", "non_convergent"} | (set() if args.retry_failed else {"failed"})
    tasks = [t for t in claude_tasks() if previous.get(t, {}).get("state") not in skip
             and (args.tasks is None or t in args.tasks) and t not in args.exclude]
    for task in tasks:
        update(task, state="queued")
    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(run_safely, tasks))


def run_safely(task):
    try:
        run_feature(task)
    except Exception as error:  # Record the failure and keep the queue moving.
        update(task, state="failed", detail=repr(error))


if __name__ == "__main__":
    main()
