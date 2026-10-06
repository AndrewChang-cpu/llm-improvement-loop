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

The loop tests ten fresh generations per revision, allows ten editor revisions after baseline, and requires 9/10 in both qualifying and confirmation batches. Repeating the command resumes saved calls; changed settings or runner code require a new output folder. Authentication or quota failures stop execution rather than count as feature failures.

## Inspect and audit

```sh
python3 view_experiment.py seaborn-heading-run
python3 run_experiment.py audit --output .experiments/seaborn-heading-run
```

The viewer prints an HTML path for scores, specifications, and changes. Before running `audit`, fill the manual verdicts in the run’s `audit/sample.json`; keep `judge-key.json` closed until review is complete.

Exact prompts: [run_experiment.py](run_experiment.py) and saved `request.json` files. Task requirements, dependencies, and selected tests: [pilot.json](experiments/pilot.json). Filesystem access is unrestricted; network access is disabled for model sessions.

Runner validation, when needed: `python3 -m unittest discover -s tests -v`.

## Section-removal analysis

```sh
python3 analyze_specifications.py sphinx-heading-reru seaborn-heading-run
```

Each approved heading is removed independently from the final specification. Other sections, including repeated requirements, remain intact. Generation, permissions, and evaluation reuse the experiment runner; no editor, fresh full-spec control, or confirmation batch is run. `--runs N` sets repetitions per removal (default: 1).

Shared results: `.experiments/ablation-analysis.json`. Detailed artifacts: `.experiments/ablations/`. Completed matching analyses are skipped; partial analyses resume. Changed inputs/settings require a different `--output` file.

Each experiment records its headings, settings, specification hash, saved full-spec scores, and each removal's per-run criterion verdicts and pass counts. Aggregate results count section occurrences and average criterion pass-rate changes relative to the saved qualifying and confirmation batches, weighting each experiment equally. One-run differences are exploratory and include generation/judge variability.
