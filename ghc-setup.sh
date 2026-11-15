#!/usr/bin/env bash
# Rebuild GHC's /tmp state after a reboot (GHC empties /tmp daily around 06:50). Safe to rerun.
# The backup loop copies this file to ~/private/llm/setup.sh; after a reboot run `bash ~/private/llm/setup.sh`.
# It restores the repo, results and Claude config from AFS, reinstalls the tools, and starts tmux
# sessions renew (Kerberos/AFS), backup (ghc-backup.sh), queue (ghc-run.sh claude) and qwen
# (ghc-run.sh qwen); the last two are skipped while claude is not logged in. Prompts only when run by hand without a Kerberos ticket. Test overrides: BASE, AFS, GHC_TMUX (tmux socket), and
# DRY_RUN=1 (no tool installs, no Ollama, and a queue session that runs nothing). Machine settings:
# KRB_PRINCIPAL (default $USER@ANDREW.CMU.EDU), KRB5_FILE (the ticket ghc-recover.sh copies here),
# REPO_URL (clone source when AFS has no mirror).
(return 0 2>/dev/null) && { echo "Run this with bash, not source." >&2; return 1; }
set -euo pipefail
USER=${USER:-$(id -un)}
BASE=${BASE:-/tmp/$USER}
AFS=${AFS:-$HOME/private/llm}
KRB_PRINCIPAL=${KRB_PRINCIPAL:-$USER@ANDREW.CMU.EDU}
KRB5_FILE=${KRB5_FILE:-/tmp/$USER-krb5cc}
REPO_URL=${REPO_URL:-https://github.com/AndrewChang-cpu/llm-improvement-loop.git}
DRY_RUN=${DRY_RUN:-0}
REPO=$BASE/llm-improvement-loop
tm() { tmux -L "${GHC_TMUX:-default}" "$@"; }

klist -s || { [ -t 0 ] && kinit "$KRB_PRINCIPAL"; } || { echo "No Kerberos ticket; run kinit" >&2; exit 1; }
aklog

mkdir -p "$BASE/bin" "$BASE/ollama" "$BASE/.cache"
chmod 700 "$BASE"

# Keep tools and caches off the 2 GB AFS home. The driver (12.4) is too old for Ollama's CUDA
# build, which fails with "out of memory", so Ollama uses the same GPU through Vulkan. Flash attention
# lets the KV cache be q8_0, which fits Qwen's 32k context in the 8 GB GPU.
cat > "$BASE/env.sh" <<EOF
export PATH=$BASE/bin:$BASE/ollama/bin:$HOME/.local/bin:\$PATH
export UV_CACHE_DIR=$BASE/.cache/uv UV_PYTHON_INSTALL_DIR=$BASE/.uv-python PIP_CACHE_DIR=$BASE/.cache/pip
export OLLAMA_MODELS=$BASE/.ollama/models OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 CUDA_VISIBLE_DEVICES=-1 OLLAMA_VULKAN=1
export CLAUDE_CONFIG_DIR=$BASE/claude-config
EOF
. "$BASE/env.sh"

# Restore from AFS. --ignore-existing keeps newer /tmp files when rerun.
[ -d "$REPO/.git" ] || git clone -q "$( [ -d "$AFS/repo.git" ] && echo "$AFS/repo.git" \
    || echo "$REPO_URL")" "$REPO"
[ -d "$AFS/results" ] && rsync -a --ignore-existing "$AFS/results/" "$REPO/.experiments/"
[ -d "$AFS/claude-config" ] && rsync -a --ignore-existing "$AFS/claude-config/" "$CLAUDE_CONFIG_DIR/"

if [ "$DRY_RUN" != 1 ]; then
    UV_VERSION=0.13.8 CODEX_VERSION=0.169.0 OLLAMA_VERSION=0.40.16
    [ -x "$BASE/bin/uv" ] || curl -LsSf "https://astral.sh/uv/$UV_VERSION/install.sh" \
        | env UV_INSTALL_DIR="$BASE/bin" UV_NO_MODIFY_PATH=1 sh
    [ -x "$BASE/bin/codex" ] || {
        curl -fsSL "https://github.com/openai/codex/releases/download/rust-v$CODEX_VERSION/codex-x86_64-unknown-linux-musl.tar.gz" \
            | tar -xz -C "$BASE/bin"
        mv "$BASE/bin/codex-x86_64-unknown-linux-musl" "$BASE/bin/codex"
    }
    [ -x "$BASE/ollama/bin/ollama" ] || curl -fsSL \
        "https://github.com/ollama/ollama/releases/download/v$OLLAMA_VERSION/ollama-linux-amd64.tar.zst" \
        | tar --zstd -x -C "$BASE/ollama"
    tm has-session -t ollama 2>/dev/null \
        || tm new-session -d -s ollama ". $BASE/env.sh && ollama serve > $BASE/ollama.log 2>&1"
    until ollama list >/dev/null 2>&1; do sleep 1; done
    ollama pull qwen3:4b
    ollama create qwen3-experiment:4b -f "$REPO/experiments/qwen3.Modelfile"
fi
# Without a Claude login everything else still runs; only the queue waits.
claude_error=
[ "$DRY_RUN" = 1 ] || { claude_error=$(cd "$BASE" && claude -p "Reply with ok" --max-turns 1 \
    --no-session-persistence 2>&1) && claude_error= || claude_error=${claude_error:-claude check failed}; }

# Tickets are renewable for 30 days; renewing hourly keeps AFS readable. Try the login ticket,
# then the one ghc-recover.sh copies from the Mac.
tm has-session -t renew 2>/dev/null || tm new-session -d -s renew "while true; do { date; { kinit -R && aklog; } \
    || { export KRB5CCNAME=FILE:$KRB5_FILE; kinit -R && aklog; } && echo renewed; } >> $BASE/renew.log 2>&1; sleep 3600; done"
tm has-session -t backup 2>/dev/null || tm new-session -d -s backup \
    "while true; do BASE=$BASE AFS=$AFS $REPO/ghc-backup.sh >> $BASE/backup.log 2>&1; sleep 900; done"
track() { [ "$DRY_RUN" = 1 ] && echo "echo 'DRY_RUN: $1 not started'; exec bash" \
    || echo "BASE=$BASE $REPO/ghc-run.sh $1 2>&1 | tee -a $BASE/$2; exec bash"; }
if [ -n "$claude_error" ]; then
    echo "WARNING: claude is not logged in ($(head -1 <<< "$claude_error")); queue and qwen not started." \
        "Run '. $BASE/env.sh && claude' and log in, then rerun this script; backup saves the login to AFS." >&2
else
    tm has-session -t queue 2>/dev/null || tm new-session -d -s queue "$(track claude ghc-run.log)"
    # Qwen track stopped by the user (2026-11-14): 0/30 runs passed at 32k.
    : tm has-session -t qwen 2>/dev/null || tm new-session -d -s qwen "$(track qwen ghc-qwen.log)"
fi
echo "Setup done: tmux sessions $(tm ls -F '#S' | tr '\n' ' '); shell setup: . $BASE/env.sh"
