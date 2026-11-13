## Goals
Add Perc, a statistical transform that replaces observations with requested percentile values and records their levels.

## Scope
Implement Perc in seaborn._stats.order, export it from seaborn.objects for Plot.add, and document it in the API reference and v0.12.1 release notes.

## Data model
Return one row per requested percentile per group, with values in the orientation-selected column and levels in percentile. GroupBy supplies keys and labels and preserves group and column order. Unrelated source columns and original coordinates need not remain.

## API contracts
Expose Perc with k defaulting to 5: an integer requests that many evenly spaced levels from 0 through 100 inclusive; a list supplies explicit levels in [0, 100]. method selects NumPy percentile behavior and defaults to linear. Implement the Stat call contract: accept data, GroupBy, orientation, and a variable-to-Scale mapping; return a data frame.

## Module architecture
Implement Perc as a Stat subclass in the statistics layer beside ordering statistics, not as aggregation or a standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Horizontal plots compute on y; vertical plots on x. Use GroupBy.apply for the per-group data-frame transform to preserve labels, order, and column arrangement. Plot's Stat dispatcher includes orientation among grouping variables, so orientations may form separate groups. Ignore missing observations and preserve requested levels.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. For NumPy before 1.22.0, pass method as interpolation; otherwise pass it as method.

## Validation
Let NumPy raise errors for unsupported inputs or methods. Add no interval-specific list-length restrictions or behavior-changing validation.

## Documentation
Describe parameters and percentile-row output, including integer levels and explicit lists. Explain the linear default and NumPy method choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. Add public so examples for default quartiles and endpoints, an integer count, explicit levels, and using Perc with a range mark for an interval. Add Perc to the Stat objects autosummary in doc/api.rst and an objects.Perc feature entry to v0.12.1 release notes.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc available.

## Behavioral acceptance criteria
Verify values, levels, grouping, orientation, missing data, and Plot.add output.

## Test requirements
Added or changed tests must follow neighboring statistics tests' fixture and class-based style. Cover counts, levels, values, orientations, method, groups and order, missing data, both imports, and Plot.add as appropriate. Choose direct-test grouping variables deliberately because included orientations create separate groups. Assert group labels and output columns, not unrelated source columns; import only test-used names.
