#!/usr/bin/env bash
# Run on the Mac (e.g. hourly from cron) to keep a copy of GHC's results.
# Never deletes local files, so the last copy survives GHC going down or /tmp being wiped.
set -euo pipefail
cd "$(dirname "$0")"
HOST=aechang@ghc40.ghc.andrew.cmu.edu
REMOTE=/tmp/aechang/llm-improvement-loop/.experiments
# Every GHC results folder; batch-100 holds tracked inputs, not results.
for dir in $(ssh -o BatchMode=yes "$HOST" ls "$REMOTE" | grep -vx batch-100); do
    mkdir -p ".experiments/$dir"
    rsync -a -e "ssh -o BatchMode=yes" --exclude 'tasks/' --exclude 'generated/' --exclude 'evaluation/' \
        "$HOST:$REMOTE/$dir/" ".experiments/$dir/"
done
echo "$(date '+%F %T') pulled GHC results"
