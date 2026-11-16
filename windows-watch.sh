#!/usr/bin/env bash
# Hourly deterministic health check; send problems to the existing supervising Orca session.
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.orca/cli/bin:$HOME/.local/bin:$PATH"
STATE=${STATE:-$HOME/llm-watch}
export QUEUE_OUTPUT=${QUEUE_OUTPUT:-.experiments/codex-low-windows} CLOG=${CLOG:-$PWD/queue.log}
mkdir -p "$STATE"
echo "=== $(date) watch"
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
prompt="Hourly Windows queue health check: $problems. Investigate and fix the loop/script in this existing session, following AGENTS.md. Preserve original judgments. Do not launch a separate fixer. Logs: $CLOG; output: $QUEUE_OUTPUT."
[ "${NOTIFY_TEST:-}" = 1 ] && prompt="Watcher notification test: delivery to the existing supervisor works. No separate fixer should run; continue the current task."
orca terminal send --terminal "$terminal" --text "$prompt" --enter --json || exit 1
[ "${NOTIFY_TEST:-}" = 1 ] || date +%s > "$STATE/notify.last"
