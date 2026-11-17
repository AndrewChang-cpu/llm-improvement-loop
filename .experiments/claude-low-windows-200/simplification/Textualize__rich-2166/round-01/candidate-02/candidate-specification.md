## Goals
- Let a Progress task be created with an unknown total (None). It renders as an indeterminate task: a pulsing bar, no percentage text, no time-remaining estimate, and blank or "?" placeholders in the size and count columns.
- Keep all finite-total rendering exactly as it is today.

## Scope
- Affected files: rich/progress.py, rich/progress_bar.py, docs/source/progress.rst, tests/test_progress.py.
- Out of scope: TimeElapsedColumn, FileSizeColumn, TransferSpeedColumn, the ProgressColumn base-class caching, and Progress.track behavior for unsized iterables. No CHANGELOG entry is required.
- Pull-request template text (checkboxes, reviewer mentions, issue links) is not part of the feature; carry none of it into code, docs, or tests.

## Assumptions
- None is the sentinel for an unknown total. Do not introduce negative numbers, sentinel constants, or new flags.
- Zero is a known total and keeps its existing behavior.
- An unknown total always pulses, whether or not the task has started.

## Terminology
- Unknown total: a total of None. Indeterminate task: a task with an unknown total.
- Blank: zero-length text, not a placeholder.
- Unknown placeholder: the single question mark in the total position of the count and download columns.
- Pulse: the existing animated bar rendering.

## Workflows
1. Creating: adding a task with an unknown total stores None and raises no error. Start behavior is unchanged; the bar pulses.
2. Default layout: columns in order are a description text column, a bar column, a task-progress column, and a time-remaining column. With an unknown total the bar pulses, the percentage column is blank, and the time-remaining column is blank. Elapsed-time output, which is not in the defaults, is unaffected.
3. Module-level track helper: builds the same column set as the defaults, with the description column included only when a description is given, and the bar column using the caller's styles. Known-total behavior is unchanged.
4. Updating: update and advance with an unknown total still increase completed, but never set finished time or finished speed. Passing a non-None total to update sets the total and returns the task to finite rendering and finish detection.
5. Standalone bar: an unknown-total bar pulses at any width and reports no percentage.

## Data model
- Task.total: optional number; None is stored as given, without coercion.
- Task.remaining: None when the total is unknown; otherwise total minus completed.
- Task.time_remaining: 0 when finished. Otherwise None when there is no speed or remaining is None. Otherwise the existing ceiling of remaining divided by speed.
- Task.percentage: keeps returning 0 for an unknown total through its existing falsy check. Do not change it; blanking is the percentage column's job.
- Task.finished_time and finished_speed: set only when the total is known and completed is at least the total.

## API contracts
- Progress.add_task: total is an optional number, default 100; None is accepted. Its documentation says None renders a pulsing animation.
- ProgressBar constructor: same total contract. The pulse flag documentation says the bar also pulses when total is None.
- ProgressBar.percentage_completed: returns None when total is None; otherwise unchanged (completed divided by total times 100, clamped to 0 through 100).
- ProgressBar.update: unchanged. A None total argument leaves the stored total unchanged.
- TaskProgressColumn (new, public, importable from rich.progress): a TextColumn subclass. Constructor parameters in order: text_format (default: the current percentage text format), text_format_no_percentage (default: empty text), style (default "none"), justify (default "left"), markup (default true), highlighter (optional, default none), table_column (optional). It stores text_format_no_percentage and passes the rest to TextColumn. On render it uses text_format_no_percentage when the task total is None and text_format otherwise, formats with the task, then applies markup, justify, style, and highlighter as TextColumn does.
- TimeRemainingColumn: when total is None, returns blank text in the style chosen by the normal path (remaining, or elapsed when elapsed_when_finished is set and the task is finished). The unknown-total check happens after style selection and before estimate formatting. Finite formatting, including the "-:--:--" and "--:--" placeholders, is unchanged.
- TotalFileSizeColumn: an unknown total renders blank text in the same total-size style.
- MofNCompleteColumn: an unknown total renders the integer completed count, the separator, then "?". Completed 5 with separator "/" renders "5/?".
- DownloadColumn: the unit is chosen from completed when total is unknown, otherwise from total; binary_units selects the unit list as before. Completed is formatted as before (precision 0 when the unit is 1, otherwise 1; thousands separators). The total part is "?" when unknown, otherwise as before. Output: completed, "/", total part, a space, suffix. Example: 2048 bytes completed with an unknown total gives "2.0/? KiB" with binary_units and "2.0/? kB" without.
- get_default_columns and the module-level track helper: the percentage text column is replaced by a default TaskProgressColumn. Column order is unchanged.
- BarColumn: passes an unknown total to the bar as None. Known totals keep the existing zero clamp.

## Module architecture
- TaskProgressColumn belongs in rich/progress.py beside the other column classes.
- Pulse rendering and the unknown-total pulse decision belong in rich/progress_bar.py.
- Task computes remaining, time_remaining, and finished state. Columns read these values and do not recompute them.
- ProgressColumn base-class caching is unchanged.

## Implementation constraints
- Implement percentage as a TextColumn subclass reusing the existing text-format and render path. Add no separate percentage rendering path; Progress does not special-case the percentage.
- Use None as the only unknown-total value.
- Check for an unknown total before every operation that uses the total: bar fill and percentage, finish-style selection, finish detection in update and advance, remaining and time_remaining in Task, and int conversions in the total-size, count, download, and time-remaining columns.
- Keep the two percentage contracts distinct: ProgressBar.percentage_completed returns None; Task.percentage returns 0.
- No new packages or third-party imports; reuse the typing, text, highlighter, style, column, and justify imports rich/progress.py already has. rich/progress.py may import rich/progress_bar.py; rich/progress_bar.py must not import rich/progress.py.
- Names: the class is exactly TaskProgressColumn; the parameter is exactly text_format_no_percentage; inherited parameter names match TextColumn.
- Format with black defaults. Tests have no extra blank lines.

## Error handling
- An unknown total must never raise. Failing base operations: dividing completed by total in the bar's percentage property (TypeError for None), and int conversions of total in the total-size, count, download, and time-remaining paths. Each returns its defined blank, placeholder, or None output.
- Other inputs keep existing behavior. Non-None totals keep existing handling with no new range checks; negative totals keep BarColumn's clamp.

## Documentation
- docs/source/progress.rst, "Indeterminate progress" section: a None total, as well as start=False, gives the pulsing animation.
- Progress.add_task docstring: total is the number of steps if known; None renders a pulsing animation. Default stays 100.
- ProgressBar docstring: a None total renders a pulse; the pulse flag also pulses when total is None.
- Task docstrings for remaining and percentage describe the None behavior.

## Reliability and compatibility
- Finite-total output is identical to the base: percentage text, ETA, count, size, download strings, bar fill, finish style, and finish time.
- Widening total to an optional number is backward compatible; None previously raised and now renders. The default percentage column changes class but yields the same finite text.
- TimeRemainingColumn reads total on every render, so any stand-in task object passed to it must provide a total attribute.

## Test requirements
- tests/test_progress.py imports TaskProgressColumn from rich.progress; a failing import stops the whole module from collecting.
- The default-columns type test expects TaskProgressColumn in the third position.
- Add a test rendering a Progress with a bar column and an unknown-total task, with a controlled clock, auto refresh off, fixed width, and truecolor. Assert the reference pulse output.
- Stand-in task objects in the compact and elapsed-when-finished time-remaining tests must set a total attribute.
- New tests assert the blank, "?", and binary-unit outputs. Do not assert "0%" or an ETA placeholder for an unknown total.
- Existing finite-total tests in tests/test_progress.py and tests/test_bar.py must still pass.
- Acceptance: a Progress with a bar column and an unknown-total task renders without error as a full-width pulse in the pulse style, with no percentage or ETA text; elapsed output is unaffected. A ProgressBar with unknown total returns None and pulses. A Task with unknown total returns None for remaining and time_remaining, 0 for percentage, and is not finished after update or advance. Finite outputs, including the three-width percentage and "-:--:--", are unchanged.
