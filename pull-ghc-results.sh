#!/usr/bin/env bash
# Mac: copy GHC's results (its untracked .experiments folders) into the Mac repo. Never deletes
# local files, so the last copy survives GHC going down or /tmp being wiped. Runs hourly from
# launchd (see install-mac-jobs.sh), which may write to ~/Documents but not run scripts from it, nor
# open folders there that another app created (open: Operation not permitted). So run it with
# `launchctl kickstart`, not by hand; a folder that fails is reported and the others still sync.
set -euo pipefail
HOST=${HOST:-aechang@ghc40.ghc.andrew.cmu.edu}
REPO=${REPO:-$(cd "$(dirname "$0")" && pwd)}
REMOTE=${REMOTE:-/tmp/aechang/llm-improvement-loop}
failed=()
for path in $(ssh -o BatchMode=yes "$HOST" "cd $REMOTE && git ls-files --others --directory --exclude-standard .experiments"); do
    mkdir -p "$(dirname "$REPO/$path")"
    rsync -a -e "ssh -o BatchMode=yes" --exclude 'tasks/' --exclude 'generated/' --exclude 'evaluation/' \
        "$HOST:$REMOTE/$path" "$REPO/$path" || failed+=("$path")
done
if [ ${#failed[@]} -gt 0 ]; then
    echo "$(date '+%F %T') not pulled: ${failed[*]} (see pull-ghc-results.sh and CLAUDE.md)" >&2; exit 1
fi
echo "$(date '+%F %T') pulled GHC results"
