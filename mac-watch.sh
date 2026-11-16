#!/usr/bin/env bash
# Hourly check of the Mac queue, run by the launchd job (install-mac-jobs.sh copies it to
# ~/.local/share/llm-ghc). Runs the deterministic health check on the Mac queue; only on PROBLEM, a
# headless Claude fixer investigates and resumes it. At most one fixer at a time and one per hour.
# FIXER_TEST=1 fakes a PROBLEM. Needs Full Disk Access for /bin/bash to read the repo in ~/Documents.
# Settings: REPO, QUEUE_OUTPUT (.experiments/manual-claude-low-v2), STATE (~/.local/share/llm-ghc/mac).
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
cd "${REPO:?}" || exit 1
STATE=${STATE:-$HOME/.local/share/llm-ghc/mac}
export QUEUE_OUTPUT=${QUEUE_OUTPUT:-.experiments/manual-claude-low-v2}
export CLOG=$REPO/$QUEUE_OUTPUT/queue.log
mkdir -p "$STATE"
# The Mac queue command; the fixer restarts it with this.
RUN="cd $REPO && nohup caffeinate -i python3.12 claude_low_queue.py --workers 3 --retry-failed --manifest experiments/feabench-1401/runner-manifest.json --tasks $QUEUE_OUTPUT/mac-tasks.txt --output $QUEUE_OUTPUT >> $CLOG 2>&1 &"
echo "$(date '+%F %T') mac queue"
health=$(BASE=$STATE bash ghc-health-check.sh 2>&1)
[ "${FIXER_TEST:-}" = 1 ] && health="PROBLEM: smoke test of the fixer path; there is no real problem"
grep -v '^result:' <<< "$health"
grep -q '^PROBLEM' <<< "$health" || exit 0
if [ "${FIXER_TEST:-}" != 1 ] && [ -f "$STATE/fixer.last" ] \
    && [ $(( $(date +%s) - $(cat "$STATE/fixer.last") )) -lt 3300 ]; then
    echo "mac fixer ran less than an hour ago; skipping"; exit 0
fi
mkdir "$STATE/fixer.lock" 2>/dev/null || { echo "another mac fixer is running; skipping"; exit 0; }
trap 'rmdir "$STATE/fixer.lock"' EXIT
[ "${FIXER_TEST:-}" = 1 ] || date +%s > "$STATE/fixer.last"
problems=$(grep '^PROBLEM' <<< "$health")
if [ "${FIXER_TEST:-}" = 1 ]; then
    prompt="Smoke test of the unattended fixer: $problems. Do not run any tools or change anything. Reply with exactly: fixer smoke ok"
else
    prompt="You are the unattended fixer for the Mac experiment queue (output $QUEUE_OUTPUT, log $CLOG; see AGENTS.md). Health check reported: $problems. Investigate only that, fix per AGENTS.md rules (never alter or redo judgments; keep original model outputs), and resume the queue if it stopped: $RUN. Do not commit or push. Reply in under 100 words: cause, what you changed, current state."
fi
echo "mac fixer: $problems"
claude -p "$prompt" --no-session-persistence --permission-mode bypassPermissions < /dev/null 2>&1 | sed 's/^/mac fixer> /'
