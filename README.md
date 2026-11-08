# Specification refinement experiment

[Research design](docs/research-design.md) · [Methodology](docs/experimental-methodology.md) · [References](docs/references.md) · [Results](docs/results.md) · [Future notes](docs/notes-for-the-future.md)

## Run

Use Python 3.9–3.11 and a Codex CLI logged in through ChatGPT. All roles default to GPT-6 Luna; no API key is required.

```sh
python3 run_experiment.py smoke
python3 run_experiment.py run --task sphinx-doc__sphinx-11989 --output .experiments/new-sphinx-run
python3 run_experiment.py run --task mwaskom__seaborn-3063 --output .experiments/new-seaborn-run
```

`run` prepares missing original/reference snapshots and reusable per-task virtual environments, verifies reference tests, then executes refinement. `prepare` performs setup without model calls. Omitting `--task` runs both pilot tasks.

The loop tests ten fresh generations per revision, allows ten editor revisions after baseline, and requires 10/10 in one batch without confirmation. Repeating the command resumes saved calls; changed settings or runner code require a new output folder. Authentication or quota failures stop execution rather than count as feature failures.

## Inspect and audit

```sh
python3 view_experiment.py seaborn-heading-run
python3 view_experiment.py .experiments/restart-simplification-2026-11-07 --simplification .experiments/simplification-three-candidates-2026-11-07 --output .experiments/evaluation.html
python3 run_experiment.py audit --output .experiments/seaborn-heading-run
```

The viewer combines features in one HTML with a feature selector. Each graph shows refinement followed by accepted simplifications; rejected proposals are omitted. Supply a batch directory or multiple loop paths, and add `--simplification DIR` for saved simplification results. Before running `audit`, fill the manual verdicts in the run’s `audit/sample.json`; keep `judge-key.json` closed until review is complete.

Exact prompts: [run_experiment.py](run_experiment.py) and saved `request.json` files. Task requirements, dependencies, and selected tests: [pilot.json](experiments/pilot.json). Filesystem access is unrestricted; network access is disabled for model sessions.

Runner validation, when needed: `python3 -m unittest discover -s tests -v`.

## Resume the 100-PR batch

From this checkout:

```sh
python3 batch_driver.py --auto-retry
```

Runs one PR at a time, with ten parallel implementation/evaluation lanes per batch. Saved work is reused. Usage-limit errors wait until the reported local reset time plus one minute, or retry hourly when no reset time is available. Temporary network errors retry after 1, 5, then 15 minutes (capped at 15). Authentication, configuration, and unexpected errors stop for inspection; permanent preparation failures are recorded separately. Ctrl+C pauses; rerun the same command to resume. Keep the terminal running and computer awake. No Orca automation or supervising LLM is required.

The driver updates `.experiments/batch-100/evaluation.html` after each completed PR. Generate one report including the batch and the earlier two features:

```sh
python3 view_experiment.py .experiments/batch-100 .experiments/restart-simplification-2026-11-07 \
  --simplification .experiments/batch-100/simplification \
  --simplification .experiments/simplification-three-candidates-2026-11-07 \
  --output /Users/andrew/orca/workspaces/llm-improvement-loop/humpback/.experiments/evaluation.html
```

## Section-removal analysis

The section-removal analysis below records the earlier protocol. New simplification validation uses:

```sh
python3 simplify_specifications.py .experiments/new-sphinx-run .experiments/new-seaborn-run --output .experiments/simplification-search
```

It reuses a current-protocol 10/10 qualifying batch, or rechecks a historical starting specification with ten fresh implementations. Each round asks three independent editor sessions to shorten the same retained specification by 10–30%. All three drafts are proposed before evaluation. Each in-range draft receives ten fresh implementations; the shortest draft scoring 10/10 becomes the next incumbent. Ties use candidate order. The first round without a qualifying candidate stops the search and preserves the previous passing version. There is no confirmation batch or one-section restriction. Word counts include headings. Historical runs remain unchanged.

Results and word counts are in the output directory's `summary.json`; each experiment keeps proposals, decisions, and detailed evaluation artifacts. Repeating the command resumes saved calls; changed inputs require a fresh output directory.

```sh
python3 analyze_specifications.py sphinx-heading-reru seaborn-heading-run
```

Each approved heading is removed independently from the final specification. Other sections, including repeated requirements, remain intact. Generation, permissions, and evaluation reuse the experiment runner; no editor, fresh full-spec control, or confirmation batch is run. `--runs N` sets repetitions per removal (default: 1).

Shared results: `.experiments/ablation-analysis.json`. Detailed artifacts: `.experiments/ablations/`. Completed matching analyses are skipped; partial analyses resume. Changed inputs/settings require a different `--output` file.

Each experiment records its headings, settings, specification hash, saved full-spec scores, and each removal's per-run criterion verdicts and pass counts. Aggregate results count section occurrences and average criterion pass-rate changes relative to the saved qualifying and confirmation batches, weighting each experiment equally. One-run differences are exploratory and include generation/judge variability.
