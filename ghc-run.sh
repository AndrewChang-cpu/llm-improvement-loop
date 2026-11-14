#!/usr/bin/env bash
# The GHC plan: finish (or resume) the Qwen run on pilot sphinx-11989. If it converges, run the GHC
# tasks with Qwen (1 worker); otherwise run them with the normal Claude setup, 3 features at a time.
# Safe to rerun: a finished stage is skipped (the Qwen result.json exists, the queue skips done
# features), and an unfinished one resumes. Logs "followup done" when all of it has finished.
cd "$(dirname "$0")" && . /tmp/aechang/env.sh
echo "=== $(date) ghc-run start"
Q=.experiments/qwen-sphinx-11989/results/sphinx-doc__sphinx-11989/result.json
[ -f "$Q" ] || python3.12 run_experiment.py run --backend ollama --judge-backend claude --effort low \
    --codex /tmp/aechang/bin/codex --task sphinx-doc__sphinx-11989 --output .experiments/qwen-sphinx-11989
status=$(python3 -c "import json;print(json.load(open('$Q'))['status'])" 2>/dev/null || echo missing)
echo "$(date) qwen status: $status"
case "$status" in
    converged) python3.12 claude_low_queue.py --workers 1 --retry-failed --generator qwen \
                   --tasks ghc-tasks.txt --output .experiments/manual-qwen-ghc ;;
    non_convergent) python3.12 claude_low_queue.py --workers 3 --retry-failed \
                   --tasks ghc-tasks.txt --output .experiments/manual-claude-low-ghc ;;
    *) echo "$(date) qwen run ended without a result; not continuing"; exit 1 ;;
esac || exit 1
# The queue exits 0 even when features fail; only finish when none is left unfinished.
out=$([ "$status" = converged ] && echo manual-qwen-ghc || echo manual-claude-low-ghc)
left=$(python3 -c "import json;print(' '.join(k for k,v in json.load(open('.experiments/$out/queue-status.json')).items() if v['state'] not in ('done','non_convergent')))")
[ -z "$left" ] || { echo "$(date) queue ended with unfinished features: $left"; exit 1; }
echo "$(date) followup done"
