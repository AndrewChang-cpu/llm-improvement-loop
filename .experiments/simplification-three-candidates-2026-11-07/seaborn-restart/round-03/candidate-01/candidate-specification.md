## Goals
Add `Perc`, a statistical transform for seaborn’s objects interface. It replaces observations with requested percentile rows and records each level.

## Scope
Define it in `seaborn._stats.order`, export it from `seaborn.objects`, and support it as a `Stat` in `Plot.add`. Update API documentation and v0.12.1 release notes.

## Data model
Return one row per requested level per group, with the percentile value on the dependent axis and the level in `percentile`. GroupBy adds grouping keys, labels, and established column order; unrelated input columns and original coordinates need not remain. Integer inputs may produce floating-point values. These are percentile rows, not an estimate or interval.

## API contracts
Expose public `Perc` with `k=5` and `method="linear"`. An integer `k` requests that many evenly spaced levels from 0 through 100 inclusive; a list supplies levels directly. Match NumPy percentile semantics. Implement the existing Stat call contract, accepting data, GroupBy, orientation, and a mapping of variables to Scale objects, and returning a data frame.

## Module architecture
Implement `Perc` as a `Stat` subclass in the statistics layer beside ordering statistics. Do not implement it as aggregation or a standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Orientation is the independent axis: for horizontal orientation, compute on y; for vertical, compute on x. Use `GroupBy.apply` for the per-group data-frame transform so grouping labels, output column arrangement, and established order are retained. Plot’s Stat dispatcher includes orientation in grouping, so distinct orientation values can form distinct groups. Ignore missing observations and preserve requested levels. Accept the required scales mapping.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. For NumPy versions before 1.22.0 use its `interpolation` keyword; from 1.22.0 onward use `method`.

## Validation
Pass the selected method to NumPy and let unsupported levels or methods raise percentile-operation exceptions. Do not impose interval-specific list-length restrictions or other validation that changes percentile behavior.

## Documentation
Document parameters, the percentile-row output, integer and explicit levels, and NumPy’s method semantics with default `linear`. List the valid methods: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, nearest. Add public examples for default quartiles and endpoints, an integer count, explicit levels, and using `Perc` with a range mark for an interval. Add `Perc` to the Stat objects autosummary in `doc/api.rst` and an `objects.Perc` feature entry to v0.12.1 release notes.

## Compatibility
Keep both `seaborn._stats.order.Perc` and `seaborn.objects.Perc` available, with NumPy keyword compatibility on either side of 1.22.0.

## Test requirements
If tests are changed or added, follow neighboring statistics tests’ fixture and class-based style. Cover counts, explicit levels, values, orientation, method, grouping and order, missing data, both imports, and `Plot.add` as appropriate. For direct tests, account for separate groups when orientations differ. Assert group labels and output columns rather than unrelated source columns; import only names used by the tests.
