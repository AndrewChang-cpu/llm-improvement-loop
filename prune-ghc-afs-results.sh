#!/usr/bin/env bash
# Mac: after pull-ghc-results.sh succeeds, free AFS space by deleting finished features from
# GHC's ~/private/llm/results. A feature is deleted only when its queue-status.json state is done
# or non_convergent (the queue never reruns those, so a restore after a reboot does not need them)
# and an rsync --checksum dry run shows every AFS file already on the Mac. queue-status.json, logs,
# claude-config and repo.git are never touched, nor features outside a queue (e.g. ghc-run.sh's
# Qwen experiment, which ghc-run.sh would rerun if its result vanished). Each deleted path is added
# to <experiment>/.mac-has, which ghc-backup.sh skips so it does not copy the feature back.
set -euo pipefail
HOST=${HOST:-aechang@ghc40.ghc.andrew.cmu.edu}
REPO=${REPO:-$(cd "$(dirname "$0")" && pwd)}
AFS=${AFS:-private/llm}   # relative to the GHC home
AUTH='[ -f /tmp/aechang-krb5cc ] && export KRB5CCNAME=FILE:/tmp/aechang-krb5cc; aklog;'
finished=$(ssh -o BatchMode=yes "$HOST" "$AUTH cd $AFS/results && python3 -c '
import glob, json, os
for status in glob.glob(\"*/queue-status.json\"):
    exp = os.path.dirname(status)
    for task, entry in json.load(open(status)).items():
        if entry.get(\"state\") in (\"done\", \"non_convergent\"):
            for kind in (\"results\", \"simplification\"):
                if os.path.isdir(f\"{exp}/{kind}/{task}\"):
                    print(f\"{exp}/{kind}/{task}\")
'")
for path in $finished; do
    missing=$(rsync -an --checksum --out-format='%n' -e "ssh -o BatchMode=yes" --rsync-path="$AUTH rsync" \
        "$HOST:$AFS/results/$path/" "$REPO/.experiments/$path/" | grep -v '/$' || true)
    if [ -n "$missing" ]; then echo "keep $path: $(wc -l <<< "$missing" | tr -d ' ') files not on the Mac"; continue; fi
    exp=${path%%/*}
    ssh -o BatchMode=yes "$HOST" "$AUTH rm -rf $AFS/results/$path && echo /${path#*/}/ >> $AFS/results/$exp/.mac-has"
    echo "pruned $path"
done
echo "$(date '+%F %T') pruned AFS results ($(ssh -o BatchMode=yes "$HOST" "$AUTH du -sh $AFS | cut -f1"))"
