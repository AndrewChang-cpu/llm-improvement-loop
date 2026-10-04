# Open research questions

## Pilot execution

The initial pilot uses Sphinx #11989 and Seaborn #3063. scikit-learn #29260, Matplotlib #22387, Scrapy #3505, and scikit-learn #29705 remain candidates for later expansion. Their feature descriptions and PR links are in [references.md](references.md#candidate-pull-requests).

The candidate screening covered all 186 shortlisted PR descriptions and changed-file structural summaries, with closer patch inspection for the strongest candidates. Historical environments and tests still need execution validation.

## Methodology and evidence

1. **Statistical claims — Problem Statement, Evidence and Data, Warrants:** Nine successes in ten runs is an observed 90% pass rate, not proof that the underlying success probability is at least 90%. Repeated sampling does not eliminate stochasticity. Define how uncertainty in the observed pass rate will be reported and how generator variability and judge variability will be measured separately.
2. **Causal interpretation — Problem Statement and Warrants:** The main experiment is feedback-driven specification refinement. Replacing stories with constraints can simultaneously change category, specificity, length, and behavioral content. Define how changes will be classified and how associations with improvement will be reported without claiming isolated category effects.
3. **Privileged solution information — Evidence and Data:** The specification editor receives reference code, generated code, and judge feedback. The code generator receives only the specification and original code. Document this reference-informed setting when interpreting results.
4. **Executable evidence — Evaluation Criteria:** A judge cannot establish build, lint, or test status without actual execution. Proposed direction: run executable checks, then supply their results to the judge alongside the patch and rubric.
5. **Criterion interpretation — Evaluation Criteria:** Document the task-specific requirements and repository evidence used to interpret the required criteria consistently. The success rule is defined: each run must pass every required criterion, and a specification passes when at least nine of ten fresh, independent runs pass. No numerical scores or weighted totals are used.
6. **Reference implementation — Problem Statement and Evidence and Data:** A merged PR is a reference implementation, not necessarily the only architecturally acceptable solution. Distinguish required public contracts and repository conventions from incidental helper names or decomposition choices.
7. **RE taxonomy — Problem Statement and Backing:** User stories and Gherkin are requirement representations, rather than necessarily distinct RE categories. Verify the proposed mapping to ISO/IEC/IEEE 29148 and the other RE sources before stating that the standard supplies the exact experimental taxonomy.
8. **Literature support — Backing and references.md:** Verify bibliographic details and whether each source supports the stated claim. MT-Bench agreement does not directly validate architectural code judgments; cited sampling designs do not establish that n=10 is sufficient; and a reported benchmark result is not automatically a directly comparable baseline for a different agent setup.
9. **Operational details — Evidence and Data and manual validation note:** The code generator uses GPT-5 nano with no tools, one response per run, ten fresh runs per revision, one candidate at a time, and a limit of ten specification revisions per PR after the baseline. The manual audit covers ten randomly selected generated patches. Specify models for the other roles, original-code context, per-run token limits, regression handling, and the response to failed confirmation or audit disagreements.

10. **Feature size:** Verify the characterization of FEA-Bench as mostly smaller-scale features before using it as a research claim.
