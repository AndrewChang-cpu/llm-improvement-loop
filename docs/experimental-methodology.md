# Experimental methodology

Research framing and evaluation criteria: [research-design.md](research-design.md).

The main experiment investigates how specification content and formulation evolve in response to structural failures, and whether that refinement converges to a specification that reliably communicates the intended implementation. The loop produces the comprehensive specification; it is not assembled in advance by adding every selected category to an unchanged baseline.

## Initial pilot

The first run covers two FEA-Bench tasks:

| Instance | Feature |
| --- | --- |
| `sphinx-doc__sphinx-11989` | Type-alias directive and role |
| `mwaskom__seaborn-3063` | Percentile statistics component |

Their PR links are in [references.md](references.md#candidate-pull-requests). Historical environments and tests must be validated before generation begins. The first run does not cover the full dataset or all 186 shortlisted tasks.

## Model roles and information access

| Role | Inputs and behavior |
| --- | --- |
| Code generator | Receives only the current specification and original, pre-change code. Uses a fresh headless Codex session with repository search, read, and edit tools for each independent run. |
| Judge | Evaluates generated code against the required criteria using the reference implementation and repository conventions; produces pass/fail judgments, evidence, and deficiencies. |
| Specification editor | Receives the current specification, reference code, generated code, and judge feedback. Produces one next revision within the fixed category inventory. |

The baseline is the original PR title and description verbatim, including any code it contains. It is solely a generation input. The reference implementation defines the target behavior, public contracts, and intended architecture for evaluation and refinement. The judge receives no PR-derived behavioral requirements, and the editor receives no separate immutable baseline requirements. The current specification is an editable draft whose conflicts with reference code should be corrected. Editor-produced specifications must instruct implementation without supplying actual programming-language code. Implementation bodies, executable examples, and code-form declarations or signatures are prohibited. API contracts may use any format that is not actual code; clearly labeled pseudocode is allowed.

The editor has privileged reference information. The code generator receives neither the reference implementation nor judge feedback directly; refinement reaches it through the specification. The comparison therefore measures reference-informed specification refinement.

All three LLM roles use GPT-6 Luna through headless Codex authenticated with the ChatGPT account. GPT-5 nano was rejected by this authentication mode. The runner uses no API keys and imposes no token budget. Subscription usage limits may interrupt execution; interruptions are resumed rather than recorded as feature failures.

Repository context is the full original repository snapshot, available through local tools. Each generator starts from a fresh copy with one snapshot commit and no remote or historical PR commits. All roles have full filesystem access. The generator is instructed not to inspect reference code, sibling runs, or judge feedback; judge and editor sessions are instructed not to modify code. These are prompt boundaries rather than filesystem enforcement. Network access is disabled. Older restricted-access runs are kept separate from this changed execution condition. One-shot generation means one agent session without external feedback; the session may make multiple tool calls. Runner commands and prompts are documented in [experiment-runner.md](experiment-runner.md).

## Specification categories

The specification editor selects document sections from the subsection names below. The ten parent categories organize the inventory; the subsection names are the allowed specification headings. Each feature may use the relevant subset; a comprehensive specification does not need to contain every section.

| Category | Subsections |
| --- | --- |
| Purpose | Goals; Scope; Assumptions; Terminology |
| Behavior | Workflows |
| Data | Data model |
| Interfaces | API contracts |
| Architecture | Module architecture; Implementation constraints; Dependencies |
| Conventions | Naming; Validation; Error handling; Logging; Documentation |
| Quality | Performance; Security; Reliability; Usability; Maintainability |
| Compatibility | Compatibility |
| Operations | Operations |
| Acceptance | Behavioral acceptance criteria; Test requirements |

This inventory defines the experiment’s specification sections, rather than claiming that all sources use an identical requirements taxonomy. It reflects the specification sections discussed during project planning.

The minimized sections retain the following coverage:

- **Goals** includes rationale; **Scope** includes exclusions.
- **Workflows** includes capabilities, edge cases, and relevant business rules.
- **Data model** includes entities, schemas, invariants, persistence, and migrations.
- **API contracts** includes public names, signatures, input/output contracts, and external integrations.
- **Module architecture** includes file placement, component responsibilities, and boundaries. **Implementation constraints** covers required abstractions, inheritance, registration mechanisms, and reuse of existing code. **Dependencies** covers permitted dependencies and dependency directions.
- **Compatibility** includes supported versions, backward compatibility, and deprecations.
- **Operations** includes configuration, deployment, observability, and resource limits.
- **Behavioral acceptance criteria** includes illustrative examples; **Test requirements** specifies required verification and regression coverage.

The editor may add, remove, or refine sections only from this inventory. Section headings must use the listed subsection names, rather than feature-specific headings such as “Index entries” or “Directive and signature behavior.” Each proposed edit identifies its parent category and section, the diagnosed deficiency it addresses, the exact change, and the hypothesis being tested. The inventory stays fixed across features and revisions; changes to it are explicit experiment-protocol revisions.

## Refinement loop

1. Use the original PR title and description verbatim as the baseline specification, without rewriting or removing code.
2. Generate code in fresh runs from the pre-change repository and evaluate it against the fixed criteria.
3. The judge diagnoses failed criteria, cites code evidence, and describes the expected architectural behavior using the reference implementation and repository conventions.
4. A specification editor proposes sections to introduce or improve within the fixed specification category inventory, records the category and subsection and the operation (`add`, `clarify`, `reformat`, or `remove`), and provides the exact edits and hypotheses.
5. Generate one next specification revision. Changes may introduce requirements, rewrite existing sections, or change how information is organized and expressed. Test one candidate at a time, without branching into competing revisions.
6. Evaluate ten fresh code-generation runs for that revision and retain the specification, diagnoses, edits, and outcomes.
7. Repeat until at least nine of ten fresh, independent runs each pass every required criterion, or ten editor-produced revisions have been evaluated after the baseline. Meeting the nine-of-ten threshold is convergence and produces the comprehensive specification for that feature; reaching the revision limit alone is not convergence.

## Evaluation and convergence

Each required criterion receives a pass/fail judgment with evidence. Failed judgments describe the specific deficiencies that the specification editor should address through the fixed specification categories. There are no 0–2 scores or weighted totals.

A code-generation run passes only if every required criterion passes. A specification passes, and the loop converges, when at least nine of ten fresh, independent runs pass. If fewer than nine runs pass, the failed criteria and supporting diagnoses feed into the next specification revision. The required criteria remain fixed throughout the loop.

The pilot stops after at most ten specification revisions per PR, excluding the original PR baseline. Tasks that reach this limit without meeting the threshold are recorded as non-convergent.

For judge validation, manually evaluate ten randomly selected generated patches from the pilot against the same required criteria and compare the manual judgments with the judge’s verdicts. Record per-criterion and overall agreement, including false passes and false failures.

## Baseline and final comparison

| Condition | Input |
| --- | --- |
| PR baseline | The original PR title and description verbatim, including any code |
| Comprehensive specification | The specification produced by the refinement loop at convergence |

Intermediate revisions provide the trajectory connecting these conditions. Confirm the converged specification’s performance using fresh runs beyond those used to select it.

## Controls and records

- Keep the feature behavior and scope defined by the reference implementation fixed. Specification wording, organization, and structural detail may change through the loop.
- Keep the specification category inventory fixed. Every edit must map to a listed category and subsection.
- Keep model configuration, pre-change repository access, agent tools, absence of an experiment-imposed token budget, and evaluation criteria fixed across revisions.
- Use fresh, isolated code-generation runs from the pre-change repository rather than carrying forward generated code from earlier revisions.
- Preserve each exact specification revision and record its parent, judge diagnosis, categories changed, edits, hypotheses, and evaluation results.
- Evaluate architectural intent and repository conventions; valid implementations beyond the reference patch may satisfy the rubric.

## Interpretation and remaining methodological details

The baseline-to-convergence comparison measures the improvement achieved by the resulting specification. The revision history provides evidence about which content and formulations accompanied that improvement. Protocol corrections are recorded in [experiment-adjustments.md](experiment-adjustments.md); results from conflicting evaluation rules are retained for diagnosis and excluded from corrected comparisons. A code failure does not establish that the specification caused it, and an adaptive trajectory alone does not isolate every edit’s causal effect.

If confirmation falls below nine passes, its failures join the revision feedback and editing continues within the ten-revision limit. A regressing revision is recorded and feeds the next edit; the loop does not branch or automatically restore an earlier specification. Category classification rules and the response to judge-audit discrepancies remain open. The current adaptive loop identifies associations between edits and outcomes rather than isolated causal effects.
