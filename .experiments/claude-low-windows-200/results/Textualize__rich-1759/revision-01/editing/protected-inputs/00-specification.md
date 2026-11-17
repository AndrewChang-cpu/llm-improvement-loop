## Goals
- Let callers see progress while bytes are read from a file, so a long consumer such as a JSON or CSV parser shows how far through its input it is.
- Provide two public entry points at module level in rich.progress and two methods on Progress:
  - open: takes a path (str, path-like object, or bytes) and returns a reader that counts bytes consumed. Text mode is the default; binary mode is selected with 'rb'.
  - wrap_file: takes an already-open binary file-like object and returns a reader that counts bytes consumed without closing the caller's file.
- The module-level functions create and manage their own Progress display for one-call use. The Progress methods attach a reader to an existing Progress and task.
- The public contract is the names open and wrap_file. Do not expose any public function or method named read for this feature. Earlier drafts that named read are superseded by the reference.

## Scope
- In scope:
  - rich/progress.py: a private reader class, a private context wrapper, two module-level functions, and two Progress methods.
  - tests/test_progress.py: new tests for the feature.
  - docs/source/progress.rst: new sections on reading from a file and from a file-like object.
  - CHANGELOG.md: one entry under Unreleased, Added.
- Out of scope: changes to track(), Progress rendering, the Task fields, column classes, or rich/__init__.py exports. No public names beyond the four entry points.
- Edits must be additive. Do not delete or alter existing code.

## Assumptions
- Target the Python versions the project already declares (3.6 and newer). Use only syntax available on those versions.
- typing_extensions is already a declared dependency for Python below 3.9. Use it only in the same version-gated way the other rich modules use it, for Literal on older interpreters.
- A caller passing a file-like object must supply total, unless the task passed in already has a total. The feature does not infer a total for file-like objects.
- Bytes are the unit for total and completed.

## Terminology
- Path input: a str, a path-like object, or bytes naming a file to open.
- File-like input: an already-open binary file object supplied by the caller.
- Reader: the object returned to the caller. It wraps a binary handle and advances a task as bytes are consumed. The reader class is private; callers only receive instances.
- Reader-owned handle: a handle the feature opened from a path. Closing the reader closes it.
- Caller-owned handle: a file-like input. Closing the reader must not close it.
- Text mode: modes 'r' and 'rt'. Binary mode: 'rb' (the letters may be given in either order).
- Task total: the total field of a progress task, in bytes.
- Context wrapper: a private helper returned by the module-level functions. It starts and stops the Progress and enters and exits the reader.

## Workflows
Module-level open (file, mode, buffering, encoding, errors, newline, total, description, and display options):
1. Build columns the way track() builds a bar display: a description text column only when description is non-empty, a bar column carrying the style options, a byte-count download column, and a time-remaining column.
2. Create a Progress from those columns and the display options (auto refresh, console, transient, time source, disable). The refresh rate falls back to 10 when the given value is falsy.
3. Ask that Progress for a reader through its open method, passing file, mode, buffering, encoding, errors, newline, total, and description. The display is not started at this point.
4. Return a context wrapper. On enter, start the Progress, enter the reader, and yield it. On exit, stop the Progress first, then exit the reader.

Module-level wrap_file (file, total, description, display options):
- Build the Progress the same way, obtain the reader from the Progress wrap_file method, and return a context wrapper that yields a binary reader.

Progress.open (file, mode defaulting to 'r', buffering, encoding, errors, newline, total, task_id, description):
1. Normalize mode by sorting its letters. Accept only 'r', 'rt', and 'rb' (and 'br'). Any other value raises ValueError that names the mode.
2. Buffering: in binary mode, a buffering value of 1 emits a RuntimeWarning saying the default buffer size is used, and buffering is reset to the default. In text mode, buffering 0 is an error. In text mode, buffering 1 requests line buffering on the text wrapper, and the byte handle uses the default buffering.
3. Total: if none is given, use the size in bytes that the file system reports for the path.
4. Task: if task_id is None, add a task with description and total. Otherwise update that task's total to the resolved total. Progress.open does not start the Progress.
5. Open the path in binary mode with the resolved buffering. Wrap the handle in a reader that owns it.
6. In text mode, wrap the reader in a standard text wrapper with encoding, errors, newline, and line buffering, and return the wrapper. In binary mode, return the reader.

Progress.wrap_file (file, total optional, task_id optional, description):
1. Resolve total. An explicit total wins. Otherwise, if task_id is given, use that task's current total. If neither yields a value, raise ValueError.
2. If task_id is None, add a task with description and the resolved total. Otherwise update that task's total to the resolved total.
3. Return a binary reader that wraps file as a caller-owned handle.

Reader behavior (all readers):
- Byte accounting: each read operation advances the task by the number of bytes actually returned. This covers read, readline, readinto, readlines (the sum of the line lengths), and iteration (the length of each yielded line).
- seek(offset, whence): delegate to the handle. After it succeeds, set the task's completed value to the returned absolute position through the Progress public update operation. Return that position.
- tell: return the handle's own position. Do not keep a separate counter.
- readable, seekable, fileno, isatty: delegate to the handle. writable: false. write: refuse with the standard unsupported-operation error, naming 'write'.
- close: close the handle only if the reader owns it. Always mark the reader closed. The closed property reports that marker, not the handle's state.
- Entering the reader enters the handle and returns the reader. Exiting the reader closes it.
- Iteration returns the reader itself, and each step yields the next line of the handle.
- The wrapped handle is exposed as a public attribute named handle so callers can inspect it.

Lifecycle:
- open and wrap_file calls never start the live display. The display starts only when the module-level context is entered. If an error happens before entering, nothing is started and nothing needs cleanup.

## Data model
- Reader state: the wrapped handle, the owning Progress, the task identifier, a flag saying whether the reader closes the handle, and a closed marker. No other per-reader state. The byte position comes from the handle.
- Task state: use the existing total and completed fields. The feature adds no fields to Task or Progress and stores no data outside memory.
- The text wrapper, when used, is the standard library text wrapper around the reader. It is not a separate type introduced by this feature.

## API contracts
- Public names: the module-level open and wrap_file in rich.progress, and the open and wrap_file methods on Progress. Nothing else is public. The reader class and the context wrapper are private, with underscore-prefixed names.
- Module-level open, positional parameters in this order: file (str, path-like, or bytes); mode, default 'r'; buffering, default -1; encoding, optional; errors, optional; newline, optional. Keyword-only parameters after these: total (optional integer, bytes); description, default 'Reading...'; auto_refresh, default true; console, optional; transient, default false; get_time, optional; refresh_per_second, default 10; style, default 'bar.back'; complete_style, default 'bar.complete'; finished_style, default 'bar.finished'; pulse_style, default 'bar.pulse'; disable, default false.
  - Returns a context manager. It yields a text reader for 'r' and 'rt', and a binary reader for 'rb'.
- Module-level wrap_file: file (binary file-like object); total (required integer, bytes, may be given by keyword). Keyword-only parameters after total: description, auto_refresh, console, transient, get_time, refresh_per_second, style, complete_style, finished_style, pulse_style, disable, with the same defaults as open. Returns a context manager that yields a binary reader.
- Progress.open: file, mode default 'r', buffering default -1, encoding, errors, newline. Keyword-only after these: total (optional integer), task_id (optional), description default 'Reading...'. Returns a binary reader for 'rb', or a text wrapper for 'r' and 'rt'. It does not return a context manager; the caller uses the result in a with statement.
- Progress.wrap_file: file (binary file-like object); total (optional integer); keyword-only task_id (optional) and description default 'Reading...'. Returns a binary reader.
- Type-level overloads: binary mode returns the binary type and text modes return the text type, for both open entry points.
- total is an integer count of bytes, never a float.
- Return annotations must describe the object actually returned. The reader must implement the standard raw I/O base class and the binary file interface, so type checkers and the text wrapper accept it.

## Module architecture
- All code changes are in rich/progress.py. Place the private reader class and context wrapper with the other progress helpers. Place the module-level functions beside track(). Place the Progress methods in the Progress class next to track().
- Progress.open and Progress.wrap_file own the file, total, and task logic. The module-level functions only build a Progress with the display options and delegate. They must not duplicate file handling.
- The reader uses only the public Progress methods for adding a task, advancing, and updating. It must not read or write Progress internals such as the task table or its lock.
- The context wrapper alone owns the ordering of start and stop.

## Implementation constraints
- Implement every read-side method explicitly on the reader: read, readline, readinto, readlines, iteration, seek, and tell. Do not add a catch-all attribute forwarder that can bypass byte accounting or let writes through. Other attributes come from the base classes.
- Do not hide type mismatches with ignore comments. Fix the declared type. Use an ignore comment only where the reference uses one for the same construct.
- Do not start the Progress inside open or wrap_file.
- Track() and existing Progress behavior must not change.

## Dependencies
- Standard library only: io, os, warnings, typing, and contextlib if needed. Existing rich imports in progress.py are reused. Do not add new rich module imports.
- No new third-party packages and no project metadata changes.
- Literal, if imported, uses the same version-gated import pattern as the other rich modules.

## Naming
- Public: open and wrap_file, both module-level and as Progress methods. The name read is not a public name for this feature.
- Private: the reader class and the context wrapper, each with a leading underscore.
- Parameter names: file, mode, buffering, encoding, errors, newline, total, task_id, description, and the display options spelled exactly as in track() and Progress.__init__.
- Mode values are the strings 'r', 'rt', and 'rb'.

## Validation
- Mode: must normalize to one of 'r', 'rt', 'rb'. Validated before any file is opened or any task is created.
- Buffering: validated as described under Workflows and Error handling.
- Total: an integer count of bytes. Path input defaults to the file size. File-like input requires an explicit total or a task that already has one.
- task_id: when supplied, it refers to an existing task. Use the Progress's existing task lookup behavior.

## Error handling
- Invalid mode: ValueError whose message includes the offending value.
- Text mode with buffering 0: ValueError.
- Binary mode with buffering 1: emit RuntimeWarning stating that line buffering is not supported in binary mode and the default buffer size is used. Continue with default buffering.
- Total cannot be determined: ValueError whose message says the number of bytes could not be determined and that total must be specified.
- write on a reader: raise the standard unsupported-operation error naming 'write'.
- Exceptions raised by the underlying handle propagate unchanged. Do not swallow them.
- An error before the module-level context is entered leaves no display running. An error inside the context stops the display and exits the reader, then propagates.

## Documentation
- docs/source/progress.rst: add a section on reading from a file. Cover Progress.open with a path, the default text mode compared with 'rb', and that the default total is the file size. Add a section on reading from a file-like object. Cover Progress.wrap_file: binary only, total required unless a task with a total is given, and the reader does not close the wrapped file.
- Use only the names open and wrap_file in the documentation. An earlier reference paragraph names a read function that the reference code does not define, so do not repeat it.
- Docstrings for the four public entry points and the reader use the Google style with Args, Returns, and Raises sections, matching track(). Describe total as a count of bytes, and state the default description.
- CHANGELOG.md: add one entry under Unreleased, Added, in the format of the neighboring entries.

## Maintainability
- Format with black at its default line length of 88. Order imports as isort does with the black profile. Within the standard library block, plain imports come before from-imports.
- Keep file-handling logic in one place (Progress.open and Progress.wrap_file).

## Reliability
- The display starts on context entry and always stops on context exit, including when the body raises.
- Exiting a reader closes a reader-owned handle and leaves a caller-owned handle open.

## Compatibility
- Purely additive. Existing names, track(), Progress, Task, and column classes keep their behavior.
- Use syntax no newer than the project's declared minimum Python version.

## Behavioral acceptance criteria
- Module-level open on a path with default mode returns text: read() returns a str equal to the file contents, and after the with block the reader reports closed.
- Explicit mode 'r' behaves the same way.
- Mode 'rb' returns bytes.
- Progress.open on a path with no total sets the task total to the file size in bytes.
- Module-level wrap_file on a caller-owned binary file returns bytes. After the context exits, the reader reports closed, the caller's file is still open, and the caller's own with block closes it.
- Progress.wrap_file with an existing task that has a total, and no total argument, reads correctly, and the task's completed value equals the bytes read.
- Each read path (read, readline, readinto, readlines, iteration) advances completed by exactly the number of bytes returned.
- seek to a position p sets completed to p. tell returns the handle's position.
- write raises the unsupported-operation error.
- File-like input with no total and a task without a total raises ValueError, and no display is started.
- Invalid mode raises ValueError. Text mode with buffering 0 raises ValueError.
- Binary mode with buffering 1 emits RuntimeWarning, and reading still succeeds.

## Test requirements
- Add tests to tests/test_progress.py in the file's existing style: each test annotated to return None, temporary files removed in a finally block, and a Console writing to an in-memory stream with forced terminal output as existing tests do.
- Cover at least: module-level open with default mode, module-level open with explicit 'r', module-level wrap_file with a caller-owned file, and Progress.wrap_file reusing an existing task's total.
- Cover the behavioral acceptance criteria where practical.
- New test code follows the repo's line-length limit.
