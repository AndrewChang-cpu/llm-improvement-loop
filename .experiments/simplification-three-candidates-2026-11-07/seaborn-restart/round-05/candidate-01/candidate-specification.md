## Goals
Add Perc, an objects statistical transform that replaces observations with requested percentile values and records levels.

## Scope
Implement Perc in seaborn._stats.order, export it from seaborn.objects for Plot.add, document its API, and add a v0.12.1 release note.

## Data model
Return one row per requested percentile per group. Put each value in the orientation-selected coordinate and its level in percentile. GroupBy supplies keys and labels, order, and column arrangement; unrelated input columns and original coordinates may be dropped.

## API contracts
Expose Perc with k defaulting to 5 and method defaulting to linear. Integer k requests that many evenly spaced levels from 0 to 100 inclusive; a list gives explicit levels in [0, 100]. Implement the Stat call contract: accept data, GroupBy, orientation, and variable-to-Scale mappings, and return a data frame.

## Module architecture
Subclass Stat in the statistics layer alongside ordering statistics. Do not use aggregation.

## Implementation constraints
Declare orientation grouping. Compute y for horizontal plots and x for vertical plots. Use GroupBy.apply for the per-group data-frame transform to preserve labels, order, and column arrangement. Plot dispatch can supply separate orientation groups. Ignore missing observations and retain every requested level.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. Before NumPy 1.22.0, pass method as interpolation; from 1.22.0 onward, as method.

## Validation
Let NumPy report unsupported levels or methods. Add no interval-specific list-length or other validation that changes NumPy behavior.

## Documentation
Document parameters and percentile-row output, integer-generated levels, explicit lists, and the linear default. List NumPy methods: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. In public so docs, show default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark for an interval. Add Perc to the Stat objects autosummary in doc/api.rst and v0.12.1 release notes as objects.Perc.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc importable.

## Test requirements
Changed or added tests must follow statistics fixtures and class style. Cover counts, explicit levels, values, method, both orientations, missing data, group labels and order, output columns, both imports, and Plot.add with marks. Direct tests must account for orientation grouping, assert actual labels and output columns rather than unrelated source columns, and import only used names.
