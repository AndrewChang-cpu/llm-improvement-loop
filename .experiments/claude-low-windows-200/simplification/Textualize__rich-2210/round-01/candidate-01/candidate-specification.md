## Goals

Show an iterations-per-second speed indicator in progress displays for tasks whose total is unknown. Two entry points must agree:

1. The module-level `track()` helper gains a `show_speed` option. When it is on, iterating over a sequence with no known length (for example a generator) shows speed instead of raising an error.
2. The `TaskProgressColumn` column gains a `show_speed` option. When it is on and the task total is unknown, the column renders speed text instead of its no-percentage text.

Tasks with a known total keep the percentage display.

## Scope

In scope: `rich/progress.py` (`TaskProgressColumn`, the module-level `track()` helper, and unknown-total handling in `Progress.track`), a CHANGELOG entry, and tests in `tests/test_progress.py`.

Out of scope: other columns, Live and Console behavior, the Task data model, and any new speed computation. Speed is read from existing Task state.

## Assumptions

- `Task` already exposes an optional total (None means unknown), a current speed, and a finished speed. The finished speed is set only when the total is known.
- The progress module already imports `Text`, `Optional`, and the `filesize` module, which provides `pick_unit_and_suffix`.

## Terminology

- **Unknown total**: a task whose total is None.
- **Speed text**: the styled Text the column returns when speed is shown.
- **Scaled speed**: a speed divided by a power of 1000 and labeled with an SI-style suffix (for example "5.0×10³ it/s").

## Workflows

1. `track()` over a Sized sequence with no explicit total: the total is the sequence length and the column shows percentage as before.
2. `track()` over a non-Sized iterable (for example a generator) with no explicit total and default `show_speed`: the task has an unknown total, iteration proceeds without error, and the column shows speed text.
3. `track()` with `show_speed` false over an unknown total: the column shows its existing no-percentage text.
4. A manually built Progress with an unknown-total task and a `TaskProgressColumn` with `show_speed` on: the column shows speed text.
5. Column render decision, in order:
   - If the task total is unknown and `show_speed` is on, return speed text computed from the task's finished speed when it is a non-zero number. If the finished speed is unset or zero, use the current speed. Do not apply `text_format_no_percentage` or the markup and highlighter path in this branch.
   - Otherwise, run the existing render path unchanged.

## Data model

- `TaskProgressColumn` stores a boolean `show_speed` attribute, set from its constructor and defaulting to off. Existing attributes are unchanged.
- Task total: an optional number; None means unknown.
- Speed passed to the speed renderer: an optional number; None renders as empty text.

## API contracts

- Module-level `track()`: add boolean option `show_speed`, default on, as the last parameter. It is passed to the `TaskProgressColumn` the helper constructs. Existing order and defaults are unchanged.
- `TaskProgressColumn` constructor: add boolean keyword option `show_speed`, default off, as the last parameter. Existing parameters keep order and defaults.
- `TaskProgressColumn` speed renderer `render_speed`: a class-level operation callable on the class without an instance. It takes one optional number, returns Text, and does not depend on instance state.
- `Progress.track()`: signature unchanged. Unknown-total behavior changes as described under Error handling.

## Module architecture

- All speed rendering lives in `TaskProgressColumn`, a TextColumn subclass. Its render override returns Text, as the column contract requires.
- Module-level `track()` only constructs and wires the column. It must not compute speed.
- `Progress.track` owns total inference: explicit total, otherwise sequence length, otherwise unknown.
- No changes to Task, Live, or Console.

## Implementation constraints

- Choose the scale with the existing `filesize.pick_unit_and_suffix` helper. Do not write a separate scaling loop or use the `filesize.decimal` formatter.
- In `Progress.track`, declare the variable holding the inferred total as an optional number before the branch that may leave it unset. Do not bind it to a float and later leave it None without that declaration. The unset case must type-check under strict checking (see Validation).
- Speed text rules, in order:
  1. If the speed is None, return an empty Text with style "progress.percentage".
  2. Otherwise pass the integer part of the speed to the helper with suffixes in this order: empty, ×10³, ×10⁶, ×10⁹, ×10¹², with base 1000.
  3. Divide the unscaled speed by the unit the helper returns.
  4. Format with one decimal place, append the suffix, then a space and "it/s".
  5. Return the Text with style "progress.percentage", not the column's own style.
- Speed source for an unknown-total task: finished speed when set to a non-zero value, otherwise current speed. Use the same truthy fallback idiom as the existing transfer-speed rendering, not an explicit None comparison.

## Dependencies

No new imports, packages, or modules. `filesize`, `Text`, and `Optional` are already available in the progress module.

## Naming

Use the exact names `show_speed` (track option and column option) and `render_speed` (class-level speed renderer). The unit label is exactly "it/s".

## Error handling

- `Progress.track`: when no total is given and the sequence is not Sized, do not raise. The total stays unknown (None) and iteration proceeds.
- When a total is given, keep existing behavior. When the sequence is Sized and no total is given, use its length.
- Failures from iterating a non-iterable value still surface through normal iteration.

## Validation

- The change must pass the repo's strict mypy check over the `rich` package, which CI runs as a typecheck step. Every assignment to the inferred total must be type-consistent.
- The change must pass the repo's black check. Use exactly two blank lines between top-level definitions (including each test function), and never three or more consecutive blank lines in any edited file.

## Documentation

- CHANGELOG.md: under Unreleased / Added, add one line stating that `show_speed` was added to `progress.track` and shows speed when the total is not known.
- `track()` docstring: add an Args entry: "Show speed if total isn't known. Defaults to True."
- `TaskProgressColumn` class docstring (not the constructor): replace the one-line description with a short summary and an Args section documenting every constructor parameter in the Google-style Args format used by sibling column classes. Each existing parameter keeps its current default. The `show_speed` entry reads: "show_speed (bool, optional): Show speed if total is unknown. Defaults to False."

## Reliability

With a known total, or with the column's `show_speed` off, rendering and output are unchanged.

## Usability

A user who passes an unsized iterable to `track()` gets a speed display by default instead of an error.

## Maintainability

Unit selection and scaling reuse the existing helper, so the module has one scaling path.

## Compatibility

- Existing callers with known totals see no change.
- Callers that relied on `track()` raising for an unsized iterable with no total now get a running task with unknown total. This is intended. Tests asserting that error must be updated (see Test requirements).

## Behavioral acceptance criteria

- The class-level speed renderer returns empty plain text for None, "5.0 it/s" for 5, "5.0×10³ it/s" for 5000, and "8.9×10⁶ it/s" for 8888888.
- `track()` over a generator with default options shows speed text in the progress column and does not raise.
- `track()` with `show_speed` off over a generator shows the no-percentage text and does not raise.
- A `TaskProgressColumn` with `show_speed` on and an unknown-total task shows speed; with it off, previous output.
- A known-total task shows percentage exactly as before, regardless of `show_speed`.

## Test requirements

- Add `test_task_progress_column_speed` in `tests/test_progress.py`. It calls the class-level speed renderer with None, 5, 5000, and 8888888 and checks the four expected plain-text values above.
- In existing tests `test_track` and `test_progress_track` in `tests/test_progress.py`, remove the ValueError assertions expecting an unsized iterable with no total to raise. Do not replace them with another error expectation.
- After removal, leave exactly two blank lines before the next top-level definition (see Validation).
- Existing known-total rendering tests must still pass unchanged.
