## Goals

Show an iterations-per-second speed indicator in progress displays for tasks whose total is unknown. Two entry points must agree:

1. The module-level `track()` helper gains a `show_speed` option. When on, iterating over a sequence with no known length (for example a generator) shows speed instead of raising an error.
2. The `TaskProgressColumn` column gains a `show_speed` option. When on and the task total is unknown, the column renders speed text instead of its no-percentage text.

Tasks with a known total keep the existing percentage display.

## Scope

In scope: `rich/progress.py` (`TaskProgressColumn`, the `track()` helper, unknown-total handling in `Progress.track`), a CHANGELOG entry, and tests in `tests/test_progress.py`.

Out of scope: other columns, Live and Console, the Task data model, and new speed computation. Speed is read from existing Task state.

## Assumptions

- `Task` exposes an optional total (None means unknown), a current speed, and a finished speed. The finished speed is set only when the total is known.
- `rich/progress.py` already imports `Text`, `Optional`, and the `filesize` module, which provides `pick_unit_and_suffix`.

## Workflows

1. `track()` over a Sized sequence with no explicit total: the total is the sequence length and the column shows percentage as before.
2. `track()` over a non-Sized iterable with no explicit total and default `show_speed`: the total is unknown, iteration proceeds without error, and the column shows speed text.
3. `track()` with `show_speed` off over an unknown total: the column shows its existing no-percentage text.
4. Column render decision, in order:
   - If the total is unknown and `show_speed` is on, return speed text. Use the finished speed when it is a non-zero number; otherwise use the current speed. Skip the `text_format_no_percentage` text and the markup and highlighter path.
   - Otherwise run the existing render path unchanged.

## Data model

- `TaskProgressColumn` stores a boolean `show_speed` attribute from its constructor, defaulting to off. Existing attributes are unchanged.
- The speed renderer receives an optional number; None renders as empty text.

## API contracts

- Module-level `track()`: add boolean `show_speed`, defaulting to on, as the last parameter. It is passed to the `TaskProgressColumn` the helper constructs. Other parameters are unchanged.
- `TaskProgressColumn` constructor: add boolean `show_speed`, defaulting to off, as the last keyword parameter.
- `TaskProgressColumn.render_speed`: a class-level operation callable without an instance. It takes one optional number, returns Text, and does not depend on instance state.
- `Progress.track()`: signature unchanged. Unknown-total behavior changes as described under Error handling.
- Names are exact: `show_speed` for both options, `render_speed`, and the unit label "it/s".

## Module architecture

- All speed rendering lives in `TaskProgressColumn`, a TextColumn subclass. Its render override returns Text.
- The module-level `track()` only constructs and wires the column. It does not compute speed.
- `Progress.track` owns total inference: explicit total, otherwise sequence length, otherwise unknown.
- No changes to Task, Live, or Console.

## Implementation constraints

- Choose the scale with the existing `filesize.pick_unit_and_suffix` helper. Do not write a separate scaling loop or use the `filesize.decimal` formatter.
- In `Progress.track`, declare the inferred-total variable as an optional number before the branch that may leave it unset, so strict mypy accepts the unset case.
- Speed text rules, in order:
  1. If the speed is None, return empty Text with style "progress.percentage".
  2. Otherwise pass the integer part of the speed to the helper with suffixes, in order: empty, ×10³, ×10⁶, ×10⁹, ×10¹², with base 1000.
  3. Divide the unscaled speed by the unit the helper returns.
  4. Format with one decimal place, append the suffix, then a space and "it/s".
  5. Return Text with style "progress.percentage", not the column's own style.
- Choose finished versus current speed with the same truthy fallback idiom as the existing transfer-speed rendering, not an explicit None comparison.
- No new imports or packages.

## Validation

- The change must pass the repo's strict mypy check and the black format check. Black requires exactly two blank lines between top-level definitions, including test functions, and never three or more consecutive blank lines in any edited file.

## Error handling

- `Progress.track`: with no total and a non-Sized iterable, do not raise. The total stays None and iteration proceeds.
- With a given total, keep existing behavior. With a Sized sequence and no total, use its length.
- Failures from iterating a non-iterable value still surface through normal iteration.

## Documentation

- CHANGELOG.md: under Unreleased / Added, one line stating that `show_speed` was added to `progress.track` and shows speed when the total is not known.
- `track()` docstring: add an Args entry: "Show speed if total isn't known. Defaults to True."
- `TaskProgressColumn` class docstring: replace the one-line description with a short summary and a Google-style Args section documenting every constructor parameter, keeping each existing default. The `show_speed` entry reads: "show_speed (bool, optional): Show speed if total is unknown. Defaults to False."

## Compatibility

- Known-total callers and calls with `show_speed` off see no change in rendering or output.
- Callers relying on `track()` raising for an unsized iterable with no total now get a running task with unknown total. This is intended; the error assertions in existing tests must be updated.

## Behavioral acceptance criteria

- The class-level speed renderer returns empty plain text for None, "5.0 it/s" for 5, "5.0×10³ it/s" for 5000, and "8.9×10⁶ it/s" for 8888888.
- `track()` over a generator with default options shows speed text and does not raise.
- `track()` with `show_speed` off over a generator shows the no-percentage text and does not raise.
- A column with `show_speed` on and an unknown-total task shows speed; with it off, previous output.
- A known total shows percentage exactly as before, regardless of `show_speed`.

## Test requirements

- Add `test_task_progress_column_speed` in `tests/test_progress.py`. It calls the class-level speed renderer with None, 5, 5000, and 8888888 and checks the four expected plain-text values above.
- In `test_track` and `test_progress_track`, remove the ValueError assertions for an unsized iterable with no total. Do not replace them with a new error expectation.
- Existing known-total rendering tests pass unchanged.
