#!/usr/bin/env bash
# Hourly health check: prints OK, or PROBLEM lines that need attention.
cd "$(dirname "$0")" || exit 1
problems=()
tmux has-session -t ollama 2>/dev/null || problems+=("ollama tmux session is gone")
curl -sf localhost:11434/api/tags >/dev/null || problems+=("ollama server not responding")
running=$(pgrep -fc "run_experiment.py run")
for log in /tmp/aechang/ghc-run.log; do
    [ -f "$log" ] || continue
    # Only the current ghc-run.sh attempt counts; earlier attempts' errors were already handled.
    current=$(awk '/=== .* ghc-run start/{buf=""} {buf=buf $0 "\n"} END{printf "%s", buf}' "$log")
    grep -qE "Traceback|Error:" <<< "$current" && problems+=("error in $log: $(grep -E 'Error' <<< "$current" | tail -1)")
done
for result in .experiments/*/results/*/result.json; do
    [ -f "$result" ] && echo "result: $result $(python3 -c "import json;print(json.load(open('$result'))['status'])")"
done
if [ "$running" -gt 0 ]; then
    newest=$(find .experiments -newermt "-60 minutes" -type f -not -path "*/tasks/*" 2>/dev/null | head -1)
    [ -n "$newest" ] || problems+=("runs active but no results file changed in 60 minutes")
elif ! grep -q "followup done" /tmp/aechang/ghc-run.log 2>/dev/null; then
    problems+=("no run_experiment process running and the follow-up has not finished")
fi
pgrep -f "claude_low_queue.py" >/dev/null && for status in .experiments/manual-*-ghc/queue-status.json; do
    [ -f "$status" ] || continue
    failed=$(python3 -c "import json;print(' '.join(k for k,v in json.load(open('$status')).items() if v['state']=='failed'))")
    [ -n "$failed" ] && problems+=("failed in $status: $failed")
done
if [ ${#problems[@]} -eq 0 ]; then echo "OK ($running runs active)"; else printf 'PROBLEM: %s\n' "${problems[@]}"; fi
