#!/usr/bin/env bash
# Rebuild the GHC tooling under /tmp/aechang after /tmp is cleared. Safe to rerun.
# It also starts the Qwen queue in tmux session ghcqueue. Shell setup afterward: `. /tmp/aechang/env.sh`.
set -euo pipefail
BASE=/tmp/aechang
REPO=$BASE/llm-improvement-loop
UV_VERSION=0.13.8
CODEX_VERSION=0.169.0
OLLAMA_VERSION=0.40.16

mkdir -p "$BASE/bin" "$BASE/ollama" "$BASE/.cache"
chmod 700 "$BASE"

# Keep tools and caches off the 2 GB AFS home. The driver (12.4) is too old for Ollama's CUDA
# build, which fails with "out of memory", so Ollama uses the same GPU through Vulkan.
cat > "$BASE/env.sh" <<EOF
export PATH=$BASE/bin:$BASE/ollama/bin:\$PATH
export UV_CACHE_DIR=$BASE/.cache/uv UV_PYTHON_INSTALL_DIR=$BASE/.uv-python PIP_CACHE_DIR=$BASE/.cache/pip
export OLLAMA_MODELS=$BASE/.ollama/models OLLAMA_FLASH_ATTENTION=0 CUDA_VISIBLE_DEVICES=-1 OLLAMA_VULKAN=1
EOF
. "$BASE/env.sh"

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

# The repo is public; GHC holds no GitHub credentials. Push from the Mac (see CLAUDE.md).
[ -d "$REPO/.git" ] || git clone https://github.com/AndrewChang-cpu/llm-improvement-loop.git "$REPO"

tmux has-session -t ollama 2>/dev/null \
    || tmux new-session -d -s ollama ". $BASE/env.sh && ollama serve > $BASE/ollama.log 2>&1"
until ollama list >/dev/null 2>&1; do sleep 1; done
ollama pull qwen3:4b
ollama create qwen3-experiment:4b -f "$REPO/experiments/qwen3.Modelfile"

if ! claude -p "Reply with ok" --max-turns 1 >/dev/null 2>&1; then
    echo "claude is not logged in: run 'claude' and log in (CLAUDE_CONFIG_DIR=$BASE/.claude if ~/.claude is unreadable), then rerun this script"
    exit 1
fi

# Qwen generates and edits; Claude judges at high effort. Reruns resume where the queue stopped.
tmux has-session -t ghcqueue 2>/dev/null || tmux new-session -d -s ghcqueue \
    "cd $REPO && . $BASE/env.sh && python3.12 claude_low_queue.py --workers 1 --retry-failed --generator qwen --tasks ghc-tasks.txt --output .experiments/manual-qwen-ghc 2>&1 | tee -a $BASE/queue.out; exec bash"
echo "Setup done; queue running in tmux session ghcqueue. Shell setup: . $BASE/env.sh"
