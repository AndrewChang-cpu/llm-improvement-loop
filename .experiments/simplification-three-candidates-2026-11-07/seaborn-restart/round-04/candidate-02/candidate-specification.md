## Goals
Add Perc, an objects statistical transform replacing observations with requested percentile values and recording each level.

## Scope
Define Perc in seaborn._stats.order, export it from seaborn.objects for Plot.add, and document it in the API reference and release notes.

## Data model
Return one row per requested percentile per group. Store values in the orientation-selected column and levels in percentile. Preserve GroupBy keys, labels, order, and column arrangement; unrelated input columns and original coordinates may be dropped.

## API contracts
Expose Perc with k defaulting to 5. An integer requests that many evenly spaced levels from 0 through 100 inclusive; a list gives explicit levels in [0, 100]. The method parameter selects NumPy percentile behavior and defaults to linear. Implement the Stat call contract, accepting data, GroupBy, orientation, and variable-to-Scale mappings, and returning a data frame.

## Module architecture
Implement Perc as a Stat subclass in the statistics layer, alongside ordering statistics; do not use aggregation or a standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Compute on y for horizontal plots and x for vertical plots. Use GroupBy.apply for the per-group data-frame transform to preserve labels, established order, and column arrangement. Plot's Stat dispatcher includes orientation among grouping variables, so orientations can form separate groups. Ignore missing observations and preserve requested levels.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. Before NumPy 1.22.0, pass method as interpolation; from 1.22.0 onward, pass it as method.

## Validation
Let NumPy raise percentile-operation exceptions for unsupported inputs or methods. Do not impose list-length restrictions or validation that changes NumPy percentile behavior.

## Documentation
Describe parameters and percentile-row output, including integer levels and explicit lists. Explain that method defaults to linear and accepts NumPy's choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. Add public examples for default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark for an interval. Add Perc to the Stat objects autosummary in doc/api.rst and add an objects.Perc feature entry to v0.12.1 release notes.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc available.

## Test requirements
When tests change, follow neighboring statistics tests' fixture and class-based style. Cover counts, explicit levels, values, orientation, method, grouping and order, missing data, both imports, and Plot.add as appropriate. Choose direct-test grouping variables deliberately because orientations form separate groups. Assert group labels and output columns, not unrelated source columns; import only test-used names.
