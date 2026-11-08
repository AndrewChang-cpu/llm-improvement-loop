## Goals
Add Perc, a statistical transform for seaborn's objects interface. Replace observations with requested percentile values and record each level.

## Scope
Define Perc in seaborn._stats.order, export it through seaborn.objects, and support use as a Stat in Plot.add. Document the API and release.

## Data model
Return one row per requested percentile per group. The computed value goes in the value column; percentile records the level. GroupBy adds keys and labels and controls column order. Preserve its labels and order. Unrelated input columns and original coordinates need not survive. Integer inputs may produce floating-point values. Results are percentile rows, not a point estimate or interval.

## API contracts
Expose public class Perc with k defaulting to 5 and method defaulting to linear. Integer k requests that many evenly spaced levels from 0 through 100 inclusive; a list supplies levels directly. Method selects NumPy percentile behavior. Implement the Stat call contract: accept data, GroupBy, orientation, and a mapping of variable names to Scale objects; return a data frame. Accept the scales mapping even though computation does not use it.

## Module architecture
Implement Perc beside ordering statistics as a Stat subclass, not as aggregation or a standalone plotting operation. Declare orientation grouping so Plot's Stat dispatcher can group by orientation. Orientation is the independent axis: horizontal plots compute on y, vertical plots on x. Use GroupBy.apply for the per-group data-frame transform, preserving labels, column arrangement, and established order. Ignore missing observations and preserve requested levels.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. For NumPy before 1.22.0, use the interpolation keyword; from 1.22.0 onward, use method. Pass method to NumPy and let percentile-operation exceptions handle unsupported inputs or methods. Do not add interval-specific list-length restrictions or validation that changes percentile behavior.

## Documentation
Explain k, method, and percentile-row output, including integer levels from 0 to 100 and explicit lists. Describe method as NumPy's percentile choice, default linear, and list its choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, nearest. Add public so examples for default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark for an interval. Add Perc to the Stat objects autosummary in doc/api.rst and add an objects.Perc feature entry to v0.12.1 release notes.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc available.

## Behavioral acceptance criteria
Integer k produces that many levels including 0 and 100; a list produces one row per requested level. Values honor method, missing observations are ignored, and orientation selects the opposite value variable. Return value, percentile, and grouping keys; Perc composes through Plot.add with valid marks and returns percentile rows.

## Test requirements
If tests are added or changed, follow neighboring statistics tests' fixture and class-based style. Cover counts, explicit levels, values, orientations, method, grouping and order, missing data, both imports, and Plot.add as appropriate. In direct tests, account for distinct orientation groups when orientation is included. Assert actual group labels and output columns; import only test-used names.
