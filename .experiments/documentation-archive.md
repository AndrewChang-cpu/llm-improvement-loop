# Archived documentation

Superseded by docs/results.md. Historical reports are retained for provenance, not pooled as current results.

---

## experiment-adjustments.md

# Experiment adjustments

## Reference authority correction — 2026-10-04

The reference implementation is the source of truth for feature behavior, public contracts, and intended architecture. The verbatim PR title and description remain the baseline generation input. No behavioral requirements are synthesized from the PR, and the PR is not supplied to the judge as a separate requirements source. The editor receives the current editable specification, reference/original/generated code, and judgment feedback, with instructions to correct draft content that conflicts with the reference.

Reason: Sphinx #11989's PR description specifies an optional `value` expression, while merged code uses `canonical`. Earlier judging enforced the former alongside tests enforcing the latter. Two revision-three patches passed every reference test but were rejected for the conflicting PR label; subsequent editing switched back to `value`.

The affected Sphinx baseline and revisions zero through three remain in `.experiments/results/`. Their outcomes are documented in [the diagnostic report](pilot-results-before-reference-authority.md) and excluded from corrected experimental results. The corrected pilot starts from fresh baseline runs in `.experiments/reference-authority/`, reusing the validated original/reference snapshots and dependency environments. All eleven criteria, ten independent runs, confirmation runs, and the ten-revision limit remain unchanged.

## Evidence verification and reference control — 2026-10-04

The judge prompt explicitly requires reference evidence for failures and prohibits inventing requirements from optional implementation choices. Earlier diagnoses incorrectly demanded `allow_nesting=True`, although the reference type-alias directive has `allow_nesting=False`.

Before resuming the pilot, evaluate copies of both reference patches using the same judge prompt and executable checks. These controls must pass every criterion. Controls are outside the ten-run experiment batches and do not count toward convergence. Both reference controls passed every criterion and their executable checks. Results are stored in `.experiments/reference-authority/reference-controls/`. This checks self-consistency with the evaluation target; it does not establish agreement with human reviewers.

Criterion removal remains a last resort. Any future adjustment must record its reason, affected artifacts, and whether it requires fresh comparisons. Changes are not silently mixed into existing cached results.

## Full filesystem access — 2026-10-04

At the user's instruction, replace the filesystem deny/minimal-read policy with `":root" = "write"` for all roles. Direct checks showed `/usr/bin/git --version` and `/usr/bin/python3 --version` worked outside the former profile but failed inside it because Apple's developer tools could not be located. Network access remains disabled. Direct checks under the new profile successfully ran Git 2.50.1 and Python 3.9.6.

Original/reference/generated task-code boundaries now depend on role instructions rather than filesystem enforcement. The generator is still instructed to inspect only its original-code workspace and specification; judges and editors must not modify code. Full filesystem access makes reference artifacts mechanically accessible, so future claims about generator blindness require transcript inspection.

Earlier constrained-access runs remain historical diagnostic results. This policy change requires a fresh output folder for a new comparison; it is not silently applied to the cached results. The loop remains stopped until the user explicitly requests resumption. The smoke check now expects workspace and outside-file reads to succeed.

Editor diagnosis: the session producing revision six read the reference parent method only through line 340 of `sphinx/domains/python/_object.py`. Its inherited canonical-registration branch begins at line 342. The editor then asserted that canonical text must not be registered. This is a concrete incomplete-source-reading error; broader edit scope and model reasoning are possible contributors, not established causes. The editor prompt has not been changed in this adjustment.

## Focused editor instruction — 2026-10-04

Add the following instruction to the existing editor prompt, retaining its existing add/clarify/reformat/remove permissions:

> Focus edits on the failures reported by the judge. Verify each diagnosis by reading the complete relevant reference methods, including inherited methods. Preserve correct requirements and explain which failed criterion each edit addresses.

This targets the incomplete method inspection and unsupported requirement reversal observed in revision six. No additional reviewer, recurring-failure mechanism, or criterion removal is introduced. The expected effect is a hypothesis to test in a fresh run; it has not been demonstrated yet.

## Remaining rerun prerequisites

The new filesystem profile passes direct Git and Python checks. A further preflight found that the default Python environment has pytest but cannot import `docutils`. This gap is addressed by the per-PR generator environment described below.

The previous run stopped during revision-six judging because Codex reported a ChatGPT usage limit. Confirm quota availability before rerunning. Use a new output folder because the filesystem policy and editor prompt have changed; preserve earlier results separately. No experimental sessions were launched during this prompt update.

## Programmatic generator test environments — 2026-10-04

Preparation creates `generator-venv` once per PR from the original checkout using the manifest's install list, verifies dependency consistency with `pip check`, and records a successful setup marker. Subsequent preparation reuses that environment. Existing prepared-task records are updated without recreating repository snapshots. Evaluation retains its separate reference-installed venv.

Generator sessions receive the environment through PATH and VIRTUAL_ENV, with the candidate checkout on PYTHONPATH, and an explicit instruction to use its Python executable for tests. They must not install packages or change the shared environment. All ten runs and revisions reuse it. No code-generation or judging sessions are launched by preparation; the experiment remains stopped.

Validation: both pilot generator environments passed dependency checks and imported their original source snapshots. The selected original Sphinx tests passed (64); Seaborn's original aggregation tests passed (9). The reference-only Seaborn `test_order.py` does not exist in the original snapshot, so that full reference test command is reserved for evaluation. The runner's 11 tests passed.

## Supervised rerun and inheritance diagnosis correction — 2026-10-04

The new experiment uses a local supervising harness that pauses after each batch and editor response for inspection by the controlling Codex session, without adding an LLM reviewer to the experiment. Reviews inspect diagnosis accuracy, specification fidelity, executable results, source access, and role-boundary violations before permitting the next phase. This is Codex supervision, not human judge validation.

The first supervised baseline (`.experiments/supervised-2026-10-04`) was stopped and invalidated before any editing: run 01's judge falsely claimed the directive lacked the `canonical` option. The generated class inherited it through PyVariable and PyObject.option_spec. It did fail to render the expression, but acceptance and rendering are different properties. Incorrect feedback could drive incorrect specification changes. The judge prompt now explicitly requires tracing inherited definitions before declaring an option, method, or registration absent and distinguishing acceptance from rendering. The fixed experiment starts from a fresh baseline in `.experiments/supervised-2026-10-04-b`; earlier judgments are not reused.

The second attempt (`...-b`) was stopped before editing after another systematic comparison error. Judges in runs 01 and 03 described reference-only tests as removed or weakened by the candidate. Run 01 changed no tests; run 03 added a test. A judge in run 05 also claimed nesting was not enabled even though its alias class inherited the same nesting flag as the reference. The judge instruction now requires original-to-candidate comparison for additions, deletions, and regressions, and distinguishes placing an object within a container from allowing nested contents inside that object. A fresh experiment starts in `.experiments/supervised-2026-10-04-c`. Criteria and generation/editor instructions are unchanged by these corrections.

Attempt `...-c` was also stopped before editing: runs 00 and 05 still falsely claimed inherited `canonical` acceptance was absent. Prompt-only inheritance instructions did not prevent the error. The Sphinx manifest now includes a deterministic API introspection command recording directive registration, effective accepted options, inheritance, and the nested-contents flag in each original/reference/generated snapshot. These facts are stored in `checks.json` for the judge and subsequently the editor via normal feedback; generators never receive the probe or its reference output. Probe outputs inform existing criteria rather than introducing a new pass condition or reviewer. Judges must not contradict successful effective-attribute inspections. Attempt `...-d` starts fresh with this instrumented evaluation; no criteria are removed. Reference and generator environments are prepared anew because the manifest changed.

Inspection also identified that editor feedback forwarded judge verdicts but not the complete executable logs: these were available only indirectly through evidence paths. Each current-batch run now forwards its full checks record, including tracebacks and API inspection facts, to the editor. This provides the actual observed failures alongside the judge's diagnosis and does not introduce recurrence tracking or another review stage. This correction is included before attempt `...-d` generation begins.

Attempt `...-d` stopped before editing when run 01 again claimed `canonical` was not accepted, contradicting the successful option probe. Its transcript showed it read the probe within a large checks dump, but the probe's facts appeared as escaped JSON strings. The parsed facts are now supplied explicitly as `verified_api_facts` in the judge prompt, separate from raw test logs. This is a context-presentation correction; its effectiveness remains to be established. Attempt `...-e` starts from a new baseline and reuses only prepared repositories and dependency environments, not candidate results or judgments.

Attempt `...-e` stopped before editing because runs 05 and 06 contradicted the explicit effective-option facts. More prominent facts alone did not eliminate these observed reasoning errors. All GPT-6 Luna roles now explicitly use high reasoning effort, rather than an unspecified CLI default. The model remains GPT-6 Luna, and all criteria remain required. Attempt `...-f` restarts fresh under this fixed generation setting. Increased effort is a hypothesis for improving diagnosis reliability, not a demonstrated fix. No conclusion about specification effectiveness is drawn from the invalidated attempts.

Attempt `...-f` completed a baseline of ten failures. Inspection found the judgments no longer contradicted inherited option acceptance or nesting facts; all generators stayed within observed role boundaries. Its first editor response mislabeled `input/output contracts` as Behavior rather than Interfaces. The editor schema permitted category/subsection combinations that the validator rejected. The schema now uses category-specific alternatives to enforce valid pairs. The untested editor response was rejected, and editing restarts in `...-g`. The ten unchanged baseline runs and judgments are reused via links with provenance in `reused-baseline.json`, because this schema correction affects only editor metadata and does not invalidate baseline generation/evaluation. No proposed specification from the rejected response was tested, and no model output was manually rewritten.

Attempt `...-g` completed revision one (zero complete passes; three executable passes). Before testing revision two, inspection found that the editor proposed index-wording clarifications as addressing runtime failures while leaving the actual translation-function shadowing cause unaddressed. Four current-run tracebacks showed it, and run 06's judge explicitly diagnosed the local name masking the translator. The editor instruction now requires addressing each distinct reported failure's cause and distinguishing runtime exceptions from output wording. No additional reviewer stage or recurring-failure history is introduced. Refinement restarts from the unchanged, valid high-effort baseline in `...-h`; revision-one results remain diagnostic rather than part of the corrected trajectory. These are pilot protocol-tuning interventions, not evidence of an autonomous, fixed-protocol loop's effectiveness.

Attempt `...-h` completed revision one (one complete pass; two executable passes), and its next editor response correctly addressed translation-function shadowing alongside prefix structure, canonical registration, and index/object labels. Transcript inspection then discovered editor writes to prior `specification.md` archives. The prompt prohibited code changes but did not prohibit specification/artifact writes. This overwrote archival input documents, although actual generation prompts and saved `feedback.json.current_specification` retained the original inputs and no source-code mutation was observed.

The loop was stopped. Original input archives were recovered from saved feedback, and overwritten versions were preserved as `specification.editor-overwrite.md`. The editor must now return JSON only and must not write any files. The runner snapshots and hashes protected judge inputs (checks/patch) and editor inputs (specification/feedback), stopping before accepting a response if they change. A simulated mutating subprocess test verifies the guard and forensic snapshot; all 12 runner tests passed.

Continuation `...-i` preserves the valid baseline and revision-one generations/judgments and the two unchanged, inspected editor JSON responses, with explicit provenance in `continuation.json` and each reused editing phase. These results are not invalidated: only archived input copies changed, while actual model input requests and response JSON stayed intact. No specifications or judgments were manually rewritten. New generations begin at revision two. Only new role calls use the corrected artifact instructions and integrity guards. This continuation is transparently recorded rather than disguised as a completely fresh run.

Continuation `...-i` completed revision two (three complete passes; five executable passes). Remaining failures were exact nested-index punctuation and absent feature tests; original contributor guidelines explicitly require unit tests. Before testing revision three, its editor wrongly justified removing the explicit translation-function no-shadowing protection because the current runs no longer raised that exception and the reference did not exhibit shadowing. Success under a preventive constraint does not show that constraint conflicts with the reference. The response was rejected without testing. The existing preserve-correct-requirements instruction now explicitly disallows that inference and requires reference evidence or redundancy with protection retained for removals. Continuation `...-j` preserves valid tested phases and regenerates only that editing phase, with provenance. The input-integrity guard succeeded for the rejected editor call; no artifact writes occurred.

## Explicit test-policy grading and candidate-test execution — 2026-10-04

The `...-j` trajectory reached revision three (eight complete passes and ten gold-suite passes); two failures correctly identified lost descriptive-body support or altered nesting lifecycle. Supplemental execution of all candidate-owned changed test modules also passed for that batch. Revision four was stopped after further audit found a systematic false-pass problem in earlier grades: revision-two runs 01, 04, and 08 passed convention_fit despite containing no test changes, while runs 02 and 03 failed that criterion for the same omission. The original Sphinx contributor guide explicitly requires unit tests for a new feature (lines 114–115 and 155). The previous baseline-to-revision pass-rate comparison is therefore invalidated, not silently relabeled.

Sphinx's manifest now explicitly defines that test-policy pass condition. A deterministic guard prevents the judge passing convention_fit when the candidate contains no test changes; the judge still evaluates whether added coverage is meaningful and follows local style. Seaborn's original contributor guide contains no mandatory test-addition rule, so that task's convention condition explicitly assesses changed-test style without inventing a mandatory addition from reference-only tests. All eleven criteria remain required; none is removed.

Formal executable checks now run original targeted test modules and candidate-owned changed test modules before applying the reference-test overlay. Reference regression checks run afterward. Both stages must pass. Reference-only modules absent from the candidate are omitted from the candidate stage, rather than treated as missing candidate tests. Bytecode/cache directories are excluded from fresh copies and bytecode writing is disabled during checks to prevent stale assertions when the same test file is overlaid. A regression case proves failing generated assertions cannot be hidden by passing reference tests. Another verifies a positive judge cannot override the required-test-change guard. The description-body flag is now included in the Sphinx API probe.

A completely fresh experiment starts in `...-k`, including new baseline generations, judgments, editor outputs, and prepared environments. Earlier candidate outputs and judgments are not reused. Older trajectories are retained as protocol-tuning diagnostics. Original commits, PR metadata, and reference diffs are reused as unchanged source data.

## Sphinx-only resumption — 2026-10-04

After the user paused execution, the corrected `...-k` baseline completed with zero passes across ten runs. Run 09 contained an inaccurate statement that canonical was rejected; its actual inherited option was accepted but unused for expression rendering. The same judge role re-evaluated that unchanged patch with the verified fact clarified; the rejected response remains archived, and the failed outcome did not change. No generation, criterion, or specification was changed by this correction.

The user subsequently authorized resuming Sphinx only. The supervising harness now filters out Seaborn. Major loop changes require user input; small systematic corrections may be made and documented. The baseline was inspected and approved for the first editing phase.

The first editor draft incorrectly made module-level type-alias index text conditional on `add_module_names`. The same editor received the verified reference branch behavior and corrected the untested draft; rejected output and the clarification are preserved in `revision-00/editing-rejected-01` and `editor-correction.json`. No generated specification was manually rewritten.

At revision-one review, run 04 was inconsistently awarded `convention_fit` despite lacking feature documentation and a changelog entry. The original contribution guide requires both for this non-trivial feature, and the reference includes both; several other candidates were correctly failed for the same omissions. Execution paused before the next editor. The unchanged patch is re-evaluated by the same judge role with those repository facts clarified, preserving its earlier judgment. Criteria, code, model, and generation settings remain unchanged. This is Codex supervision, not human judge calibration or an additional experimental reviewer role.

The bounded revision-one retry changed run 04 from pass to fail: it verified the missing documentation/changelog and also caught the public object label `type` versus reference `type alias`. The batch therefore has zero complete passes out of ten. All generated patches remain unchanged. The corrected verdicts were approved for the next editing phase; the earlier positive judgment remains archived as an evaluator error.

## Reference fixture isolation — 2026-10-04

Before approving revision two in `...-k`, supervision found a deterministic harness artifact in revision-one run 08. Its candidate-added `type_aliases.rst` was correctly linked from the candidate toctree and passed candidate tests. Overlaying the reference index replaced that link while retaining the candidate-only document, causing a reference warning assertion failure. Execution stopped immediately; the completed editor response was not approved or tested.

Reference checks now restore the evaluation copy's entire tests directory from the original snapshot before overlaying reference test changes, after candidate-owned checks finish. Candidate production changes remain in place. This isolates the two fixture sets without changing the rubric or concealing candidate-owned test failures. A regression fixture reproduces the index/data conflict; all 15 runner tests pass. The unchanged real run-08 patch now passes both stages. Its earlier failure record is preserved, and `fixture-isolation-validation/run-08/checks.json` contains the corrected diagnostic execution.

Attempt `...-k` remains protocol-tuning data because its editor received a false test failure. Attempt `...-l` starts a fresh Sphinx-only baseline and trajectory, reusing only unchanged original/reference repositories and prepared environments. No prior candidate outputs, judgments, or editor responses are reused. No criteria were removed; there is no added reviewer role.

## No manual corrections inside the loop — 2026-10-04

The user explicitly rejected selective regrading with manually supplied factual corrections. Such corrections must stop, including analogous case-specific editor retries. The latest `...-l` baseline judge again incorrectly claimed inherited canonical acceptance was absent; a same-role retry with a case-specific hint completed before this instruction, but no baseline review was approved and no editor received its output. The experiment remains stopped. Earlier interventions remain archived as protocol-tuning diagnostics. Stronger judge selection is a proposal, not an implemented model change. The consolidated [hiccup record](experiment-hiccups.md) captures observed failures, interventions and unresolved concerns.

## Unassisted Luna continuation — 2026-10-04

The user authorized continuing the Sphinx loop with Luna to observe whether future iterations recover from judgment errors. The threshold remains nine of ten; seven of ten was discussed but not adopted. Run-09's original uncorrected judgment in `...-l` is restored as active, and the manually hinted retry is archived as `judgment-manually-corrected-excluded` / `verdict-manually-corrected-excluded.json`. No editor received the corrected feedback. Continuation uses all original baseline judgments, including the known factual error, without selective retries or corrective hints. Monitoring may report errors but does not repair judge/editor outputs. Seaborn remains excluded.

## Completed unassisted continuation — 2026-10-04

The Sphinx Luna trajectory in `...-l` converged at revision five, with 9/10 complete passes and 9/10 fresh confirmation passes. Original judgments and editor responses were forwarded unchanged after restoring the original baseline verdict; no case-specific corrective retry influenced editing. Eight ten-run batches were evaluated (80 runs), including revision-four confirmation that failed at 7/10 and triggered another refinement. Both final batches passed all selected executable checks; two failed convention fit for missing resolved-role regression coverage. Raw per-batch/per-criterion results and remaining judge inconsistencies are recorded in [the results report](sphinx-luna-results.md). No model or threshold change was made. Seaborn remains excluded.

## Approved subsection headings — 2026-10-04

The methodology inventory was minimized and finalized, including Implementation constraints under Architecture. The editor prompt now requires exact listed subsection names as section headings, selects only relevant sections, and prohibits invented headings. Parent categories organize the inventory. This is prompt guidance only: the free-form specification response, iteration logic, and validation remain unchanged. No experiment was run; completed results retain their original protocol. Future runs need a new output folder because the category inventory and runner source changed.


---

## experiment-hiccups.md

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


---

## experiment-runner.md

# Experiment runner and prompts

Implementation: [run_experiment.py](../run_experiment.py). Pilot inputs, task-specific rubric requirements, dependencies, and executable checks: [pilot.json](../experiments/pilot.json). Usage: [README.md](../README.md).

## Preparation and isolation

The runner fetches each original commit and applies the merged PR diff to a separate reference copy. Each code generator receives a fresh original snapshot with one Git commit and no remote. Linked worktrees are avoided because their shared Git history could expose reference changes.

Each headless Codex session uses ChatGPT authentication, GPT-6 Luna with explicitly fixed high reasoning effort, a named permission profile allowing full filesystem access, and disabled network, external apps, web search, additional agents, memory, and hooks. All roles have full filesystem access. The generator is instructed to inspect only its original-code workspace and specification; judges and editors are instructed not to modify code. These task-code boundaries are prompt instructions rather than filesystem enforcement. Role outputs and transcripts are stored outside the generator workspace. Each batch runs ten independent lanes concurrently, with separate repositories, evaluations, and logs.

The smoke command first runs a deterministic read probe through `codex sandbox` with the same permission profile. It requires both workspace and outside-file reads to succeed. It then asks Luna to read a workspace file and requires a recorded successful tool result. A model's unsupported claim of successful access is insufficient.

The historical reference environments were validated locally: 66 selected Sphinx tests and 15 selected Seaborn tests passed. These are the manifest's targeted regression tests, not complete build, lint, typecheck, or repository-wide test coverage. Dependencies are installed into per-task virtual environments. The original snapshots fail the same feature tests, confirming that the candidate source is imported instead of the installed reference package. Some dependency ranges and transitive dependencies remain unpinned; retain the prepared environments for the pilot. Evaluation sets the candidate repository as its working directory and Python import path, and overlays reference test files onto a separate evaluation copy. The judge still sees the generator's original patch and any test changes it made.

Candidate-owned targeted and changed test modules execute before the reference test overlay. The evaluation copy's tests directory is then restored from the original snapshot before reference test changes are applied; candidate-only fixtures therefore cannot be orphaned by replacing a reference toctree or fixture index. Candidate production changes remain in place. Reference regression tests execute afterward; both stages must pass. Workspace copies exclude bytecode caches and checks disable bytecode writing so overlaid assertions cannot reuse stale compiled tests.

## Exact role instructions

Preparation also creates a reusable `generator-venv` per PR, installing the original project and manifest dependencies and validating them with `pip check`. A success marker avoids reinstalling on subsequent preparation. Generator sessions receive this environment's PATH, VIRTUAL_ENV, candidate PYTHONPATH, and explicit Python executable; they may run tests but must not modify the shared environment. Evaluation keeps its separate reference-installed venv. No model sessions are needed to create environments.

The following text is the current instruction portion of each prompt. The runner appends the described task-specific input. `request.json` preserves the full expanded prompt for every call.

### PR baseline

The original PR title and description are used verbatim, including any code, solely as the initial generation specification. They are not separate requirements for the judge or editor. There is no baseline-generation LLM or rewriting step. The exact baseline is saved as `baseline.md`.

### Code generator

> Implement this feature in the repository. Inspect and edit repository files. Do not use the network, other repository directories, additional agents, or outside feedback. Do not modify tests to conceal failures. Do not commit changes. Run tests using {generator_python}. This prepared environment is shared; do not install packages or modify it.

`SPECIFICATION:` and the current specification follow this instruction. Output: repository changes and a short `summary`. No judge feedback or reference paths appear in this prompt.

### Judge

> Evaluate this patch against every fixed criterion. Read the original, reference, and generated code using the supplied paths. The reference implementation is the source of truth for the feature's behavior, public contracts, and intended architecture. Accept valid alternative implementations without requiring textual identity or incidental private helper names. Do not invent requirements from optional implementation choices. Verify each claimed failure against the actual reference and analogous original code. Before claiming an option, method, or registration is missing, trace its complete inherited definitions in both implementations. Distinguish accepting an option from rendering its value. Determine additions, removals, and regressions against the original snapshot and patch.diff, not a reference-to-generated diff. Reference-only tests absent from the candidate are not deleted tests. Distinguish an object nested inside a container from that object allowing nested contents; verify the actual reference behavior rather than inferring a required flag. Cite file:line evidence for each criterion and describe each failure. Use checks.json for executable status and recorded API inspection facts; do not contradict a successful inspection of an effective inherited attribute. Never invent execution results. Do not modify files.

The appended JSON contains parsed verified API facts from successful inspection commands and all eleven task-specific criterion requirements, and original/reference/generated repository paths. The judge context contains `patch.diff` and `checks.json`. Output: a boolean verdict, evidence, and deficiency for each criterion. The Sphinx check records additionally contain effective directive options, descriptive-body/nesting flags, and inheritance from original/reference/generated API inspection. Each run verdict forwards the complete checks record into editor feedback. Sphinx requires test changes under its original contribution policy; a missing-test-change guard forces convention_fit false. Seaborn has no mandatory new-test requirement in this pilot. The runner rejects missing or duplicate criteria and forces the executable criterion to fail when the recorded checks fail.

### Specification editor

> Read feedback.json and the original, reference, and generated code. Produce ONE next specification describing the feature implemented by the reference code. The reference implementation is the source of truth for behavior, public contracts, and architecture. The current specification is an editable draft, not an independent source of requirements; correct or remove any content that conflicts with the reference implementation. Introduce or improve sections only within the listed categories and subsections. Use the exact listed subsection names as specification section headings; parent categories only group the inventory. Include the relevant subset and do not invent headings. Explain exact edits and hypotheses. You may add, clarify, reformat, or remove content. Focus edits on the failures reported by the judge. Verify each diagnosis by reading the complete relevant reference methods, including inherited methods. Preserve correct requirements and explain which failed criterion each edit addresses. Do not remove a correct constraint because current runs satisfy it. Justify removal with reference evidence or redundancy, preserving its protection. Address the cause of each distinct reported failure. For runtime errors, identify the failing operation and cause before proposing a specification change; changing output wording does not resolve an exception. The specification must instruct the agent how to implement the feature, not supply the implementation. Do not include actual programming-language code, implementation bodies, executable examples, or code-form declarations or signatures. Do not copy reference code into the specification. Express API contracts, names, types, and structural constraints in any format that is not actual code. Pseudocode is allowed; label it as pseudocode. Remove any actual code from the current specification. Do not modify any code or execute another generator. Return the specification and edit explanations only in the requested JSON response. Do not write, edit, or delete any files, including specifications, feedback, and experiment artifacts.

The appended JSON supplies original/reference paths. `feedback.json` contains the current specification, fixed categories and subsections, criterion requirements, and the current batch's judgments and generated paths. Failed confirmation runs are included when present. Output: one replacement specification and edit records with category, subsection, operation, exact change, and hypothesis.

## Specification code policy

The original PR baseline is preserved verbatim and may contain code. Editor-produced specifications instruct the agent how to write code; they must not supply actual programming-language code. Implementation bodies, executable examples, and code-form declarations or signatures are prohibited, including copied reference code. API names, types, contracts, and structural instructions can use any format that is not actual code. Clearly labeled pseudocode is allowed. The editor prompt enforces this instruction; inspect resulting specifications for compliance because schema validation cannot reliably distinguish all actual code from pseudocode.

## Evaluation uncertainties

Luna is both generator and judge. Agreement with human architectural judgments is unmeasured until the manual audit, and references are not treated as the only acceptable implementation. The runner checks evidence is present; it does not verify that every cited line exists or supports the judgment.

The editor's declared categories and subsections are validated, but semantic adherence to that inventory and preservation of behavioral scope still depend on model compliance and inspection. Success across nine of ten observed runs is an operational convergence threshold, not proof of a population success probability of at least 90%.

Protected judge/editor input files are snapshotted and hashed around each new role call; mutations stop the script before accepting the response. These guards preserve evidence while full filesystem access remains enabled.

Infrastructure failures stop the script and preserve completed artifacts. Candidate code is executed locally during checks; those checks are separate from Codex sessions. Pilot execution uses the verbatim PR baseline and the three role prompts above.

## Experiment adjustments

Changes to the pilot protocol and their reasons are recorded in [experiment-adjustments.md](experiment-adjustments.md). Corrected runs use `.experiments/reference-authority/`; earlier diagnostic runs remain in `.experiments/results/` and are excluded from corrected results.


---

## open-research-questions.md

# Open research questions

## Pilot execution

The initial pilot uses Sphinx #11989 and Seaborn #3063. scikit-learn #29260, Matplotlib #22387, Scrapy #3505, and scikit-learn #29705 remain candidates for later expansion. Their feature descriptions and PR links are in [references.md](references.md#candidate-pull-requests).

The candidate screening covered all 186 shortlisted PR descriptions and changed-file structural summaries, with closer patch inspection for the strongest candidates. Both pilot reference environments now pass their configured tests: Sphinx 66 and Seaborn 15. Applying those reference tests to the original snapshots fails on the missing features, confirming that evaluation imports the candidate source rather than the installed reference package.

## Methodology and evidence

1. **Statistical claims — Problem Statement, Evidence and Data, Warrants:** Nine successes in ten runs is an observed 90% pass rate, not proof that the underlying success probability is at least 90%. Repeated sampling does not eliminate stochasticity. Define how uncertainty in the observed pass rate will be reported and how generator variability and judge variability will be measured separately.
2. **Causal interpretation — Problem Statement and Warrants:** The main experiment is feedback-driven specification refinement. Replacing stories with constraints can simultaneously change category, specificity, length, and behavioral content. Define how changes will be classified and how associations with improvement will be reported without claiming isolated category effects.
3. **Privileged solution information — Evidence and Data:** The specification editor receives reference code, generated code, and judge feedback. The code generator receives only the specification and original code. Document this reference-informed setting when interpreting results.
4. **Executable evidence — Evaluation Criteria:** A judge cannot establish build, lint, or test status without actual execution. The runner executes the configured checks and supplies results to the judge. Failed checks force the executable criterion to fail. The pilot currently runs selected tests, not complete build, lint, or regression suites.
5. **Criterion interpretation — Evaluation Criteria:** Document the task-specific requirements and repository evidence used to interpret the required criteria consistently. The success rule is defined: each run must pass every required criterion, and a specification passes when at least nine of ten fresh, independent runs pass. No numerical scores or weighted totals are used.
6. **Reference implementation — Problem Statement and Evidence and Data:** A merged PR is a reference implementation, not necessarily the only architecturally acceptable solution. Distinguish required public contracts and repository conventions from incidental helper names or decomposition choices.
7. **RE taxonomy — Problem Statement and Backing:** User stories and Gherkin are requirement representations, rather than necessarily distinct RE categories. Verify the proposed mapping to ISO/IEC/IEEE 29148 and the other RE sources before stating that the standard supplies the exact experimental taxonomy.
8. **Literature support — Backing and references.md:** Verify bibliographic details and whether each source supports the stated claim. MT-Bench agreement does not directly validate architectural code judgments; cited sampling designs do not establish that n=10 is sufficient; and a reported benchmark result is not automatically a directly comparable baseline for a different agent setup.
9. **Operational details — Evidence and Data and manual validation note:** All three LLM roles use GPT-6 Luna in fresh headless Codex sessions through ChatGPT authentication. The generator accesses the full original repository with local tools; judge and editor access authorized original, reference, and generated copies. There is no experiment-imposed token budget. The loop tests one candidate at a time, ten runs per revision, at most ten editor revisions after baseline, and ten fresh confirmation runs. Failed confirmation feeds further editing if revisions remain. The original PR title and description are the verbatim baseline, including code. Actual programming-language code is prohibited in editor-produced specifications; clearly labeled pseudocode and any non-code API-contract format are allowed. Determine how audit disagreements affect reported results.

10. **Feature size:** Verify the characterization of FEA-Bench as mostly smaller-scale features before using it as a research claim.


---

## pilot-results-before-reference-authority.md

# Pilot results

Status: held after Sphinx revision three while resolving contradictory baseline/reference contracts. Baseline inputs are the original PR titles and descriptions verbatim. All runs use GPT-6 Luna. The tables below distinguish judge-reported criterion failures from observed executable test failures.

## Evaluation reliability

Full-run failures are supported by executed tests. Qualitative diagnoses require review. In the Sphinx baseline, at least one judge demanded `allow_nesting=True` for alias directives. The reference `PyTypeAlias` does not set that flag; nesting an alias inside a class uses the surrounding class context. This is an unsupported diagnostic requirement, even though the affected run still fails actual tests.

Sphinx PR #11989 describes the optional alias expression using the `value` option; the merged code and reference tests use `canonical`. The baseline follows the former while evaluation uses the latter. This interface mismatch contributes to the repeated failures and limits interpretation of any improvement as purely improved architectural instructions.

Direct inspection of the reference confirms that `PyTypeAlias` accepts `canonical`, does not accept `value`, and has `allow_nesting=False`. Revision three produced two patches passing all reference tests, but both were rejected for not implementing the original PR description's `value` option. The next editor output then switched back to `value`, demonstrating oscillation between two conflicting targets. An authoritative-contract rule must be fixed before the results can be interpreted.

Results are exploratory pilot observations. Codex review of judgments is an additional automated review, not human validation. The human-audit sample will remain unfilled until a human reviews it.

## sphinx-doc__sphinx-11989

### revision-00

Full passes: **0/10**.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 10/10 |
| `convention_fit` | 10/10 |
| `requirement_intent` | 10/10 |
| `extension_point_adherence` | 8/10 |
| `architectural_fit` | 4/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 9/10 |
| Collection error: `tests/test_domains/test_domain_py.py` | 1/10 |

Full artifacts: `.experiments/results/sphinx-doc__sphinx-11989/revision-00`.

### revision-01

Full passes: **0/10**.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 9/10 |
| `extension_point_adherence` | 3/10 |
| `convention_fit` | 10/10 |
| `requirement_intent` | 10/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 1/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 1/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 1/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 1/10 |
| Collection error: `tests/test_domains/test_domain_py.py` | 1/10 |

Full artifacts: `.experiments/results/sphinx-doc__sphinx-11989/revision-01`.

### revision-02

Full passes: **0/10**.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `requirement_intent` | 10/10 |
| `convention_fit` | 9/10 |
| `api_contract` | 5/10 |
| `extension_point_adherence` | 1/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 2/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata_signature` | 1/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata_signature_old` | 1/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata_with_union_type_operator` | 1/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata` | 1/10 |
| Collection error: `tests/test_domains/test_domain_py.py` | 1/10 |

Full artifacts: `.experiments/results/sphinx-doc__sphinx-11989/revision-02`.


### revision-03

Full passes: **0/10**. Two runs pass all executable checks but fail subjective judgments against the conflicting PR option name.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `api_contract` | 9/10 |
| `convention_fit` | 9/10 |
| `requirement_intent` | 9/10 |
| `patch_and_checks` | 8/10 |
| `extension_point_adherence` | 3/10 |
| `architectural_fit` | 2/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 8/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 2/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 2/10 |


---

## pilot-results.md

# Corrected pilot results

Status: stopped. Revisions zero through five are complete; revision six has partial judgments because Codex reported a usage limit. Both reference-patch controls passed all eleven criteria and their executable checks. The filesystem policy and editor prompt have since changed; these recorded outcomes belong to the earlier restricted-access condition.

The reference implementation is authoritative for behavior, public contracts, and intended architecture. The original PR title and description supply only the baseline generation prompt. Judge inputs contain no PR-derived behavioral requirements; the editor receives the current editable draft rather than a separate immutable baseline.

Artifacts: `.experiments/reference-authority/`. Earlier results using conflicting contracts are retained in [the diagnostic report](pilot-results-before-reference-authority.md) and are excluded from this comparison. Protocol changes are recorded in [experiment-adjustments.md](experiment-adjustments.md).

All eleven criteria remain required. A run passes only when every criterion passes; convergence and confirmation each require at least nine of ten fresh runs. There are at most ten editor revisions after the baseline.

At each completed revision, report full pass counts, judge-reported criterion failures, and observed executable test failures. Codex review of sampled judgments is additional automated review, not human validation.

## Batch outcomes

### sphinx-doc__sphinx-11989/revision-00

Full passes: **0/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 10/10 |
| `extension_point_adherence` | 8/10 |
| `convention_fit` | 10/10 |
| `requirement_intent` | 10/10 |
| `architectural_fit` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 2/10 |

Observed collection errors:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py` | 5/10 |

### sphinx-doc__sphinx-11989/revision-01

Full passes: **0/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `convention_fit` | 9/10 |
| `requirement_intent` | 8/10 |
| `api_contract` | 7/10 |
| `extension_point_adherence` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 7/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 10/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 8/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-02

Full passes: **0/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 8/10 |
| `convention_fit` | 9/10 |
| `requirement_intent` | 9/10 |
| `extension_point_adherence` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 10/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 6/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 7/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-03

Full passes: **1/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `convention_fit` | 9/10 |
| `requirement_intent` | 8/10 |
| `patch_and_checks` | 5/10 |
| `api_contract` | 5/10 |
| `extension_point_adherence` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 4/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 4/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-04

Full passes: **1/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `convention_fit` | 9/10 |
| `patch_and_checks` | 8/10 |
| `api_contract` | 5/10 |
| `requirement_intent` | 8/10 |
| `extension_point_adherence` | 3/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 8/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 5/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-05

Full passes: **2/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `convention_fit` | 8/10 |
| `patch_and_checks` | 6/10 |
| `api_contract` | 7/10 |
| `requirement_intent` | 7/10 |
| `extension_registration` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 3/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 3/10 |

Observed collection errors:

None.



---

## sphinx-luna-results.md

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


---

## seaborn-luna-results.md

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
