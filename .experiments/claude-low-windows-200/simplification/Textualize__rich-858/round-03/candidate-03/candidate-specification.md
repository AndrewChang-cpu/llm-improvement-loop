## Goals

- Add TimeElapsedColumn, a progress column showing how long a task has been running as hours:minutes:seconds, truncated to whole seconds.
- When a task reaches its total, freeze its displayed value at the elapsed time recorded at that moment.
- Format the placeholder and duration consistently with TimeRemainingColumn.
- Add a __rich__ method to the palette class so the palette renders as a table.

## Scope

In scope:
- The new column in the progress module, next to TimeRemainingColumn.
- A finished-time value on each task, captured and cleared by Progress methods as described in Workflows.
- Deriving a task's finished state from that value.
- A default style entry for the column text.
- Palette.__rich__, its tests, and a changelog entry.

Out of scope:
- Signature changes to any public method.
- New dependencies, clocks, or public Progress methods.
- Unrelated edits, such as markup and docstring cleanups, the console size pragma, docs fixes, the version bump, demo wiring, and the color demo block.

## Assumptions

- Time comes from the task's existing clock through the existing elapsed calculation. No new time source is added.
- The test module's mock clock returns its current value and advances one unit per call while automatic mode is on, so the number and order of clock reads matter.

## Terminology

- elapsed: the task's existing elapsed value. Absent if the task has not started. Otherwise the current time, or the stop time if stopped, minus the start time.
- finished time: the elapsed value recorded by a capture. Absent until captured. Zero is a valid captured value; "present" means not absent.
- capture: recording the finished time under the rules in Workflows.
- finished: true if and only if a finished time is present.

## Workflows

1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, show its finished time and do not read elapsed.
   - Otherwise show the task's elapsed value, read exactly once during this render.
   - If the shown value is absent, output the placeholder "-:--:--" styled with progress.elapsed.
   - Otherwise truncate to whole seconds, convert with the same conversion TimeRemainingColumn uses, and style with progress.elapsed.
   - Unlike TimeRemainingColumn, set no refresh cap. Render on every call and cache nothing.
2. Capture on update. Progress update keeps its existing order: apply the given values, refresh if requested, read the current time, and do the sample bookkeeping. Then, as the last step inside the same lock, if completed is at least total and no finished time is present, read elapsed exactly once and store it. Do not check whether elapsed is present; an absent value is stored as absent, leaving the task unfinished.
3. Capture on advance. Progress advance applies the same rule after it adds to completed and appends its sample, inside its lock. Its own time read stays before the lock, as in the base code.
4. Clearing. The task's internal reset clears the sample history and the finished time. Progress update calls this internal reset whenever a total is passed in. Progress reset also clears the finished time explicitly before refreshing. Start, stop, and stop_task neither capture nor clear. Progress reset with completed equal to total does not capture.
5. Total change. When update receives a total, the finished time is cleared first, then the capture rule runs in the same call with the new total. The task is finished afterward only if completed is at or above the new total.
6. Completed lowered. Lowering completed does not clear the finished time. Only a reset or an update that receives a total clears it.
7. Creation. add_task does not capture, even if completed is at or above total. Such a task reports unfinished until the first update or advance that triggers the capture rule.

## Data model

- Task gains a public field finished_time: an optional number of seconds, default absent. Declare it as a plain defaulted field after the callable clock field and before the visibility flag, as in the reference. Positional callers that pass the visibility flag or later fields are affected; keyword callers are not.
- Give it a short docstring in the style of the other Task fields.
- The Task finished property changes from "completed is at least total" to "a finished time is present". It is read-only, returns a boolean, and its docstring describes the new check.
- Consumers inherit the new definition: the bar column's finished styling, Task.time_remaining (zero when finished), and Progress.finished.

## API contracts

- TimeElapsedColumn is a public class in the progress module, a subclass of the existing ProgressColumn base, and exported the same way as TimeRemainingColumn. Its constructor takes no arguments. Its render method takes a task and returns a rich Text object styled progress.elapsed.
- Task.finished_time is public, readable, and writable.
- Palette.__rich__ is a public method taking only the instance and returning a rich Table with:
  - Three columns in order: index, RGB, Color.
  - Title "Palette". Caption is the number of colors followed by " colors", right-justified. Highlighting enabled.
  - One row per palette color, in palette order.
  - Index cell: the index as a plain string, so table highlighting applies.
  - RGB cell: a plain string holding the stored triplet's text form, a parenthesized tuple of three integers separated by comma and space. It must not show the ColorTriplet type name or its field names.
  - Color cell: a text object of 16 space characters with a background built from the stored triplet.
- Progress method signatures do not change.

## Module architecture

- The column class lives in rich/progress.py directly after the bar column and before TimeRemainingColumn. It sets no refresh cap, writes no state, and reads only the public Task attributes finished, finished_time, and elapsed. It adds no imports.
- Capture and clear logic lives in Progress update, advance, and reset, and in the Task's internal reset.
- The style default goes in rich/default_styles.py among the progress.* entries, with a yellow foreground.
- Palette.__rich__ lives in rich/palette.py. The palette module must not import the table, text, style, or color modules at module level, because the color module imports the palette data at module level and a top-level import would create a cycle. Import those names inside the method, and use a type-checking-only import for the table annotation.

## Implementation constraints

- Clock reads are pinned by tests, because the test clock advances on every read:
  - Each column call performs one shared clock read in the base column call, before the column's render logic. A finished render reads no clock. The column adds no other reads and no caching.
  - Each capture reads elapsed exactly once, only when the rule fires, and stores that value directly.
  - In update, the capture is the last clock-related step. In advance, the capture's read comes after advance's own time read.
  - Do not change the order of existing reads in update, advance, or reset.
- Use the existing lock. Do not add a lock. The finished time is captured at most once until cleared, and capture happens inside the same lock as the state change it depends on.

## Documentation

- The column class has a one-line docstring; its render method and Palette.__rich__ each have a short docstring.
- CHANGELOG.md gets a new unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Compatibility

- Keep these reference behaviors; do not "fix" them:
  - Lowering completed after a finish keeps the task finished.
  - An update that receives a total clears the finished time and recaptures in the same call if completed is at or above the new total.
  - add_task or reset with completed at or above total reports unfinished until an update or advance.
- Changes to other columns are limited to these effects.

## Behavioral acceptance criteria

- An unstarted task renders "-:--:--" with the progress.elapsed style. A started, unfinished task renders live elapsed time as hours:minutes:seconds.
- A task reaching completed at least total freezes at the elapsed value at that moment, even while other tasks run. Example: a task reaching its total 10 seconds after starting keeps showing 0:00:10 while a still-running second task shows live time.
- Stopping a progress display or calling stop_task does not freeze a value. Progress reset clears the frozen value, and a reset task that is started again shows live time.
- By default the column text is yellow through the default styles table; a user theme can override it.
- The standard palette's __rich__ returns a table with 16 rows, one per color. Each RGB cell shows the stored triplet's tuple text, and the index and RGB cells are plain strings.

## Test requirements

- Add a unit test for TimeElapsedColumn in the progress test module, following the per-column pattern used for TimeRemainingColumn. Drive the task through public Progress update and advance calls with a controlled clock, not by assigning the finished time. Check three states: unstarted (placeholder), running (live elapsed), and finished (frozen even after the clock advances).
- Update test_columns as one coupled change, in the same patch:
  - Add TimeElapsedColumn to its column list immediately after TimeRemainingColumn, and import it with the other progress names.
  - Regenerate its expected output from the base expected output. Change only: (a) each row gains one progress.elapsed cell, after the time-remaining cell and before the file-size cell; (b) bar widths shrink in every frame because the new column takes layout width; (c) clock-derived values (elapsed and speed) that shift because of the extra clock reads.
  - Every other character stays byte-identical to the base, including escape sequences and line breaks. Padding inside a size span is what the render adds to fill that column's width in that frame. Do not add or drop padding by hand, and do not carry it from a frame or row with a different column width.
  - Derive each clock-derived value by tracing clock reads in order, as in Implementation constraints. Do not estimate. A finished task's elapsed value is the value stored at its capture read and stays fixed in later frames. Trace each frame's reads before writing its cells.
  - If the test can be run, run test_columns and confirm every difference from the base falls into category (a), (b), or (c). If it cannot be run, say so in the final report and cite the trace used.
  - Afterward, verify the column list has the new column in position and every rendered row has one more cell than before.
- Add tests/test_palette.py with one test, test_rich_cast. It imports the module-level standard palette object from rich._palettes, calls __rich__ directly on it with no arguments, and asserts the result is a Table with 16 rows. Do not wrap the palette in a new Palette; its constructor takes a sequence of color triplets.
- Add no new test framework or fixture library.
