## Goals

Add `Perc`, a statistical transformation for the seaborn objects interface. It replaces observations with values computed at requested percentiles, preserving each percentile level alongside its computed value.

## Scope

Define the statistic in `seaborn._stats.order` and export it through `seaborn.objects`. It must compose as a `Stat` transform in the existing `Plot.add` workflow.

## Workflows

Callers can use `Perc` as a plot-layer statistical transform. For each group, it computes percentiles of the value variable opposite the plot orientation and returns the percentile results for downstream marks. Group formation, result combination, and group ordering follow the existing `GroupBy` behavior.

## Data model

Return one row for each requested percentile in each group. Each row contains the computed value in the value column opposite the orientation and its level in a `percentile` column. Preserve grouping columns and their labels in the combined result. Percentile values may be floating-point values, including when the source observations are integers; consumers and tests must not require integer result dtypes. This is a percentile transformation, not a single summary estimate or a min/max interval.

## API contracts

The public statistic is named `Perc`. Its `k` parameter accepts either an integer count or a list of percentile levels and defaults to 5. An integer requests that many evenly spaced levels from 0 through 100, inclusive. A list supplies the requested levels directly. Its `method` parameter selects NumPy percentile interpolation behavior and defaults to `linear`. The statistic follows the existing `Stat` call contract, receiving a data frame, `GroupBy`, orientation, and scale mapping, and returning a data frame.

## Module architecture

Define `Perc` in `seaborn._stats.order`, alongside ordering statistics. Export it from `seaborn.objects` by importing it from that module. Keep it as a `Stat` subclass; percentile behavior belongs in the statistics layer, not in `seaborn._stats.aggregation`.

## Implementation constraints

Mark the statistic as grouping by orientation. The orientation identifies the independent axis; calculate percentiles from the opposite, value axis: horizontal orientation uses the y variable, and vertical orientation uses the x variable. Apply the data-frame-to-data-frame percentile operation through `GroupBy.apply`, which combines results with group labels and the established group ordering. Preserve those grouping columns in the returned data; do not discard them after applying the groups. Exclude missing values from the values used for percentile computation. Preserve the requested percentile levels in the returned `percentile` column.

## Dependencies

Use the existing NumPy, pandas, `GroupBy`, `Scale`, and `Stat` abstractions. Preserve NumPy compatibility by using its `interpolation` percentile keyword before version 1.22.0 and its `method` keyword from version 1.22.0 onward.

## Naming

Use the public name `Perc` and parameter names `k` and `method`. Use `percentile` as the result column for percentile levels.

## Validation

Support the integer-count and explicit-list forms for `k`; do not add validation beyond the behavior of the established percentile operation. Pass the selected `method` through to NumPy percentile calculation. Do not impose interval-only list-length restrictions.

## Error handling

Preserve exceptions raised by the percentile operation for unsupported inputs or methods. Preserve grouping keys when combining results so downstream plotting receives the coordinates and grouping data it needs.

## Documentation

Document that an integer `k` means an evenly spaced count of percentiles from 0 through 100, while a list specifies levels directly. Document `method` as the interpolation choice and describe the percentile-row output, including that computed values may be floating point.

## Compatibility

Keep the `seaborn._stats.order.Perc` import path available as well as the `seaborn.objects.Perc` public export. Support the NumPy percentile keyword conventions on both sides of the 1.22.0 version boundary.

## Behavioral acceptance criteria

For an integer count, return that many evenly spaced percentile levels, including 0 and 100, with computed values and matching `percentile` entries. For an explicit list, return one result per listed level. Honor the requested interpolation method. Work with either orientation by computing from the opposite value variable, and with grouped data while preserving group columns, labels, and established ordering. Ignore missing observations when computing percentiles. Retain output coordinates and grouping data needed for downstream marks in the `Plot.add` workflow. Results represent percentile rows rather than a point estimate or interval.

## Test requirements

When tests are added or updated, place statistic tests in `tests/_stats/test_order.py` and follow the neighboring statistics tests’ fixture and test-class organization. For an ungrouped percentile-count test, use grouping that leaves the data in one group; alternatively, assert the expected percentile rows separately for each group. Check computed numeric values and percentile levels without requiring integer dtypes. Cover explicit-list inputs, both orientation mappings, interpolation method, grouped data and ordering, missing observations, both import paths, preservation of group columns, and use through the existing `Plot.add` transform workflow. Ensure plotting integration exercises non-empty transformed coordinates and does not fail when a mark resolves its properties.
