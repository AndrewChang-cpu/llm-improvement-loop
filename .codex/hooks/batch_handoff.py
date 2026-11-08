#!/usr/bin/env python3
"""Persist batch state before Codex automatically compacts this project's session."""
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / ".experiments/batch-100"


def active_lock():
    path = BATCH / "batch.lock"
    try:
        with path.open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(lock, fcntl.LOCK_UN)
    except OSError:
        return False
    return False


def main():
    BATCH.mkdir(parents=True, exist_ok=True)
    checkpoint = BATCH / "checkpoint.json"
    state = json.loads(checkpoint.read_text()) if checkpoint.is_file() else {}
    lock_held = active_lock()
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    handoff = {
        "saved_at": timestamp,
        "status": state.get("status", "not_started"),
        "manifest": state.get("manifest"),
        "active_task": state.get("active_task"),
        "next_action": state.get("next_action"),
        "automation_id": state.get("automation", {}).get("id"),
        "batch_lock_held": lock_held,
        "checkpoint_path": str(checkpoint),
    }
    content = "# Automatic compaction handoff\n\n" + json.dumps(handoff, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix="handoff-", dir=BATCH)
    with os.fdopen(fd, "w") as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, BATCH / "handoff.md")
    record = {**handoff, "handoff_sha256": hashlib.sha256(content.encode()).hexdigest()}
    with (BATCH / "compaction-events.jsonl").open("a") as events:
        events.write(json.dumps(record, sort_keys=True) + "\n")
        events.flush()
        os.fsync(events.fileno())
    event = json.loads(sys.stdin.read() or "{}")
    print(json.dumps({"continue": True, "systemMessage":
                      f"Saved FEA-Bench batch handoff before {event.get('trigger', 'automatic')} compaction."}))


if __name__ == "__main__":
    main()
