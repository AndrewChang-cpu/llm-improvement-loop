# Pilot results

## Restarted refinement and simplification (2026-11-07)

New refinement requires 10/10 in one batch, without confirmation. Sphinx restarted from the PR baseline and scored **0, 1, 8, 8, 8, 10** passes across revisions 0–5. Its passing specification contains 813 words. Seaborn scored **0, 5, 8, 7, 6, 8, 10** across revisions 0–6. Its passing specification contains 964 words. Simplification has retained two shorter specifications, 678 and then 558 words, each scoring 10/10. Round 3 is in progress; an account usage-limit interruption is recorded separately.

Sphinx's first, single-proposal simplification reduced 813 words to 528 (35%) and scored 9/10. It was rejected. The revised search proposes three independent drafts per round, each 10–30% shorter, evaluates each eligible draft ten times, and retains the shortest 10/10 candidate. The first round without a qualifying candidate stops the search.

| Sphinx candidate | Words | Reduction | Recorded passes | Outcome |
| --- | ---: | ---: | ---: | --- |
| 1 | 616 | 24.2% | 8/10 | Rejected |
| 2 | 578 | 28.9% | 8/10 | Rejected |
| 3 | 659 | 18.9% | 9/10 | Rejected |

No reduction was accepted; the retained specification remains 813 words. All 30 candidates passed the configured executable checks. The five rejected implementations had index behavior that differed from the reference: module-prefix handling when module names are disabled, or qualified aliases declared outside a class directive. Post-run execution reproduced those output differences; no judge verdict was replaced or fed corrected feedback.

**Diagnostic output differences do not automatically establish evaluation failures.** Applying the same three diagnostic cases to the original passing batch and all shortened batches produced the counts below. These checks cover only those index cases, not the full rubric.

| Batch | Recorded passes | Implementations matching all three diagnostic cases |
| --- | ---: | ---: |
| Original 813-word specification | 10/10 | 8/10 |
| Candidate 1 | 8/10 | 5/10 |
| Candidate 2 | 8/10 | 8/10 |
| Candidate 3 | 9/10 | 8/10 |

Two original passes and four shortened-specification passes differ from the reference on at least one diagnostic case. These include minor label differences, such as a trailing dot, which alone do not establish architectural or core-behavior failures. The probes therefore do not invalidate the recorded passes. The scores also do not establish that shortening caused a regression or that 813 words are necessary. No rubric or verdict has been changed.

Artifacts: [restarted refinement](../.experiments/restart-simplification-2026-11-07/), [three-candidate search](../.experiments/simplification-three-candidates-2026-11-07/), and [post-run validity audit](../.experiments/simplification-three-candidates-2026-11-07/sphinx-restart/index-validity-audit.json). Subscription-limit interruptions are logged separately and resumed from saved calls; they are not implementation failures. Access-log screening has found no forbidden generator reads; original snapshots match their pinned commits. The Sphinx original/reference hashes remained unchanged in the first completed run. Final access and snapshot checks accompany the completed results.

## Simplification validation (2026-11-07)

Fresh starting-specification batches used the current 10/10 requirement, with no confirmation. Historical results below remain unchanged.

| Existing experiment | Starting words | Fresh passes | Outcome |
| --- | ---: | ---: | --- |
| `sphinx-heading-reru` | 667 | 6/10 | Did not qualify for simplification |
| `seaborn-heading-run` | 588 | 9/10 | Did not qualify for simplification |

Sphinx had four runs with executable failures: two index-caption mismatches, one runtime error, and one malformed generated-test fixture. Seaborn passed every executable check; one judge rejected documentation example naming. Original judgments were retained. Neither task reached the simplification editor, so no live evidence of shortening or retained quality was obtained. The simplification acceptance/stopping logic passed mocked checks as part of 22 passing local tests; the Luna/tool smoke and both reference environments passed. No 100-PR run was started.

[Results JSON](../.experiments/simplification-validation-2026-11-07/summary.json) records the batches and criterion counts. Detailed outputs and logs are in the same validation directory. A shorter specification is accepted only if it reduces whitespace-separated word count by at least 10% and passes 10/10 fresh generations; the first unsuccessful attempt stops the loop and retains its previous passing version.

## Sphinx fresh-batch comparison

The starting specification is byte-for-byte identical to the historical final specification. All patches start from the same implementation-file Git blob (`75c2cdd`). This comparison examines generated patches and recorded checks, not a complete access-log audit for leakage.

| Fresh run | Difference from historical passing implementations | Recorded result |
| --- | --- | --- |
| `run-01`, `run-03` | Index text adds the literal words `containing class`: `Alias2 (type alias in containing class example.Class)` instead of `Alias2 (type alias in example.Class)`. Historical passing patches omit those words. | Candidate tests pass; reference tests reject the caption. |
| `run-02` | `get_index_text` unpacks `name, _ = name_cls`, shadowing the imported translation function `_`. For a nested alias, `_` is `None`, so calling it raises `TypeError`. Historical passing code uses another unpacking name. | Both candidate and reference tests fail. |
| `run-04` | Implementation passes reference tests, but its generated test strings omit a blank line between `.. py:class:: Container` and the nested directive. The parser interprets the nested directive as signature text instead of class content. | Candidate tests fail. The judge repeats the symptom as a nested-alias implementation deficiency; this comparison instead identifies malformed test input. No verdict was changed. |

The unchanged specification itself uses the ambiguous example “alias (type alias in containing class)”. Two fresh implementations interpret `containing class` literally. This is a concrete specification defect that earlier passing implementations happened to avoid. The two historical failed implementations instead used a different node structure for the `type` marker (`desc_sig_keyword` rather than plain text), which failed reference tree/HTML assertions. Thus the old and new failed samples do not share a single implementation defect.

Sources: [historical revision](../.experiments/sphinx-heading-reru/results/sphinx-doc__sphinx-11989/revision-02/), [fresh batch](../.experiments/simplification-validation-2026-11-07/sphinx-heading-reru/starting-batch/), and [unchanged specification](../.experiments/simplification-validation-2026-11-07/sphinx-heading-reru/starting-specification.md). These findings explain the observed failures but do not establish why their frequency changed or rule out leakage.

## Historical refinement and ablation results

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
