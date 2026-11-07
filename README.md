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
python3 run_experiment.py audit --output .experiments/seaborn-heading-run
```

The viewer prints an HTML path for scores, specifications, and changes. Before running `audit`, fill the manual verdicts in the run’s `audit/sample.json`; keep `judge-key.json` closed until review is complete.

Exact prompts: [run_experiment.py](run_experiment.py) and saved `request.json` files. Task requirements, dependencies, and selected tests: [pilot.json](experiments/pilot.json). Filesystem access is unrestricted; network access is disabled for model sessions.

Runner validation, when needed: `python3 -m unittest discover -s tests -v`.

## Section-removal analysis

The section-removal analysis below records the earlier protocol. New simplification validation uses:

```sh
python3 simplify_specifications.py sphinx-heading-reru seaborn-heading-run --output .experiments/simplification-validation-2026-11-07
```

It reuses a current-protocol 10/10 qualifying batch, or rechecks a historical starting specification with ten fresh implementations, then asks the editor for at least a 10% word-count reduction. Only 10/10 candidates are retained. The first insufficient reduction or failed batch stops simplification and preserves the last passing version. A starting batch below 10/10 does not qualify for simplification. There is no confirmation batch or one-section restriction. Counts use whitespace-separated words, including headings. Historical runs remain unchanged; new refinement runs use the current 10/10 stopping rule.

Results and word counts are in the output directory's `summary.json`; each experiment keeps proposals, decisions, and detailed evaluation artifacts. Repeating the command resumes saved calls; changed inputs require a fresh output directory.

```sh
python3 analyze_specifications.py sphinx-heading-reru seaborn-heading-run
```

Each approved heading is removed independently from the final specification. Other sections, including repeated requirements, remain intact. Generation, permissions, and evaluation reuse the experiment runner; no editor, fresh full-spec control, or confirmation batch is run. `--runs N` sets repetitions per removal (default: 1).

Shared results: `.experiments/ablation-analysis.json`. Detailed artifacts: `.experiments/ablations/`. Completed matching analyses are skipped; partial analyses resume. Changed inputs/settings require a different `--output` file.

Each experiment records its headings, settings, specification hash, saved full-spec scores, and each removal's per-run criterion verdicts and pass counts. Aggregate results count section occurrences and average criterion pass-rate changes relative to the saved qualifying and confirmation batches, weighting each experiment equally. One-run differences are exploratory and include generation/judge variability.
