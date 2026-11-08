## Goals
Add Perc, a statistical transformation for seaborn's objects interface. For each requested percentile, replace observations with its computed value and record the percentile level.

## Scope
Define Perc in seaborn._stats.order, export it through seaborn.objects, and support it as a Stat in Plot.add. Document its public API and add a v0.12.1 release note.

## Workflows
For each group supplied by the Stat workflow, compute percentiles of the value variable opposite the plot orientation. Group formation and output order follow GroupBy, including orientation and any plot-selected grouping variables.

## Data model
Return one row per requested level per group. Each row has the computed value in the value column and its requested level in a percentile column. GroupBy.apply combines these returned columns with grouping keys and labels, reorders columns according to its established behavior, and orders groups as configured. Other input columns and original coordinates need not survive. Computed values may be floating point even for integer inputs. Output is percentile rows, not a single estimate or interval.

## API contracts
Name the public statistic Perc. Its k parameter accepts an integer count or a list of levels and defaults to 5; an integer requests that many evenly spaced levels from 0 through 100 inclusive, while a list specifies levels directly. The method string selects NumPy percentile behavior and defaults to linear. Implement the existing Stat call contract: accept a data frame, GroupBy, orientation, and mapping of variables to Scale objects; return a data frame.

## Module architecture
Implement Perc as a Stat subclass in seaborn._stats.order alongside ordering statistics, and import it into seaborn.objects. Keep percentile computation in the statistics layer; do not place it in aggregation or implement a standalone plot operation.

## Implementation constraints
Declare that Perc groups by orientation. Orientation is the independent axis, so use y for horizontal plots and x for vertical plots. Compute each group through GroupBy.apply, preserving its grouping labels, column behavior, and configured order. The Plot dispatcher includes orientation among grouping variables when group_by_orient is true, so distinct orientation values can form separate groups. Exclude missing observations from percentile computation and retain requested levels in output. Accept the scales argument required by Stat.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions. For NumPy versions before 1.22.0, pass the percentile choice through the interpolation keyword; from 1.22.0 onward, use the method keyword.

## Naming
Use parameter names k and method and the result column name percentile.

## Validation
Support integer counts and explicit level lists. Pass method to NumPy and allow its errors for unsupported inputs or choices to propagate. Do not restrict list length to interval endpoints or add validation that changes NumPy behavior.

## Documentation
Describe the parameters, defaults, percentile-row output, and the integer versus list meaning of k. Explain that method chooses NumPy percentile behavior and enumerate its valid choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. Provide public examples for default quartiles and endpoints, an integer count, an explicit list, and combining Perc with a range mark for an interval. Add Perc to the public Stat objects autosummary in doc/api.rst and add an objects.Perc feature entry to the v0.12.1 release notes.

## Compatibility
Expose both seaborn._stats.order.Perc and seaborn.objects.Perc. Support NumPy percentile keyword conventions on both sides of the 1.22.0 boundary.

## Behavioral acceptance criteria
Integer counts produce that many evenly spaced levels including 0 and 100; explicit lists produce one row per supplied level. Values honor the selected method, ignore missing observations, and use the variable opposite orientation. Grouped results preserve GroupBy-defined labels and order. Return computed values, levels, and grouping keys, without requiring unrelated input columns. Perc composes with Plot.add and marks when plot inputs and properties are valid; results remain percentile rows, not an estimate or interval.

## Test requirements
Follow neighboring statistics test organization with a shared fixture class for data and GroupBy setup and a Perc test class with methods for integer and explicit levels, values, both orientations, method choice, grouping/order, missing observations, both import paths, and Plot.add use. In direct tests, configure GroupBy to express intended groups, including distinct values of an orientation variable; assert grouping labels only for actual grouping variables. Assert value and percentile columns without requiring unrelated source columns. Import only names used.
