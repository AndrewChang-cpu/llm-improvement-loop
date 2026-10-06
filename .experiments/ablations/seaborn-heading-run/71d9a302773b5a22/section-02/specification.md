## Goals

Add `Perc`, a statistical transformation for seaborn’s objects plotting API. It replaces observations along the value axis with requested percentile values and retains percentile levels as output data for later plot processing.

## Workflows

A caller can use `Perc` as a layer’s statistical transform. For each applicable group, compute the requested percentiles of the value-axis variable. Follow the existing orientation and grouping conventions so the transform works with either value axis and with grouping variables.

## API contracts

Expose `Perc` with public parameters `k` and `method`. Default `k` to 5 and `method` to `linear`. An integer `k` specifies that many evenly spaced percentile levels from 0 through 100, inclusive; a list of numbers specifies the exact percentile levels. Use `method` to select percentile interpolation, following the options accepted by NumPy.

Implement the existing `Stat` call contract: the transform receives the data frame, supplied `GroupBy`, orientation, and scales, and returns a data frame. Make `Perc` importable from `seaborn._stats.order` and expose it through `seaborn.objects`.

## Module architecture

Implement `Perc` in `seaborn._stats.order` alongside order-statistics functionality. Keep percentile computation in the statistics layer; do not use the aggregation-layer estimate or interval behavior for this transform.

## Implementation constraints

Subclass the existing `Stat` abstraction and declare that orientation participates in grouping. Select the value variable using the established orientation mapping, then delegate group processing to the supplied `GroupBy.apply` operation. Within each group, exclude missing values before computing percentiles. Use NumPy percentile behavior, accounting for the older `interpolation` argument name and the newer `method` argument name. Keep the transform stateless beyond its declared parameters.

## Dependencies

Use existing NumPy, pandas, and seaborn abstractions. Do not add dependencies.

## Naming

Use `Perc`, `k`, `method`, and `percentile` for the public class, percentile specification, interpolation choice, and output coordinate, respectively.

## Validation

Treat integer counts and explicit lists as distinct input forms: counts generate evenly spaced levels, while lists provide the levels directly and may contain any number of values. Do not impose validation that conflicts with NumPy’s percentile behavior.

## Documentation

Document `k` and `method`, their defaults, the integer-count and explicit-list meanings, and the role of `method` in interpolation. Follow the local `Stat` documentation pattern, including an Examples section whose usage material is maintained in the objects-stat documentation source. Include usage that demonstrates the default, integer, and explicit-list forms and combining the transform with a range mark. Register `Perc` in the public objects API reference’s Stat objects listing and add a feature entry to the current release notes.

## Compatibility

Preserve the public import locations `seaborn._stats.order` and `seaborn.objects`. Keep compatibility with NumPy versions that use either percentile keyword name.

## Behavioral acceptance criteria

For integer `k`, produce that many evenly spaced percentile levels from 0 to 100, inclusive. For an explicit list, compute the requested levels in their supplied order. Compute values using the selected interpolation method after excluding missing observations. Apply the operation independently to each observed group and to the value variable selected by orientation. Include the corresponding percentile coordinate on every output row.

## Test requirements

Cover integer-count and explicit-list behavior, interpolation selection, both orientations, grouped data, missing observations, public imports, and composition with the objects plotting API. Follow local statistics-test organization, using fixture and test classes consistent with neighboring and reference order-statistics tests.
