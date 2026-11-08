#!/usr/bin/env python3
"""Resume the frozen FEA-Bench batch one PR at a time."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
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


class BatchCodex(runner.Codex):
    def run(self, role, prompt, cwd, output, *args, **kwargs):
        settings_path = next((parent / "settings.json" for parent in output.parents
                              if (parent / "settings.json").exists()), None)
        settings = runner.read_json(settings_path) if settings_path else {}
        if settings.get("task", {}).get("concise_test_output"):
            prompt += ("\n\nFor test commands, redirect full stdout/stderr to a unique temporary log "
                       "outside the repository (use mktemp). Initially display only the command's "
                       "exit status, log path, and last 40 lines. Preserve the test command's exit "
                       "status when displaying the tail. Read more of your own log when needed to "
                       "diagnose failures. Do not skip tests or change evaluation requirements.")
        return super().run(role, prompt, cwd, output, *args, **kwargs)


def save(path, value):
    runner.write_json(path, value)


def write_checkpoint(status, active_task=None, next_action=None):
    path = BATCH / "checkpoint.json"
    state = runner.read_json(path) if path.exists() else {}
    state.update(status=status, automation_enabled=False, heartbeat_epoch=time.time())
    state["active_task"] = active_task
    if next_action:
        state["next_action"] = next_action
    save(path, state)


def failure_details(error):
    details = str(error)
    if "Logs:" not in details:
        return details
    # Inspect the failed call itself, including failures during simplification.
    folder = Path(details.split("Logs:", 1)[1].splitlines()[0].strip())
    events = folder / "events.jsonl"
    errors = []
    if events.exists():
        for line in events.read_text(errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") in {"error", "turn.failed"}:
                errors.append(json.dumps(event))
    stderr = folder / "stderr.log"
    return details + "\n" + ("\n".join(errors) if errors else
                              stderr.read_text(errors="replace")[-12000:] if stderr.exists() else "")


def failure_kind(error, phase, task_dir=None):
    details = failure_details(error).lower()
    if any(term in details for term in TRANSIENT):
        return "waiting_retry"
    if any(term in details for term in AUTH):
        return "waiting_auth"
    if any(term in details for term in QUOTA):
        return "waiting_quota"
    if isinstance(error, (ValueError, FileNotFoundError)):
        return "experiment_error"
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


def finish_batch():
    state_path = BATCH / "checkpoint.json"
    state = runner.read_json(state_path)
    state.update(status="complete", automation_enabled=False, heartbeat_epoch=time.time(), active_task=None)
    save(state_path, state)


def quota_delay(details, now=None):
    now = time.time() if now is None else now
    match = re.search(r"try again at (\d{1,2}:\d{2})\s*(AM|PM)", details, re.IGNORECASE)
    if not match:
        return 3600
    clock = datetime.strptime(" ".join(match.groups()).upper(), "%I:%M %p")
    current = datetime.fromtimestamp(now)
    reset = current.replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)
    reset += timedelta(minutes=1)
    if reset <= current:
        reset += timedelta(days=1)
    return reset.timestamp() - now


def wait_for_retry(state, network_retries):
    if state["status"] == "waiting_quota":
        delay = quota_delay(state["failures"][-1]["details"])
    else:
        delay = (60, 300, 900)[min(network_retries, 2)]
    deadline = time.time() + delay
    checkpoint = runner.read_json(BATCH / "checkpoint.json")
    checkpoint["retry_at_epoch"] = deadline
    save(BATCH / "checkpoint.json", checkpoint)
    print(f"{state['id']}: {state['status']}; retry at {time.ctime(deadline)}. "
          "Ctrl+C pauses safely.", flush=True)
    # Keep the batch lock while sleeping; no supervisor or extra model call is needed.
    while time.time() < deadline:
        time.sleep(min(60, max(0, deadline - time.time())))


def archive_partial_generations(task_id):
    folders = list((BATCH / "results" / task_id).glob("revision-*/run-*/generation"))
    folders += list((BATCH / "simplification" / task_id).glob("round-*/candidate-*/run-*/generation"))
    for folder in folders:
        if (folder / "complete.json").exists() or not (folder / "events.jsonl").exists():
            continue
        generated = folder.parent / "generated"
        runner.archive_incomplete_call(folder)
        archive = sorted((folder / "incomplete-attempts").iterdir())[-1]
        if not (generated / ".git").exists():
            continue
        diff = subprocess.run(["git", "diff", "HEAD", "--binary"], cwd=generated,
                              capture_output=True, check=True).stdout
        (archive / "partial-patch.diff").write_bytes(diff)
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"],
                                   cwd=generated, capture_output=True, check=True).stdout
        for name in untracked.decode().split("\0"):
            if name:
                target = archive / "untracked" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(generated / name, target, follow_symlinks=False)


def update_html():
    if not list((BATCH / "results").glob("*/revision-*/specification.md")):
        return
    args = [sys.executable, str(ROOT / "view_experiment.py"), str(BATCH),
            "--output", str(BATCH / "evaluation.html")]
    if list((BATCH / "simplification").glob("*/settings.json")):
        args += ["--simplification", str(BATCH / "simplification")]
    subprocess.run(args, check=True)


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
    console = sys.stdout
    print(f"{task_id}: preparing (attempt {state['attempts']}); log: {log_path}",
          file=console, flush=True)
    phase = "prepare"
    try:
        with log_path.open("a") as log, redirect_stdout(log), redirect_stderr(log):
            print(f"\n=== attempt {state['attempts']} {task_id} {time.ctime()} ===", flush=True)
            archive_partial_generations(task_id)
            prepared = runner.prepare_task(task, BATCH)
            phase = "experiment"
            state.update(status="running", updated_at=time.time(), phase=phase)
            save(state_path, state)
            write_checkpoint("running", task_id, f"run {task_id}")
            print(f"{task_id}: running refinement loop", file=console, flush=True)
            result_dir = BATCH / "results" / task_id
            # Retain the prompt policy of an already-started task when resuming it.
            saved_settings = result_dir / "settings.json"
            if saved_settings.exists():
                if runner.read_json(saved_settings)["task"].get("concise_test_output"):
                    prepared["concise_test_output"] = True
            else:
                prepared["concise_test_output"] = True
            result = runner.run_task(prepared, result_dir, agent, categories)
            if result["status"] == "converged":
                write_checkpoint("simplifying", task_id, f"simplify {task_id}")
                print(f"{task_id}: converged; running simplification loop", file=console, flush=True)
                simplify_result = simplify_specifications.simplify(
                    result_dir, BATCH / "simplification" / task_id, agent.executable)
                result["simplification_status"] = simplify_result["status"]
            state.update(status=result["status"], result=result, updated_at=time.time(), phase=None)
            save(state_path, state)
            return state
    except Exception as error:
        kind = failure_kind(error, phase)
        fingerprint = error_fingerprint(error)
        history = state.get("failures", [])
        repeats = sum(item.get("fingerprint") == fingerprint for item in history) + 1
        history.append({"at": time.time(), "phase": phase, "kind": kind,
                        "fingerprint": fingerprint, "error": str(error),
                        "details": failure_details(error),
                        "traceback": traceback.format_exc()[-12000:]})
        if kind == "prep_failed_permanent":
            status = kind
        elif kind in {"waiting_quota", "waiting_retry", "waiting_auth"}:
            status = kind
        else:
            status = "experiment_error"
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
    parser.add_argument("--auto-retry", action="store_true", help="Wait and resume on quota or temporary network errors")
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
        # Share the adapter with simplification without changing the pinned runner source.
        runner.Codex = BatchCodex
        agent = runner.Codex(args.model, args.codex)
        categories = runner.categories_from_docs()
        active_task = None
        try:
            update_html()
            for position, task in enumerate(tasks, 1):
                active_task = task["id"]
                task_state_path = BATCH / "task-state" / task["id"] / "state.json"
                if task_state_path.exists() and runner.read_json(task_state_path).get("status") in TERMINAL:
                    continue
                network_retries = 0
                while True:
                    print(f"[{position}/{len(tasks)}] {task['id']}", flush=True)
                    state = run_task(task, agent, categories)
                    summary(tasks)
                    if state["status"] in TERMINAL:
                        update_html()
                        print(f"Finished {task['id']}: {state['status']}", flush=True)
                        break
                    retryable = state["status"] in {"waiting_quota", "waiting_retry"}
                    if args.auto_retry and retryable:
                        wait_for_retry(state, network_retries)
                        network_retries += state["status"] == "waiting_retry"
                        continue
                    print(f"Paused at {task['id']} ({state['status']}); "
                          f"see {task_state_path}. Completed calls remain saved.", flush=True)
                    return 0 if retryable else 1
                if args.one_task:
                    return 0
        except KeyboardInterrupt:
            write_checkpoint("paused", active_task, "Rerun batch_driver.py --auto-retry to resume")
            summary(tasks)
            print("Paused. Completed calls are saved; rerun the same command to resume.", flush=True)
            return 130
        results = summary(tasks)
        if all(value in TERMINAL for value in results.values()):
            finish_batch()
        else:
            write_checkpoint("running", None, "resume next nonterminal task")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
