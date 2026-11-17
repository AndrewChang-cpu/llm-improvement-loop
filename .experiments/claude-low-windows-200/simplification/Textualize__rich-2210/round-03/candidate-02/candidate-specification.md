## Goals

Show an iterations-per-second speed indicator for tasks whose total is unknown. Two entry points must agree:

1. The module-level `track()` helper gains a `show_speed` option. When on, iterating a sequence with no known length (for example a generator) shows speed instead of raising an error.
2. The `TaskProgressColumn` column gains a `show_speed` option. When on and the task total is unknown, it renders speed text instead of its no-percentage text.

Tasks with a known total keep the percentage display.

## Scope

In scope: `rich/progress.py` (`TaskProgressColumn`, `track()`, unknown-total handling in `Progress.track`), a CHANGELOG entry, and `tests/test_progress.py`. Out of scope: other columns, Live, Console, the Task data model, and new speed computation.

## Assumptions

- `Task` exposes an optional total (None means unknown), a current speed, and a finished speed. The finished speed is set only when the total is known.
- `rich/progress.py` already imports `Text`, `Optional`, and `filesize`, which provides `pick_unit_and_suffix`. No new imports are needed.

## Workflows

1. `track()` over a Sized sequence with no explicit total: the total is the sequence length and percentage shows as before.
2. `track()` over a non-Sized iterable with no explicit total and default `show_speed`: the total is unknown, iteration proceeds, and the column shows speed.
3. Column render, in order: if the total is unknown and `show_speed` is on, return speed text using the finished speed when non-zero, otherwise the current speed. Skip `text_format_no_percentage`, including its markup and highlighter. Otherwise run the existing render path unchanged.

## Data model

`TaskProgressColumn` stores a boolean `show_speed` attribute, default off. Existing attributes are unchanged.

## API contracts

- Module-level `track()`: add boolean `show_speed`, default on, as the last parameter, passed to the `TaskProgressColumn` it constructs. Other parameters unchanged.
- `TaskProgressColumn` constructor: add boolean `show_speed`, default off, as the last keyword parameter.
- `TaskProgressColumn.render_speed`: class-level callable usable without an instance. Takes one optional number, returns Text, and does not depend on instance state. None renders as empty text.
- `Progress.track()`: signature unchanged; unknown-total behavior changes per Error handling.

## Module architecture

- All speed rendering lives in `TaskProgressColumn`, a TextColumn subclass whose render override returns Text.
- The module-level `track()` only constructs and wires the column.
- `Progress.track` owns total inference: explicit total, else sequence length, else unknown.
- No changes to Task, Live, or Console.

## Implementation constraints

- Scale with `filesize.pick_unit_and_suffix`. Do not use the `filesize.decimal` formatter or a custom scaling loop.
- In `Progress.track`, declare the inferred-total variable as an optional number before the branch that may leave it unset, so strict mypy accepts it.
- Speed text rules, in order:
  1. If speed is None, return empty Text with style "progress.percentage".
  2. Otherwise pass the integer part of the speed to the helper with suffixes, in order: empty, ×10³, ×10⁶, ×10⁹, ×10¹², and base 1000.
  3. Divide the unscaled speed by the unit the helper returns.
  4. Format with one decimal place, append the suffix, then a space and "it/s".
  5. Return Text with style "progress.percentage", not the column's own style.
- Choose finished versus current speed with the same truthy fallback idiom as the existing transfer-speed rendering, not an explicit None comparison.

## Naming

Use exact names `show_speed` (track and column options) and `render_speed`. The unit label is exactly "it/s".

## Error handling

- `Progress.track`: with no total and a non-Sized sequence, do not raise; the total stays None and iteration proceeds.
- With a given total, keep existing behavior. With a Sized sequence and no total, use its length.
- Other iteration failures still surface.

## Validation

- Must pass the strict mypy CI check and the black format check.
- Use exactly two blank lines between top-level definitions, including test functions, and never three or more consecutive blank lines in any edited file.

## Documentation

- CHANGELOG.md, under Unreleased / Added: one line saying `show_speed` was added to `progress.track` and shows speed when the total is not known.
- `track()` docstring Args entry: "Show speed if total isn't known. Defaults to True."
- `TaskProgressColumn` class docstring: short summary and Google-style Args section documenting every constructor parameter with its default. The `show_speed` entry reads: "show_speed (bool, optional): Show speed if total is unknown. Defaults to False."

## Compatibility

- Known-total callers and callers with `show_speed` off see no change.
- Callers relying on `track()` raising for an unsized iterable with no total now get a running task, which is intended. Update those error assertions in existing tests.

## Behavioral acceptance criteria

- Speed renderer returns empty plain text for None, "5.0 it/s" for 5, "5.0×10³ it/s" for 5000, and "8.9×10⁶ it/s" for 8888888.
- `track()` over a generator with default options shows speed and does not raise.
- A known total shows percentage exactly as before, regardless of `show_speed`.

## Test requirements

- Add `test_task_progress_column_speed` in `tests/test_progress.py`. It calls the speed renderer with None, 5, 5000, and 8888888 and checks the four plain-text values above.
- In `test_track` and `test_progress_track`, remove the ValueError assertions for an unsized iterable with no total, adding none. Leave exactly two blank lines before the next top-level definition.
- Existing known-total rendering tests pass unchanged.
