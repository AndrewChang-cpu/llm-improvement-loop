# Pilot results

All roles used GPT-6 Luna. A run passes every required criterion; convergence requires at least 9/10 in an initial batch and 9/10 in a fresh confirmation batch using the same specification.

## Current runs

| Batch | Sphinx #11989 | Seaborn #3063 |
| --- | ---: | ---: |
| PR baseline | 0/10 | 0/10 |
| Revision 1 | 0/10 | 6/10 |
| Revision 2 | 9/10 | 10/10 |
| Revision 2 confirmation | 9/10 | 10/10 |
| Outcome | Converged | Converged |

Both runs use the same runner version and approved heading inventory. Each evaluated 40 patches. Final specifications use approved headings.

| Run | Artifact folder under `.experiments/` |
| --- | --- |
| Sphinx | `sphinx-heading-reru/results/sphinx-doc__sphinx-11989/` |
| Seaborn | `seaborn-heading-run/results/mwaskom__seaborn-3063/` |

Each folder contains `result.json`, `comprehensive-specification.md`, and per-revision specifications, edits, patches, checks, and judgments. Confirmation is inside its qualifying revision folder.

## Failures and improvements

| Task | Baseline failures | Later failures | Final result |
| --- | --- | --- | --- |
| Sphinx | Executable checks, API, extension-point use, intent, conventions | Revision 1: checks, API, intent, conventions, registration | One initial-batch failure: checks/API; one confirmation failure: checks |
| Seaborn | Executable checks, API, intent, conventions; architecture in one run | Revision 1: four convention failures involving documentation or test organization | All criteria passed in both final batches |

Seaborn revision 1 passed all executable checks. Revision 2 clarified documentation, API listing, release notes, and test organization. All ten revision-1 patches omitted API listing updates, yet six received full passes: documentation judging was inconsistent. Original judgments were retained.

## Section-removal analysis

One fresh generation per removed section; no editor, fresh full-spec control, or confirmation. Scores below count runs passing all eleven criteria.

| Removed section | Sphinx | Seaborn |
| --- | ---: | ---: |
| Goals | 1/1 | 1/1 |
| Scope | 1/1 | — |
| Terminology | 1/1 | — |
| Workflows | 1/1 | 1/1 |
| Data model | 1/1 | 1/1 |
| API contracts | 0/1 | 0/1 |
| Module architecture | 1/1 | 1/1 |
| Implementation constraints | 1/1 | 1/1 |
| Documentation | 1/1 | 0/1 |
| Behavioral acceptance criteria | 0/1 | 1/1 |
| Test requirements | 0/1 | 1/1 |
| Dependencies | — | 1/1 |
| Naming | — | 0/1 |
| Validation | — | 1/1 |
| Compatibility | — | 1/1 |
| **Total** | **8/11** | **10/13** |

- **Sphinx failures:** API contracts (index output), Behavioral acceptance criteria (signature rendering), Test requirements (missing tests and executable failure).
- **Seaborn failures:** API contracts (incorrect generated-test expectations), Documentation (missing parameter/behavior documentation), Naming (unused import).
- Removing Goals, Workflows, Data model, Module architecture, or Implementation constraints passed in both tasks. Overlapping information remains in other sections; these results do not establish that the removed sections are unnecessary.
- Both API-contract removals failed overall, but their failure causes differed. One-run differences include generation and judge variability and are exploratory, not causal rankings.

[Shared JSON](../.experiments/ablation-analysis.json) records raw criterion judgments, evidence, settings, section counts, and aggregate pass-rate changes against the saved twenty-run full-spec results. Detailed artifacts are under `.experiments/ablations/`. Completed matching analyses are skipped; repeating the command verified this without new model calls. Transcript inspection found no generator reads of reference/feedback or judge reads of specifications; protected inputs were unchanged.

## Experiment timeline

Approximate sequence; early stages are reconstructed from planning and archived pilot records.

- **Initial design:** Proposed testing RE categories against historical features, using ten generations per specification and an LLM judge focused on architecture.
- **Narrowed the data:** Selected FEA-Bench feature tasks and began with Sphinx #11989 and Seaborn #3063 rather than the full dataset.
- **Defined the main experiment:** Chose one feedback-driven revision at a time. The comprehensive specification would emerge from convergence, rather than adding every category or testing each category independently.
- **Simplified evaluation:** Replaced weighted 0–2 scores with pass/fail criteria. Every required criterion must pass; the threshold remained 9/10.
- **Simplified the baseline:** Replaced a generated behavioral prompt with the original PR title and description verbatim, including code.
- **Established role boundaries:** Generator sees the specification and original code; judge and editor see reference code. Adopted tool-enabled headless Codex with Luna for all roles. Edited specifications must instruct implementation without supplying actual code.
- **Encountered conflicting requirements:** Sphinx’s PR described `value`, while merged code used `canonical`. Judging both as authoritative rejected implementations that matched reference tests and drove contradictory revisions.
- **Fixed evaluation authority:** Made reference code authoritative for judging and editing. Kept the PR solely as baseline input, with no separate PR-derived requirements for judge or editor.
- **Resolved execution restrictions:** Enabled full filesystem access so Git and Python worked, while keeping model-session networking disabled. Added reusable per-PR generator and evaluation virtual environments.
- **Encountered incorrect diagnoses:** Judges confused inherited option acceptance with expression rendering and invented nesting/deletion failures. Added complete-inheritance instructions, original-to-candidate comparisons, recorded API facts, and full executable logs in editor feedback.
- **Narrowed editor instructions:** Required verification against complete reference methods, edits addressing actual failure causes, and preservation of correct constraints. No additional reviewer was added.
- **Protected experiment records:** An editor overwrote specification archives. Prohibited file writes and added snapshots and integrity checks for protected judge/editor inputs.
- **Corrected the test harness:** Reference overlays could hide failing candidate tests or orphan candidate fixtures. Ran candidate tests first, then restored original fixtures and overlaid reference tests. Made Sphinx’s documented test-addition policy explicit.
- **Removed manual intervention:** During supervision, Codex selectively retried judges/editors with factual hints. You prohibited this. Those attempts became diagnostic records; the unassisted trajectory used original judgments, including errors.
- **Observed initial convergence:** Sphinx reached revision 5 at 9/10 plus 9/10 confirmation. Revision 4’s 10/10 dropped to 7/10 in confirmation, showing why one qualifying batch was insufficient.
- **Standardized specification structure:** Replaced bespoke headings with approved subsection names. Updated the editor prompt without adding heading-enforcement logic.
- **Reran under the final category inventory:** Sphinx converged at revision 2 with 9/10 plus 9/10 confirmation; Seaborn converged at revision 2 with 10/10 plus 10/10. Seaborn needed no protocol changes during execution.

The PR/reference conflict was conflicting evaluation authority, not evidence of unintended generator leakage. Reference access by the editor is intentional. Full filesystem access makes generator isolation dependent on instructions; Seaborn transcript inspection found no reference/feedback reads. Earlier corrected or superseded trajectories remain separate from current results. Detailed provenance is in [the archive](../.experiments/documentation-archive.md).

## Final specifications and interpretation

| Specification | Main implementation guidance | Sections | Confirmed result |
| --- | --- | ---: | --- |
| [Sphinx](../.experiments/sphinx-heading-reru/results/sphinx-doc__sphinx-11989/comprehensive-specification.md) | Reuse PyObject and annotation parsing; define canonical display/registration, roles, indexing, nesting boundaries, documentation, and regression coverage | 11 | 9/10 + 9/10 |
| [Seaborn](../.experiments/seaborn-heading-run/results/mwaskom__seaborn-3063/comprehensive-specification.md) | Reuse Stat and GroupBy; define percentile parameters, output rows, orientation, missing values, module/export locations, compatibility, documentation, and tests | 13 | 10/10 + 10/10 |

Both specifications instruct implementation without supplying implementation code. They share nine sections: Goals, Workflows, Data model, API contracts, Module architecture, Implementation constraints, Documentation, Behavioral acceptance criteria, and Test requirements. Additional sections express task-specific needs.

The successful outputs combine behavioral intent with concrete repository mechanisms and public contracts. Seaborn’s functional checks passed at revision 1, but documentation/test conventions required another revision; passing tests alone did not satisfy the evaluation.

The process demonstrates convergence for two reference-informed tasks. It does not establish which category was necessary, that the final specs are minimal, or that the same improvements follow without reference access. Some instructions overlap across sections, and multiple changes were introduced together.

Judgment uncertainty remains: Seaborn’s revision-1 documentation omission was inconsistently graded, and human calibration is pending. Confirmation provides additional observed evidence, not proof that the underlying success probability is at least 90%.
