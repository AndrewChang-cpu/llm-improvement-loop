#!/usr/bin/env bash
# Mac: bring GHC back after its daily reboot, without the user. Gets a renewable Kerberos ticket
# from the password in the Keychain and copies it to GHC (/tmp/aechang-krb5cc, mode 600; ssh -K
# does not work because GHC rejects GSSAPI login). On GHC it runs aklog and, if /tmp/aechang or
# its tmux sessions are gone, `bash ~/private/llm/setup.sh`. Then it runs ghc-health-check.sh and,
# only on PROBLEM, a headless `claude -p` fixer on GHC (see below). Safe to rerun by hand.
# --check only reports GHC's tmux/repo state. GHC_ENV passes setup.sh test overrides, e.g.
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
[ "${1:-}" = --check ] && exit 0

# Health check; only on PROBLEM, a fresh headless Claude on GHC investigates and resumes the run.
# At most one fixer at a time and one per hour. FIXER_TEST=1 fakes a PROBLEM with a no-op prompt.
STATE=${STATE:-$HOME/.local/share/llm-ghc}
health=$(ssh -o BatchMode=yes "$HOST" 'cd /tmp/aechang/llm-improvement-loop && bash ghc-health-check.sh' 2>&1)
[ "${FIXER_TEST:-}" = 1 ] && health="PROBLEM: smoke test of the fixer path; there is no real problem"
grep -v '^result:' <<< "$health"
grep -q '^PROBLEM' <<< "$health" || exit 0
if [ "${FIXER_TEST:-}" != 1 ] && [ -f "$STATE/fixer.last" ] \
    && [ $(( $(date +%s) - $(cat "$STATE/fixer.last") )) -lt 3300 ]; then
    echo "fixer ran less than an hour ago; skipping"; exit 0
fi
mkdir "$STATE/fixer.lock" 2>/dev/null || { echo "another fixer is running; skipping"; exit 0; }
trap 'rm -f "$CC"; rmdir "$STATE/fixer.lock"' EXIT
[ "${FIXER_TEST:-}" = 1 ] || date +%s > "$STATE/fixer.last"
problems=$(grep '^PROBLEM' <<< "$health")
if [ "${FIXER_TEST:-}" = 1 ]; then
    prompt="Smoke test of the unattended fixer: $problems. Do not run any tools or change anything. Reply with exactly: fixer smoke ok"
else
    prompt="You are the unattended fixer for the GHC experiment run (plan: ghc-run.sh, two independent tracks: claude in tmux session 'queue' with log /tmp/aechang/ghc-run.log, qwen in session 'qwen' with log /tmp/aechang/ghc-qwen.log). Health check reported: $problems. Investigate only that, fix per CLAUDE.md rules (never alter or redo judgments; keep original model outputs), and resume the run, e.g. tmux kill-session -t queue; tmux new-session -d -s queue \"./ghc-run.sh claude 2>&1 | tee -a /tmp/aechang/ghc-run.log; exec bash\" (qwen likewise). Do not commit or push. Reply in under 100 words: cause, what you changed, current state."
fi
echo "fixer: $problems"
ssh -o BatchMode=yes "$HOST" "export KRB5CCNAME=FILE:/tmp/aechang-krb5cc; aklog; cd /tmp/aechang/llm-improvement-loop && . /tmp/aechang/env.sh \
    && timeout 50m claude -p $(printf %q "$prompt") --no-session-persistence --permission-mode bypassPermissions < /dev/null" 2>&1 | sed 's/^/fixer> /'
