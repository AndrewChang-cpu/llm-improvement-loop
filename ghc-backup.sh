#!/usr/bin/env bash
# Mirror the repo and results to AFS, since GHC empties /tmp at every boot. Needs a live AFS token.
cd "$(dirname "$0")"
MIRROR=$HOME/private/llm-improvement-loop.git
[ -d "$MIRROR" ] || git clone -q --bare . "$MIRROR"
git push -q --force "$MIRROR" main
rsync -a --exclude 'tasks/' --exclude 'generated/' --exclude 'evaluation/' --exclude batch-100 \
    .experiments/ "$HOME/private/ghc-results-backup/"
echo "$(date '+%F %T') backed up to AFS"
