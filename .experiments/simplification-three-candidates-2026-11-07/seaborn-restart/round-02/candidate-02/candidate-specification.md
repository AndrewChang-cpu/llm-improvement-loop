## Goals
Add Perc, a percentile transform for seaborn's objects interface. Replace observations with requested percentile values and record each level.

## Scope
Implement Perc in seaborn._stats.order as a Stat, export it from seaborn.objects for use with Plot.add, and document it in the API reference and v0.12.1 release notes.

## Data model
For each GroupBy group, return one row per requested level. Each row has the percentile value in the value column and its level in percentile; GroupBy supplies labels and grouping keys and preserves established ordering. Other input columns and original coordinates need not remain. Values may be floating point for integer inputs. The output represents percentile rows, not a point estimate or interval.

## API contracts
Expose Perc with k defaulting to 5 and method defaulting to linear. Integer k requests that many evenly spaced levels from 0 through 100 inclusive; a list supplies levels directly. Method selects NumPy percentile behavior. Implement the Stat call contract, accepting data, GroupBy, orientation, and a mapping of variables to Scale objects and returning a data frame.

## Module architecture
Keep the transform in the statistics layer, beside ordering statistics, and export it through seaborn.objects. Use the existing Stat extension point rather than an aggregation or standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Orientation is the independent axis, so compute the opposite value variable: y for horizontal plots and x for vertical plots. Use GroupBy.apply for the per-group data-frame transform to retain its labels, columns, and ordering. Plot's Stat dispatcher includes orientation among grouping variables, so orientation values can form separate groups. Ignore missing observations in the percentile calculation, retain requested levels, and accept the required scales mapping.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. NumPy versions before 1.22.0 require the interpolation percentile keyword; versions from 1.22.0 use method.

## Naming
Use Perc, k, method, and percentile for the level column.

## Validation
Support integer counts and explicit lists. Pass method through to NumPy and let unsupported values or methods raise percentile-operation exceptions. Do not impose interval-specific list-length restrictions or other validation that changes percentile behavior.

## Documentation
Document the parameters and row-per-percentile output. Explain integer levels from 0 to 100 and explicit levels; describe method as NumPy's percentile choice, defaulting to linear, with valid choices inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. Include examples using the public so namespace for default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark to show an interval. Add Perc to the public Stat objects autosummary in doc/api.rst and add an objects.Perc feature entry to the v0.12.1 release notes.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc available and support NumPy percentile keyword conventions on both sides of version 1.22.0.

## Behavioral acceptance criteria
Integer k produces k evenly spaced levels including 0 and 100; lists produce one row per requested level. Values honor method, orientation selects the opposite value variable, and missing observations are ignored. Grouped results preserve GroupBy labels and ordering and include the value, percentile, and grouping keys without requiring unrelated columns. The transform composes through Plot.add with valid mark inputs.

## Test requirements
If tests are added or changed, follow neighboring statistics tests' fixture and class-based style. Cover counts, explicit levels, values, orientations, methods, grouping/order, missing data, public imports, and Plot.add as appropriate. Choose direct-test grouping variables deliberately because orientation may split groups; assert actual labels and output columns, not unrelated source columns, and import only names used by tests.
