#!/usr/bin/env bash
# The GHC plan, as two independent tracks (setup.sh runs each in its own tmux session):
#   claude (session queue, log ghc-run.log): the GHC tasks with the normal Claude setup, 3 at a time.
#   qwen (session qwen, log ghc-qwen.log): a side run of Qwen (32k context) on pilot sphinx-11989.
#   Nothing waits on it.
# Safe to rerun: a finished track is skipped and an unfinished one resumes. Logs "<track> done".
cd "$(dirname "$0")" && . /tmp/aechang/env.sh
track=${1:?usage: ghc-run.sh claude|qwen}
echo "=== $(date) ghc-run $track start"
case "$track" in
claude)
    python3.12 claude_low_queue.py --workers 3 --retry-failed \
        --tasks ghc-tasks.txt --output .experiments/manual-claude-low-ghc || exit 1
    # The queue exits 0 even when features fail; only finish when none is left unfinished.
    left=$(python3 -c "import json;print(' '.join(k for k,v in json.load(open('.experiments/manual-claude-low-ghc/queue-status.json')).items() if v['state'] not in ('done','non_convergent')))")
    [ -z "$left" ] || { echo "$(date) queue ended with unfinished features: $left"; exit 1; } ;;
qwen)
    Q=.experiments/qwen32k-sphinx-11989/results/sphinx-doc__sphinx-11989/result.json
    [ -f "$Q" ] || python3.12 run_experiment.py run --backend ollama --judge-backend claude --effort low \
        --codex /tmp/aechang/bin/codex --task sphinx-doc__sphinx-11989 --output .experiments/qwen32k-sphinx-11989
    [ -f "$Q" ] || { echo "$(date) qwen run ended without a result"; exit 1; }
    echo "$(date) qwen status: $(python3 -c "import json;print(json.load(open('$Q'))['status'])")" ;;
*) echo "unknown track $track" >&2; exit 2 ;;
esac
echo "$(date) $track done"
