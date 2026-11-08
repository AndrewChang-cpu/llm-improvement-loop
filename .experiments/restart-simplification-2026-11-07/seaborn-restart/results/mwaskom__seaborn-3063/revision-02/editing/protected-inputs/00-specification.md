Goals

Add `Perc`, a statistical transformation for the seaborn objects interface. It replaces observations with values computed at requested percentiles, preserving each percentile level alongside its computed value.

Scope

Define the statistic in `seaborn._stats.order` and export it through `seaborn.objects`. It must compose as a `Stat` transform in the existing `Plot.add` workflow.

Workflows

Callers can use `Perc` as a plot-layer statistical transform. For each group, it computes percentiles of the value variable opposite the plot orientation and returns the percentile results for downstream marks. Grouping and combination of group results use the existing `GroupBy` behavior.

Data model

The result has one row for each requested percentile in each group. Each row includes the computed value in the value column opposite the orientation and the corresponding level in a `percentile` column. Group labels are retained by the grouping operation. This is a percentile transformation, not a single summary estimate or a min/max interval.

API contracts

The public statistic is named `Perc`. Its `k` parameter accepts either an integer count or a list of percentile levels and defaults to 5. An integer requests that many evenly spaced levels from 0 through 100, inclusive; for example, a count of 5 yields levels 0, 25, 50, 75, and 100. A list specifies the requested levels directly, within the 0-to-100 range. Its `method` parameter is a string selecting NumPy percentile interpolation behavior and defaults to `linear`. The statistic follows the existing `Stat` call contract, receiving a data frame, `GroupBy`, orientation, and scale mapping, and returning a data frame.

Module architecture

Define `Perc` in `seaborn._stats.order`, alongside ordering statistics. Export it from `seaborn.objects` by importing it from that module. Keep it as a `Stat` subclass; percentile behavior belongs in the statistics layer, not in `seaborn._stats.aggregation`.

Implementation constraints

Mark the statistic as grouping by orientation. The orientation identifies the independent axis; calculate percentiles from the opposite, value axis: horizontal orientation uses the y variable, and vertical orientation uses the x variable. Apply a data-frame-to-data-frame percentile operation through `GroupBy.apply` so group variables are retained and results follow established group ordering. Exclude missing values from the values used for percentile computation. Preserve the requested percentile levels in the returned `percentile` column.

Dependencies

Use the existing NumPy, pandas, `GroupBy`, `Scale`, and `Stat` abstractions. Preserve NumPy compatibility by using its `interpolation` percentile keyword before version 1.22.0 and its `method` keyword from version 1.22.0 onward.

Naming

Use the public name `Perc` and parameter names `k` and `method`. Use `percentile` as the result column for percentile levels.

Validation

Accept the integer-count and explicit-list forms for `k`, with percentile levels in the inclusive range from 0 to 100, and pass the selected `method` through to NumPy percentile calculation. Do not impose interval-only list-length restrictions. Do not add separate parameter validation beyond the behavior of the established percentile operation.

Error handling

Preserve exceptions raised by the percentile operation for unsupported inputs or methods. Do not convert failures into interval-shaped output or reinterpret an integer count as a percentile level.

Documentation

Document that an integer `k` means an evenly spaced count of percentiles from 0 through 100, while a list specifies levels directly within that range. Include the five-level example yielding 0, 25, 50, 75, and 100. Document `method` as the interpolation choice and describe the percentile-row output.

Compatibility

Keep the `seaborn._stats.order.Perc` import path available as well as the `seaborn.objects.Perc` public export. Support the NumPy percentile keyword conventions on both sides of the 1.22.0 version boundary.

Behavioral acceptance criteria

For an integer count, return that many evenly spaced percentile levels, including 0 and 100, with computed values and matching `percentile` entries. For an explicit list, return one result per listed level. Honor the requested interpolation method. Work with either orientation by computing from the opposite value variable, and with grouped data while preserving group labels and established ordering. Ignore missing observations when computing percentiles. Results must represent percentile rows rather than a point estimate or interval.

Test requirements

When tests are added or updated, place statistic tests in `tests/_stats/test_order.py` and follow the neighboring statistics tests’ fixture and test-class organization. Cover integer and explicit-list inputs, orientation-to-value-axis mapping, interpolation method, grouped data and ordering, missing observations, both import paths, and use through the existing `Plot.add` transform workflow.
