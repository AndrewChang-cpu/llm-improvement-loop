# Specification ablation analysis

The ablations produced **three failures in Sphinx and three in Seaborn**. The strongest evidence concerns Sphinx’s **API contracts** and **Test requirements**, and Seaborn’s **Documentation**. Those failures correspond directly to instructions that were removed. The other failures have weaker connections to the omitted sections.

## What each failed removal revealed

| Removed section | Specific failure | Interpretation |
|---|---|---|
| **Sphinx: API contracts** | The generated index entry was `Class.Alias2 (in module example)` instead of `Alias2 (type alias in example.Class)`. Candidate tests passed; reference tests failed. | This section contained the exact distinction between module-level and class-nested index entries. The remaining instructions communicated that nested aliases must work, but did not adequately communicate their expected index representation. This is the clearest example of lost specification detail producing a corresponding implementation deviation. |
| **Sphinx: Test requirements** | The patch added no feature tests, violating repository policy. It also assigned a tuple element to `_`, hiding Sphinx’s translation function; subsequent calls raised `TypeError`. Seven reference tests failed. | The explicit request for feature regression coverage affected whether tests were produced. Existing candidate-stage tests passed because they did not exercise the new behavior sufficiently. Feature tests could have exposed the runtime bug during generation, although this run does not establish that adding them would necessarily have prevented it. |
| **Seaborn: Documentation** | Both executable test stages passed, but the class documentation lacked explanations of `k`, percentile selection, and `method`. Convention fit failed. | The removed section specified a separate deliverable: explaining the public interface. Knowing how to implement the parameters did not automatically lead the agent to document them. |
| **Sphinx: Behavioral acceptance criteria** | The implementation used a different signature-prefix node, failing expected doctree and HTML assertions. | The remaining API contracts still described the signature, and similar rendering failures occurred with the full specification. This result provides limited evidence that the acceptance section itself was essential. |
| **Seaborn: API contracts** | Reference tests passed, but generated tests incorrectly expected floating-point values and too few percentile rows. | The implementation retained the required behavior. The patch failed because its verification assertions were wrong, so this is weaker evidence for API contracts being necessary to implement the feature correctly. |
| **Seaborn: Naming** | Both executable stages passed. Convention fit failed because the module contained an unused `pandas` import. | The failure did not concern the required class, parameter, or column names. There is no clear connection between removing Naming and introducing that import. |

The distinction between **implementation failure and evaluation failure** matters here. Seaborn’s Documentation and Naming removals produced working implementations that nevertheless failed the broader rubric. Its API-contract removal produced reference-correct code accompanied by incorrect tests.

## What the passing removals reveal

Removing **Goals, Workflows, Data model, Module architecture, or Implementation constraints** passed in both projects.

These sections often overlap. In Seaborn, for example, removing Data model still leaves Behavioral acceptance criteria requiring the requested percentile levels and a percentile coordinate on each output row. Removing Module architecture still leaves API contracts naming the import locations.

Sphinx similarly repeats object registration, canonical handling, and cross-reference requirements across several sections. Removing one section therefore does not remove all information about that concern.

Consequently, these results measure **whether a particular section adds necessary information beyond the rest of the document**. They do not show that goals, architecture, or data models are unimportant.

## What this says about specification content

The useful signal is **distinct, actionable obligations**:

- Exact output contracts prevented an otherwise plausible interpretation of Sphinx’s indexing behavior.
- Explicit coverage requirements prompted work that existing tests did not require.
- Documentation instructions prompted an artifact that correct implementation alone did not guarantee.

No removal failed architectural fit, file placement, dependency direction, or extension-point adherence. For these two tasks, the remaining specifications and repository context preserved those properties.

The evidence supports investigating **Sphinx API contracts, Sphinx Test requirements, and Seaborn Documentation** first. With one generation per removal and historical full-spec comparisons, they are the strongest candidates for useful content—not established necessities or a general ranking of specification categories.
