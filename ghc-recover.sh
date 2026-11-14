#!/usr/bin/env bash
# Mac: bring GHC back after its daily reboot, without the user. Gets a renewable Kerberos ticket
# from the password in the Keychain and copies it to GHC (/tmp/aechang-krb5cc, mode 600; ssh -K
# does not work because GHC rejects GSSAPI login). On GHC it runs aklog and, if /tmp/aechang or
# its tmux sessions are gone, `bash ~/private/llm/setup.sh`. Safe to rerun by hand.
# --check only reports. GHC_ENV passes setup.sh test overrides, e.g.
# GHC_ENV="BASE=/tmp/aechang-smoke AFS=~/private/llm-smoke GHC_TMUX=smoke DRY_RUN=1".
set -uo pipefail
HOST=${HOST:-aechang@ghc40.ghc.andrew.cmu.edu}
echo "$(date '+%F %T') recover ${1:-}"
CC=$(mktemp)
trap 'rm -f "$CC"' EXIT
kinit --renewable -c "FILE:$CC" aechang@ANDREW.CMU.EDU </dev/null || { echo "kinit from Keychain failed" >&2; exit 1; }
ssh -o BatchMode=yes "$HOST" 'umask 077; cat > /tmp/aechang-krb5cc' < "$CC" || exit 1
ssh -o BatchMode=yes "$HOST" "export KRB5CCNAME=FILE:/tmp/aechang-krb5cc ${GHC_ENV:-}; bash -s -- ${1:-}" <<'REMOTE'
aklog || { echo "aklog failed on GHC" >&2; exit 1; }
BASE=${BASE:-/tmp/aechang}
missing=$(for s in renew backup queue; do tmux -L "${GHC_TMUX:-default}" has-session -t $s 2>/dev/null || echo $s; done)
[ -d "$BASE/llm-improvement-loop/.git" ] || missing="$missing repo"
if [ -z "$missing" ]; then echo "GHC healthy"; exit 0; fi
echo "GHC missing:" $missing
[ "${1:-}" = --check ] && exit 2
bash "${AFS:-$HOME/private/llm}/setup.sh" < /dev/null
REMOTE
