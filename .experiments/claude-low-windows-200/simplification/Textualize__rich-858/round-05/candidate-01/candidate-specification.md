## Goals
- Add Progress column TimeElapsedColumn showing running time as hours:minutes:seconds, truncated to whole seconds.
- When a task reaches its total, freeze its displayed value at the elapsed time recorded then.
- Add a __rich__ method to the palette class so the palette renders as a table.

## Scope
In scope:
- The new column, the finished-time value per task, the finished state derived from it, a default style entry, Palette.__rich__ with tests, and a changelog entry.

Out of scope:
- Signature changes to public methods, new dependencies, new clocks, or new public Progress methods.
- Unrelated edits such as exception chaining, comment cleanups, the version bump, and demo wiring.

## Assumptions
- Time comes from the task's existing clock through the existing elapsed calculation. No new time source is added.
- The test module's mock clock advances one unit per read, so the number and order of clock reads matter.

## Terminology
- elapsed: the task's existing elapsed value. Absent if the task has not started; otherwise the current time (or the stop time if stopped) minus the start time.
- finished time: the elapsed value recorded by a capture. Absent until captured. Zero is valid; "present" means not absent.
- capture: storing the finished time under the Workflows rules. Clear: setting it back to absent.
- finished: true if and only if a finished time is present.

## Workflows
1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, show its finished time and do not read elapsed.
   - Otherwise read elapsed exactly once and show it.
   - If the shown value is absent, output "-:--:--" styled progress.elapsed.
   - Otherwise truncate to whole seconds, convert as TimeRemainingColumn does, and style with progress.elapsed.
2. Capture on update. Progress update keeps its existing order: apply given values, refresh if requested, read the current time, do the sample bookkeeping. Then, as the last step inside the same lock, if completed is at least total and no finished time is present, read elapsed once and store it, even if absent.
3. Capture on advance. Progress advance applies the same rule after adding to completed and appending its sample, inside its lock. Its own time read stays before the lock.
4. Clearing. The task's internal reset clears the sample history and the finished time. Progress update calls this internal reset whenever a total is passed. Progress reset also clears the finished time explicitly before refreshing. Start, stop, and stop_task neither capture nor clear. Progress reset with completed equal to total does not capture.
5. Total change. An update that receives a total clears the finished time first, then applies completed and runs the capture rule.
6. Completed lowered. Lowering completed does not clear a captured finished time.
7. Creation. add_task never captures.

## Data model
- Task gains a public field finished_time: an optional number of seconds, default absent, with a short docstring like the other Task fields. Declare it as a plain defaulted field after the callable clock field and before the visibility flag, as in the reference. Positional callers passing later fields are affected; keyword callers are not.
- The Task finished property becomes "a finished time is present" instead of "completed is at least total". It stays read-only and returns a boolean.
- Consumers inherit this: the bar column's finished styling, Task.time_remaining (zero when finished), and Progress.finished.

## API contracts
- TimeElapsedColumn: public class in the progress module, subclass of the ProgressColumn base, exported like TimeRemainingColumn. No constructor arguments. Its render takes a task and returns a rich Text styled progress.elapsed.
- Task.finished_time: public, readable, and writable, with the semantics in Terminology.
- Palette.__rich__: public method taking only the instance, returning a rich Table:
  - Columns in order: index, RGB, Color. Title "Palette". Caption is the color count followed by " colors", right-justified. Highlighting enabled.
  - One row per palette color, in palette order.
  - Index cell: the index as a plain string.
  - RGB cell: plain string of the triplet, a parenthesized tuple of three integers separated by comma and space, without the ColorTriplet type name or field names.
  - Color cell: a text object of 16 spaces with a background built from the triplet.

## Module architecture
- The column class lives in rich/progress.py directly after the bar column and before TimeRemainingColumn. It sets no refresh cap, writes no state, reads only the public Task attributes finished, finished_time, and elapsed, and has a one-line docstring.
- The style default goes in rich/default_styles.py among the progress.* entries, with a yellow foreground.
- Palette.__rich__ lives in rich/palette.py. That module must not import table, text, style, or color modules at module level; the color module imports the palette data, creating a cycle. Import them inside the method, and import the table type for annotations only under type checking.
- CHANGELOG.md gets a new unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Implementation constraints
- Clock reads are pinned by tests, since the test clock advances on every read:
  - Each column call performs one shared clock read in the base column call, before render logic. A finished render reads no clock. The column adds no other reads.
  - Each capture reads elapsed exactly once, only when the rule fires, and stores that value directly.
  - In update, the capture is the last clock-related step. In advance, the capture's read comes after advance's own time read.
  - Do not change the order of existing reads in update, advance, or reset.
- Use the existing lock; do not add one. Capture inside it so readers never see a count without its captured value.
- The finished time is captured at most once until cleared.
- Add no imports, packages, or configuration to rich/progress.py beyond what it already uses.

## Compatibility
- In normal progression (completed rising to total, no reset) the new finished property matches the old one. These reference behaviors must not be "fixed":
  - Lowering completed after a finish keeps the task finished.
  - An update that receives a total recaptures in the same call if completed is at or above the new total.
  - add_task or reset with completed at or above total reports unfinished until an update or advance.

## Behavioral acceptance criteria
- An unstarted task renders "-:--:--" with the progress.elapsed style.
- A started, unfinished task renders elapsed time, changing as time passes.
- When a task first reaches completed at least total, its value freezes at the elapsed value then. A task reaching its total 10 seconds after starting shows 0:00:10.
- Progress reset clears the frozen value. A reset task that is started again shows live time.
- By default the column text is yellow; a user theme can override it.
- The standard palette's __rich__ returns a table with one row per color.

## Test requirements
- Add a unit test for TimeElapsedColumn in the progress test module, following the TimeRemainingColumn pattern. Drive the task through public update and advance calls with a controlled clock, not by assigning the finished time. Check unstarted, running, and finished (frozen) states.
- Update test_columns as one coupled change:
  - Add TimeElapsedColumn after TimeRemainingColumn in its column list, and import it with the other progress names.
  - Regenerate its expected output from the base. Change only: (a) each row gains one progress.elapsed cell, after the time-remaining cell and before the file-size cell; (b) bar widths shrink in every frame; (c) clock-derived values (elapsed and speed) that shift because of the extra clock reads.
  - Every other character stays byte-identical, including escape sequences and padding. Do not add or drop padding by hand.
  - Derive clock-derived values by tracing clock reads in order. A finished task's elapsed value is the value stored at its capture read and stays fixed in later frames.
  - If the test can be run, run test_columns and confirm every difference falls into category (a), (b), or (c). If it cannot be run, say so and cite the trace used.
- Add tests/test_palette.py with one test, test_rich_cast. It imports the module-level standard palette from rich._palettes, calls __rich__ with no arguments, and asserts a Table with 16 rows. Do not wrap the palette in a new Palette; the constructor takes a sequence of triplets.
- Add no new test framework or fixture library.
