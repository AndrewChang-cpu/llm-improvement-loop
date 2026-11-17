## Goals

- Add a progress display column, TimeElapsedColumn, that shows how long a progress task has been running as hours:minutes:seconds, using whole seconds only (fractional seconds are truncated).
- When a task reaches its total, freeze the displayed value at the elapsed time recorded at that moment, so later renders do not keep counting.
- Keep the column's placeholder and duration text consistent with TimeRemainingColumn.
- Add a __rich__ method to the palette class so the palette can be rendered as a table. This method is part of the required behavior, and its test is required for this change.

## Scope

In scope:
- The new column class in the progress module, placed next to TimeRemainingColumn.
- A finished-time value on each progress task, captured by the progress object's update and advance operations and cleared by the progress object's reset and by the task's internal reset.
- A change to how a task's finished state is derived, so it follows the captured value (see Data model).
- A default theme style entry for the column's text.
- A __rich__ method on the palette class (see API contracts).
- Tests and a changelog entry.

Out of scope:
- Changes to start_task, stop, stop_task, or any other public method signature.
- Changes to other columns beyond the finished-state effects described under Compatibility.
- New dependencies, new clocks, or new public Progress methods.
- Unrelated edits: exception chaining in markup, markup tag normalization, color docstring and comment edits, the console size pragma, a docs reST fix, the version bump, the process_renderables demo wiring and its extra re-raise, and the color demo block at the bottom of the palette module. Do not implement these.

## Assumptions

- Time is read from the task's existing clock through the existing elapsed calculation. No new time source is introduced.
- Existing column rendering and refresh behavior stay as in the base code.
- The test module's mock clock returns its current value and then advances by one unit on each call while automatic mode is on. The number and order of clock reads are therefore visible in expected test output (see Implementation constraints).

## Terminology

- elapsed: the task's existing elapsed value. It is absent if the task has not started. Otherwise it is the current time, or the stop time if the task was stopped, minus the start time.
- finished time: the elapsed value recorded by a capture (see Workflows). It is absent until captured. Zero is a valid captured value; "present" means not absent.
- capture: recording the finished time under the rule in Workflows.
- clear: setting the finished time back to absent.
- finished: true if and only if a finished time is present.

## Workflows

1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, the value shown is the task's finished time. The column does not read elapsed in this case.
   - Otherwise the value shown is the task's elapsed value, read exactly once during this render.
   - If the value shown is absent, output the placeholder "-:--:--" styled with progress.elapsed.
   - Otherwise truncate the value to whole seconds, convert it to a duration with the same conversion TimeRemainingColumn uses for its remaining time, and style it with progress.elapsed.
   - The column must not set a refresh cap. It renders on every call and does not reuse cached output. This differs from TimeRemainingColumn, which sets a refresh cap.
2. Capture on update. In the progress object's update operation, keep the existing order: apply the given values, refresh if requested, read the current time, and do the sample bookkeeping. Then, as the last step and still inside the same lock: if completed is at least total and no finished time is present, read the task's elapsed value exactly once and store that value as the finished time. Do not add a separate check for whether elapsed is present. An absent value is stored as absent, which leaves the task unfinished.
3. Capture on advance. The advance operation applies the same rule after it adds to completed and appends its sample, still inside its lock. Its own time read happens before the lock, as in the base code.
4. Clearing. Two places clear the finished time:
   - The task's internal reset clears the sample history and the finished time. The progress object's update calls this internal reset whenever a total is passed in, not only when the total value changes.
   - The progress object's reset clears the finished time explicitly before refreshing. This is redundant with the internal reset and harmless.
   Start, stop, and stop_task neither capture nor clear. Progress.reset with completed equal to total does not capture; the task stays unfinished until the next update or advance.
5. Total change. When update receives a total, the finished time is cleared first. Then completed is applied, and the capture rule runs in the same call. The task is finished after that call only if completed is at or above the new total, and the captured value is the elapsed time at that call.
6. Completed lowered. Once captured, the finished time stays until it is cleared by reset or by an update that receives a total. Lowering completed does not clear it, so the task remains finished.
7. Creation. add_task does not capture a finished time, even if completed is at or above total. Such a task reports unfinished until the first update or advance call that triggers the capture rule.

## Data model

- Task has a new public field, the finished time: an optional number of seconds, default absent. Declare it as a plain defaulted field placed after the callable clock field and before the visibility flag, as in the reference. It is a normal public field, not excluded from initialization, so it can be passed by keyword like the other public fields. Because it sits before the visibility flag, any caller that passes the visibility flag or later fields positionally is affected; callers that use keywords are unaffected.
- The field has a short docstring in the same style as the other Task fields, stating that it holds the time the task was finished.
- The Task finished property changes from "completed is at least total" to "a finished time is present". It is read-only and returns a boolean.
- Consumers inherit the new definition: the bar column's finished styling, Task.time_remaining (which returns zero when finished), and Progress.finished (true when there are no tasks, otherwise true when every task is finished).

## API contracts

- TimeElapsedColumn is a public class in the progress module and a subclass of the existing ProgressColumn base. It is exported the same way as TimeRemainingColumn; the module defines no export list.
- Its constructor takes no arguments.
- Its render method takes a task and returns a rich Text object.
- The style name it applies is progress.elapsed.
- The Task finished-time field is a public, readable and writable attribute with the semantics in Terminology.
- Palette.__rich__ is a public method on the palette class. It takes only the instance and returns a rich Table with these properties:
  - Three columns, in this order: index, RGB, Color.
  - Title "Palette". Caption is the number of colors followed by " colors", right-justified. Highlighting is enabled on the table.
  - One row per palette color, in palette order. Row count equals the number of colors in the palette.
  - Index cell: the index as a plain string, not a styled text object, so the table's highlighting applies to it.
  - RGB cell: a plain string holding the text form of the color's stored triplet exactly as the palette stores it: a parenthesized tuple of three integers separated by comma and space. It must not show the name of the ColorTriplet type or its field names.
  - Color cell: a text object of 16 space characters whose background is the color built from the stored triplet.
- Progress method signatures do not change.

## Module architecture

- The column class lives in rich/progress.py. Its position is directly after the bar column class and directly before the TimeRemainingColumn class, so the module order of these three classes is: bar column, the new column, time-remaining column.
- The column class sets no refresh cap, so it inherits the base default of no cap.
- Capture and clear logic lives in Progress.update, Progress.advance, Progress.reset, and the Task's internal reset. The column writes no state.
- The column reads only public Task attributes: finished, the finished time, and elapsed.
- The style default is registered in the default styles table in rich/default_styles.py, among the progress.* entries, with a yellow foreground.
- Palette.__rich__ lives in rich/palette.py. The palette module must not import the table, text, style, or color modules at module level. The color module imports the palette data at module level, so a top-level import would create a cycle. Import those names inside the method, and use a type-checking-only import for the table annotation.

## Implementation constraints

- Clock reads are part of the behavior the tests pin, because the test clock advances on every read. Therefore:
  - Each column call performs one clock read in the shared column base call, before the column's own render logic runs. The new column's render adds one more read of elapsed only when the task is unfinished; when the task is finished, render reads no clock. The column must not add any other reads.
  - Because the column is uncapped, every frame calls its render and its reads happen in the order listed here. Do not add caching to the column.
  - Each capture performs exactly one read of elapsed, and only when the capture rule fires. It stores that value directly.
  - In update, the capture is the last clock-related step. In advance, the capture's read comes after advance's own time read.
  - Do not change the order of existing reads in update, advance, or reset.
- Use the existing lock. Do not add a lock.

## Dependencies

- No new imports, packages, or configuration in rich/progress.py. The column uses the duration type and text type already imported there.
- Palette.__rich__ uses the table, text, style, and color types through the lazy-import rule in Module architecture.

## Naming

- Column class: TimeElapsedColumn, matching TimeRemainingColumn.
- Style name: progress.elapsed.
- Placeholder: "-:--:--", identical to TimeRemainingColumn's placeholder.
- Task field: finished_time.
- Palette method: __rich__, the name the rich renderable protocol requires.

## Documentation

- The column class has a one-line docstring. Its render method has a short docstring.
- The Task finished-time field has a docstring stating that it holds the time the task was finished.
- The Task finished property's docstring must describe the new check, that a finished time has been captured. Replace the old "completed" wording.
- Palette.__rich__ has a short docstring.
- CHANGELOG.md gets a new unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Reliability

- The finished time is captured at most once until it is cleared. Later updates and advances must not overwrite a captured value.
- Capture happens inside the same lock as the state change it depends on, so readers never see a completed count without the matching captured value.
- A task that has not started never gets a finished time from update or advance, because the absent elapsed value is stored as absent. Do not add a separate guard for this.

## Compatibility

- The change to the finished property is intentional. In normal progression (completed rising to total, no reset) it matches the old definition. These differences from the old definition are reference behavior and must not be "fixed":
  - Lowering completed after a finish keeps the task finished.
  - An update that receives a total clears the finished time and recaptures in the same call if completed is at or above the new total.
  - add_task with completed at or above total reports unfinished until an update or advance.
  - reset with completed at total reports unfinished until an update or advance.
- Existing code that constructs Task objects with keyword arguments is unaffected. Positional callers that pass the visibility flag or later fields are affected by the new field's position; no such caller exists in the repository.

## Behavioral acceptance criteria

- An unstarted task renders "-:--:--" with the progress.elapsed style.
- A started, unfinished task renders its elapsed time as hours:minutes:seconds, truncated to whole seconds, and the value changes as time passes.
- When a task first reaches completed at least equal to total, its displayed value freezes at the elapsed value at that moment. It does not change on later renders, even while other tasks keep running.
- Example: a task that reaches its total 10 seconds after it started keeps showing 0:00:10 afterward, while a second task still running continues to show its live time.
- Stopping a progress display, or calling stop_task on a single task, does not freeze a task's value. Only reaching the total does.
- Progress reset clears the frozen value. A reset task that is started again shows live time.
- By default, the column's text is styled yellow through the default styles table. A user theme can override it.
- The standard palette's __rich__ returns a table with one row per color; the standard palette has 16 rows.
- In the palette table, the RGB cell for each color shows the stored triplet's tuple text, not the ColorTriplet type's text, and the index and RGB cells are plain strings.

## Test requirements

- Add a unit test for TimeElapsedColumn in the progress test module, following the per-column pattern used for TimeRemainingColumn. It drives the task through the public Progress update and advance operations with a controlled clock, not by assigning the finished time by hand, and checks three states: unstarted (placeholder), running (live elapsed), and finished (value frozen at the finish time, even when the clock has advanced further).
- Update the existing column-list integration test (test_columns) as one coupled change:
  - Add TimeElapsedColumn to its Progress column list immediately after TimeRemainingColumn.
  - Regenerate that test's expected rendered output in the same patch. Each row gains one progress.elapsed cell, placed after the time-remaining cell and before the file-size cell. Elapsed cells for completed tasks show the frozen values.
  - The expected output's control structure must match the base expected output: the same number of frames, the same erase and cursor-up sequences, and the same line breaks. Only cell text changes, plus the bar widths, which shrink because the new column takes layout width. Do not add or remove erase or cursor sequences.
  - The column-list edit and the expected-output edit must not be made separately. After editing, verify that the column list contains the new column in that position and that every rendered row in the expected output has one more cell than before. A column added to the list without the matching expected cells, or expected cells without the column in the list, is a failure.
  - Because the mock clock advances on each read, and the speed cells come from the same reads, all clock-derived cells (elapsed and speed) can shift. Derive each value by tracing the clock reads in order, as described in Implementation constraints. Do not estimate values, and do not leave the base expected string unchanged.
- Add a palette test module at tests/test_palette.py. Its single test is named test_rich_cast. It calls __rich__ on the standard palette, asserts the result is a Table, and asserts the table's row count is 16.
- Do not add a new test framework or fixture library.
