# Seaborn pilot results: Luna loop

Seaborn PR #3063 converged at revision two: **10/10 full passes and 10/10 fresh confirmation passes**. The original PR baseline scored 0/10. All roles used GPT-6 Luna with high reasoning effort; the stopping threshold remained 9/10.

| Specification | Full passes | Candidate tests pass | Reference tests pass |
| --- | --- | --- | --- |
| revision-00 | 0/10 | 10/10 | 0/10 |
| revision-01 | 6/10 | 10/10 | 10/10 |
| revision-02 | 10/10 | 10/10 | 10/10 |
| revision-02/confirmation | 10/10 | 10/10 | 10/10 |

Forty patches were generated and judged, with two specification-editor calls. Each confirmation candidate was independently generated from the same revision-two specification.

## What changed

The baseline contains a short plotting example and image link. Its implementations interpreted integer input as a percentile level rather than a count, omitted interpolation selection, or produced scalar/interval output instead of percentile-labeled rows. All failed the reference test collection because the expected `seaborn._stats.order` module was absent. Their own tests passed, demonstrating that candidate-written tests alone did not establish the reference contract.

Revision one specified public parameters and defaults, output data, order-statistics module placement, Stat inheritance, GroupBy use, orientation, missing values, and NumPy compatibility. All ten patches then passed both executable test stages. Four still failed convention fit for documentation or test organization.

Revision two expanded Documentation to cover usage examples, API listing, and release notes, and clarified Test requirements to follow local fixture/test-class organization. Both subsequent batches passed every criterion.

The final specification uses thirteen approved headings: Goals, Workflows, Data model, API contracts, Module architecture, Implementation constraints, Dependencies, Naming, Validation, Documentation, Compatibility, Behavioral acceptance criteria, and Test requirements. Neither edited specification contains implementation code.

## Observed uncertainty

Documentation judgments were inconsistent in revision one. All ten patches omitted public API listing updates; six nevertheless received full passes. Runs 05 and 06 explicitly cited that omission as a convention failure. Original verdicts were retained and forwarded unchanged; no selective regrading or corrective hints were used.

The result shows convergence for this task, not the isolated causal contribution of individual categories. Most improvement addressed the public API, output behavior, import location, and documentation. Human judge calibration remains pending.

## Provenance

No runner, prompt, model, rubric, or threshold changes were made during this run. Recorded generator file changes stayed inside each candidate workspace. Command inspection found no generator reads of reference/feedback artifacts or judge reads of PR descriptions/current specifications. Protected-input integrity checks passed. Filesystem access remains unrestricted, so these are observed boundaries rather than enforced isolation.

Artifacts: `.experiments/seaborn-heading-run/results/mwaskom__seaborn-3063/`, including `result.json`, `analysis.json`, and `comprehensive-specification.md`. Ten randomly selected cases are available in `.experiments/seaborn-heading-run/audit/sample.json` for human review.
