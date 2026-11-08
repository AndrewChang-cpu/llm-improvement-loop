## Goals
Add Perc, a statistical transformation for seaborn's objects interface. It replaces observations with values at requested percentiles and records each level alongside its computed value.

## Scope
Implement Perc in seaborn._stats.order as a Stat subclass and export it from seaborn.objects. Make it usable through Plot.add. Document its public parameters, output, and use in the API documentation, and add a feature entry to the v0.12.1 release notes.

## Workflows
For each group supplied to the Stat, compute percentiles of the value variable opposite the plot orientation and return rows for downstream marks. Group formation and result order follow the supplied GroupBy, including orientation and any other grouping variables selected by the plot workflow. The result must compose with Plot.add and work with a mark when inputs and properties are valid.

## Data model
Return one row for each requested percentile in each group. Include the computed value in the value column opposite the orientation, the requested level in a column named percentile, and grouping columns with their labels. GroupBy.apply combines columns returned by the per-group transformation with grouping keys; unrelated input columns and original coordinates need not be retained. Computed values may be floating point even when observations are integers. This is percentile output, not one summary estimate or a min/max interval.

## API contracts
The public name is Perc. Parameter k accepts an integer count or a list of levels, defaulting to 5. An integer requests that many evenly spaced levels from 0 through 100, inclusive; a list is used directly. Parameter method selects NumPy percentile behavior and defaults to linear. Implement the existing Stat call contract: accept a data frame, GroupBy, orientation, and mapping of variables to Scale objects; return a data frame.

## Module architecture
Keep the computation in seaborn._stats.order alongside ordering statistics. Export it from seaborn.objects by importing it from that module. Do not place it in seaborn._stats.aggregation or implement it as a standalone plotting operation.

## Implementation constraints
Declare that Perc groups by orientation. Orientation identifies the independent axis: horizontal orientation computes from y, while vertical orientation computes from x. Use GroupBy.apply for the per-group data-frame transformation so grouping labels, column arrangement, and established ordering follow GroupBy behavior. The Plot Stat dispatcher adds the orientation variable to grouping when the statistic declares orientation grouping, so distinct orientation values may form separate groups. Exclude missing observations from percentile computation, preserve requested levels in the result, and accept the scales mapping required by Stat.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and version abstractions; introduce no dependency. For NumPy versions before 1.22.0, use the interpolation percentile keyword; from 1.22.0 onward, use the method keyword.

## Naming
Use Perc, k, and method as the public names. Name the percentile-level result column percentile.

## Validation
Support integer counts and explicit lists without imposing interval-only list-length restrictions or other validation that changes NumPy percentile behavior. Pass method through to percentile computation. Let errors for unsupported inputs or methods propagate.

## Documentation
Describe the parameters and the one-row-per-level output. Explain the default count of five, its evenly spaced levels from 0 through 100, and that explicit lists supply levels directly. Document method as NumPy's percentile choice, default linear, and list all valid choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. Include public usage examples for the default quartiles and endpoints, an integer count, an explicit list, and combining Perc output with a range mark to represent an interval. Add Perc to the public Stat objects autosummary in doc/api.rst and mention objects.Perc in the v0.12.1 release notes.

## Compatibility
Keep both seaborn._stats.order.Perc and seaborn.objects.Perc available, and support NumPy percentile keyword conventions on both sides of version 1.22.0.

## Behavioral acceptance criteria
Integer k returns exactly that many evenly spaced levels including 0 and 100, each paired with its computed value; list k returns one row per supplied level. Honor method, both orientations, and missing-value exclusion. Grouped results preserve the labels and order defined by GroupBy, including when the orientation variable is a grouping key. Return the value, percentile, and grouping columns produced by GroupBy.apply without requiring unrelated source columns. The transform composes with Plot.add and supplies percentile rows to marks.

## Test requirements
If adding tests, cover count and list forms, computed values, both orientation mappings, method selection, grouping and ordering, missing observations, public exports, and Plot.add use. In direct tests, group by variables intended to define each case, assert only actual grouping labels and output columns, and do not assume unrelated input columns survive GroupBy.apply.
