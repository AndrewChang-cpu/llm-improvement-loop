## Goals
Add Perc, a statistical transform for seaborn's objects interface. For each group, it replaces observations with requested percentile values and records each level.

## Scope
Implement Perc in seaborn._stats.order, export it from seaborn.objects, and support it as a Stat in Plot.add. Document the public statistic in API documentation and release notes.

## Workflows
Compute percentiles of the value variable opposite the plot orientation for each Stat group. Return rows for downstream marks. Group formation, labels, and ordering follow GroupBy, including plot-selected grouping variables and orientation.

## Data model
Return one row per requested level per group, with the computed value in the value column and level in percentile. GroupBy adds grouping keys and labels. Unrelated input columns and original coordinates need not survive. Values may be floating point for integer inputs; output is percentile rows, not a point estimate or interval.

## API contracts
The public class is Perc. Parameter k defaults to 5 and accepts an integer count or list of levels. A count requests evenly spaced levels from 0 through 100 inclusive; a list supplies levels directly. Parameter method selects NumPy percentile behavior and defaults to linear. Implement the Stat call contract: receive data, GroupBy, orientation, and a mapping of variables to Scale objects; return a data frame.

## Module architecture
Keep computation in the statistics layer as a Stat subclass beside ordering statistics. Export Perc through seaborn.objects for Plot.add composition. Do not implement it as an aggregation or standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Orientation is the independent axis, so horizontal plots compute on y and vertical plots on x. Use GroupBy.apply for the per-group data-frame transform, retaining its labels, column arrangement, and ordering. Plot's Stat dispatcher then separates distinct orientation values into groups. Exclude missing observations, preserve requested levels, and accept the required scales mapping.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. Before NumPy 1.22.0 use its interpolation keyword; from 1.22.0 use method.

## Naming
Use Perc, parameters k and method, and percentile for the level column.

## Validation
Pass method to NumPy and let percentile-operation exceptions propagate for unsupported values or methods. Do not impose interval-only list-length restrictions or other validation that changes percentile behavior.

## Documentation
Explain k, method, and the one-row-per-level output. State that integer k creates evenly spaced levels from 0 to 100 and lists give explicit levels. Describe method as NumPy's percentile choice, defaulting to linear, and list valid choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, nearest. Include examples using public namespace so for default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark for an interval. Add Perc to the public Stat objects autosummary in doc/api.rst and add an objects.Perc feature entry to v0.12.1 release notes.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc available, with NumPy keyword conventions supported on both sides of version 1.22.0.

## Behavioral acceptance criteria
Counts return that many evenly spaced levels including endpoints; lists return one row per requested level. Values honor method, orientation selects the opposite value variable, missing observations are ignored, and grouped output preserves GroupBy labels and ordering. Return the value, percentile, and grouping keys without requiring unrelated columns. The transform composes through Plot.add with valid mark inputs and returns percentile rows.

## Test requirements
If tests change, follow neighboring statistics fixtures and class-based style. Cover counts, explicit levels, values, orientation, method, grouping/order, missing data, both imports, and Plot.add as appropriate. Choose direct-test grouping variables deliberately because orientation may split groups; assert actual labels and output columns, not unrelated source columns, and import only names used.
