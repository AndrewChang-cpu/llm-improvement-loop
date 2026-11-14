# CLAUDE.md

Read `AGENTS.md` first; its rules apply here too.

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
- Keep docs concise. Commit only the files your change touches, because other work happens in the same tree.

## Dependencies

- `git`, `uv`, `python3.12` (for the queue), and the `claude` CLI, logged in.
- Python per task comes from `environment-specs.json` → `official_spec.python`. `claude_low_queue.py` raises versions below 3.8 to 3.8. Keep that on Linux for comparability, even where 3.6 or 3.7 is available.
- Matplotlib tasks build FreeType with `CFLAGS=-DFT_CONFIG_OPTION_SYSTEM_ZLIB LDFLAGS=-lz`. The queue sets these on every OS, so Linux needs a C compiler, `make`, and zlib headers (`test -f /usr/include/zlib.h`).

## GHC machine (`ghc40.ghc.andrew.cmu.edu`)

- The AFS home quota is 2 GB, so work in `/tmp/aechang/llm-improvement-loop` (local disk, not backed up, `chmod 700 /tmp/aechang`). Keep caches out of home too: `export UV_CACHE_DIR=/tmp/aechang/.cache/uv UV_PYTHON_INSTALL_DIR=/tmp/aechang/.uv-python PIP_CACHE_DIR=/tmp/aechang/.cache/pip`.
- Run the queue inside `tmux`. AFS tokens expire, which can make `~/.claude` unreadable. If `claude` auth fails, set `CLAUDE_CONFIG_DIR=/tmp/aechang/.claude` and log in again.
- `/tmp` is not backed up. Pull results back to the Mac regularly, for example: `rsync -a --exclude 'tasks/' --exclude 'generated/' --exclude 'evaluation/' aechang@ghc40.ghc.andrew.cmu.edu:/tmp/aechang/llm-improvement-loop/.experiments/manual-claude-low-v2/ <mac backup dir>/`.

## Moving from the Mac

Recorded files (`settings.json`, `request.json`, `verdict.json`, …) contain absolute paths under `/Users/andrew/Documents/Class/17679/llm-improvement-loop/llm-improvement-loop`. Resumed tasks reject any request or setting that differs. Before the first run, rewrite that prefix in the copied JSON files once:

```sh
cd /tmp/aechang/llm-improvement-loop
OLD=/Users/andrew/Documents/Class/17679/llm-improvement-loop/llm-improvement-loop NEW=$PWD
grep -rlIZ --include='*.json' "$OLD" .experiments/manual-claude-low-v2 | xargs -0 sed -i "s#$OLD#$NEW#g"
```

First steps on the new machine:

1. Read `queue-status.json` for counts. At the move there were 86 tasks: 6 done, 1 refining (`matplotlib__matplotlib-16832`), 79 queued.
2. Run `git log` and `git status`. Another worker was fixing the environment specs for the sklearn (47), sphinx (16), and flask (1) tasks. Their fixes may be uncommitted in the copied tree, and some (x86_64 Python 3.8 for `numpy==1.19.2`) were macOS-only.
3. Prepare one task, with the same Python the queue would pick, and confirm that `tasks/<task>/reference-validation.json` shows the reference checks passing: `"$(uv python find 3.8)" run_experiment.py prepare --manifest .experiments/batch-100/runner-manifest.json --task <task> --output "$PWD/.experiments/manual-claude-low-v2"`.
4. Restart the queue in tmux.
