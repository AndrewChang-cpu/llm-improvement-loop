# References and source annotations

## Backing references

Zheng et al. (2023), "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." Supports the validity of the automated evaluation method. It proves that an LLM evaluator, when grading against a strict rubric, achieves over 80% agreement with human expert assessments, justifying its use to score structural coherency at scale.

ISO/IEC/IEEE 29148:2018 (Systems and software engineering — Life cycle processes — Requirements engineering). Supports the real-world validity of the RE categories being tested. It provides a formalized taxonomy distinguishing functional requirements (user stories) from non-functional architectural constraints, ensuring the specification mutations are grounded in standard industrial classifications.

Hou et al. (2023), "Large Language Models for Software Engineering: A Systematic Literature Review." Supports the core warrant logic. By synthesizing empirical studies on LLM code generation, it confirms that prompt structure and contextual constraints directly govern output accuracy, validating the premise that specific RE elements will causally shift the agent's architectural adherence.

## Paper notes

### LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead

https://dl.acm.org/doi/10.1145/3797276

This paper uses a similar research methodology that I plan on using and gives a technical foundation for the use of LLM-as-a-judge. It justifies that metrics like Pass@k can’t measure non-functional properties that I’m trying to measure, like stylistic consistency and architectural intent. It also supports my n=10 model because evaluator uncertainty is a fundamental flaw in subjective software assessments.

### An Empirical Study of the Non-Determinism of ChatGPT in Code Generation

https://dl.acm.org/doi/10.1145/3697010

This paper provides evidence supporting my assertions that LLM code output is very non-deterministic, which justifies by n=10 agent design. In this paper, the researchers generate 5 code candidates per task. The non-deterministic nature also supports my claim that LLMs prompts often don’t capture intent and bloated specifications degrade the quality of code.

### FEA-Bench: A Benchmark for Evaluating Repository-Level Code Generation for Feature Implementation

https://aclanthology.org/2025.acl-long.839.pdf

One piece of feedback I received was that SWE-bench isn’t appropriate for my research problem because I would run the risk of verifying how well LLMs and specs can fix bugs. FEA-Bench is an alternative dataset better suited for evaluating LLM performance creating new features. I can use this paper’s performance as a baseline reference on which I’m trying to improve. This paper finds that state-of-the-art models only resolve under 10% of feature tasks, which is evidence that supports my claim that LLMs struggle in existing codebases.

### LLM-Assisted Repository-Level Generation with Structured Spec-Driven Engineering

https://arxiv.org/html/2605.02455v1

This paper tries to solve the same research as my project. Their approach is to use structured spec-driven engineering to guide LLM code generation. They use Gherkin specifications and three open source repositories, and I may look into incorporating these into my experiments. There are differences in our methodologies, though. For example, my approach uses LLMs to generate specifications and for qualitative evaluations, whereas that's done by humans in this paper.

### ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification

https://dl.acm.org/doi/10.1145/3660810

Both this paper and my project address the limitation that LLMs can't capture intent (related work on similar research questions). Similarly, we use k different code solutions to address LLM stochasticity (work using a similar research methodology). One thing that's interesting about their approach is that they use LLMs to reason about the differences between solutions. I will probably do something similar. I also think that their approach for using high temperature during the sampling phase but zero temperature during the final code generation is a good idea for my project.

## Categorized references

### 1. Seminal / Foundational Papers

Liu, Xu, and McAuley (2024), “RepoBench: Benchmarking Repository-Level Code Auto-Completion Systems.”

RepoBench splits repository-level code auto-completion into three sub-tasks: cross-file retrieval (RepoBench-R), next-line code completion with in-file and cross-file context (RepoBench-C), and end-to-end pipeline evaluation (RepoBench-P). Their experiments show that completion accuracy drops sharply when models fail to retrieve imported code snippets. In my project, this paper provides evidence that LLMs struggle with multi-file dependencies, showing why we would feed explicit architectural constraints and evaluation criteria to the agent.

Toulmin Role: Evidence

Le et al. (2026), “Towards Architecture-Driven Code Generation with Generative AI: An Empirical Study.”

This paper evaluates five popular LLM tools using architecture-driven prompts based on a RESTful architecture and UML specifications when generating fullstack software. The authors find that all five tools fail to generate architecturally coherent systems without manual intervention. This is proof that LLMs struggle to maintain architectural compliance, motivating my iterative specification-refinement loop.

Toulmin Role: Evidence

### 2. Books or Book Chapters

van Lamsweerde, Axel (2009), Requirements Engineering: From System Goals to UML Models to Software Specifications. John Wiley & Sons.

This textbook defines a goal-oriented framework, showing how high-level user goals are systematically refined into formal software specifications, domain data models, and non-functional design constraints. I use van Lamsweerde's classification in my methodology section to define how the refinement loop rewrites broad user stories into formal software specs.

Toulmin Role: Backing

Wohlin et al. (2024), Experimentation in Software Engineering. Springer.

This textbook describes how to design controlled software engineering experiments, specifically covering factor isolation (holding blocking variables constant while mutating a single independent variable) and categorizing various validity threats. This justifies my methodology of holding the target repository and base LLM constant while mutating one RE category at a time.

Toulmin Role: Backing

### 3. Published Reports

Nascimento et al. (2025), “Designing Empirical Studies on LLM-Based Code Generation: Towards a Reference Framework.”

This paper proposes a reference framework for empirical LLM code studies organized around problem sources, quality attributes, and metrics. It incorporates output variance alongside fixed temperature and sampling parameters to capture LLM non-determinism. This backs my decision to measure output stability across 10 independent runs and require a 90% pass rate before determining a set of specifications is effective.

Toulmin Role: Backing

Tambon et al. (2025), “Bugs in Large Language Models Generated Code: An Empirical Study.”

By manually inspecting 333 bugs in LLM-generated code, the authors identify ten recurring defect types, showing that LLMs frequently hallucinate non-existent objects, call wrong API attributes, and misinterpret requirements. These defect categories in my evaluation design section justify why my grading rubric checks API signatures, import paths, and class inheritance rather than just functional logic.

Toulmin Role: Evidence

### 4. Concrete-Example Papers

Arun et al. (2025), “LLMs for Generation of Architectural Components: An Exploratory Empirical Study in the Serverless World.”

The authors mask serverless functions across 4 open-source repositories and regenerate them under varying levels of repository context. Models achieve lower pass rates when only given a README compared to prompts containing an architectural codebase summary and in-repo function examples. My experiment setup directly mirrors this paper's experimental design in that I take merged pull requests from open-source repos, revert the repo to its pre-PR state, and test which specification variants enable the agent to recreate the ground-truth code.

Toulmin Role: Evidence

Pan et al. (2026), “Toward Executable Repository-Level Code Generation via Environment Alignment.”

EnvGraph builds a structured graph of a repository's internal module references and external dependencies to guide LLM code generation. Across repository-level benchmarks, supplying these dependency boundaries improves functional correctness and non-functional quality compared to baselines. This shows that giving an LLM explicit dependency rules improves code structure in codebases.

Toulmin Role: Evidence

### 5. Terminology-Defining Papers or Standards

ISO/IEC/IEEE 29148:2018, Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.

This standard defines the industry taxonomy for software requirements. It defines the distinction between functional requirements (user stories and behavioral capabilities) and non-functional requirements (external interfaces, data schemas, and architectural design constraints). This guides the exact specification categories my refinement loop produces.

Toulmin Role: Backing

ISO/IEC/IEEE 42010:2022, Systems and Software Engineering — Architecture Description.

This standard defines some vocabulary for software engineering. It explains how system concerns are captured through architectural views, structural models, component boundaries, etc. This provides a basis for how I define successful structure in my evaluation suite.

Toulmin Role: Context/Terminology

### 6. Credible Author-Experience / Practitioner Sources

Jiang and Nam (2025), “An Empirical Study of Developer-Provided Context for AI Coding Assistants in Open-Source Projects.”

By analyzing .cursorrules files across 401 open-source repositories, this paper observes that engineers generally write project information, conventions, and guidelines. This shows that my project premise matches real-world behavior in that engineers already use explicit structural constraints to stop AI agents from breaking brownfield repos.

Toulmin Role: Evidence

Li, Liang, and Avgeriou (2023), “Warnings: Violation Symptoms Indicating Architecture Erosion.”

By analyzing 606 architectural code review comments, this study shows that maintainers detect architecture nonconformance generally through structural inconsistencies, violated architecture patterns (such as layered patterns), and broken API specifications and design rules. Because human reviewers define architectural health by module structure, layering, and API/design rules, grading an LLM's output on those properties validly measures architectural compliance.

Toulmin Role: Warrant

### 7. Timely Sources

Wang et al. (2025), “Can LLMs Replace Human Evaluators? An Empirical Study of LLM-as-a-Judge in Software Engineering.”

This study compares LLM-as-a-judge grading against human grading across code generation, translation, and summarization. It shows that while test-based metrics like Pass@k miss non-functional code quality, output-based LLM judges align closely with human scores. This justifies using an LLM judge to grade semantic structural adherence (which unit tests miss) and explains why I aggregate across 10 runs (and manually spot-check a random sample of grades to verify the quality of my LLM judgement).

Toulmin Role: Warrant

Liu et al. (2026), “Robustness Evaluation and Enhancement of LLMs in Code Generation: An Empirical Study.”

The authors test 25 code-generation LLMs by transforming input code to change how it is structured without changing its functional meaning. It proves that model pass rates swing widely based solely on input representation. Because LLM code generation is highly sensitive to how inputs are formatted, maintaining task meaning while reformatting user stories into structured technical constraints can causally demonstrate architectural compliance.

Toulmin Role: Warrant

### 8. Frameworks or APIs

GitHub Spec Kit

GitHub Spec Kit is an open-source toolkit for specification-driven AI coding that breaks feature requests into four distinct markdown artifacts: a project constitution, functional specification, technical plan, and data/interface contracts. Spec Kit gives background on a real-world framework that structures specifications into separate functional and architectural layers.

Toulmin Role: Context/Terminology

Import Linter Documentation and API

Import Linter is a static analysis framework for Python that parses a codebase’s module dependencies to enforce architectural contracts, such as layers, subpackage isolation, and banned imports. I can use Import Linter's contract rules in the static pass of the evaluation pipeline to check whether generated code violates the architectural constraints.

Toulmin Role: Context/Terminology

## Dataset sources

- FEA-Bench official repository and reconstruction/evaluation tooling: https://github.com/microsoft/FEA-Bench
- FEA-Bench public task metadata: https://huggingface.co/datasets/microsoft/FEA-Bench
- FEA-Bench dataset card: https://github.com/microsoft/FEA-Bench/blob/main/datasetcard.md
- FEA-Bench publication page: https://aclanthology.org/2025.acl-long.839/

## Candidate pull requests

| FEA-Bench instance | Feature | Source |
| --- | --- | --- |
| `sphinx-doc__sphinx-11989` | Type-alias directive and role | https://github.com/sphinx-doc/sphinx/pull/11989 |
| `mwaskom__seaborn-3063` | Percentile statistics component | https://github.com/mwaskom/seaborn/pull/3063 |
| `scikit-learn__scikit-learn-29260` | Metadata routing for SequentialFeatureSelector | https://github.com/scikit-learn/scikit-learn/pull/29260 |
| `matplotlib__matplotlib-22387` | Color sequence registry | https://github.com/matplotlib/matplotlib/pull/22387 |
| `scrapy__scrapy-3505` | JSON request subclass | https://github.com/scrapy/scrapy/pull/3505 |
| `scikit-learn__scikit-learn-29705` | FrozenEstimator wrapper | https://github.com/scikit-learn/scikit-learn/pull/29705 |

## Model documentation

- Codex models: https://developers.openai.com/codex/models
- Headless Codex: https://developers.openai.com/codex/noninteractive

All pilot roles use GPT-6 Luna through ChatGPT-authenticated Codex. The installed CLI successfully completed a GPT-6 Luna request; GPT-5 nano was rejected for ChatGPT account authentication.
