## Goals

- Add a Progress column, TimeElapsedColumn, showing a task's running time as hours:minutes:seconds, truncated to whole seconds.
- When a task reaches its total, freeze its displayed value at the elapsed time recorded then.
- Keep the placeholder and duration format consistent with TimeRemainingColumn.
- Make the palette class render as a table through a __rich__ method.

## Scope

In scope:
- The new column, a finished-time value on each task, capture and clear logic in Progress, a default style entry, Palette.__rich__ with tests, and a changelog entry.

Out of scope:
- Signature changes to public methods, new dependencies, new clocks, or new public Progress methods.
- Unrelated edits such as markup exception chaining, comment cleanups, version bump, and demo wiring.

## Assumptions

- Time comes from the task's existing clock through the existing elapsed calculation. Existing rendering and refresh behavior stay as in the base code.
- The test mock clock returns its current value and advances one unit per read, so the number and order of clock reads matter.

## Terminology

- elapsed: the task's existing elapsed value. Absent if the task has not started. Otherwise the current time (or the stop time if stopped) minus the start time.
- finished time: the elapsed value recorded by a capture. Absent until captured. Zero is valid; "present" means not absent.
- capture: recording the finished time under the Workflows rules. Clear: setting it back to absent.
- finished: true if and only if a finished time is present.

## Workflows

1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, show its finished time and do not read elapsed.
   - Otherwise show elapsed, read exactly once during this render.
   - If the shown value is absent, output "-:--:--" styled progress.elapsed.
   - Otherwise truncate to whole seconds, convert with the conversion TimeRemainingColumn uses, and style with progress.elapsed.
   - Set no refresh cap, and cache nothing.
2. Capture on update. Progress update keeps its existing order: apply given values, refresh if requested, read the current time, do sample bookkeeping. Then, as the last step inside the same lock, if completed is at least total and no finished time is present, read elapsed exactly once and store it. An absent value is stored as absent.
3. Capture on advance. Progress advance applies the same rule after adding to completed and appending its sample, inside its lock. Its own time read stays before the lock.
4. Clearing. The task's internal reset clears the sample history and the finished time. Progress update calls it whenever a total is passed. Progress reset clears the finished time explicitly before refreshing. Start, stop, and stop_task neither capture nor clear. Progress reset with completed equal to total does not capture.
5. Total change. When update receives a total, the finished time is cleared first, then completed is applied and the capture rule runs in the same call. The task is finished afterward only if completed is at or above the new total.
6. Lowering completed. Once captured, the finished time stays until a reset or an update that receives a total.
7. Creation. add_task does not capture, even if completed is at or above total.

## Data model

- Task gains a public field finished_time: an optional number of seconds, default absent. Declare it as a plain defaulted field after the callable clock field and before the visibility flag, as in the reference. Positional callers passing the visibility flag or later fields are affected; keyword callers are not.
- Give it a short docstring in the style of the other Task fields.
- The Task finished property becomes "a finished time is present". It stays read-only and returns a boolean.
- Consumers inherit the new definition: the bar column's finished styling, Task.time_remaining, and Progress.finished.

## API contracts

- TimeElapsedColumn is a public class in the progress module, a subclass of ProgressColumn, exported like TimeRemainingColumn. Its constructor takes no arguments. Its render method takes a task and returns a rich Text object styled progress.elapsed.
- Task.finished_time is public, readable, and writable.
- Palette.__rich__ is a public method taking only the instance and returning a rich Table:
  - Three columns in order: index, RGB, Color. Title "Palette". Caption is the number of colors followed by " colors", right-justified. Highlighting enabled.
  - One row per palette color, in palette order.
  - Index cell: the index as a plain string.
  - RGB cell: a plain string of the triplet's text form, a parenthesized tuple of three integers separated by comma and space, without the ColorTriplet type name or field names.
  - Color cell: a text object of 16 space characters with a background built from the stored triplet.
- Progress method signatures do not change.

## Module architecture

- The column class lives in rich/progress.py directly after the bar column and before TimeRemainingColumn. It sets no refresh cap, writes no state, reads only the public Task attributes finished, finished_time, and elapsed, and has a one-line docstring.
- Capture and clear logic lives in Progress update, advance, and reset, and in the Task's internal reset.
- The style default goes in rich/default_styles.py among the progress.* entries, with a yellow foreground.
- Palette.__rich__ lives in rich/palette.py. That module must not import table, text, style, or color modules at module level, because the color module imports the palette data at module level and that creates a cycle. Import those names inside the method, and use a type-checking-only import for the table annotation.
- CHANGELOG.md gets an unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Implementation constraints

- Clock reads are pinned by tests, because the test clock advances on every read:
  - Each column call performs one shared clock read in the base column call, before render logic. A finished render reads no clock. The column adds no other reads.
  - Each capture reads elapsed exactly once, only when the rule fires, and stores that value directly.
  - In update, the capture is the last clock-related step. In advance, the capture's read comes after advance's own time read.
  - Do not change the order of existing reads in update, advance, or reset.
- Use the existing lock; do not add one. Capture happens inside it, so readers never see a completed count without its captured value.
- The finished time is captured at most once until cleared.
- Add no imports to rich/progress.py.

## Compatibility

- In normal progression (completed rising to total, no reset), the new finished property matches the old definition. These behaviors must not be "fixed":
  - Lowering completed after a finish keeps the task finished.
  - An update that receives a total clears and recaptures in the same call if completed is at or above the new total.
  - add_task or reset with completed at or above total reports unfinished until an update or advance.

## Behavioral acceptance criteria

- An unstarted task renders "-:--:--" with the progress.elapsed style.
- A started, unfinished task renders live elapsed time.
- When a task first reaches completed at least total, its value freezes at the elapsed value at that moment. Example: a task reaching its total 10 seconds after starting keeps showing 0:00:10.
- Stopping a display or calling stop_task does not freeze a value.
- Progress reset clears the frozen value. A reset task that is started again shows live time.
- By default the column text is yellow; a user theme can override it.
- The standard palette's __rich__ returns a table with 16 rows.

## Test requirements

- Add a unit test for TimeElapsedColumn in the progress test module, following the TimeRemainingColumn pattern. Drive the task through public Progress update and advance calls with a controlled clock, not by assigning the finished time. Check unstarted (placeholder), running (live elapsed), and finished (frozen after the clock advances).
- Update test_columns as one coupled change:
  - Add TimeElapsedColumn to its column list immediately after TimeRemainingColumn, and import it with the other progress names.
  - Regenerate its expected output from the base expected output. Change only: (a) each row gains one progress.elapsed cell after the time-remaining cell and before the file-size cell; (b) bar widths shrink in every frame because the new column takes layout width; (c) clock-derived values (elapsed and speed) that shift because of the extra clock reads.
  - Every other character stays byte-identical to the base, including escape sequences and padding inside styled spans. Do not add or drop padding by hand, and do not carry padding from a frame or row with a different column width.
  - Derive each clock-derived value by tracing clock reads in order. A finished task's elapsed value is the value stored at its capture read and stays fixed in later frames.
  - If test_columns can run, run it and confirm every difference falls into (a), (b), or (c) before accepting the expected text. If it cannot run, say so in the final report and cite the trace used.
  - Verify afterward that the column list has the new column in position and every rendered row has one more cell than before.
- Add tests/test_palette.py with one test, test_rich_cast. It imports the module-level standard palette from rich._palettes, calls __rich__ directly, and asserts the result is a Table with 16 rows. Do not wrap the palette in a new Palette; its constructor takes a sequence of triplets and wrapping raises an error.
- Add no new test framework or fixture library.
