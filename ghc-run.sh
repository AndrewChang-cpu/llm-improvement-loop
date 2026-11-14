#!/usr/bin/env bash
# The GHC plan: finish (or resume) the Qwen run on pilot sphinx-11989. If it converges, run the GHC
# tasks with Qwen; otherwise run them with the normal Claude setup, 3 features at a time.
cd "$(dirname "$0")" && . /tmp/aechang/env.sh
python3.12 run_experiment.py run --backend ollama --judge-backend claude --effort low \
    --codex /tmp/aechang/bin/codex --task sphinx-doc__sphinx-11989 --output .experiments/qwen-sphinx-11989
Q=.experiments/qwen-sphinx-11989/results/sphinx-doc__sphinx-11989/result.json
status=$(python3 -c "import json;print(json.load(open('$Q'))['status'])" 2>/dev/null || echo missing)
echo "$(date) qwen status: $status"
case "$status" in
    converged) python3.12 claude_low_queue.py --workers 1 --retry-failed --generator qwen \
                   --tasks ghc-tasks.txt --output .experiments/manual-qwen-ghc ;;
    non_convergent) python3.12 claude_low_queue.py --workers 3 --retry-failed \
                   --tasks ghc-tasks.txt --output .experiments/manual-claude-low-ghc ;;
    *) echo "$(date) qwen run ended without a result; not continuing"; exit 1 ;;
esac
echo "$(date) followup done"
