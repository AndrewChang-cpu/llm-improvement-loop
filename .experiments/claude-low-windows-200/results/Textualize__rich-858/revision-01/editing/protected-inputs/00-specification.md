## Goals

- Add a progress display column, TimeElapsedColumn, that shows how long a progress task has been running in hours:minutes:seconds form, with whole seconds only.
- Once a task has finished, freeze the displayed elapsed value at the moment the task finished, so later rendering does not keep counting.
- Keep the column's look and placeholder consistent with the existing TimeRemainingColumn.

## Scope

In scope:
- The new column class in the progress module, next to TimeRemainingColumn.
- A completion-time value recorded on each progress task, set when the task first reaches its total and cleared on reset.
- A change to how the task's finished state is derived, so it follows the recorded completion-time value (see Data model).
- A default theme style entry for the column's text.
- Tests and a changelog entry.

Out of scope:
- Changes to Progress.start_task, Progress.stop, Progress.stop_task, or any other public method signature.
- Changes to other columns beyond the effects of the finished-state change described under Compatibility.
- New dependencies, new clocks, or new public Progress methods.

## Assumptions

- Time is read from the task's existing clock through the existing elapsed calculation. No new time source is introduced.
- Existing column rendering and refresh behavior stay as they are in the base code.

## Terminology

- **elapsed**: the task's existing elapsed value. It is absent (None) if the task has not started. Otherwise it is the current time, or the stop time if the task was stopped, minus the start time.
- **finished time** (finished_time): the elapsed value captured once, at the moment the task first reaches completed greater than or equal to total. It is absent (None) until captured.
- **finished**: true if and only if a finished time has been captured.
- **latch**: a value that is set once and then left unchanged until it is explicitly cleared.

## Workflows

1. Rendering. When TimeElapsedColumn renders a task:
   - If the task is finished, the value shown is the task's finished time. Otherwise the value shown is the task's elapsed value.
   - If the value shown is absent, the column outputs the placeholder "-:--:--" styled with the progress.elapsed style.
   - Otherwise, the value is truncated to whole seconds and formatted as an hours:minutes:seconds duration, styled with the progress.elapsed style.
   - The column may apply a refresh cap, but it is not required to.
2. Capturing the finished time on update. In the update operation of the progress object, after the task's values and speed samples are applied, and still inside the same lock: if the task's completed value is at least its total and no finished time is recorded, record the task's current elapsed value as the finished time. If the elapsed value is absent (task not started), nothing is recorded.
3. Capturing the finished time on advance. The advance operation applies the same rule after it adds to completed and records its sample.
4. Clearing. Clearing the finished time happens in two places: the task's internal reset, which runs when update changes the total, and the progress object's reset operation, which clears it explicitly before refreshing. Starting, stopping, or stopping a single task does not capture or clear the finished time.
5. Effect on completion. Because the finished state now follows the captured finished time, a task that has been completed remains finished even if its completed value is later lowered, until it is reset or its total is changed and it is not yet at or above that total.

## Data model

- Task has a new public field, the finished time, holding an optional number of seconds with a default of absent. Place it after the callable clock field and before the visibility flag, so existing positional arguments keep their meaning. It has a short docstring in the same style as the other fields.
- The Task finished property changes from "completed is at least total" to "a finished time has been captured." The property is read-only and returns a boolean.
- Consumers of the finished property inherit the new definition. These include the bar column's finished text, the task's time-remaining estimate (which returns zero when finished), and the progress object's all-tasks-finished check.

## API contracts

- TimeElapsedColumn is a public class in the progress module and a subclass of the existing ProgressColumn base. It is exported in the same way as TimeRemainingColumn.
- Its constructor takes no arguments.
- Its rendering method takes a task and returns a rich Text object.
- The style name it applies is progress.elapsed.
- The new Task field is a public, readable and writable attribute with the semantics in Terminology.
- Progress method signatures do not change.

## Module architecture

- The column class lives in rich/progress.py, placed between the bar column and TimeRemainingColumn.
- Capturing and clearing the finished time belongs to the progress object's update, advance and reset operations, and to the task's internal reset. The column itself does not write any state.
- The column reads only public task attributes (elapsed, finished, finished time). It must not read progress-object internals.
- The style default must be registered in the default styles table in rich/default_styles.py, inside the progress group next to progress.remaining, with a yellow foreground. Without this registration, the column text is unstyled and cannot be themed by default.

## Dependencies

- No new imports, packages, or configuration. The column uses the duration type and the text type already imported by rich/progress.py.

## Naming

- Class name: TimeElapsedColumn, matching the TimeRemainingColumn naming.
- Style name: progress.elapsed, matching the existing progress.<name> style family.
- Placeholder: "-:--:--", identical to TimeRemainingColumn's placeholder.

## Documentation

- The column class has a one-line docstring. The render method has a short docstring. The Task field has a docstring stating that it holds the time the task was finished.
- CHANGELOG.md gets a new unreleased section with an Added entry naming Progress.TimeElapsedColumn.

## Reliability

- The finished time is captured at most once per task until it is cleared. Later updates and advances must not overwrite a captured value.
- Capture happens inside the same lock as the state change it depends on, so readers never see a completed count without the matching captured value.
- A task that has not started never gets a finished time from update or advance.

## Compatibility

- The change to the finished property is intentional. In normal progression (completed rising to total, no reset) its result matches the old definition. It differs only when a task has been completed and then its completed value is lowered, or when its total is changed, and those cases follow the latch rules in Workflows.
- Existing code that constructs Task objects with keyword arguments is unaffected. The new field has a default.

## Behavioral acceptance criteria

- An unstarted task renders "-:--:--" with the progress.elapsed style.
- A started, unfinished task renders its elapsed time as hours:minutes:seconds with whole seconds, truncated, and the value changes as time passes.
- When a task first reaches completed at least equal to total, its displayed value freezes at the elapsed value at that moment. It does not change on later renders, even while other tasks keep running and the display stays active.
- Example: a task that reaches its total 10 seconds after it started keeps showing 0:00:10 afterward, while a second task still running continues to show its live time.
- Stopping a progress display, or calling stop on a single task, does not freeze a task's value. Only reaching the total does.
- Progress reset clears the frozen value; a reset task that is started again shows live time.
- By default, the column's text is styled yellow through the default styles table. A user theme can override it.

## Test requirements

- Add a unit test for TimeElapsedColumn in the progress test module, following the existing per-column test pattern used for TimeRemainingColumn. It uses a task with a controlled clock and checks three states: unstarted (placeholder), running (live elapsed), and finished (value frozen at the finished time, even when the clock has advanced further).
- Add TimeElapsedColumn to the existing column-list integration test and update that test's expected output so the elapsed cell appears with the progress.elapsed style and the frozen values for completed tasks.
- Do not add a new test framework or fixture library.
