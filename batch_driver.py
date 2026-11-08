#!/usr/bin/env python3
"""Resume the frozen FEA-Bench batch one PR at a time."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

import run_experiment as runner
import simplify_specifications


ROOT = Path(__file__).resolve().parent
BATCH = ROOT / ".experiments/batch-100"
TERMINAL = {"converged", "non_convergent", "prep_failed_permanent", "experiment_error_terminal"}
TRANSIENT = ("connection reset", "connectionerror", "temporary failure", "name resolution",
             "timed out", "timeout", "network is unreachable", "bad gateway", "service unavailable",
             "api rate limit exceeded", "secondary rate limit", "http error 502", "http error 503")
QUOTA = ("usage limit", "quota", "rate_limit", "rate limit", "too many requests", "http error 429")
AUTH = ("unauthorized", "authentication failed", "not authenticated", "login expired", "token expired")


def save(path, value):
    runner.write_json(path, value)


def write_checkpoint(status, active_task=None, next_action=None):
    path = BATCH / "checkpoint.json"
    state = runner.read_json(path) if path.exists() else {}
    state.update(status=status, automation_enabled=status != "complete", heartbeat_epoch=time.time())
    state["active_task"] = active_task
    if next_action:
        state["next_action"] = next_action
    save(path, state)


def latest_call_logs(task_dir):
    candidates = list(task_dir.rglob("stderr.log")) + list(task_dir.rglob("events.jsonl"))
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return "\n".join(path.read_text(errors="replace")[-12000:]
                     for path in candidates[:4] if path.is_file())


def failure_kind(error, phase, task_dir):
    details = f"{type(error).__name__}: {error}\n{latest_call_logs(task_dir)}".lower()
    if any(term in details for term in QUOTA):
        return "waiting_quota"
    if any(term in details for term in TRANSIENT):
        return "waiting_retry"
    if any(term in details for term in AUTH):
        return "waiting_auth"
    if phase == "prepare":
        return "prep_failed_permanent"
    return "experiment_error"


def error_fingerprint(error):
    message = str(error).split("Logs:", 1)[0]
    return hashlib.sha256((type(error).__name__ + ":" + message).encode()).hexdigest()


def install_read_only_github_auth():
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or not shutil.which("gh"):
        return
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        os.environ["GH_TOKEN"] = result.stdout.strip()


def finish_automation():
    state_path = BATCH / "checkpoint.json"
    state = runner.read_json(state_path)
    state.update(status="complete", automation_enabled=False, heartbeat_epoch=time.time(), active_task=None)
    save(state_path, state)
    automation = state.get("automation", {}).get("id")
    if automation and shutil.which("orca"):
        subprocess.run(["orca", "automations", "edit", automation, "--disabled", "--json"],
                       capture_output=True, text=True)


def run_task(task, agent, categories):
    task_id = task["id"]
    task_root = BATCH / "task-state" / task_id
    task_root.mkdir(parents=True, exist_ok=True)
    state_path = task_root / "state.json"
    state = runner.read_json(state_path) if state_path.exists() else {"id": task_id, "attempts": 0}
    if state.get("status") in TERMINAL:
        return state
    state.update(status="preparing", attempts=state.get("attempts", 0) + 1,
                 updated_at=time.time(), error=None)
    save(state_path, state)
    write_checkpoint("preparing", task_id, f"prepare {task_id}")
    log_path = task_root / "attempts.log"
    phase = "prepare"
    try:
        with log_path.open("a") as log, redirect_stdout(log), redirect_stderr(log):
            print(f"\n=== attempt {state['attempts']} {task_id} {time.ctime()} ===", flush=True)
            prepared = runner.prepare_task(task, BATCH)
            phase = "experiment"
            state.update(status="running", updated_at=time.time(), phase=phase)
            save(state_path, state)
            write_checkpoint("running", task_id, f"run {task_id}")
            result_dir = BATCH / "results" / task_id
            result = runner.run_task(prepared, result_dir, agent, categories)
            if result["status"] == "converged":
                write_checkpoint("simplifying", task_id, f"simplify {task_id}")
                simplify_result = simplify_specifications.simplify(
                    result_dir, BATCH / "simplification" / task_id, agent.executable)
                result["simplification_status"] = simplify_result["status"]
            state.update(status=result["status"], result=result, updated_at=time.time(), phase=None)
            save(state_path, state)
            return state
    except Exception as error:
        kind = failure_kind(error, phase, BATCH / "results" / task_id)
        fingerprint = error_fingerprint(error)
        history = state.get("failures", [])
        repeats = sum(item.get("fingerprint") == fingerprint for item in history) + 1
        history.append({"at": time.time(), "phase": phase, "kind": kind,
                        "fingerprint": fingerprint, "error": str(error),
                        "traceback": traceback.format_exc()[-12000:]})
        if kind == "prep_failed_permanent":
            status = kind
        elif kind in {"waiting_quota", "waiting_retry", "waiting_auth"}:
            status = kind
        elif repeats >= 3:
            status = "experiment_error_terminal"
        else:
            status = "waiting_retry"
        state.update(status=status, phase=phase, failures=history,
                     updated_at=time.time(), repeated_failure_count=repeats)
        save(state_path, state)
        write_checkpoint(status, task_id, f"retry or inspect {task_id}")
        return state


def summary(tasks):
    results = {}
    for task in tasks:
        path = BATCH / "task-state" / task["id"] / "state.json"
        status = runner.read_json(path).get("status", "pending") if path.exists() else "pending"
        results[task["id"]] = status
    save(BATCH / "summary.json", {
        "selected": len(tasks), "terminal": sum(status in TERMINAL for status in results.values()),
        "statuses": {status: sum(value == status for value in results.values())
                     for status in sorted(set(results.values()))},
        "tasks": results,
    })
    return results


def validate_manifest(tasks):
    ids = [task["id"] for task in tasks]
    if len(ids) != 100 or len(set(ids)) != 100:
        raise ValueError("Frozen runner manifest must contain exactly 100 unique task IDs")
    if set(ids) & {"sphinx-doc__sphinx-11989", "mwaskom__seaborn-3063"}:
        raise ValueError("The pilot tasks must not be rerun")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=BATCH / "runner-manifest.json")
    parser.add_argument("--one-task", action="store_true", help="Stop after one selected task")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    tasks = runner.read_json(args.manifest)
    validate_manifest(tasks)
    install_read_only_github_auth()
    lock_path = BATCH / "batch.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another batch driver owns the lock; no work started.", file=sys.stderr)
            return 2
        agent = runner.Codex(args.model, args.codex)
        categories = runner.categories_from_docs()
        for task in tasks:
            task_state_path = BATCH / "task-state" / task["id"] / "state.json"
            if task_state_path.exists() and runner.read_json(task_state_path).get("status") in TERMINAL:
                continue
            state = run_task(task, agent, categories)
            results = summary(tasks)
            if state["status"] in {"waiting_quota", "waiting_retry", "waiting_auth"}:
                print(f"Paused at {task['id']} ({state['status']}); completed calls remain saved.", flush=True)
                return 0
            if args.one_task:
                return 0
            if all(value in TERMINAL for value in results.values()):
                finish_automation()
                break
        results = summary(tasks)
        if all(value in TERMINAL for value in results.values()):
            finish_automation()
        else:
            write_checkpoint("running", None, "resume next nonterminal task")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
