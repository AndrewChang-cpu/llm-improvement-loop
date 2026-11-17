## Goals
- Let a Progress task have an unknown total (None). It renders as an indeterminate task: a pulsing bar, no percentage text, no time-remaining estimate, and blank or "?" placeholders in the size and count columns.
- Keep all finite-total rendering unchanged.

## Scope
- Affected files: rich/progress.py, rich/progress_bar.py, docs/source/progress.rst, tests/test_progress.py.
- Out of scope: TimeElapsedColumn, FileSizeColumn, TransferSpeedColumn, the ProgressColumn base class caching, and Progress.track behavior for unsized iterables. A CHANGELOG entry is not required.
- Do not copy pull-request template text (checkboxes, reviewer mentions, issue links) into code, docs, or tests.

## Assumptions
- None is the sentinel for an unknown total. Do not introduce negative numbers or sentinel constants.
- Zero is a known total with its existing behavior.
- An unknown total always pulses, whether or not the task has started.

## Terminology
- Unknown total: a task whose total is None. Indeterminate task: one with an unknown total.
- Blank: zero-length text, not a placeholder.
- Unknown placeholder: the single "?" shown in the total position of the count and download columns.
- Pulse: the existing animated bar rendering.

## Workflows
1. Adding a task with an unknown total stores None without error. Start behavior is unchanged; the bar pulses.
2. Default layout: columns in order are description text, bar, task-progress, and time-remaining. With an unknown total the bar pulses, the percentage column is blank, and the time-remaining column is blank. Elapsed-time output, which is not a default, is unaffected.
3. The module-level track helper builds the same column set as the defaults: description column only when a description is given, the bar column using the caller's styles, the task-progress column, and the time-remaining column. Known-total behavior is unchanged.
4. update and advance with an unknown total still increase completed but never set finished time or finished speed. Passing a non-None total to update sets the total and restores finite rendering and finish detection.
5. A standalone bar with an unknown total pulses at any width and reports no percentage.

## Data model
- Task.total: optional number; None stored as given, no coercion.
- Task.remaining: None when total is unknown; otherwise total minus completed.
- Task.time_remaining: 0 when finished. Otherwise None when there is no speed or remaining is None. Otherwise the existing ceiling of remaining divided by speed.
- Task.percentage: keeps returning 0 for an unknown total through its existing falsy check. Do not change it; blanking is the percentage column's job.
- Task.finished_time and Task.finished_speed: set only when total is known and completed is at least total.

## API contracts
- Progress.add_task: total is an optional number, default 100; None accepted. Documentation says None renders a pulsing animation.
- ProgressBar constructor: total is an optional number, default 100; None accepted. The pulse flag documentation says the bar also pulses when total is None.
- ProgressBar.percentage_completed: returns None when total is None. Otherwise unchanged: completed divided by total times 100, clamped to 0 through 100.
- ProgressBar.update: unchanged. A None total argument leaves the stored total unchanged.
- TaskProgressColumn (new, public, importable from rich.progress): subclass of TextColumn. Constructor takes, in order: text_format (default: the existing percentage text format), text_format_no_percentage (default: empty text), style (default "none"), justify (default "left"), markup (default true), highlighter (optional, default none), table_column (optional). It stores text_format_no_percentage and passes the rest to TextColumn. Rendering uses text_format_no_percentage when the task total is None, otherwise text_format, formats with the task, then applies markup, justify, style, and highlighter as TextColumn does.
- TimeRemainingColumn: when the total is None, returns blank text using the same style selection as the normal path (progress.remaining, or progress.elapsed when elapsed_when_finished is set and the task is finished). The unknown-total check follows style selection and precedes estimate formatting. Finite-total formatting, including "-:--:--" and "--:--" placeholders, is unchanged.
- TotalFileSizeColumn: unknown total renders blank text in the same total-size style.
- MofNCompleteColumn: unknown total renders completed, separator, "?". Example: completed 5, separator "/" gives "5/?".
- DownloadColumn: unit chosen from completed when total is unknown, from total otherwise. binary_units selects binary or decimal units as before. Completed part is formatted as before (precision 0 when unit is 1, otherwise 1; thousands separators). Total part is "?" when unknown, otherwise formatted as before. Output: completed, "/", total part, space, suffix. Example: 2048 bytes completed, unknown total: "2.0/? KiB" with binary_units, "2.0/? kB" without.
- get_default_columns and the track helper: the percentage text column is replaced by a default-built TaskProgressColumn. Order unchanged.
- BarColumn: passes an unknown total through as None. For known totals, the existing zero clamp is kept.

## Module architecture
- TaskProgressColumn lives in rich/progress.py beside TextColumn and the other column classes.
- Pulse rendering and the unknown-total pulse decision live in rich/progress_bar.py.
- Task computes remaining, time_remaining, and finished state. Columns read these and do not recompute them.
- The ProgressColumn base class caching is unchanged.

## Implementation constraints
- Implement percentage as a TextColumn subclass reusing the existing text-format and render path. No separate percentage path and no special-casing in Progress.
- None is the only unknown-total value. No sentinel numbers, new constants, or new flags.
- Check for an unknown total before every operation that uses it: bar fill and percentage, finish-style selection, finish detection in update and advance, remaining and time_remaining in Task, and int conversions in the total-size, count, download, and time-remaining columns.
- Keep the two percentage contracts distinct: ProgressBar.percentage_completed returns None; Task.percentage returns 0.

## Dependencies
- No new packages or third-party imports. Reuse the typing, text, highlighter, style, column, and justify imports already in rich/progress.py.
- rich/progress.py may depend on rich/progress_bar.py. rich/progress_bar.py must not import rich/progress.py.

## Naming
- Public class name exactly TaskProgressColumn. New parameter name exactly text_format_no_percentage. Inherited parameter names match TextColumn.
- No new public name for the unknown-total value; it is None.

## Validation
- total accepts None. Other totals keep existing handling and no new range checks. Negative totals keep BarColumn's existing clamp.
- Format with black using default arguments, as the pre-commit hook requires. Tests have no extra blank lines.

## Error handling
- An unknown total must never raise. Base-code failures: dividing completed by total in the bar's percentage property raises TypeError for None, and int conversions of total in total-size, count, download, and time-remaining paths. Each must return the defined blank, placeholder, or None output.
- Error behavior for other inputs is unchanged.

## Documentation
- docs/source/progress.rst, "Indeterminate progress" section: a None total, as well as start=False, gives the pulsing animation.
- Progress.add_task docstring: total is the number of steps if known; None renders a pulsing animation. Default stays 100.
- ProgressBar docstring: None total renders a pulse; the pulse flag also pulses when total is None.
- Task docstrings for remaining and percentage describe the None behavior.

## Reliability
- Finite-total output matches base behavior: percentage text, ETA, count, size, download strings, bar fill, finish style, finish time.
- An unknown total never sets finished time or finished speed, so no finished ETA appears.

## Compatibility
- Widening total to an optional number is backward compatible for finite values. None previously raised; now it renders.
- The default percentage column changes class but gives the same text for finite totals.
- TimeRemainingColumn reads total on every render, so stand-in task objects must provide a total attribute. Existing test stand-ins must add one.

## Behavioral acceptance criteria
- A Progress with a bar column and an unknown-total task renders without error: full-width pulse in the pulse style, no percentage or ETA text, elapsed output unaffected.
- Default columns in order: text, bar, TaskProgressColumn, time-remaining.
- The track helper uses a TaskProgressColumn as its percentage column.
- ProgressBar with unknown total: percentage_completed returns None and renders a pulse.
- Task with unknown total: remaining and time_remaining return None; percentage returns 0; not finished after update or advance.
- Unknown total: percentage column blank; time-remaining blank; total-size blank; count "completed/?"; download "completed/? unit" with unit from completed and binary_units honored.
- Finite outputs unchanged, including three-width percentage and "-:--:--" placeholder for finite tasks without an estimate.

## Test requirements
- tests/test_progress.py imports TaskProgressColumn from rich.progress. A failing import stops the whole module from collecting.
- The default-columns type test expects TaskProgressColumn in third position.
- Add a test rendering a Progress with a bar column and an unknown-total task, with a controlled clock, auto refresh off, fixed width, and truecolor. Assert the reference pulse output for that setup.
- Stand-in task objects in compact and elapsed-when-finished time-remaining tests must set a total attribute.
- New tests assert the blank, "?", and binary-unit outputs above. Do not assert "0%" or an ETA placeholder for unknown totals.
- Existing finite-total tests in tests/test_progress.py and tests/test_bar.py must still pass.
