#!/usr/bin/env python3
"""Allow an hourly recovery run only for a ready, idle, incomplete batch."""
import argparse
import datetime as dt
import fcntl
import json
from pathlib import Path
import sys
import time


def should_run(state_path, lock_path, now=None, max_idle_seconds=3600):
    if not state_path.is_file():
        return False
    state = json.loads(state_path.read_text())
    if not state.get("automation_enabled") or state.get("status") in {"complete", "cancelled"}:
        return False
    try:
        with lock_path.open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            fcntl.flock(lock, fcntl.LOCK_UN)
    except OSError:
        return False
    if state["status"] == "waiting_quota":
        return True
    heartbeat = state.get("heartbeat_epoch")
    return heartbeat is None or (now or time.time()) - heartbeat >= max_idle_seconds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--max-idle-seconds", type=int, default=3600)
    args = parser.parse_args()
    if should_run(args.state, args.lock, max_idle_seconds=args.max_idle_seconds):
        return 0
    print("batch is disabled, terminal, or already active", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
