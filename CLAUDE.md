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

GHC reboots daily around 06:50, and every boot empties `/tmp`. What must survive lives on AFS in `~/private/llm/` (keep it under ~500 MB): `setup.sh`, `CLAUDE.md`, `repo.git` (bare mirror), `claude-config/` (credentials, settings, this project's 3 newest transcripts, so `claude --continue` works) and `results/` (small result files only; the Mac keeps the full copy). Everything else is rebuilt under `/tmp/aechang`.

After a reboot run `bash ~/private/llm/setup.sh` (with bash, not `source`; it needs a Kerberos ticket and asks for the password only when run by hand without one). It is safe to rerun. It restores the repo, results and Claude config (`CLAUDE_CONFIG_DIR=/tmp/aechang/claude-config`), reinstalls uv, Codex and Ollama, builds the Qwen model, and starts tmux sessions `renew` (hourly `kinit -R && aklog`), `backup` (`ghc-backup.sh` every 15 minutes, which also refreshes `~/private/llm/setup.sh` from `ghc-setup.sh`) and `queue` (`ghc-run.sh`, the current plan). If `claude` is not logged in, it does everything but start `queue`: log in (`. /tmp/aechang/env.sh && claude`), and rerun it. Always use Claude on GHC through `env.sh`: a `claude` on `~/.claude` would rotate the shared login and invalidate the backed-up one. `ghc-health-check.sh` prints OK or the problems.

The Mac does this unattended: launchd job `edu.cmu.aechang.llm-ghc` (installed by `install-mac-jobs.sh`, hourly at :05) runs `ghc-recover.sh`, which gets a renewable ticket from the Kerberos password in the Mac Keychain, copies it to GHC as `/tmp/aechang-krb5cc` (GHC rejects GSSAPI login, so `ssh -K` cannot forward it), and runs `setup.sh` if `/tmp/aechang` or a tmux session is missing; then `pull-ghc-results.sh` and, if that succeeded, `prune-ghc-afs-results.sh`, which deletes from AFS the features whose queue state is `done` or `non_convergent` once a checksum dry run shows the Mac has every file (logged in `<experiment>/.mac-has`, which the backup skips). Run `ghc-recover.sh --check` by hand to see GHC's state. Log: `~/.local/share/llm-ghc/job.log`. Tickets are renewable for 30 days.

Notes:

- The sandboxes of Claude and Codex need user namespaces, which Ubuntu's AppArmor blocks here (no sudo), so on Linux both run unsandboxed.
- The NVIDIA driver (12.4) is too old for Ollama's CUDA build, which fails with "CUDA error: out of memory", so Ollama runs on the GPU through Vulkan. `ghc-setup.sh` writes these settings to `/tmp/aechang/env.sh`; source it in every shell.
- The AFS home quota is 2 GB, so work in `/tmp/aechang/llm-improvement-loop` (local disk, not backed up, `chmod 700 /tmp/aechang`). Keep caches out of home too: `export UV_CACHE_DIR=/tmp/aechang/.cache/uv UV_PYTHON_INSTALL_DIR=/tmp/aechang/.uv-python PIP_CACHE_DIR=/tmp/aechang/.cache/pip`.
- Run the queue inside `tmux`. AFS tokens expire, so Claude's config lives in `/tmp/aechang/claude-config` (set by `env.sh`), not `~/.claude`.
- The repo is a clone of the public GitHub repo; manifests are tracked in git. GHC has no GitHub credentials, and commits made here exist only on GHC.
- Before starting the queue, prepare one GHC task and confirm that `tasks/<task>/reference-validation.json` shows the reference checks passing:
  `"$(uv python find 3.9)" run_experiment.py prepare --manifest .experiments/batch-100/runner-manifest.json --task sphinx-doc__sphinx-9822 --output "$PWD/.experiments/manual-qwen-ghc"` (use the Python the queue would pick for that task).
- `pull-ghc-results.sh` copies GHC's untracked `.experiments/` folders (e.g. `manual-qwen-ghc`, and `manual-claude-low-ghc` with the earlier Claude runs) into the Mac repo without deleting anything. It runs from launchd, not cron: cron has no access to `~/Documents`, and launchd can write there but cannot run scripts from it, so `install-mac-jobs.sh` copies the scripts to `~/.local/share/llm-ghc/`; rerun it after changing them.
