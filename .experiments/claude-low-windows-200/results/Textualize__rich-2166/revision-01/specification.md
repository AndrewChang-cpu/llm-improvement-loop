## Goals
- Let a Progress task be created with an unknown total (total set to None). Such a task renders as an indeterminate task: a pulsing bar, with no percentage text, no time-remaining estimate, and blank or "?" placeholders in the size and count columns.
- Keep all finite-total rendering exactly as it is today.

## Scope
- Affected files: rich/progress.py, rich/progress_bar.py, docs/source/progress.rst, tests/test_progress.py.
- Out of scope: TimeElapsedColumn, FileSizeColumn, TransferSpeedColumn, the caching in the ProgressColumn base class, and the existing behavior of the Progress.track method for unsized iterables. A CHANGELOG entry is not required by the reference.
- Not part of the feature: pull-request template text (type-of-change boxes, checklist, reviewer mentions, issue links). Do not carry any of it into code, docs, or tests.

## Assumptions
- None is the sentinel for an unknown total. Negative numbers and dedicated sentinel constants were considered and rejected; do not introduce either.
- Zero is a known total and keeps its existing behavior.
- An unknown total always pulses, whether or not the task has been started.

## Terminology
- Unknown total: a task whose total is None.
- Indeterminate task: a task with an unknown total.
- Blank: a zero-length text output, not a placeholder.
- Unknown placeholder: the single question mark shown in the total position of the count and download columns.
- Pulse: the existing animated bar rendering.

## Workflows
1. Creating an indeterminate task: adding a task with an unknown total stores the None value and raises no error. The start behavior is unchanged; the bar pulses because the total is unknown.
2. Default layout: the default columns, in order, are a description text column, a bar column, a task-progress column, and a time-remaining column. For an unknown total the bar pulses, the percentage column is blank, and the time-remaining column is blank. Elapsed-time output, which is not in the defaults, is unaffected.
3. Module-level track helper: builds the same column set as the defaults, with the description column included only when a description is given, the bar column using the caller's styles, the task-progress column, and the time-remaining column. Known-total behavior is unchanged.
4. Updating: update and advance with an unknown total still increase completed. They never set finished time or finished speed while the total is unknown. Passing a non-None total to update sets the task's total and returns the task to finite rendering and finish detection.
5. Standalone bar: a bar with an unknown total pulses at any width and reports no percentage.

## Data model
- Task.total: an optional number. None is stored as given, with no coercion.
- Task.remaining: None when the total is unknown; otherwise total minus completed.
- Task.time_remaining: returns 0 when the task is finished. Otherwise it returns None when there is no speed or when remaining is None. Otherwise it returns the existing ceiling of remaining divided by speed.
- Task.percentage: keeps returning 0 when the total is unknown, through its existing falsy check. Do not change it. Blanking is the percentage column's job.
- Task.finished_time and Task.finished_speed: set only when the total is known and completed is at least the total.

## API contracts
- Progress.add_task: the total parameter is an optional number with default 100, and None is accepted. Its documentation says None renders a pulsing animation.
- ProgressBar constructor: total is an optional number with default 100, and None is accepted. The pulse flag documentation says the bar also pulses when total is None.
- ProgressBar.percentage_completed: returns an optional number. It returns None when the total is None. Otherwise it is unchanged: completed divided by total times 100, clamped to 0 through 100.
- ProgressBar.update: unchanged. A None total argument leaves the stored total unchanged.
- TaskProgressColumn (new, public, importable from rich.progress): a subclass of TextColumn. Its constructor takes, in this order: text_format (default: the existing percentage text format used by the current default percentage column), text_format_no_percentage (default: empty text), style (default "none"), justify (default "left"), markup (default true), highlighter (optional, default none), and table_column (optional). It stores text_format_no_percentage and passes the other values to the TextColumn constructor. Its render step uses text_format_no_percentage when the task total is None and text_format otherwise, formats with the task, and then applies markup, justify, style, and highlighter the same way TextColumn does.
- TimeRemainingColumn: when the task total is None, returns blank text using the same style selection as the normal path (progress.remaining, or progress.elapsed when elapsed_when_finished is set and the task is finished). The unknown-total check happens after the style is chosen and before any estimate formatting. Finite-total formatting, including the "-:--:--" and "--:--" placeholders for finite tasks without an estimate, is unchanged.
- TotalFileSizeColumn: an unknown total renders blank text with the same total-size style.
- MofNCompleteColumn: an unknown total renders the integer completed count, then the separator, then "?". For example, completed 5 with separator "/" renders as "5/?".
- DownloadColumn: the unit is chosen from completed when the total is unknown and from the total otherwise. The binary_units setting selects the binary or decimal unit list exactly as before, in both cases. The completed part is formatted as before (precision 0 when the unit is 1, otherwise 1; thousands separators). The total part is "?" when the total is unknown and otherwise formatted as before. The output is completed, "/", total part, a space, and the suffix. For example, 2048 bytes completed with an unknown total gives "2.0/? KiB" with binary_units and "2.0/? kB" without.
- get_default_columns and the module-level track helper: the percentage text column is replaced by a TaskProgressColumn built with its defaults. Column order is unchanged.
- BarColumn: passes an unknown total through to the bar as None. For a known total, the existing clamp at zero is kept.

## Module architecture
- TaskProgressColumn belongs in rich/progress.py beside TextColumn and the other column classes.
- Pulse rendering and the decision to pulse for an unknown total belong in rich/progress_bar.py.
- Task state (remaining, time_remaining, finished) is computed in Task. Columns read those values and do not recompute them.
- The caching in the ProgressColumn base class is unchanged.

## Implementation constraints
- Implement the percentage behavior as a TextColumn subclass that reuses the existing text-format and render path. Do not add a separate percentage rendering path, and do not special-case the percentage inside Progress.
- Use None as the only unknown-total value. Do not add sentinel numbers, new constants, or new flags.
- Check for an unknown total before every operation that uses the total: the bar fill and percentage computation, the finish-style selection, finish detection in update and advance, remaining and time_remaining in Task, and the int conversions in the total-size, count, download, and time-remaining columns.
- Keep the two percentage contracts distinct: ProgressBar.percentage_completed returns None for an unknown total, and Task.percentage returns 0.

## Dependencies
- No new packages and no new third-party imports. Reuse the imports rich/progress.py already has for typing, text, highlighter, style, column, and justify types.
- Allowed direction: rich/progress.py may depend on rich/progress_bar.py. rich/progress_bar.py must not import rich/progress.py.

## Naming
- The public class name is exactly TaskProgressColumn, following the naming of the other *Column classes.
- The new parameter name is exactly text_format_no_percentage. The inherited parameter names (text_format, style, justify, markup, highlighter, table_column) match TextColumn.
- No new public name is introduced for the unknown-total value; it is None.

## Validation
- total accepts None. Other total values keep their existing handling, with no new range checks. Negative totals keep the clamp that BarColumn already applies.
- Code is formatted with black using default arguments, as the repository pre-commit hook requires. Tests have no extra blank lines.

## Error handling
- An unknown total must never raise. The failing operations in the base code are: dividing completed by total in the bar's percentage property, which raises TypeError for None, and int conversions of total in the total-size, count, download, and time-remaining paths. Each of these must return the defined blank, placeholder, or None output instead.
- Error behavior for other inputs is unchanged.

## Documentation
- docs/source/progress.rst, "Indeterminate progress" section: state that a None total, as well as start=False, gives the pulsing animation.
- Progress.add_task docstring: describe total as the number of steps if known, and state that None renders a pulsing animation. Keep the default at 100.
- ProgressBar docstring: state that a None total renders a pulse, and that the pulse flag also pulses when the total is None.
- Task docstrings for remaining and percentage describe the None behavior described above.

## Reliability
- Finite-total output is identical to the base behavior: percentage text, ETA, count, size, download strings, bar fill, finish style, and finish time.
- An unknown total never sets finished time or finished speed, so an indeterminate task never shows a finished ETA.

## Compatibility
- Widening total to an optional number is backward compatible for finite values. Before this change, None raised an error; now it renders.
- The default percentage column changes class but produces the same text for finite totals.
- TimeRemainingColumn reads the task total on every render, so any stand-in task object passed to it must provide a total attribute. Existing test stand-ins must add one.

## Behavioral acceptance criteria
- A Progress with a bar column and an unknown-total task renders without error. The bar is a full-width pulse in the pulse style. No percentage text and no ETA text appear. Elapsed output is unaffected.
- The default columns, in order, are a text column, a bar column, a TaskProgressColumn, and a time-remaining column.
- The module-level track helper uses a TaskProgressColumn as its percentage column.
- A ProgressBar with an unknown total returns None from percentage_completed and renders a pulse.
- A Task with an unknown total returns None for remaining and time_remaining, returns 0 for percentage, and is not finished after update or advance.
- For an unknown total: the percentage column is blank; the time-remaining column is blank; the total-size column is blank; the count column renders "completed/?"; the download column renders "completed/? unit", with the unit chosen from completed and binary_units honored.
- Finite-total outputs are unchanged, including the three-width percentage and the "-:--:--" placeholder for finite tasks without an estimate.

## Test requirements
- tests/test_progress.py must import TaskProgressColumn from rich.progress. A failing import stops the whole module from collecting, so every test in it fails.
- The default-columns type test expects TaskProgressColumn in the third position.
- Add a test that renders a Progress with a bar column and an unknown-total task, with a controlled clock, auto refresh off, a fixed width, and truecolor. Assert the reference pulse output for that setup.
- Stand-in task objects used by the compact and elapsed-when-finished time-remaining tests must set a total attribute.
- New tests assert the blank, "?", and binary-unit outputs listed above. Do not assert a "0%" percentage or an ETA placeholder for an unknown total.
- Existing finite-total tests in tests/test_progress.py and tests/test_bar.py must still pass.
