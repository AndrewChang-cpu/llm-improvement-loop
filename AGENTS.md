# Agent guide

The one guide for every agent (Codex reads this file; `CLAUDE.md` imports it). Answer the user's question directly first; keep replies under 100 words.

## What this repo does

Iterative specification refinement on FEA-Bench PRs. Each revision of a feature's specification gets 10 independent implementations, which are then judged on 11 criteria. A feature converges at 10/10 passes, with at most 10 editor revisions. A converged specification is then simplified: 3 candidates per round, each cutting 10–30% of the words, keeping the shortest that still gets 10/10. Design: [docs/research-design.md](docs/research-design.md), [docs/experimental-methodology.md](docs/experimental-methodology.md); results: [docs/results.md](docs/results.md).

| Script | Role |
|---|---|
| `run_experiment.py` | `prepare` (repos and venvs for a task), `run` (refinement loop), `smoke` (backend login and file access) |
| `simplify_specifications.py` | simplification of a converged `results/<task>` |
| `claude_low_queue.py` | queue: refine, then simplify, each task, 3 in parallel by default |
| `view_experiment.py` | evaluation viewer (HTML file, or live with `--serve PORT`) |
| `retire_workspaces.py` | turns judged runs into `patch.diff` (or `generated.tar.gz`) to free disk |
| `experiments/build_windows_100.py` | builds `experiments/windows-100/` (the Windows PRs) |
| `ghc-health-check.sh`, `windows-watch.sh` | deterministic hourly health check (OK or PROBLEM); the Windows watcher notifies the existing supervisor only on PROBLEM |

## Machines and task lists

All 1,401 FEA-Bench PRs are split across the five `tasks/*.txt` lists (`experiments/build_feabench_1401.py`; union is all of FEA-Bench, no overlap). Use `--manifest experiments/feabench-1401/runner-manifest.json` for every list: it holds every PR, with earlier manifests' entries unchanged so started features resume. Machines run disjoint tasks, listed in `tasks/<machine>.txt` (one task per line, `#` comments). Never move a task another machine has started; move only unstarted ones.

| Machine | Tasks | Backend | Manifest | Output |
|---|---|---|---|---|
| Mac | `tasks/mac.txt` (Claude PRs of batch-100) | claude | default (batch-100) | `.experiments/manual-claude-low-v2` |
| GHC | `tasks/ghc.txt` | claude | default (batch-100) | `.experiments/manual-claude-low-ghc` |
| Windows (WSL2) | `tasks/windows.txt` (100 random FEA-Bench PRs outside batch-100) | codex | `experiments/windows-100/runner-manifest.json` | `.experiments/codex-low-windows` |

## Running a queue

Before starting or restarting any run, ask the user to confirm the task list, backend and `--workers` (default 3). From the repo root, inside `tmux`:

```sh
# Claude (Mac shown; GHC uses ghc-run.sh)
python3.12 claude_low_queue.py --workers 3 --retry-failed --tasks tasks/mac.txt --output .experiments/manual-claude-low-v2 2>&1 | tee -a queue.log
# Codex (Windows)
python3.12 claude_low_queue.py --backend codex --workers 3 --retry-failed \
    --manifest experiments/windows-100/runner-manifest.json --tasks tasks/windows.txt \
    --output .experiments/codex-low-windows 2>&1 | tee -a queue.log
```

- Resume: rerun the same command. `done` and `non_convergent` tasks are skipped, others resume from saved calls; `--retry-failed` also retries `failed` ones.
- Progress: `<output>/queue-status.json` (state per task) and `<output>/<task>.log`. View: `python3 view_experiment.py <output> --simplification <output>/simplification --serve 8000`, then open http://localhost:8000.
- Results: `<output>/results/<task>/` (refinement; `result.json` status `converged` or `non_convergent`) and `<output>/simplification/<task>/`. Repository copies are deleted when a task finishes.
- Usage limits and API errors wait 10 minutes and retry; a task that fails otherwise is `failed` with the reason in its log.
- One feature by hand: `python3 run_experiment.py run --backend claude|codex --effort low --manifest M --task T --output O`, then, only if converged, `python3 simplify_specifications.py O/results/T --output O/simplification`.
- Quick checks: `python3 run_experiment.py smoke --backend codex|claude --output .experiments/<name>-smoke`; tests: `python3 -m unittest discover -s tests`.

## Rules

- Never correct judgments by hand or ask for replacement judgments. Keep the original model outputs.
- Simplify only when `results/<task>/result.json` has `"status": "converged"`.
- No tests by default (decided 2026-11-15): features started from then on install no environments, generators may not run repository code, and no post-run checks run; criterion 1 is patch application only. `--tests` (runner and queue) opts new features into tests. A started feature keeps the setting it began with (`no_tests` in `results/<task>/settings.json`).
- Every session: `git pull` before starting or restarting a queue, so it runs the current protocol. Keep `--safe-mode` in the Claude command (`claude_command` in `run_experiment.py`): Claude 2.1.325 supports it, and it keeps user CLAUDE.md, plugins and hooks out of experiment sessions. If a CLI rejects it, update that CLI rather than removing the flag.
- Generators and editors run at `--effort low`; judges always run at high effort (the runner enforces this). Codex uses GPT-6 Luna and Claude uses Haiku, each judging its own runs.
- Existing result and simplification folders reject changed settings. When you edit `run_experiment.py` or `simplify_specifications.py`, add the old `runner_sha256` (and old `simplifier_sha256`) to the compatibility lists in `resume_settings` (`run_experiment.py`) and `simplify_specifications.py`, so running experiments keep resuming.
- Result files record paths relative to their experiment folder or the repo; readers remap old absolute paths (e.g. from GHC's `/tmp/aechang`). Never pass machine-specific paths in code; use arguments or environment variables.
- Run experiments token-efficiently: launch, log, and wait; inspect a few intermediate results only to catch setup failures, and individual artifacts only to explain outcomes.
- Keep docs concise: outcomes, decisions, evidence; compact tables; link raw artifacts. Update existing summaries instead of appending; label superseded protocols.
- Commit only the files your change touches (other work shares the tree); never commit secrets or `tasks/<task>/` workspaces.

## Requirements (all machines)

`git`, `rsync`, `tmux`, `uv`, `python3.12` (the queue), a C/C++ compiler, `make`, zlib headers, and a logged-in `claude` or `codex` CLI. Each task's Python comes from `environment-specs.json` (`official_spec.python`) via `uv`; the queue raises versions below 3.8 to 3.8. The queue sets `CFLAGS=-DFT_CONFIG_OPTION_SYSTEM_ZLIB LDFLAGS=-lz` for matplotlib. On Linux, Claude and Codex run unsandboxed (AppArmor blocks their sandboxes); model sessions have no network.

## Mac

- Setup: `brew install uv tmux python@3.12`; `claude auth login` (Claude Code at `~/.local/bin/claude`) and/or `codex login`.
- Run the Mac queue as above. macOS-only workarounds already in manifests: `SKLEARN_NO_OPENMP=1`, `-Wno-error` CFLAGS, and x86_64/Rosetta Python 3.8 for the numpy 1.19.2 sklearn group.
- GHC supervision: launchd job `edu.cmu.aechang.llm-ghc` (install or update with `./install-mac-jobs.sh` after changing `ghc-recover.sh`, `pull-ghc-results.sh` or `prune-ghc-afs-results.sh`; it copies them to `~/.local/share/llm-ghc/`, because launchd cannot run scripts from `~/Documents`). Hourly at :05 it runs `ghc-recover.sh` (Kerberos ticket from the Keychain → GHC `/tmp/<user>-krb5cc`; runs setup if `/tmp/<user>` or a tmux session is gone; on a health-check PROBLEM, a headless `claude -p` fixer on GHC, at most hourly; `FIXER_TEST=1` tests it), then `pull-ghc-results.sh` (copies GHC's untracked `.experiments/` folders here, never deletes) and `prune-ghc-afs-results.sh` (frees AFS of finished features the Mac has). Log: `~/.local/share/llm-ghc/job.log`. State: `./ghc-recover.sh --check`.
- Mac queue supervision: the same hourly job then runs `mac-watch.sh`: `ghc-health-check.sh` on `.experiments/manual-claude-low-v2` (no tokens) and, only on PROBLEM, sends the problem (with the queue restart command; `mac-tasks.txt` there = `tasks/mac.txt` + `tasks/mac-100.txt`) to the existing supervising Orca session via `orca terminal send`, at most hourly. It never launches a separate fixer. Terminal handle: one line in `~/.local/share/llm-ghc/mac/supervisor-terminal` (`orca terminal list --json`); update it if the session is replaced. Needs Full Disk Access for `/bin/bash` (granted 2026-11-16). `NOTIFY_TEST=1` tests delivery.
- Run the pull only via `launchctl kickstart gui/$(id -u)/edu.cmu.aechang.llm-ghc`: launchd cannot open `~/Documents` folders that another app created (`open: Operation not permitted`), unless `/bin/bash` has Full Disk Access.
- Script settings (env vars, defaults keep current behavior): `HOST` (GHC login, `aechang@ghc40.ghc.andrew.cmu.edu`), `GHC_USER`, `GHC_BASE` (`/tmp/<user>`), `KRB_PRINCIPAL` (`<user>@ANDREW.CMU.EDU`), `REPO`, `REMOTE`, `AFS`, `LABEL`.

## GHC (`ghc40.ghc.andrew.cmu.edu`, Linux)

- GHC reboots daily around 06:50 and empties `/tmp`. Work lives in `BASE=/tmp/<user>` (`/tmp/aechang`; repo at `$BASE/llm-improvement-loop`). What must survive is on AFS in `~/private/llm/` (2 GB quota; keep it under ~500 MB): `setup.sh`, `AGENTS.md`, `CLAUDE.md`, `repo.git` (bare mirror), `claude-config/` and `results/` (small files only).
- After a reboot: `bash ~/private/llm/setup.sh` (bash, not `source`; safe to rerun). It restores repo, results and Claude config, installs uv, Codex and Ollama into `$BASE`, writes `$BASE/env.sh` (source it in every shell), and starts tmux sessions `renew` (hourly `kinit -R && aklog`), `backup` (`ghc-backup.sh` every 15 min, which also refreshes AFS's `setup.sh`, guides and `repo.git`) and `queue` (`ghc-run.sh claude`: `tasks/ghc.txt`, 5 workers, log `$BASE/ghc-run.log`). Without a Claude login it starts all but `queue`: run `. $BASE/env.sh && claude`, log in, rerun setup. The Qwen track (`ghc-run.sh qwen`) is stopped.
- Always use Claude through `env.sh` (`CLAUDE_CONFIG_DIR=$BASE/claude-config`); a `claude` on `~/.claude` rotates the shared login.
- Health: `bash ghc-health-check.sh` prints OK or PROBLEM lines (stopped queue, failed task, a refining/simplifying task with no file changed in 60 minutes).
- Deploy code: commit and push on the Mac, then on GHC `git pull` (no GitHub credentials there; GHC commits stay local) and push the AFS mirror: `export KRB5CCNAME=FILE:/tmp/aechang-krb5cc; aklog; git push -q --force ~/private/llm/repo.git main`. Running tasks keep their loaded code; each new step uses the new code, so keep the compatibility lists current.
- Other settings: `ghc-setup.sh` takes `BASE`, `AFS`, `KRB_PRINCIPAL`, `KRB5_FILE`, `REPO_URL`, and test overrides `GHC_TMUX`, `DRY_RUN=1`; `ghc-run.sh` takes `BASE`, `GHC_TASKS`, `GHC_OUTPUT`.
- Ollama (Qwen side runs) uses the GPU through Vulkan; the 12.4 driver is too old for its CUDA build.

## Windows (WSL2, Ubuntu)

The code is Unix-only; run it in WSL2, in the Linux filesystem (`~`), not `/mnt/c`.

1. PowerShell (admin): `wsl --install -d Ubuntu`, reboot, create the Linux user. Keep Windows awake while running (Settings → Power → never sleep).
2. Ubuntu: `sudo apt update && sudo apt install -y build-essential git rsync tmux curl zlib1g-dev pkg-config libfreetype6-dev`.
3. uv and Python: `curl -LsSf https://astral.sh/uv/install.sh | sh`, open a new shell, `uv python install 3.12` and put it on PATH as `python3.12` (`ln -s "$(uv python find 3.12)" ~/.local/bin/python3.12`).
4. Codex CLI (as GHC pins it): `curl -fsSL https://github.com/openai/codex/releases/download/rust-v0.169.0/codex-x86_64-unknown-linux-musl.tar.gz | tar -xz -C ~/.local/bin && mv ~/.local/bin/codex-x86_64-unknown-linux-musl ~/.local/bin/codex`, then `codex login` (ChatGPT login; no API key). Optional Claude: `curl -fsSL https://claude.ai/install.sh | bash && claude auth login`.
5. `git clone https://github.com/AndrewChang-cpu/llm-improvement-loop.git ~/llm-improvement-loop && cd ~/llm-improvement-loop`, then `python3 run_experiment.py smoke --backend codex --output .experiments/codex-smoke-windows`.
6. After the user confirms, start the Codex queue in tmux:
   `mkdir -p ~/llm-watch && tmux new-session -d -s queue "BASE=$HOME/llm-watch GHC_TASKS=tasks/windows.txt GHC_OUTPUT=.experiments/codex-low-windows BACKEND=codex MANIFEST=experiments/windows-100/runner-manifest.json ./ghc-run.sh claude 2>&1 | tee -a $PWD/queue.log; exec bash"`
7. Hourly watcher: `sudo apt install -y cron && sudo systemctl enable --now cron`, then add with `crontab -e`:
   `5 * * * * $HOME/llm-improvement-loop/windows-watch.sh >> $HOME/llm-watch/watch.log 2>&1`.
   Set the existing supervising Orca terminal handle in `~/llm-watch/supervisor-terminal` (one line; discover with `orca terminal list --json`). Each run executes `ghc-health-check.sh` without tokens. On PROBLEM (queue stopped unfinished, a failed task, or no feature file changed in 60 minutes), it sends a prompt to that existing session through `orca terminal send`, at most once per hour. It never launches a separate fixer. The supervising session and Orca must remain available; update the handle if the session is replaced. Test delivery with `NOTIFY_TEST=1 ./windows-watch.sh`. Log: `~/llm-watch/watch.log`.

- Tasks: `tasks/windows.txt` = `experiments/windows-100/`, a seeded uniform random sample of the 1,299 FEA-Bench PRs outside batch-100 and the two pilots (the study's goal is all 1,401). Each PR is installed the way FEA-Bench's harness does it: batch-100's validated install lists for repositories batch-100 covers, otherwise the install table FEA-Bench inherits from SWE-bench (converted to pip; sympy tests selected by name with `pytest -k`). These environments are unvalidated; a task whose reference checks fail ends `failed` during preparation (see its log) and needs a manifest fix, not a rerun.
- Sync results back: commit `.experiments/codex-low-windows` (`.gitignore` drops workspaces) on a branch and push, or `rsync -a --exclude tasks/ .experiments/codex-low-windows/ <mac>:<repo>/.experiments/codex-low-windows/`.
