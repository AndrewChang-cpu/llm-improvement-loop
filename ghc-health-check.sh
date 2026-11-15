#!/usr/bin/env bash
# Hourly health check of the two ghc-run.sh tracks: prints OK, or PROBLEM lines that need attention.
# The Claude track is a problem when it stops unfinished; the Qwen side track only while it runs
# (a finished or stopped Qwen track is reported but never flagged).
cd "$(dirname "$0")" || exit 1
BASE=${BASE:-/tmp/${USER:-$(id -un)}}   # ghc-setup.sh's folder, which holds the track logs
# The Windows watcher points these at its own queue (windows-watch.sh).
CLOG=${CLOG:-$BASE/ghc-run.log} QUEUE_OUTPUT=${QUEUE_OUTPUT:-.experiments/manual-claude-low-ghc}
problems=()
# Only the current attempt in a log counts; earlier attempts' errors were already handled.
log_error() {
    [ -f "$2" ] || return
    local current=$(awk '/=== .* ghc-run .*start/{buf=""} {buf=buf $0 "\n"} END{printf "%s", buf}' "$2")
    grep -qE "Traceback|Error:" <<< "$current" && problems+=("$1: error in $2: $(grep -E 'Error' <<< "$current" | tail -1)")
}
# The track's log counts too, so a track restarted less than an hour ago is not reported as stuck.
stuck() {
    [ -n "$(find "$2" "$3" -mmin -60 -type f -not -path "*/tasks/*" 2>/dev/null | head -1)" ] \
        || problems+=("$1: running but no file in $2 changed in 60 minutes")
}
# A feature being refined or simplified is stuck when none of its files changed in 60 minutes:
# results, simplification, tasks/ (where preparing installs and builds) and its log.
stuck_features() {
    local exp=$2 task
    [ -f "$exp/queue-status.json" ] || return
    for task in $(python3 -c "import json;print(' '.join(k for k,v in json.load(open('$exp/queue-status.json')).items() if v['state'] in ('refining','simplifying')))"); do
        [ -n "$(find "$exp/results/$task" "$exp/simplification/$task" "$exp/tasks/$task" "$exp/$task.log" \
            -mmin -60 -type f -print -quit 2>/dev/null)" ] || problems+=("$1: $task changed no file in 60 minutes (see $exp/$task.log)")
    done
}
for result in .experiments/*/results/*/result.json; do
    [ -f "$result" ] && echo "result: $result $(python3 -c "import json;print(json.load(open('$result'))['status'])")"
done

if pgrep -f "[c]laude_low_queue.py" >/dev/null; then
    claude=running
    log_error claude "$CLOG"
    stuck claude $QUEUE_OUTPUT "$CLOG"
    stuck_features claude $QUEUE_OUTPUT
    status=$QUEUE_OUTPUT/queue-status.json
    failed=$([ -f "$status" ] && python3 -c "import json;print(' '.join(k for k,v in json.load(open('$status')).items() if v['state']=='failed'))")
    [ -n "$failed" ] && problems+=("claude: failed in $status: $failed")
elif grep -q "claude done" "$CLOG" 2>/dev/null; then claude=done
else claude=stopped; problems+=("claude: queue not running and not finished (see $CLOG)")
fi

QLOG=$BASE/ghc-qwen.log
if pgrep -f "[r]un_experiment.py run --backend ollama" >/dev/null; then
    qwen=running
    tmux has-session -t ollama 2>/dev/null || problems+=("qwen: ollama tmux session is gone")
    curl -sf localhost:11434/api/tags >/dev/null || problems+=("qwen: ollama server not responding")
    log_error qwen "$QLOG"
    stuck qwen .experiments/qwen32k-sphinx-11989 "$QLOG"
elif grep -q "qwen done" "$QLOG" 2>/dev/null; then qwen=done
else qwen=stopped
fi

if [ ${#problems[@]} -eq 0 ]; then echo "OK (claude $claude, qwen $qwen)"; else printf 'PROBLEM: %s\n' "${problems[@]}"; fi
