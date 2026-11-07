# Experiment execution

- Run experiments token efficiently: launch the script, save its output to a log, and wait for completion rather than reading every intermediate artifact.
- Inspect intermediate results for a small sample of features when useful to catch setup failures early. Do not inspect every implementation, judgment, or revision during a batch.
- After completion, read aggregate results and inspect individual artifacts only to explain failures or noteworthy outcomes.
- Do not manually correct or request replacement judgments within an experiment trajectory. Preserve the original model outputs.
- Validate the simplification loop on the existing Sphinx and Seaborn experiments first. Do not start the 100-PR experiment until the user reviews these results and authorizes it.
