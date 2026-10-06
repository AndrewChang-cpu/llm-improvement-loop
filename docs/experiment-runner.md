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
