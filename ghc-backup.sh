#!/usr/bin/env bash
# Copy what /tmp loses at every boot to AFS (~/private/llm, kept under ~500 MB of the 2 GB quota):
# the repo, GHC's results (small files only; the Mac pulls everything) and the Claude config with
# this project's newest transcripts. Needs a live AFS token.
set -euo pipefail
cd "$(dirname "$0")"
BASE=${BASE:-/tmp/aechang}
AFS=${AFS:-$HOME/private/llm}
CONFIG=$BASE/claude-config
mkdir -p "$AFS/results" "$AFS/claude-config"
[ -d "$AFS/repo.git" ] || git clone -q --bare . "$AFS/repo.git"
git push -q --force "$AFS/repo.git" main
cp ghc-setup.sh "$AFS/setup.sh"
cp CLAUDE.md "$AFS/CLAUDE.md"

# GHC's results are the untracked folders in .experiments; tracked ones are in the mirror.
# Skip features prune-ghc-afs-results.sh (Mac) deleted after confirming the Mac has them.
git ls-files --others --directory --exclude-standard .experiments | while read -r path; do
    dest=$AFS/results/${path#.experiments/}
    skip=(); [ -f "$dest.mac-has" ] && skip=(--exclude-from="$dest.mac-has")
    rsync -a --prune-empty-dirs --max-size=2m --exclude-from=<(sed -n 's|^\.experiments/\*\*/||p' .gitignore) \
        --exclude 'tasks/' --exclude '*.tar.gz' --exclude '*.jsonl' "${skip[@]}" "$path" "$dest"
done

if [ -d "$CONFIG" ]; then
    rsync -a --ignore-missing-args "$CONFIG"/{.credentials.json,.claude.json,settings.json,history.jsonl} "$AFS/claude-config/"
    for project in "$CONFIG"/projects/*/; do
        [ -d "$project" ] || continue
        name=$(basename "$project")
        mkdir -p "$AFS/claude-config/projects/$name"
        [ -d "$project/memory" ] && rsync -a "$project/memory" "$AFS/claude-config/projects/$name/"
        # Keep the 3 newest transcripts (and their subagent folders) so `claude --continue` works.
        keep=$(ls -t "$project" | grep '\.jsonl$' | head -3 | sed 's/\.jsonl$//' || true)
        for id in $keep; do rsync -a --ignore-missing-args "$project/$id.jsonl" "$project/$id" "$AFS/claude-config/projects/$name/"; done
        for old in "$AFS/claude-config/projects/$name"/*.jsonl; do
            id=$(basename "$old" .jsonl)
            [ -e "$old" ] && ! grep -qx "$id" <<< "$keep" && rm -rf "$old" "${old%.jsonl}"
        done
    done
fi
echo "$(date '+%F %T') backed up to AFS ($(du -sh "$AFS" | cut -f1))"
