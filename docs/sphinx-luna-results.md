# Sphinx pilot results: Luna loop

Sphinx PR11989 converged at revision five: **9/10 full passes, followed by 9/10 fresh confirmation passes**. Baseline: 0/10. All roles used GPT-6 Luna with high reasoning effort; the threshold stayed 9/10.

| Specification | Full passes | Candidate tests pass | Reference tests pass |
| --- | --- | --- | --- |
| revision-00 | 0/10 | 10/10 | 0/10 |
| revision-01 | 0/10 | 10/10 | 8/10 |
| revision-02 | 2/10 | 10/10 | 9/10 |
| revision-03 | 4/10 | 10/10 | 6/10 |
| revision-04 | 10/10 | 10/10 | 10/10 |
| revision-04/confirmation | 7/10 | 10/10 | 9/10 |
| revision-05 | 9/10 | 10/10 | 10/10 |
| revision-05/confirmation | 9/10 | 10/10 | 10/10 |

All twenty revision-five implementations passed the selected candidate and reference suites. One candidate in each batch failed convention fit because its added tests did not verify role parsing/resolved links. Registration and direct object lookup alone were judged insufficient.

The loop progressively added canonical-expression parsing, index rules, nesting restrictions, documentation, resolved-link tests, generic object references, and signature punctuation. Revision four's 10/10 did not reproduce in confirmation (7/10), prompting another refinement.

File placement and dependency boundaries already passed in the baseline. Most measured gains concern API behavior, existing annotation-parser use, indexing, documentation, and test coverage; this task gives limited evidence about broader architectural placement.

## Judge errors and recovery

Two observed judges falsely denied inherited `canonical` acceptance: baseline run09 and revision-four confirmation run08. Their API probes explicitly show acceptance. The baseline editor independently recognized acceptance versus rendering; later refinement retained canonical support. The loop converged despite these errors. This supports Luna's viability for this pilot, but does not establish that judgment errors generally average out.

Revision-two runs04 and08 were awarded full passes despite lacking feature documentation/changelog changes, unlike several comparable candidates. Their judgments were not replaced. Scores above are recorded judge decisions, not independently validated truth.

## Provenance

Original judgments and editor responses were forwarded unchanged. A previously requested hinted baseline retry was excluded before any editor consumed it; the original verdict was restored. No selective regrading, corrective hints, model changes, or rubric changes affected this trajectory. Earlier attempts are separate protocol-tuning data. Seaborn was not run.

Generator command inspection found no reads of reference/feedback artifacts. Full filesystem access means this is an observed boundary, not technical isolation. Human judge calibration remains pending; the generated audit sample is available for that review.

Artifacts: `.experiments/supervised-2026-10-04-l/results/sphinx-doc__sphinx-11989/`, including `analysis.json`, `result.json`, and `comprehensive-specification.md`. Detailed per-criterion counts are in `analysis.json`; experiment problems are in [the hiccup record](experiment-hiccups.md).
