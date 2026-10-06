## Goals

Add `Perc`, a statistical transformation that replaces observations along the value axis with requested percentile values. It must compose with the seaborn objects plotting API and preserve the percentile levels as data so they can be used by later plot processing.

## Workflows

A caller can pass `Perc` as the statistical transform for a plot layer. For each applicable group, compute all requested percentiles of the value-axis variable. Use the existing orientation and grouping conventions so the same behavior works when either axis is the value axis and when grouping variables are present.

## Data model

For every requested percentile, return a row containing the computed value in the value-axis column and its percentile level in a column named `percentile`. Preserve grouping-variable columns on the corresponding rows. Return one row per requested percentile per group; do not collapse the results to a single estimate or an interval row.

## API contracts

Expose `Perc` with the public parameters `k` and `method`. The default `k` is 5 and the default `method` is `linear`. An integer `k` specifies the number of evenly spaced percentile levels from 0 through 100; an explicit list of numbers specifies the percentile levels to compute. Pass the selected interpolation method through to percentile computation, supporting the methods accepted by NumPy. Preserve the Stat call contract: the transform receives the data, the supplied `GroupBy`, the orientation, and scales, and returns a DataFrame.

## Module architecture

Implement `Perc` in `seaborn._stats.order` alongside order-statistics functionality, and export it from `seaborn.objects`. Keep percentile computation in the statistics layer; do not turn this operation into the aggregation-layer estimate or interval behavior.

## Implementation constraints

Subclass the existing `Stat` abstraction and declare that orientation participates in grouping. Select the value variable using the established orientation mapping, then delegate group handling to the supplied `GroupBy.apply` operation. Within each group, compute percentile values after dropping missing observations. Use NumPy percentile behavior, retaining compatibility with versions that use the older interpolation parameter name as well as versions that use the method parameter name. Keep the transform stateless beyond its declared parameters and do not add dependencies.

## Naming

Use `Perc`, `k`, `method`, and `percentile` for the public class, percentile specification, interpolation selection, and output coordinate respectively.

## Validation

Treat the documented `k` forms as distinct inputs: integer counts generate evenly spaced levels, while lists are used as the explicit levels. Do not reinterpret an integer as a percentile value or restrict explicit lists to pairs. Use a method supported by the installed NumPy percentile API; do not introduce validation behavior that conflicts with that API.

## Documentation

Document `k` and `method`, including the integer-count and explicit-list meanings, the default values, and that `method` selects percentile interpolation. Follow the local Stat documentation style.

## Compatibility

Keep `Perc` importable from `seaborn._stats.order` and available through `seaborn.objects`; these locations are part of the feature contract.

## Behavioral acceptance criteria

For integer `k`, produce that many evenly spaced percentile levels from 0 to 100, inclusive. For an explicit list, produce the requested levels in that order. Compute each value using the selected interpolation method after excluding missing observations. Apply the operation independently to each group and to the value variable selected by orientation. Include the corresponding percentile coordinate on every output row.

## Test requirements

Cover integer-count and explicit-list behavior, interpolation selection, both orientations, grouped data, and missing observations. Keep tests consistent with existing statistics tests and ensure the feature can be imported from both its statistics module and `seaborn.objects`.
