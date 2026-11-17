## Goals

Show an iterations-per-second speed indicator in progress displays for tasks whose total is unknown. Two entry points must agree:

1. The module-level `track()` helper gains a `show_speed` option. When on, iterating a sequence with no known length (for example a generator) shows speed instead of raising an error.
2. The `TaskProgressColumn` column gains a `show_speed` option. When on and the task total is unknown, it renders speed text instead of its no-percentage text.

Known totals keep the percentage display.

## Scope

In scope: `rich/progress.py` (`TaskProgressColumn`, the `track()` helper, unknown-total handling in `Progress.track`), a CHANGELOG entry, and tests in `tests/test_progress.py`. Out of scope: other columns, Live, Console, the Task data model, and new speed computation. Speed comes from existing Task state.

## Assumptions

- `Task` exposes an optional total (None means unknown), a current speed, and a finished speed. The finished speed is set only when the total is known.
- `rich/progress.py` already imports `Text`, `Optional`, and the `filesize` module, which provides `pick_unit_and_suffix`. No new imports are needed.

## Workflows

1. `track()` over a Sized sequence with no explicit total: the total is the sequence length and the column shows percentage as before.
2. `track()` over a non-Sized iterable with no explicit total and default `show_speed`: the total is unknown, iteration proceeds, and the column shows speed text.
3. Column render decision, in order:
   - If the total is unknown and `show_speed` is on, return speed text. Use the finished speed when it is non-zero, otherwise the current speed. Skip the `text_format_no_percentage` path, including its markup and highlighter.
   - Otherwise run the existing render path unchanged.

## Data model

- `TaskProgressColumn` stores a boolean `show_speed` attribute, default off. Existing attributes are unchanged.

## API contracts

- Module-level `track()`: add boolean `show_speed`, default on, as the last parameter, and pass it to the `TaskProgressColumn` the helper constructs.
- `TaskProgressColumn` constructor: add boolean `show_speed`, default off, as the last keyword parameter.
- `TaskProgressColumn.render_speed`: a class-level callable usable without an instance. It takes one optional number, returns Text, and does not depend on instance state. None renders as empty text.

## Architecture

- All speed rendering lives in `TaskProgressColumn`, a TextColumn subclass whose render override returns Text.
- The module-level `track()` only constructs and wires the column.
- `Progress.track` owns total inference: explicit total, otherwise sequence length, otherwise unknown.
- No changes to Task, Live, or Console.

## Implementation constraints

- Choose the scale with `filesize.pick_unit_and_suffix`. Do not write a separate scaling loop or use the `filesize.decimal` formatter.
- In `Progress.track`, declare the inferred-total variable as an optional number before the branch that may leave it unset, so strict mypy accepts that case.
- Speed text rules, in order:
  1. If the speed is None, return empty Text with style "progress.percentage".
  2. Otherwise pass the integer part of the speed to the helper with suffixes, in order: empty, ×10³, ×10⁶, ×10⁹, ×10¹², and base 1000.
  3. Divide the unscaled speed by the unit the helper returns.
  4. Format with one decimal place, append the suffix, then a space and "it/s".
  5. Return Text with style "progress.percentage", not the column's own style.
- For finished-versus-current speed, use the same truthy fallback idiom as the existing transfer-speed rendering, not an explicit None comparison.

## Error handling

- `Progress.track`: with no total and a non-Sized iterable, do not raise. The total stays None and iteration proceeds.
- With a given total, keep existing behavior. With a Sized sequence and no total, use its length.
- Failures from iterating a non-iterable value still surface through normal iteration.

## Documentation

- CHANGELOG.md: under Unreleased / Added, one line stating `show_speed` was added to `progress.track` and shows speed when the total is not known.
- `track()` docstring: add an Args entry, "Show speed if total isn't known. Defaults to True."
- `TaskProgressColumn` class docstring: a short summary and a Google-style Args section documenting every constructor parameter with its default. The `show_speed` entry reads "show_speed (bool, optional): Show speed if total is unknown. Defaults to False."

## Compatibility

- Callers that use known totals or leave `show_speed` off see no change.
- Callers that relied on `track()` raising for an unsized iterable with no total now get a running task. This is intended; update the existing error assertions.

## Acceptance criteria

- The speed renderer returns empty plain text for None, "5.0 it/s" for 5, "5.0×10³ it/s" for 5000, and "8.9×10⁶ it/s" for 8888888.
- `track()` over a generator with default options shows speed text and does not raise.
- A known total shows percentage exactly as before, regardless of `show_speed`.

## Validation

- Must pass the repo's strict mypy check (CI typecheck step) and the black format check.
- Use exactly two blank lines between top-level definitions, including test functions, and never three or more consecutive blank lines in any edited file.

## Test requirements

- Add `test_task_progress_column_speed` in `tests/test_progress.py`. It calls the speed renderer with None, 5, 5000, and 8888888 and checks the four expected plain-text values above.
- In `test_track` and `test_progress_track`, remove the ValueError assertions for an unsized iterable with no total. Do not replace them with a new error expectation.
- Existing known-total rendering tests pass unchanged.
