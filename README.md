# Specification refinement experiment

The runner prepares Sphinx #11989 and Seaborn #3063, then runs the PR-baseline and specification-refinement experiment described in [the methodology](docs/experimental-methodology.md).

Use Python 3.9–3.11 for the pilot's historical dependency versions and an installed Codex CLI logged in through ChatGPT. GPT-6 Luna is the default for all roles. No API key is required.

```sh
python3 run_experiment.py smoke
python3 run_experiment.py prepare
python3 run_experiment.py run --output .experiments/reference-authority --task sphinx-doc__sphinx-11989
```

`smoke` checks full filesystem access and a real model tool call. `prepare` downloads the PRs, creates original/reference snapshots and virtual environments, and verifies the reference tests without calling an LLM. `run` prepares any missing environment and executes the loop. Omit `--task` to run both pilot tasks.

The script tests ten fresh generations per revision, allows ten editor revisions after the original PR baseline, and confirms a qualifying specification with ten additional generations. Each batch runs ten independent lanes concurrently; each lane generates, checks, and judges its patch in sequence. There is no experiment-imposed token budget.

Corrected pilot artifacts live in `.experiments/reference-authority/`: specifications, role prompts, model transcripts, patches, checks, judgments, and edit histories. Repeating a command resumes completed calls. Authentication or quota failures stop execution rather than becoming feature failures. Changed experiment settings or runner code require a new `--output` directory.

After a run, manually fill the boolean judgments in `.experiments/reference-authority/audit/sample.json` using the supplied repository paths and requirements, then compare with the judge:

```sh
python3 run_experiment.py audit --output .experiments/reference-authority
```

The separate `judge-key.json` contains automated judgments; keep it closed until manual review is complete. The audit samples up to ten generated patches.

Implementation checks, if needed:

```sh
python3 -m unittest discover -s tests -v
```

Read [runner details and prompts](docs/experiment-runner.md) before starting the pilot.

View saved results without running the experiment:

```sh
python3 view_experiment.py reference-authority
```

Open the printed `evaluation.html` path in a browser. The chart shows category pass counts across revisions; below it, browse specifications or their changes from the previous revision. Partial batches show only saved judgments. You can also pass another loop directory or a specific task directory, and use `--output` to choose the HTML location.

Full filesystem access is now configured. Earlier restricted-access runs are diagnostic artifacts; choose a new `--output` folder for future experiment comparisons. The loop is currently stopped.
