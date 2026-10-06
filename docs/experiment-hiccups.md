# Experiment problems

Only problems that affected results or the refinement loop are listed here. Routine setup issues are omitted. Detailed history remains in [Experiment adjustments](experiment-adjustments.md).

- **Conflicting evaluation authority.** Earlier judges enforced the PR’s `value` option while reference tests expected `canonical`. Evaluation now uses the reference implementation as truth.
- **Incorrect or inconsistent judgments.** Judges missed inherited `canonical` support, demanded nesting behavior absent from the reference, misidentified deleted tests, and inconsistently enforced test/documentation conventions. Explicit evidence and stronger instructions have not eliminated these errors.
- **Seaborn documentation inconsistency.** All ten revision-one patches omitted API listing updates, but six received full passes; two failing judges explicitly cited that omission. Verdicts were retained unchanged. The loop converged at revision two with 10/10 plus 10/10 confirmation; see [results](seaborn-luna-results.md).
- **Incorrect specification revisions.** Editors introduced requirements contradicting the reference, changed wording without addressing runtime failures, and attempted to remove correct constraints. Complete check logs and more focused instructions were added.
- **Archived specifications overwritten.** An editor modified earlier specification files. Archives were recovered; explicit write prohibitions and input-integrity checks were added.
- **Unreliable test evaluation.** Reference overlays could hide failing generated tests or orphan valid generated fixtures. Candidate tests now run first; reference checks use their own fixture set. The fixture correction was verified against the affected patch and regression checks.
- **Manual intervention in the loop.** Codex selectively retried judges/editors with corrective hints. Those trajectories are diagnostic, not evidence of an autonomous loop. Future manual corrections are prohibited.

The Sphinx loop converged with Luna at revision five: 9/10 passes and 9/10 fresh confirmation passes, using original judgments without corrective hints. The threshold remained 9/10. See [results](sphinx-luna-results.md). Full filesystem access still leaves role boundaries dependent on instructions; human judge calibration remains pending.
