# CLAUDE.md

Read `AGENTS.md` first; its rules apply here too.

## Responses

- When the user asks a question, answer it directly first, before anything else.
- Keep responses under 100 words.

## Purpose

Iterative specification refinement on FEA-Bench PRs. Each revision of a feature's specification gets 10 independent implementations, which are then judged. A feature converges when 10/10 implementations pass all criteria, with at most 10 revisions. A converged specification is then simplified: 3 candidates per round, each cutting 10–30% of the words, keeping the shortest candidate that still gets 10/10.

## Scripts

| Script | Role |
|---|---|
| `run_experiment.py` | `prepare` (repos and venvs for a task) and `run` (refinement loop) |
| `simplify_specifications.py` | simplification of a converged `results/<task>` |
| `claude_low_queue.py` | queue: refine, then simplify, for each Claude PR in `experiment-commands.txt` |
| `view_experiment.py` | evaluation viewer |
| `retire_workspaces.py` | turns judged runs into `patch.diff` (or `generated.tar.gz`) to free disk |

Queue (one feature at a time; the user may raise `--workers` later):

```sh
python3.12 claude_low_queue.py --workers 1 --retry-failed
```

- Output: `.experiments/manual-claude-low-v2/`, with `queue-status.json` (state of each task) and `<task>.log`.
- Required inputs: `.experiments/batch-100/runner-manifest.json` and `.experiments/batch-100/environment-specs.json`.
- Reruns skip `done` and `non_convergent` tasks and resume the others. `tasks/<task>/` (repos and venvs) is recreated by `prepare`.

## Rules

- Never correct judgments by hand or ask for replacement judgments. Keep the original model outputs.
- Simplify only when `results/<task>/result.json` has `"status": "converged"`.
- Existing result and simplification folders reject changed settings. When you edit `run_experiment.py` or `simplify_specifications.py`, add the old `runner_sha256` to the compatibility lists (`resume_settings` in `run_experiment.py` and the list in `simplify_specifications.py`).
- Generators and editors run at `--effort low`. Judges always run at high effort.
- `claude_low_queue.py --generator qwen` has a local Ollama Qwen (`qwen3-experiment:4b`, via the Codex CLI) generate and edit, while Claude (haiku, high effort) judges.
- Keep docs concise. Commit only the files your change touches, because other work happens in the same tree.

## Dependencies

- `git`, `uv`, `python3.12` (for the queue), and the `claude` CLI, logged in.
- Python per task comes from `environment-specs.json` → `official_spec.python`. `claude_low_queue.py` raises versions below 3.8 to 3.8. Keep that on Linux for comparability, even where 3.6 or 3.7 is available.
- Builds need a C/C++ compiler, `make`, and zlib headers (`test -f /usr/include/zlib.h`). The queue sets `CFLAGS=-DFT_CONFIG_OPTION_SYSTEM_ZLIB LDFLAGS=-lz` for matplotlib on every OS.
- macOS-only workarounds are not needed on x86_64 Linux: `SKLEARN_NO_OPENMP=1` and `-Wno-error` CFLAGS (gcc has OpenMP), and x86_64/Rosetta Python 3.8 for the numpy 1.19.2 sklearn group (native here).

## Splitting work across machines

The Mac and GHC run disjoint features. `ghc-tasks.txt` lists GHC's features (31 sklearn and sphinx features no machine had started). Each machine has its own output folder.

```sh
# Mac
python3.12 claude_low_queue.py --workers 1 --retry-failed --exclude ghc-tasks.txt
# GHC
python3.12 claude_low_queue.py --workers 1 --retry-failed --generator qwen --tasks ghc-tasks.txt --output .experiments/manual-qwen-ghc
```

`--tasks` and `--exclude` take a file (one task per line) or a comma-separated list.

## GHC machine (`ghc40.ghc.andrew.cmu.edu`)

GHC runs the Qwen queue (`--generator qwen`, output `.experiments/manual-qwen-ghc`). After `/tmp` is wiped:

1. Run `bash ~/private/ghc-setup.sh` (a copy of `ghc-setup.sh`; keep the two identical). It installs uv, Codex and Ollama under `/tmp/aechang`, clones the repo, builds the Qwen model, and starts the queue in tmux session `ghcqueue`. If it says `claude` is not logged in, log in and rerun it.
2. Before the queue runs, or the queue restarts those features from scratch, push the Mac's copy of the results back: `rsync -a .experiments/manual-qwen-ghc/ aechang@ghc40.ghc.andrew.cmu.edu:/tmp/aechang/llm-improvement-loop/.experiments/manual-qwen-ghc/` (from the Mac). The simplest order is: stop the queue (`tmux kill-session -t ghcqueue`), rsync, rerun the setup script.

Notes:

- The sandboxes of Claude and Codex need user namespaces, which Ubuntu's AppArmor blocks here (no sudo), so on Linux both run unsandboxed.
- The NVIDIA driver (12.4) is too old for Ollama's CUDA build, which fails with "CUDA error: out of memory", so Ollama runs on the GPU through Vulkan. `ghc-setup.sh` writes these settings to `/tmp/aechang/env.sh`; source it in every shell.
- The AFS home quota is 2 GB, so work in `/tmp/aechang/llm-improvement-loop` (local disk, not backed up, `chmod 700 /tmp/aechang`). Keep caches out of home too: `export UV_CACHE_DIR=/tmp/aechang/.cache/uv UV_PYTHON_INSTALL_DIR=/tmp/aechang/.uv-python PIP_CACHE_DIR=/tmp/aechang/.cache/pip`.
- Run the queue inside `tmux`. AFS tokens expire, which can make `~/.claude` unreadable. If `claude` auth fails, set `CLAUDE_CONFIG_DIR=/tmp/aechang/.claude` and log in again.
- The repo is a clone of the public GitHub repo; manifests are tracked in git. GHC has no GitHub credentials, and commits made here exist only on GHC.
- Before starting the queue, prepare one GHC task and confirm that `tasks/<task>/reference-validation.json` shows the reference checks passing:
  `"$(uv python find 3.9)" run_experiment.py prepare --manifest .experiments/batch-100/runner-manifest.json --task sphinx-doc__sphinx-9822 --output "$PWD/.experiments/manual-qwen-ghc"` (use the Python the queue would pick for that task).
- `/tmp` is not backed up. The Mac runs `pull-ghc-results.sh` hourly from cron (`0 * * * * <repo>/pull-ghc-results.sh >> /tmp/pull-ghc.log 2>&1`). It copies every GHC folder in `.experiments/` except `batch-100` (e.g. `manual-qwen-ghc`, and `manual-claude-low-ghc` with the earlier Claude runs) without deleting anything, and needs passwordless SSH from the Mac to GHC.
