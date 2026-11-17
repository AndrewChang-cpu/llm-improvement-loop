## Goals

- Add a progress column, TimeElapsedColumn, that shows how long a task has been running as hours:minutes:seconds, truncated to whole seconds.
- When a task reaches its total, freeze the displayed value at the elapsed time recorded at that moment, so later renders do not keep counting.
- Keep the placeholder and duration text consistent with TimeRemainingColumn.
- Add a __rich__ method to the palette class so the palette renders as a table. Its test is required.

## Scope

In scope:
- The new column class in the progress module, placed next to TimeRemainingColumn.
- A finished-time value on each task, captured by Progress update and advance, and cleared by Progress reset and by the task's internal reset.
- Deriving a task's finished state from the captured value.
- A default style entry for the column's text.
- Palette.__rich__.
- Tests and a changelog entry.

Out of scope:
- Changes to start_task, stop, stop_task, or any other public method signature.
- Changes to other columns beyond the effects in Compatibility.
- New dependencies, new clocks, or new public Progress methods.
- Unrelated edits: exception chaining in markup, markup tag normalization, color docstring and comment edits, the console size pragma, a docs reST fix, the version bump, the process_renderables demo wiring and its extra re-raise, and the color demo block at the bottom of the palette module.

## Assumptions

- Time comes from the task's existing clock through the existing elapsed calculation. No new time source is added.
- Existing column rendering and refresh behavior stay as in the base code.
- The test module's mock clock returns its current value, then advances by one unit per call while automatic mode is on. The number and order of clock reads therefore appear in expected test output.

## Terminology

- elapsed: the task's existing elapsed value. Absent if the task has not started. Otherwise the current time, or the stop time if stopped, minus the start time.
- finished time: the elapsed value recorded by a capture. Absent until captured. Zero is a valid captured value; "present" means not absent.
- capture: recording the finished time under the rule in Workflows.
- clear: setting the finished time back to absent.
- finished: true if and only if a finished time is present.

## Workflows

1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, the shown value is its finished time. The column does not read elapsed.
   - Otherwise the shown value is the task's elapsed value, read exactly once during this render.
   - If the shown value is absent, output the placeholder "-:--:--" styled with progress.elapsed.
   - Otherwise truncate the value to whole seconds, convert it with the same conversion TimeRemainingColumn uses, and style it with progress.elapsed.
   - The column sets no refresh cap, unlike TimeRemainingColumn. It renders on every call and does not cache output.
2. Capture on update. Progress update keeps its existing order: apply the given values, refresh if requested, read the current time, and do the sample bookkeeping. Then, as the last step inside the same lock: if completed is at least total and no finished time is present, read the task's elapsed value exactly once and store it as the finished time. Do not add a separate check for whether elapsed is present. An absent value is stored as absent, leaving the task unfinished.
3. Capture on advance. Progress advance applies the same rule after it adds to completed and appends its sample, inside its lock. Its own time read happens before the lock, as in the base code.
4. Clearing. Two places clear the finished time:
   - The task's internal reset clears the sample history and the finished time. Progress update calls this internal reset whenever a total is passed in, not only when the total value changes.
   - Progress reset clears the finished time explicitly before refreshing. This is redundant with the internal reset and harmless.
   Start, stop, and stop_task neither capture nor clear. Progress reset with completed equal to total does not capture, so the task stays unfinished until the next update or advance.
5. Total change. When update receives a total, the finished time is cleared first. Then completed is applied and the capture rule runs in the same call. The task is finished after that call only if completed is at or above the new total, and the captured value is the elapsed time at that call.
6. Completed lowered. Once captured, the finished time stays until a reset or an update that receives a total clears it. Lowering completed does not clear it.
7. Creation. add_task does not capture, even if completed is at or above total. Such a task reports unfinished until the first update or advance that triggers the capture rule.

## Data model

- Task gains a public field, finished_time: an optional number of seconds, default absent. Declare it as a plain defaulted field placed after the callable clock field and before the visibility flag, as in the reference. It is not excluded from initialization, so it can be passed by keyword. Callers that pass the visibility flag or later fields positionally are affected by the new position; callers that use keywords are not.
- Give the field a short docstring in the style of the other Task fields, stating that it holds the time the task was finished.
- The Task finished property changes from "completed is at least total" to "a finished time is present". It is read-only and returns a boolean. Its docstring must describe this new check and replace the old "completed" wording.
- Consumers inherit the new definition: the bar column's finished styling, Task.time_remaining (zero when finished), and Progress.finished (true when there are no tasks, otherwise true when every task is finished).

## API contracts

- TimeElapsedColumn is a public class in the progress module, a subclass of the existing ProgressColumn base, and exported the same way as TimeRemainingColumn. The module defines no export list.
- Its constructor takes no arguments. Its render method takes a task and returns a rich Text object. It applies the style progress.elapsed.
- Task.finished_time is a public, readable and writable attribute with the semantics in Terminology.
- Palette.__rich__ is a public method taking only the instance. It returns a rich Table with:
  - Three columns, in order: index, RGB, Color.
  - Title "Palette". Caption is the number of colors followed by " colors", right-justified. Highlighting enabled.
  - One row per palette color, in palette order.
  - Index cell: the index as a plain string, not a styled text object, so the table's highlighting applies.
  - RGB cell: a plain string holding the stored triplet's text form, a parenthesized tuple of three integers separated by comma and space. It must not show the ColorTriplet type name or its field names.
  - Color cell: a text object of 16 space characters with a background built from the stored triplet.
- Progress method signatures do not change.

## Module architecture

- The column class lives in rich/progress.py, directly after the bar column class and directly before TimeRemainingColumn. The module order is therefore: bar column, the new column, time-remaining column.
- The column sets no refresh cap, inheriting the base default. It writes no state and reads only the public Task attributes finished, finished_time, and elapsed.
- Capture and clear logic lives in Progress update, advance, and reset, and in the Task's internal reset.
- The style default goes in the default styles table in rich/default_styles.py, among the progress.* entries, with a yellow foreground.
- Palette.__rich__ lives in rich/palette.py. The palette module must not import the table, text, style, or color modules at module level, because the color module imports the palette data at module level and a top-level import would create a cycle. Import those names inside the method, and use a type-checking-only import for the table annotation.

## Implementation constraints

- Clock reads are pinned by tests, because the test clock advances on every read. Therefore:
  - Each column call performs one shared clock read in the base column call, before the column's render logic. The new column's render reads elapsed only when the task is unfinished. A finished render reads no clock. The column adds no other reads and no caching.
  - Each capture reads elapsed exactly once, only when the capture rule fires, and stores that value directly.
  - In update, the capture is the last clock-related step. In advance, the capture's read comes after advance's own time read.
  - Do not change the order of existing reads in update, advance, or reset.
- Use the existing lock. Do not add a lock.

## Dependencies

- No new imports, packages, or configuration in rich/progress.py. The column uses the duration and text types already imported there.
- Palette.__rich__ uses the table, text, style, and color types through the lazy-import rule above.

## Naming

- Column: TimeElapsedColumn, matching TimeRemainingColumn.
- Style: progress.elapsed.
- Placeholder: "-:--:--", identical to TimeRemainingColumn's.
- Task field: finished_time.
- Palette method: __rich__, as the rich renderable protocol requires.

## Documentation

- The column class has a one-line docstring. Its render method has a short docstring.
- Palette.__rich__ has a short docstring.
- CHANGELOG.md gets a new unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Reliability

- The finished time is captured at most once until cleared. Later updates and advances must not overwrite it.
- Capture happens inside the same lock as the state change it depends on, so readers never see a completed count without the matching captured value.
- A task that has not started never gets a finished time from update or advance, because the absent elapsed value is stored as absent. Add no separate guard.

## Compatibility

- The finished property change is intentional. In normal progression (completed rising to total, no reset) it matches the old definition. The following differences are reference behavior and must not be "fixed":
  - Lowering completed after a finish keeps the task finished.
  - An update that receives a total clears the finished time and recaptures in the same call if completed is at or above the new total.
  - add_task with completed at or above total reports unfinished until an update or advance.
  - reset with completed at total reports unfinished until an update or advance.
- Keyword-based Task construction is unaffected. Positional callers that pass the visibility flag or later fields are affected; no such caller exists in the repository.

## Behavioral acceptance criteria

- An unstarted task renders "-:--:--" with the progress.elapsed style.
- A started, unfinished task renders elapsed time as hours:minutes:seconds, truncated to whole seconds, and the value changes as time passes.
- When a task first reaches completed at least equal to total, its value freezes at the elapsed value at that moment and does not change on later renders, even while other tasks run. Example: a task reaching its total 10 seconds after starting keeps showing 0:00:10, while a still-running second task continues to show live time.
- Stopping a progress display, or calling stop_task, does not freeze a value. Only reaching the total does.
- Progress reset clears the frozen value. A reset task that is started again shows live time.
- By default the column text is styled yellow through the default styles table. A user theme can override it.
- The standard palette's __rich__ returns a table with one row per color; the standard palette has 16 rows. Each RGB cell shows the stored triplet's tuple text, and the index and RGB cells are plain strings.

## Test requirements

- Add a unit test for TimeElapsedColumn in the progress test module, following the per-column pattern used for TimeRemainingColumn. Drive the task through public Progress update and advance calls with a controlled clock, not by assigning the finished time by hand. Check three states: unstarted (placeholder), running (live elapsed), and finished (value frozen at the finish time, even after the clock advances further).
- Update the existing column-list integration test (test_columns) as one coupled change:
  - Add TimeElapsedColumn to its Progress column list immediately after TimeRemainingColumn, and import it with the other progress names.
  - Regenerate its expected rendered output in the same patch. Start from the base expected output and change only: (a) each row gains one progress.elapsed cell, placed after the time-remaining cell and before the file-size cell; (b) bar widths shrink in every frame because the new column takes layout width; (c) clock-derived cell values (elapsed and speed) that shift because of the extra clock reads. Elapsed cells for completed tasks show frozen values.
  - Every other character stays byte-identical to the base: escape sequences, erase and cursor-up sequences, line breaks, and padding inside styled spans. Padding inside a file-size or total-size span is the space the render adds to fill that column's width in that frame. Do not add or drop padding by hand, and do not carry it from a frame or row with a different column width. Base padding is not automatically valid after the layout change.
  - Do not add or remove erase or cursor sequences.
  - Derive each clock-derived value by tracing clock reads in order, as in Implementation constraints. Do not estimate. A finished task's elapsed value is the value stored at its capture read and stays fixed in later frames. Trace the reads for each frame before writing its cells.
  - If the test can be run, run test_columns against the new implementation and confirm every difference from the base falls into category (a), (b), or (c) before accepting the expected text. If it cannot be run, say so in the final report and cite the trace used.
  - The column-list edit and the expected-output edit must not be made separately. Afterward, verify the column list contains the new column in position and every rendered row has one more cell than before. A column without matching expected cells, or the reverse, is a failure.
- Add tests/test_palette.py with one test named test_rich_cast. It imports the module-level standard palette object from rich._palettes, calls __rich__ directly on that object with no arguments, and asserts the result is a Table with 16 rows. Do not wrap the palette object in a new Palette, because the constructor takes a sequence of color triplets and wrapping raises an error.
- Do not add a new test framework or fixture library.
