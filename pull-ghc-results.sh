#!/usr/bin/env bash
# Run on the Mac (e.g. hourly from cron) to keep a copy of GHC's results.
# Never deletes local files, so the last copy survives GHC going down or /tmp being wiped.
set -euo pipefail
cd "$(dirname "$0")"
HOST=aechang@ghc40.ghc.andrew.cmu.edu
REMOTE=/tmp/aechang/llm-improvement-loop/.experiments
for dir in manual-qwen-ghc manual-claude-low-ghc; do
    ssh -o BatchMode=yes "$HOST" test -d "$REMOTE/$dir" || continue
    mkdir -p ".experiments/$dir"
    rsync -a -e "ssh -o BatchMode=yes" --exclude 'tasks/' --exclude 'generated/' --exclude 'evaluation/' \
        "$HOST:$REMOTE/$dir/" ".experiments/$dir/"
done
echo "$(date '+%F %T') pulled GHC results"
