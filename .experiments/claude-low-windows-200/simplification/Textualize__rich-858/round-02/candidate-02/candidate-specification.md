## Goals
- Add a progress column, TimeElapsedColumn, showing how long a task has run as hours:minutes:seconds, truncated to whole seconds.
- When a task reaches its total, freeze its displayed value at the elapsed time recorded at that moment.
- Keep the placeholder and duration text consistent with TimeRemainingColumn.
- Add a __rich__ method to the palette class so the palette renders as a table.

## Scope
In scope:
- The new column class in the progress module, next to TimeRemainingColumn.
- A finished-time value on each task, captured by Progress update and advance, and cleared by Progress reset and the task's internal reset.
- Deriving a task's finished state from that value.
- A default style entry for the column's text.
- Palette.__rich__ and its test, plus a changelog entry.

Out of scope:
- Changes to start_task, stop, stop_task, or any other public method signature.
- Changes to other columns beyond the Compatibility effects.
- New dependencies, clocks, or public Progress methods.
- Unrelated edits: markup exception chaining, markup tag normalization, color docstring and comment edits, the console size pragma, a docs reST fix, the version bump, the process_renderables demo wiring and its extra re-raise, and the color demo block at the bottom of the palette module.

## Assumptions
- Time comes from the task's existing clock through the existing elapsed calculation. No new time source is added.
- Existing column rendering and refresh behavior stay as in the base code.
- The test module's mock clock returns its current value and advances by one unit per call while automatic mode is on. Clock read count and order therefore appear in expected test output.

## Terminology
- elapsed: the task's existing elapsed value. Absent if the task has not started. Otherwise the current time, or the stop time if stopped, minus the start time.
- finished time: the elapsed value recorded by a capture. Absent until captured. Zero is a valid captured value; "present" means not absent.
- capture: recording the finished time under the rules in Workflows.
- clear: setting the finished time back to absent.
- finished: true if and only if a finished time is present.

## Workflows
1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, the shown value is its finished time, and the column does not read elapsed.
   - Otherwise the shown value is the task's elapsed value, read exactly once during this render.
   - If the shown value is absent, output the placeholder "-:--:--" styled progress.elapsed.
   - Otherwise truncate the value to whole seconds, convert it as TimeRemainingColumn does, and style it progress.elapsed.
   - Set no refresh cap, unlike TimeRemainingColumn. Render on every call and cache nothing.
2. Capture on update. Progress update keeps its existing order: apply the given values, refresh if requested, read the current time, and do the sample bookkeeping. Then, as the last step inside the same lock: if completed is at least total and no finished time is present, read elapsed exactly once and store it. Add no separate check for whether elapsed is present; an absent value is stored as absent, leaving the task unfinished.
3. Capture on advance. Progress advance applies the same rule after it adds to completed and appends its sample, inside its lock. Its own time read happens before the lock, as in the base code.
4. Clearing. The task's internal reset clears the sample history and the finished time. Progress update calls this internal reset whenever a total is passed in, not only when the total changes. Progress reset also clears the finished time explicitly before refreshing; this is redundant and harmless. Start, stop, and stop_task neither capture nor clear. Progress reset with completed equal to total does not capture.
5. Total change. When update receives a total, the finished time is cleared first. Then completed is applied and the capture rule runs in the same call. The task is finished after that call only if completed is at or above the new total, and the captured value is the elapsed time at that call.
6. Completed lowered. Once captured, the finished time stays until a reset or an update that receives a total. Lowering completed does not clear it.
7. Creation. add_task does not capture, even if completed is at or above total. The task reports unfinished until the first update or advance that triggers the capture rule.

## Data model
- Task gains a public field finished_time: an optional number of seconds, default absent. Declare it as a plain defaulted field after the callable clock field and before the visibility flag, as in the reference. It is not excluded from initialization, so keyword callers are unaffected; callers that pass the visibility flag or later fields positionally are affected.
- Give it a short docstring stating that it holds the time the task was finished.
- The Task finished property changes from "completed is at least total" to "a finished time is present". It is read-only, returns a boolean, and its docstring describes this check in place of the old "completed" wording.
- Consumers inherit the new definition: the bar column's finished styling, Task.time_remaining (zero when finished), and Progress.finished.

## API contracts
- TimeElapsedColumn is a public class in the progress module, a subclass of the ProgressColumn base, exported the same way as TimeRemainingColumn. The module defines no export list.
- Its constructor takes no arguments. Its render method takes a task and returns a rich Text object styled progress.elapsed.
- Task.finished_time is a public, readable and writable attribute with the semantics in Terminology.
- Palette.__rich__ is a public method taking only the instance. It returns a rich Table with:
  - Three columns, in order: index, RGB, Color.
  - Title "Palette". Caption is the number of colors followed by " colors", right-justified. Highlighting enabled.
  - One row per palette color, in palette order.
  - Index cell: the index as a plain string, so the table's highlighting applies.
  - RGB cell: a plain string of the stored triplet's tuple text, three integers separated by comma and space, with no ColorTriplet type name or field names.
  - Color cell: a text object of 16 space characters with a background built from the stored triplet.
- Progress method signatures do not change.

## Module architecture
- The column class lives in rich/progress.py directly after the bar column and directly before TimeRemainingColumn.
- The column sets no refresh cap, inheriting the base default. It writes no state and reads only the public Task attributes finished, finished_time, and elapsed.
- Capture and clear logic lives in Progress update, advance, and reset, and in the Task's internal reset.
- The style default goes in rich/default_styles.py among the progress.* entries, with a yellow foreground.
- Palette.__rich__ lives in rich/palette.py. The palette module must not import the table, text, style, or color modules at module level, since the color module imports the palette data at module level and would create a cycle. Import those names inside the method, and use a type-checking-only import for the table annotation.

## Implementation constraints
- Clock reads are pinned by tests, because the test clock advances on every read:
  - Each column call performs one shared clock read in the base column call, before the render logic. The new render reads elapsed only when unfinished; a finished render reads no clock. No other reads and no caching.
  - Each capture reads elapsed exactly once, only when the rule fires, and stores that value directly.
  - In update, the capture is the last clock-related step. In advance, the capture's read comes after advance's own time read.
  - Do not change the order of existing reads in update, advance, or reset.
- Use the existing lock. Do not add a lock.

## Dependencies
- No new imports, packages, or configuration in rich/progress.py. The column uses the duration and text types already imported there.
- Palette.__rich__ uses the table, text, style, and color types through the lazy-import rule above.

## Naming
- Column: TimeElapsedColumn, matching TimeRemainingColumn. Style: progress.elapsed. Placeholder: "-:--:--", identical to TimeRemainingColumn's. Task field: finished_time. Palette method: __rich__.

## Documentation
- The column class has a one-line docstring. Its render method and Palette.__rich__ have short docstrings.
- CHANGELOG.md gets a new unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Reliability
- The finished time is captured at most once until cleared. Later updates and advances must not overwrite it.
- Capture happens inside the same lock as the state change it depends on, so readers never see a completed count without its captured value.
- An unstarted task never gets a finished time from update or advance, because the absent elapsed value is stored as absent. Add no separate guard.

## Compatibility
- The finished property change is intentional and matches the old definition in normal progression (completed rising to total, no reset). These reference behaviors must not be "fixed":
  - Lowering completed after a finish keeps the task finished.
  - An update that receives a total clears the finished time and recaptures in the same call if completed is at or above the new total.
  - add_task or reset with completed at or above total reports unfinished until an update or advance.
- Keyword-based Task construction is unaffected. No repository caller passes the visibility flag or later fields positionally.

## Behavioral acceptance criteria
- An unstarted task renders "-:--:--" with the progress.elapsed style.
- A started, unfinished task renders elapsed time as hours:minutes:seconds, truncated to whole seconds, and changes as time passes.
- When a task first reaches its total, its value freezes at the elapsed value at that moment, even while other tasks run. Example: a task reaching its total 10 seconds after starting keeps showing 0:00:10 while a still-running second task shows live time.
- Stopping a display or calling stop_task does not freeze a value. Progress reset clears the frozen value, and a reset task that is started again shows live time.
- By default the column text is yellow through the default styles table. A user theme can override it.
- The standard palette's __rich__ returns a table with 16 rows, one per color. Its RGB cells show the stored triplet's tuple text, and its index and RGB cells are plain strings.

## Test requirements
- Add a unit test for TimeElapsedColumn in the progress test module, following the pattern used for TimeRemainingColumn. Drive the task through public Progress update and advance calls with a controlled clock, never by assigning the finished time by hand. Check three states: unstarted (placeholder), running (live elapsed), and finished (value frozen, even after the clock advances).
- Update the existing test_columns integration test as one coupled change:
  - Add TimeElapsedColumn to its Progress column list immediately after TimeRemainingColumn, and import it with the other progress names.
  - Regenerate its expected output in the same patch, starting from the base expected output. Change only: (a) each row gains one progress.elapsed cell after the time-remaining cell and before the file-size cell; (b) bar widths shrink in every frame because the new column takes layout width; (c) clock-derived values (elapsed and speed) that shift from the extra clock reads. Elapsed cells for completed tasks show frozen values.
  - Every other character stays byte-identical to the base: escape and cursor sequences, line breaks, and padding inside styled spans. Padding inside a size span is the space the render adds to fill that column's width in that frame. Do not add, drop, or carry over padding by hand from a frame or row with a different column width.
  - Derive each clock-derived value by tracing clock reads in order, as in Implementation constraints. Do not estimate. A finished task's elapsed value is the value stored at its capture read and stays fixed. Trace each frame's reads before writing its cells.
  - If the test can run, run test_columns and confirm every difference from the base falls into (a), (b), or (c) before accepting the expected text. If it cannot run, say so in the final report and cite the trace used.
  - Make the column-list edit and the expected-output edit together. Afterward, verify the column list has the new column in position and every rendered row has one more cell than before. A column without matching expected cells, or the reverse, is a failure.
- Add tests/test_palette.py with one test, test_rich_cast. It imports the module-level standard palette object from rich._palettes, calls __rich__ on it with no arguments, and asserts the result is a Table with 16 rows. Do not wrap the palette in a new Palette; its constructor takes a sequence of triplets, and wrapping raises an error.
- Add no new test framework or fixture library.
