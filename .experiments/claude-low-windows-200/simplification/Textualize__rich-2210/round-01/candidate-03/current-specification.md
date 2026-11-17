## Goals

Show an iterations-per-second speed indicator in progress displays for tasks whose total is unknown. The feature has two entry points that must agree:

1. The module-level `track()` helper gains a `show_speed` option. When it is on, iterating over a sequence with no known length (for example a generator) shows speed instead of an error.
2. The `TaskProgressColumn` column gains a `show_speed` option. When it is on and the task total is unknown, the column renders the speed text instead of its no-percentage text.

Tasks with a known total keep the existing percentage display.

## Scope

In scope:
- `rich/progress.py`: `TaskProgressColumn`, the module-level `track()` helper, and unknown-total handling in `Progress.track`.
- A CHANGELOG entry under Unreleased / Added.
- Tests in `tests/test_progress.py`.

Out of scope: other columns, Live and Console behavior, changes to the Task data model, and any new speed computation. Speed is read from existing Task state.

## Assumptions

- `Task` already exposes an optional total (None means unknown), a current speed, and a finished speed. The finished speed is set only when the total is known.
- The progress module already imports `Text`, `Optional`, and the `filesize` module, which provides a helper named `pick_unit_and_suffix`.

## Terminology

- **Unknown total**: a task whose total is None.
- **Speed text**: the styled Text object the column returns when speed is shown.
- **Scaled speed**: a speed value divided by a power of 1000 and labeled with an SI-style suffix (for example "5.0×10³ it/s").

## Workflows

1. `track()` over a Sized sequence with no explicit total: the total is the sequence length and the column shows percentage as before.
2. `track()` over a non-Sized iterable (for example a generator) with no explicit total and the default `show_speed`: the task is created with an unknown total, iteration proceeds without error, and the column shows speed text.
3. `track()` with `show_speed` set to false over an unknown total: the column shows its existing no-percentage text.
4. A manually built Progress with a task whose total is unknown and a `TaskProgressColumn` with `show_speed` on: the column shows speed text.
5. Column render decision, in order:
   - If the task total is unknown and the column's `show_speed` is on, return the speed text computed from the task's finished speed when that value is set to a non-zero number. If the finished speed is unset or zero, compute the speed text from the task's current speed instead. Do not apply the `text_format_no_percentage` text or the markup and highlighter path in this branch.
   - Otherwise, run the existing render path unchanged.

## Data model

- `TaskProgressColumn` stores a boolean `show_speed` attribute, set from its constructor and defaulting to off. Existing stored attributes are unchanged.
- Task total: an optional number; None means unknown.
- Speed value passed to the speed renderer: an optional number; None means no speed is available and renders as empty text.

## API contracts

- Module-level `track()`: add a boolean option named `show_speed` with default on. It is the last parameter, after the existing options. It is passed to the `TaskProgressColumn` the helper constructs. Existing parameter order and defaults are unchanged.
- `TaskProgressColumn` constructor: add a boolean option named `show_speed` with default off as the last keyword parameter. Existing parameters keep their order and defaults.
- `TaskProgressColumn` speed renderer, named `render_speed`: it must be a class-level operation that can be called on the class itself without an instance. It takes one optional number and returns Text. It must not depend on instance state.
- `Progress.track()`: its signature is unchanged. Its unknown-total behavior changes as described under Error handling.

## Module architecture

- All speed rendering lives in `TaskProgressColumn`, a TextColumn subclass. Its render override returns Text, as the column contract requires.
- The module-level `track()` only constructs and wires the column. It must not compute speed itself.
- `Progress.track` owns total inference (explicit total, otherwise sequence length, otherwise unknown).
- No changes to Task, Live, or Console.

## Implementation constraints

- Use the existing `filesize.pick_unit_and_suffix` helper to choose the scale. Do not write a separate scaling loop, and do not use the `filesize.decimal` formatter for this text.
- Typing of the inferred total in `Progress.track`: declare the variable that holds the inferred total as an optional number before the branch that may leave it unset. Do not first bind it to a float and then leave it unset (None) in another branch without that optional declaration. The unset case must type-check under the repo's strict type checking (see Validation).
- Speed text rules (apply in this order):
  1. If the speed is None, return an empty Text with style "progress.percentage".
  2. Otherwise, pass the integer part of the speed to the helper with the suffix list, in order: empty, ×10³, ×10⁶, ×10⁹, ×10¹², and base 1000.
  3. Divide the unscaled speed by the unit the helper returns.
  4. Format the result with one decimal place, then append the suffix, then a space and "it/s".
  5. Return the Text with style "progress.percentage" (not the column's own style).
- Speed source for an unknown-total task: use the finished speed when it is set to a non-zero value; otherwise use the current speed. Use the same truthy fallback idiom the existing transfer-speed rendering uses, not a separate explicit None comparison.

## Dependencies

- No new imports, packages, or modules. `filesize`, `Text`, and `Optional` are already available in the progress module.

## Naming

- Use the exact names `show_speed` (both the track option and the column option) and `render_speed` (the class-level speed renderer). The unit label is exactly "it/s".

## Error handling

- `Progress.track`: when no total is given and the sequence is not Sized, do not raise. The task total stays unknown (None) and iteration proceeds.
- When a total is given, keep the existing behavior. When the sequence is Sized and no total is given, use its length.
- Failures from iterating a non-iterable value still surface through normal iteration.

## Validation

- The change must pass the repo's strict static type check for the `rich` package. The project configures strict mypy over the `rich` package and runs a typecheck step in CI, so every assignment to the inferred total must be type-consistent under that check.
- The change must also pass the repo's black format check, which CI runs over the repository. Layout must match black exactly: exactly two blank lines between top-level definitions (including each test function), and never three or more consecutive blank lines in any edited file.

## Documentation

- CHANGELOG.md: under Unreleased / Added, add one line stating that `show_speed` was added to `progress.track` and shows speed when the total is not known.
- `track()` docstring: add an Args entry for `show_speed`: "Show speed if total isn't known. Defaults to True."
- `TaskProgressColumn` class docstring (not the constructor): replace the one-line description with a short summary and an Args section that documents every constructor parameter of `TaskProgressColumn`, in the same Google-style Args format used by sibling column classes. Each existing parameter keeps its current default in its entry. The `show_speed` entry reads: "show_speed (bool, optional): Show speed if total is unknown. Defaults to False."

## Reliability

- With a known total, or with the column's `show_speed` off, rendering and output are unchanged from before this feature.

## Usability

- A user who passes an unsized iterable to `track()` gets a speed display by default instead of an error.

## Maintainability

- Unit selection and scaling reuse the existing helper so there is one scaling path in the module.

## Compatibility

- Existing callers with known totals see no change.
- Callers that relied on `track()` raising for an unsized iterable with no total will now get a running task with unknown total. This is intended. Existing tests that assert that error must be updated (see Test requirements).

## Behavioral acceptance criteria

- The speed renderer called on the class returns empty plain text for None, "5.0 it/s" for 5, "5.0×10³ it/s" for 5000, and "8.9×10⁶ it/s" for 8888888.
- `track()` over a generator with default options shows speed text in the progress column and does not raise.
- `track()` with `show_speed` off over a generator shows the no-percentage text and does not raise.
- A `TaskProgressColumn` with `show_speed` on and a task with an unknown total shows speed; with `show_speed` off it shows the previous output.
- A task with a known total shows the percentage exactly as before, regardless of `show_speed`.

## Test requirements

- Add a test named `test_task_progress_column_speed` in `tests/test_progress.py` that calls the class-level speed renderer with None, 5, 5000, and 8888888 and checks the four expected plain-text values above.
- In the two existing tests named `test_track` and `test_progress_track` in `tests/test_progress.py`, remove the ValueError assertions that expect an unsized iterable with no total to raise. Do not replace them with a new error expectation.
- After removing those assertions, leave exactly two blank lines before the next top-level definition, so the file stays black-clean (see Validation).
- Existing tests for known-total rendering must still pass unchanged.
