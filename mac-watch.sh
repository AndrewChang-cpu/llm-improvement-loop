#!/usr/bin/env bash
# Hourly check of the Mac queue, run by the launchd job (install-mac-jobs.sh copies it to
# ~/.local/share/llm-ghc). Runs the deterministic health check on the Mac queue; only on PROBLEM, it
# sends the problem to the supervising Orca session (terminal id in $STATE/supervisor-terminal), at most
# once per hour. NOTIFY_TEST=1 fakes a PROBLEM. Needs Full Disk Access for /bin/bash to read the repo in ~/Documents.
# Settings: REPO, QUEUE_OUTPUT (.experiments/manual-claude-low-v2), STATE (~/.local/share/llm-ghc/mac).
export PATH="/usr/local/bin:$HOME/.local/bin:/opt/homebrew/bin:$PATH"
cd "${REPO:?}" || exit 1
STATE=${STATE:-$HOME/.local/share/llm-ghc/mac}
export QUEUE_OUTPUT=${QUEUE_OUTPUT:-.experiments/manual-claude-low-v2}
export CLOG=$REPO/$QUEUE_OUTPUT/queue.log
mkdir -p "$STATE"
# The Mac queue command; the supervisor restarts it with this.
RUN="cd $REPO && nohup caffeinate -i python3.12 claude_low_queue.py --workers 3 --retry-failed --manifest experiments/feabench-1401/runner-manifest.json --tasks $QUEUE_OUTPUT/mac-tasks.txt --output $QUEUE_OUTPUT >> $CLOG 2>&1 &"
echo "$(date '+%F %T') mac queue"
health=$(BASE=$STATE bash ghc-health-check.sh 2>&1)
[ "${NOTIFY_TEST:-}" = 1 ] && health="PROBLEM: notification delivery test; no action required"
grep -v '^result:' <<< "$health"
grep -q '^PROBLEM' <<< "$health" || exit 0
mkdir "$STATE/notify.lock" 2>/dev/null || { echo "another notification is running; skipping"; exit 0; }
trap 'rmdir "$STATE/notify.lock"' EXIT
if [ "${NOTIFY_TEST:-}" != 1 ] && [ -f "$STATE/notify.last" ] \
    && [ $(( $(date +%s) - $(cat "$STATE/notify.last") )) -lt 3300 ]; then
    echo "notified less than an hour ago; skipping"; exit 0
fi
terminal=${SUPERVISOR_TERMINAL:-$(cat "$STATE/supervisor-terminal" 2>/dev/null)}
[ -n "$terminal" ] || { echo "ERROR: no supervising terminal configured in $STATE/supervisor-terminal"; exit 1; }
problems=$(grep '^PROBLEM' <<< "$health")
prompt="Hourly Mac queue health check: $problems. Investigate and fix in this existing session, following AGENTS.md (never alter or redo judgments). Resume the queue if it stopped: $RUN. Output: $QUEUE_OUTPUT; log: $CLOG."
[ "${NOTIFY_TEST:-}" = 1 ] && prompt="Mac watcher notification test: delivery to the existing supervisor works. No action needed; reply in one line."
echo "mac notify: $problems"
orca terminal send --terminal "$terminal" --text "$prompt" --enter --json || exit 1
[ "${NOTIFY_TEST:-}" = 1 ] || date +%s > "$STATE/notify.last"
