#!/usr/bin/env bash
# Hourly watcher for the Windows (WSL2) Codex queue, run by cron (see AGENTS.md, Windows).
# Runs the deterministic health check; only on PROBLEM, a headless Codex fixer investigates and
# resumes the queue. At most one fixer at a time and one per hour. FIXER_TEST=1 fakes a PROBLEM.
# Log: ~/llm-watch/watch.log. Settings: STATE (~/llm-watch), QUEUE_OUTPUT, CLOG.
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$PATH"
STATE=${STATE:-$HOME/llm-watch}
export QUEUE_OUTPUT=${QUEUE_OUTPUT:-.experiments/codex-low-windows} CLOG=${CLOG:-$PWD/queue.log}
mkdir -p "$STATE"
# The Windows queue command (AGENTS.md); the fixer restarts it with this.
RUN="BASE=$STATE GHC_TASKS=tasks/windows.txt GHC_OUTPUT=$QUEUE_OUTPUT BACKEND=codex MANIFEST=experiments/windows-100/runner-manifest.json ./ghc-run.sh claude 2>&1 | tee -a $CLOG; exec bash"
echo "=== $(date) watch"
health=$(BASE=$STATE bash ghc-health-check.sh 2>&1)
[ "${FIXER_TEST:-}" = 1 ] && health="PROBLEM: smoke test of the fixer path; there is no real problem"
grep -v '^result:' <<< "$health"
grep -q '^PROBLEM' <<< "$health" || exit 0
if [ "${FIXER_TEST:-}" != 1 ] && [ -f "$STATE/fixer.last" ] \
    && [ $(( $(date +%s) - $(cat "$STATE/fixer.last") )) -lt 3300 ]; then
    echo "fixer ran less than an hour ago; skipping"; exit 0
fi
mkdir "$STATE/fixer.lock" 2>/dev/null || { echo "another fixer is running; skipping"; exit 0; }
trap 'rmdir "$STATE/fixer.lock"' EXIT
[ "${FIXER_TEST:-}" = 1 ] || date +%s > "$STATE/fixer.last"
problems=$(grep '^PROBLEM' <<< "$health")
if [ "${FIXER_TEST:-}" = 1 ]; then
    prompt="Smoke test of the unattended fixer: $problems. Do not run any tools or change anything. Reply with exactly: fixer smoke ok"
else
    prompt="You are the unattended fixer for the Windows (WSL2) Codex queue: tmux session 'queue', log $CLOG, output $QUEUE_OUTPUT (see AGENTS.md, Windows). Health check reported: $problems. Investigate only that, fix per AGENTS.md rules (never alter or redo judgments; keep original model outputs), and resume the queue: tmux kill-session -t queue; tmux new-session -d -s queue \"$RUN\". Do not commit or push. Reply in under 100 words: cause, what you changed, current state."
fi
echo "fixer: $problems"
timeout 50m codex -a never exec --dangerously-bypass-approvals-and-sandbox "$prompt" < /dev/null 2>&1 | tail -20 | sed 's/^/fixer> /'
