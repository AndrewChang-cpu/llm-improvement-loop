#!/usr/bin/env python3
"""Restore the persisted batch handoff after a Codex compaction."""
import json
from pathlib import Path
import sys


HANDOFF = Path(__file__).resolve().parents[2] / ".experiments/batch-100/handoff.md"


def main():
    content = HANDOFF.read_text() if HANDOFF.is_file() else "No FEA-Bench handoff is recorded yet."
    event = json.loads(sys.stdin.read() or "{}")
    if event.get("source") != "compact":
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "Persisted FEA-Bench batch state from before compaction:\n\n" + content,
    }}))


if __name__ == "__main__":
    main()
