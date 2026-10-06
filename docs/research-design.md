# Research problem and experimental design

## Refined Problem Statement

In industrial software engineering, development in production codebases requires strict adherence to existing structural paradigms. While Large Language Models (LLMs) can generate functionally correct code, they frequently exhibit excessive agency by deviating from established repository patterns and ignoring structural constraints. Currently, engineering teams lack empirical data on which specific requirements engineering (RE) categories—such as technical constraints, user stories, or data models—effectively force an LLM to follow intended architectural designs. Without this knowledge, specifications remain bloated and incomplete, and AI-generated code requires heavy manual refactoring to match the author's exact organizational intent.

By treating software specifications as executable hypotheses and evaluating LLM-generated code structure, we can empirically isolate the exact specification elements required to enforce structural coherency in AI-generated code.

This research will evaluate how specification content and formulation guide architectural adherence. The experiment will use a controlled set of feature requests from open-source production codebases utilizing specific design patterns (e.g., explicit layered architectures). Starting from a basic behavioral-intent prompt, an iterative feedback loop will diagnose structural deficiencies in generated code and revise the specification by introducing or improving relevant specification categories. The comprehensive specification is the result of this loop at convergence, rather than a predetermined collection of components appended to the baseline.

To measure variability across repeated runs, each specification variant will be processed by n=10 independent LLM sub-agents. An automated LLM-as-a-judge will evaluate the output against the repository’s reference implementation using pass/fail judgments for each required criterion, supported by evidence and descriptions of deficiencies. The primary evaluation metric will be the proportion of runs that pass every required criterion, including structural coherency—correct file placement, exact API signature matching, the use of existing dependencies, etc. Algorithmic logic will be evaluated through the behavioral requirements rather than assigned a numerical weight.

The scope of this research is strictly limited to feature requests within existing brownfield environments. Success is defined primarily as structural and organizational adherence to the intended design, not merely functional execution; a patch that passes unit tests but violates the required architecture will be categorized as a structural failure. Furthermore, due to the non-deterministic nature of LLMs, a specification variant will only be deemed effective if it achieves a 90% structural pass rate across the ten parallel agents, acknowledging that a single successful generation is insufficient proof of a specification's quality.

## Evaluation Criteria

All to be checked by the LLM-as-a-judge for simplicity and generalizability. Each required criterion receives a pass/fail judgment supported by evidence. A run passes only when every required criterion passes; the specification passes when at least nine of ten fresh, independent runs pass. No numerical criterion scores or weighted totals are used.

### Static checks

- Patch applies; build/typecheck/lint/test status.
- Required file/module location.
- API name, visibility, parameters, types, and return contract.
- Allowed/forbidden imports and dependency directions.
- Required registration, interface implementation, or extension-point use.
- No newly introduced dependencies, or only approved ones.

### Subjective checks

Evaluate each required item as pass or fail and require evidence with file/line references. For failures, describe the specific deficiency to inform specification refinement:

- Architectural fit: Does the patch place responsibilities in the repository’s intended layer or component, rather than merely an allowed folder?
- Extension-point adherence: Does it reuse the established abstraction, factory, service, handler, repository, or framework mechanism instead of creating a parallel path?
- Abstraction integrity: Does it avoid leaking domain, persistence, transport, or framework details across boundaries?
- Repository convention fit: Does its error handling, validation, naming, logging, and test style match analogous local code?
- Requirement intent: Does the implementation satisfy the behavioral intent and constraints that tests do not fully cover?

When a user is generating their specs, they should select the above criteria that are relevant to their use case. Different users/use cases want different levels of LLM agency.

The required criteria for each feature are fixed before evaluating its baseline and remain unchanged throughout refinement. Their interpretation follows that feature’s requirements and repository conventions.

## Evidence and Data

Documentary data will consist of historical feature requests and their merged pull requests drawn primarily from FEA-Bench, with additional data sources potentially included after their suitability is assessed. FEA-Bench is a feature-implementation benchmark containing 1,401 task instances from 83 GitHub repositories. Its public release provides task metadata; the descriptions and patches must be reconstructed from GitHub using the benchmark tooling. The current repository shortlist is scikit-learn, Matplotlib, boto3, Scrapy, Django, Seaborn, Flask, and Sphinx. Quantitative data will consist of per-criterion and per-run pass/fail judgments generated by an automated LLM-as-a-judge, with pass rates aggregated across 10 agent runs for each specification variant.

FEA-Bench and the shortlisted Python repositories provide candidate brownfield environments with established implementation patterns. Selecting feature additions from these sources is intended to require the LLM to navigate structural boundaries rather than make only localized logic tweaks. Each task’s relevant architectural or implementation pattern must be established individually; repository membership alone does not demonstrate that a feature exercises a particular pattern.

The experiment begins by extracting historical feature requests, capturing both the initial codebase state and the merged reference implementation. The original PR title and description, including any code, serve directly as the baseline specification. Each specification revision will be processed by ten fresh headless Codex sessions, generating code from the initial repository state. The LLM-as-a-judge will evaluate these outputs against the reference implementation using the same evaluation criteria throughout the loop. Reference code defines target behavior, public contracts, and architecture; the PR description supplies only the baseline generation input and is not an independent evaluation requirement. A specification editor with access to the current specification, reference code, generated code, and judge feedback will produce one next revision at a time. The code generator will receive only the specification and original code, with repository search, read, and edit tools. All roles use GPT-6 Luna through ChatGPT-authenticated Codex. The comparison is between the PR baseline and the comprehensive specification produced at convergence, with intermediate revisions retained to analyze the refinement trajectory.

A specification variant meets the observed acceptance threshold when at least nine of ten fresh, independent runs each pass every required criterion. This is the loop’s convergence rule. Repeated runs measure variability in generated outputs.

A major limitation is the reliability of the LLM-as-a-judge, which may exhibit self-preference bias or hallucinate structural success if the generated logic is convincing. Additionally, brownfield repositories contain historical technical debt; the human-written reference PR itself might occasionally bend intended architectural rules, potentially confusing the evaluator. Finally, because current LLMs struggle inherently with complex codebase navigation, a high baseline failure rate might make it difficult to isolate the exact impact of individual specification variables.

## Warrants

Improved architectural adherence between the PR baseline and the comprehensive specification would support the effectiveness of the resulting specification. Intermediate revisions will record the categories introduced or changed, the formulations used, and the corresponding evaluation results. These trajectories can identify specification changes associated with improvement while the repository and model are held constant; they do not by themselves establish that any individual category is the sole cause of that improvement.

Treating specifications as executable hypotheses allows their structural pass rates and output variability to be measured across n=10 runs. Consistent results would provide evidence that an observed improvement extends beyond a single successful generation. However, several confounding factors must be considered when interpreting these patterns. A consistent failure across all variants might indicate that the repository's state overwhelmed the LLM's context window and reasoning limits, rather than representing a failure of the specification itself. Additionally, the automated LLM-as-a-judge could introduce variance through self-preference bias, scoring a variant highly because the generated code matches its pre-trained biases rather than strictly adhering to the repository's intended brownfield architecture.

## Backing

Zheng et al. (2023), "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." Supports the validity of the automated evaluation method. It proves that an LLM evaluator, when grading against a strict rubric, achieves over 80% agreement with human expert assessments, justifying its use to score structural coherency at scale.

ISO/IEC/IEEE 29148:2018 (Systems and software engineering — Life cycle processes — Requirements engineering). Supports the real-world validity of the RE categories being tested. It provides a formalized taxonomy distinguishing functional requirements (user stories) from non-functional architectural constraints, ensuring the specification mutations are grounded in standard industrial classifications.

Hou et al. (2023), "Large Language Models for Software Engineering: A Systematic Literature Review." Supports the core warrant logic. By synthesizing empirical studies on LLM code generation, it confirms that prompt structure and contextual constraints directly govern output accuracy, validating the premise that specific RE elements will causally shift the agent's architectural adherence.

## Manual judge validation

Ten randomly selected generated patches from the initial pilot will be manually evaluated against the same required criteria to assess agreement with the LLM-as-a-judge.

## Experimental methodology

The feedback-driven specification refinement loop, category inventory, controls, and comparisons are documented in [Experimental methodology](experimental-methodology.md).

## Dataset scope

The initial pilot uses Sphinx #11989 and Seaborn #3063. The broader shortlist below remains the pool for later task selection.

The eight shortlisted repositories contain 186 FEA-Bench task instances:

| Repository | FEA-Bench tasks |
| --- | ---: |
| scikit-learn/scikit-learn | 83 |
| matplotlib/matplotlib | 34 |
| boto/boto3 | 17 |
| scrapy/scrapy | 9 |
| django/django | 7 |
| mwaskom/seaborn | 5 |
| pallets/flask | 1 |
| sphinx-doc/sphinx | 30 |
| **Total** | **186** |
