## Goals
- Let a Progress task have an unknown total (None). It renders as an indeterminate task: a pulsing bar, no percentage text, no time-remaining estimate, and blank or "?" placeholders in the size and count columns.
- Keep all finite-total rendering exactly as it is today.

## Scope
- Affected files: rich/progress.py, rich/progress_bar.py, docs/source/progress.rst, tests/test_progress.py.
- Out of scope: TimeElapsedColumn, FileSizeColumn, TransferSpeedColumn, the ProgressColumn base class caching, and the existing Progress.track behavior for unsized iterables. No CHANGELOG entry is required.
- Do not carry pull-request template text into code, docs, or tests.

## Assumptions
- None is the only sentinel for an unknown total. Do not introduce negative numbers, sentinel constants, or new flags.
- Zero is a known total and keeps its existing behavior.
- An unknown total always pulses, whether or not the task has started.

## Terminology
- Unknown total: a total of None. Indeterminate task: a task with an unknown total.
- Blank: zero-length text. Unknown placeholder: the single "?" in the total position of the count and download columns.

## Workflows
1. Creating an indeterminate task: adding a task with an unknown total stores None and raises no error. Start behavior is unchanged; the bar pulses.
2. Default layout: the columns, in order, are a description text column, a bar column, a task-progress column, and a time-remaining column. For an unknown total the bar pulses, and the percentage and time-remaining columns are blank. Elapsed-time output, which is not in the defaults, is unaffected.
3. Module-level track helper: builds the same column set as the defaults. The description column is included only when a description is given, and the bar column uses the caller's styles.
4. Updating: update and advance with an unknown total still increase completed, but never set finished time or finished speed. Passing a non-None total to update sets the total and restores finite rendering and finish detection.
5. Standalone bar: a bar with an unknown total pulses at any width and reports no percentage.

## Data model
- Task.total: an optional number, stored as given with no coercion.
- Task.remaining: None when the total is unknown; otherwise total minus completed.
- Task.time_remaining: 0 when finished. Otherwise None when there is no speed or when remaining is None. Otherwise the existing ceiling of remaining divided by speed.
- Task.percentage: keeps returning 0 when the total is unknown, through its existing falsy check. Blanking is the percentage column's job.
- Task.finished_time and Task.finished_speed: set only when the total is known and completed is at least the total.

## API contracts
- Progress.add_task and the ProgressBar constructor: total is an optional number, default 100, and None is accepted. Their documentation says None renders a pulsing animation.
- ProgressBar.percentage_completed: returns None when total is None. Otherwise unchanged: completed divided by total times 100, clamped to 0 through 100.
- ProgressBar.update: unchanged. A None total argument leaves the stored total unchanged.
- TaskProgressColumn (new, public, importable from rich.progress): a TextColumn subclass. Its constructor takes, in order: text_format (default: the existing percentage text format), text_format_no_percentage (default: empty text), style (default "none"), justify (default "left"), markup (default true), highlighter (optional, default none), and table_column (optional). It stores text_format_no_percentage and passes the rest to the TextColumn constructor. When the task total is None it renders text_format_no_percentage, otherwise text_format, and then processes the text as TextColumn does.
- TimeRemainingColumn: when the task total is None, returns blank text. The style is chosen first, using the same selection as the normal path. The unknown-total check comes after style selection and before any estimate formatting. Finite-total placeholders such as "-:--:--" and "--:--" are unchanged.
- TotalFileSizeColumn: an unknown total renders blank text with the same total-size style.
- MofNCompleteColumn: an unknown total renders the completed count, the separator, then "?". Completed 5 with separator "/" renders "5/?".
- DownloadColumn: the unit is chosen from completed when the total is unknown, and from the total otherwise. The binary_units setting selects the unit list as before. The completed part is formatted as before. The total part is "?" when the total is unknown. Example: 2048 bytes completed with an unknown total gives "2.0/? KiB" with binary_units and "2.0/? kB" without.
- get_default_columns and the module-level track helper: the percentage text column is replaced by a TaskProgressColumn with its defaults. Column order is unchanged.
- BarColumn: passes an unknown total through as None. For a known total, the existing clamp at zero is kept.

## Module architecture
- TaskProgressColumn belongs in rich/progress.py beside the other column classes. Pulse rendering and the unknown-total pulse decision belong in rich/progress_bar.py.
- Task computes remaining, time_remaining, and finished state. Columns read those values and do not recompute them.

## Implementation constraints
- Implement the percentage behavior as a TextColumn subclass that reuses the existing text-format and render path. Do not add a separate percentage path or special-case the percentage inside Progress.
- Check for an unknown total before every operation that uses it: the bar fill and percentage, finish-style selection, finish detection in update and advance, remaining and time_remaining in Task, and the int conversions in the total-size, count, download, and time-remaining columns.
- ProgressBar.percentage_completed returns None for an unknown total, while Task.percentage returns 0. Keep these distinct.

## Dependencies
- No new packages or third-party imports. Reuse the imports rich/progress.py already has.
- rich/progress.py may depend on rich/progress_bar.py. rich/progress_bar.py must not import rich/progress.py.

## Naming
- The public class name is exactly TaskProgressColumn. The new parameter name is exactly text_format_no_percentage. Inherited parameter names match TextColumn.

## Validation
- Other total values keep their existing handling, with no new range checks.
- Format code with black using default arguments, as the pre-commit hook requires.

## Error handling
- An unknown total must never raise. Two base-code paths fail today: dividing completed by total in the bar's percentage property, and int conversions of total in the total-size, count, download, and time-remaining paths. Each must return the defined blank, placeholder, or None output.
- Error behavior for other inputs is unchanged.

## Documentation
- docs/source/progress.rst, "Indeterminate progress" section: state that a None total, as well as start=False, gives the pulsing animation.
- Progress.add_task docstring: describe total as the number of steps if known, and state that None renders a pulse. Keep the default at 100.
- ProgressBar docstring: state that a None total renders a pulse and that the pulse flag also pulses when total is None.
- Task docstrings for remaining and percentage describe the None behavior above.

## Reliability
- Finite-total output is identical to the base behavior, including percentage text, ETA, count, size, download strings, bar fill, finish style, and finish time.
- An unknown total never sets finished time or speed, so an indeterminate task never shows a finished ETA.

## Compatibility
- Widening total to an optional number is backward compatible for finite values. None previously raised an error; now it renders.
- TimeRemainingColumn reads the task total on every render, so any stand-in task object must provide a total attribute. Existing test stand-ins must add one.

## Behavioral acceptance criteria
- A Progress with a bar column and an unknown-total task renders without error: a full-width pulse in the pulse style, with no percentage or ETA text. Elapsed output is unaffected.
- The default columns, in order, are a text column, a bar column, a TaskProgressColumn, and a time-remaining column. The track helper uses a TaskProgressColumn as its percentage column.
- A ProgressBar with an unknown total returns None from percentage_completed and renders a pulse.
- A Task with an unknown total returns None for remaining and time_remaining, returns 0 for percentage, and is not finished after update or advance.
- For an unknown total: the percentage, time-remaining, and total-size columns are blank; the count column renders "completed/?"; the download column renders "completed/? unit" with the unit chosen from completed and binary_units honored.
- Finite-total outputs are unchanged, including the three-width percentage and the "-:--:--" placeholder.

## Test requirements
- tests/test_progress.py must import TaskProgressColumn from rich.progress. A failing import stops the whole module from collecting.
- The default-columns type test expects TaskProgressColumn in the third position.
- Add a test rendering a Progress with a bar column and an unknown-total task, with a controlled clock, auto refresh off, fixed width, and truecolor. Assert the reference pulse output for that setup.
- Stand-in task objects used by the compact and elapsed-when-finished time-remaining tests must set a total attribute.
- New tests assert the blank, "?", and binary-unit outputs above. Do not assert a "0%" percentage or an ETA placeholder for an unknown total.
- Existing finite-total tests in tests/test_progress.py and tests/test_bar.py must still pass.
