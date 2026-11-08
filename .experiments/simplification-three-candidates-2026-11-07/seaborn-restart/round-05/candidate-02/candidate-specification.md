## Goals
Add Perc, an objects statistical transform that replaces observations with requested percentile values and records each level.

## Scope
Implement in seaborn._stats.order, export through seaborn.objects, support Plot.add, document the API, and add a v0.12.1 release note.

## Data model
Return one row per requested percentile in each group. Put the value in the orientation-selected column and the level in percentile. Use GroupBy to preserve group labels, established order, and column arrangement; unrelated input columns and original coordinates may be dropped.

## API contracts
Expose Perc with k defaulting to 5 and method defaulting to linear. An integer k requests that many evenly spaced levels from 0 through 100 inclusive; a list gives explicit levels in [0, 100]. Follow the Stat call contract: receive data, GroupBy, orientation, and variable-to-Scale mappings; return a data frame.

## Module architecture
Define Perc as a Stat subclass in the statistics layer alongside ordering statistics. Do not implement it as aggregation or a standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Compute on y for horizontal plots and x for vertical plots. Use GroupBy.apply for each group's data-frame transform. Plot's dispatcher includes orientation among grouping variables, so inputs may contain separate orientation groups. Ignore missing observations and retain all requested levels.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. For NumPy before 1.22.0, pass method as interpolation; from 1.22.0 onward, pass it as method.

## Validation
Let NumPy report unsupported percentile inputs and methods. Add no list-length or other validation that changes NumPy behavior.

## Documentation
Document parameters and percentile-row output, the linear default, and NumPy's methods: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. In public so documentation, demonstrate default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark for an interval. Add Perc to the Stat objects autosummary in doc/api.rst and to v0.12.1 release notes as objects.Perc.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc importable.

## Test requirements
Cover counts, explicit levels, values, methods, both orientations, missing data, group labels and order, output columns, both imports, and Plot.add with marks. Direct tests must account for orientation grouping and assert actual labels and output columns, not unrelated source columns.
