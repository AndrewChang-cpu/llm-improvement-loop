## Goals
Add Perc, an objects statistical transform that replaces observations with requested percentile values and records their levels.

## Scope
Define Perc in seaborn._stats.order, export it through seaborn.objects, and support it as a Stat in Plot.add. Document it in the API reference and release notes.

## Data model
Return one row per requested percentile per group. The computed value is in the orientation-selected value column and its level in percentile. GroupBy supplies keys and labels and determines column order; unrelated input columns and original coordinates need not survive.

## API contracts
Expose public class Perc with k defaulting to 5: an integer requests that many evenly spaced levels from 0 through 100 inclusive; a list supplies explicit levels in [0, 100]. The method parameter selects NumPy percentile behavior and defaults to linear. Implement the Stat call contract, accepting data, GroupBy, orientation, and a mapping of variables to Scale objects, and returning a data frame.

## Module architecture
Implement Perc as a Stat subclass in the statistics layer, alongside ordering statistics. Do not use aggregation or a standalone plotting operation.

## Implementation constraints
Declare orientation grouping. Horizontal plots compute on y; vertical plots compute on x. Use GroupBy.apply for the per-group data-frame transform to retain labels, established order, and column arrangement. Plot's Stat dispatcher includes orientation among grouping variables, so orientations can form separate groups. Ignore missing observations and preserve requested levels.

## Dependencies
Use existing NumPy, pandas, GroupBy, Scale, Stat, and Version abstractions; add no dependencies. With NumPy before 1.22.0, pass method as interpolation; from 1.22.0, pass it as method.

## Validation
Let NumPy raise percentile-operation exceptions for unsupported inputs or methods. Do not add interval-specific list-length restrictions or other validation that changes percentile behavior.

## Documentation
Describe parameters and percentile-row output, including integer levels from 0 to 100 and explicit lists. Explain that method defaults to linear and accepts NumPy's choices: inverted_cdf, averaged_inverted_cdf, closest_observation, interpolated_inverted_cdf, hazen, weibull, linear, median_unbiased, normal_unbiased, lower, higher, midpoint, and nearest. Add public so examples for default quartiles and endpoints, an integer count, explicit levels, and combining Perc with a range mark for an interval. Add Perc to the Stat objects autosummary in doc/api.rst and add an objects.Perc feature entry to v0.12.1 release notes.

## Compatibility
Keep seaborn._stats.order.Perc and seaborn.objects.Perc available.

## Behavioral acceptance criteria
Verify integer and explicit levels, selected method, orientation, missing observations, grouped labels and order, output columns, and Plot.add composition with valid marks. Results remain percentile rows.

## Test requirements
If tests are added or changed, follow neighboring statistics tests' fixture and class-based style. Cover counts, explicit levels, values, orientations, method, grouping and order, missing data, both imports, and Plot.add as appropriate. Choose direct-test grouping variables deliberately: included orientations form separate groups. Assert actual group labels and output columns, not unrelated source columns; import only test-used names.
