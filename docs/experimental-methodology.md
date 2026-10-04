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
| Behavioral-prompt generator | Reads the PR description and generates the initial behavioral-intent prompt. Preserve this prompt as the baseline. |
| Code generator | Receives only the current specification and original, pre-change code. Uses GPT-5 nano with no tools. Generates a patch in a single response for each independent run. |
| Judge | Evaluates generated code against the required criteria using the reference implementation and repository conventions; produces pass/fail judgments, evidence, and deficiencies. |
| Specification editor | Receives the current specification, reference code, generated code, and judge feedback. Produces one next revision within the fixed category inventory. |

The editor has privileged reference information. The code generator receives neither the reference implementation nor judge feedback directly; refinement reaches it through the specification. The comparison therefore measures reference-informed specification refinement.

GPT-5 nano is the selected low-cost code-generation model; its official documentation is listed in [references.md](references.md#model-documentation). Model assignments for the behavioral-prompt generator, judge, and editor still need to be specified.

Repository context means the original source files included in the code generator’s prompt. With no tools, the generator cannot retrieve files itself. The original-code context must be selected before baseline generation and kept identical across revisions; its exact contents and token limits still need to be specified.

## Specification categories

The specification editor uses the following fixed category inventory and its listed subsections. Each feature may use the relevant subset; a comprehensive specification does not need to contain every category.

| Category | Subsections |
| --- | --- |
| Purpose | Goals; rationale; scope; non-goals; assumptions; terminology |
| Behavior | Capabilities; workflows; business rules; edge cases |
| Data | Entities; schemas; invariants; persistence; migrations |
| Interfaces | APIs; signatures; input/output contracts; integrations |
| Architecture | File placement; responsibilities; boundaries; dependencies; extension points |
| Conventions | Naming; validation; error handling; logging; documentation |
| Quality | Performance; security; reliability; usability; maintainability |
| Compatibility | Backward compatibility; supported versions; deprecations |
| Operations | Configuration; deployment; observability; resource limits |
| Acceptance | Examples; acceptance criteria; test requirements |

This inventory defines the experiment’s specification sections, rather than claiming that all sources use an identical requirements taxonomy. It reflects the specification sections discussed during project planning.

The editor may introduce a missing section or improve an existing section within this inventory. It must not invent categories or subsections during the loop. Each proposed edit identifies its category and subsection, the diagnosed deficiency it addresses, the exact change, and the hypothesis being tested. The inventory stays fixed across features and revisions. Category boundaries and rules for classifying overlapping requirements still need to be defined before execution.

## Refinement loop

1. Generate a basic behavioral-intent prompt from the PR description, describing what the feature must do.
2. Generate code in fresh runs from the pre-change repository and evaluate it against the fixed criteria.
3. The judge diagnoses failed criteria, cites code evidence, and describes the expected architectural behavior using the reference implementation and repository conventions.
4. A specification editor proposes sections to introduce or improve within the fixed specification category inventory, records the category and subsection and the operation (`add`, `clarify`, `reformat`, or `remove`), and provides the exact edits and hypotheses.
5. Generate one next specification revision. Changes may introduce requirements, rewrite existing sections, or change how information is organized and expressed. Test one candidate at a time, without branching into competing revisions.
6. Evaluate ten fresh code-generation runs for that revision and retain the specification, diagnoses, edits, and outcomes.
7. Repeat until at least nine of ten fresh, independent runs each pass every required criterion, or ten editor-produced revisions have been evaluated after the baseline. Meeting the nine-of-ten threshold is convergence and produces the comprehensive specification for that feature; reaching the revision limit alone is not convergence.

## Evaluation and convergence

Each required criterion receives a pass/fail judgment with evidence. Failed judgments describe the specific deficiencies that the specification editor should address through the fixed specification categories. There are no 0–2 scores or weighted totals.

A code-generation run passes only if every required criterion passes. A specification passes, and the loop converges, when at least nine of ten fresh, independent runs pass. If fewer than nine runs pass, the failed criteria and supporting diagnoses feed into the next specification revision. The required criteria remain fixed throughout the loop.

The pilot stops after at most ten specification revisions per PR, excluding the initial behavioral baseline. Tasks that reach this limit without meeting the threshold are recorded as non-convergent.

For judge validation, manually evaluate ten randomly selected generated patches from the pilot against the same required criteria and compare the manual judgments with the judge’s verdicts. Record per-criterion and overall agreement, including false passes and false failures.

## Baseline and final comparison

| Condition | Input |
| --- | --- |
| Behavioral baseline | The initial basic description of what the feature must do |
| Comprehensive specification | The specification produced by the refinement loop at convergence |

Intermediate revisions provide the trajectory connecting these conditions. Confirm the converged specification’s performance using fresh runs beyond those used to select it.

## Controls and records

- Keep the feature’s behavioral intent and scope fixed. Specification wording, organization, and structural detail may change through the loop.
- Keep the specification category inventory fixed. Every edit must map to a listed category and subsection.
- Keep model configuration, pre-change repository access, agent tools, per-run generation budget, and evaluation criteria fixed across revisions.
- Use fresh, isolated code-generation runs from the pre-change repository rather than carrying forward generated code from earlier revisions.
- Preserve each exact specification revision and record its parent, judge diagnosis, categories changed, edits, hypotheses, and evaluation results.
- Evaluate architectural intent and repository conventions; valid implementations beyond the reference patch may satisfy the rubric.

## Interpretation and remaining methodological details

The baseline-to-convergence comparison measures the improvement achieved by the resulting specification. The revision history provides evidence about which content and formulations accompanied that improvement. A code failure does not establish that the specification caused it, and an adaptive trajectory alone does not isolate every edit’s causal effect.

Category boundaries and classification rules, model assignments for the behavioral-prompt generator, judge, and editor, the original-code context and per-run token limits, handling of regressions between successive revisions, and the response to failed confirmation or judge-audit discrepancies still need to be specified.
