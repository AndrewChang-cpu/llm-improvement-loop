## Goals
- Let callers see progress while bytes are read from a file, so a long consumer such as a JSON or CSV parser can show how far through its input it is.
- Provide two public entry points at module level in rich.progress and two methods on Progress:
  - open: takes a path (str, path-like object, or bytes) and returns a reader that counts bytes consumed. Text mode is the default; binary mode is selected with 'rb'.
  - wrap_file: takes an already-open binary file-like object and returns a reader that counts bytes consumed without closing the caller's file.
- The module-level functions create and manage their own Progress display for one-call use. The Progress methods attach a reader to an existing Progress and task.
- The public names are open and wrap_file only. Do not expose a public read function or method for this feature.

## Scope
- In scope:
  - rich/progress.py: a private reader class, a private context wrapper, two module-level functions, and two Progress methods.
  - tests/test_progress.py: new tests for the feature.
  - docs/source/progress.rst: new subsections on reading from a file and from a file-like object.
  - CHANGELOG.md: one entry under Unreleased, Added.
- Out of scope: changes to track(), Progress rendering, the Task fields, column classes, or rich/__init__.py exports. No public names beyond the four entry points.
- Edits must be additive. Do not delete or alter existing code.

## Assumptions
- Target the Python versions the project already declares (3.6.2 and newer). Use only syntax available on those versions.
- typing_extensions is already a declared dependency for Python below 3.9. Use it only in the same version-gated way the other rich modules use it, for Literal on interpreters older than 3.8.
- A caller passing a file-like object must supply total, unless the task passed in already has a total. The feature does not infer a total for file-like objects.
- Bytes are the unit for total and completed.

## Terminology
- Path input: a str, a path-like object, or bytes naming a file to open.
- File-like input: an already-open binary file object supplied by the caller.
- Reader: the object returned to the caller. It wraps a binary handle and advances a task as bytes are consumed. The reader class is private; callers only receive instances.
- Reader-owned handle: a handle the feature opened from a path. Closing the reader closes it.
- Caller-owned handle: a file-like input. Closing the reader must not close it.
- Text mode: the mode string is exactly 'r' or 'rt'. Binary mode: any other accepted spelling, namely 'rb' and 'br'.
- Task total: the total field of a progress task, in bytes.
- Context wrapper: a private helper returned by the module-level functions. It starts and stops the Progress and enters and exits the reader.
- Text wrapper: the standard library text wrapper placed around a reader.

## Workflows
Module-level open (file, mode, buffering, encoding, errors, newline, total, description, and display options):
1. Build columns the way track() builds a bar display: a description text column only when description is non-empty, a bar column carrying the style options, a byte-count download column, and a time-remaining column.
2. Create a Progress from those columns and the display options (auto refresh, console, transient, time source, disable). The refresh rate falls back to 10 when the given value is falsy.
3. Ask that Progress for a reader through its open method, passing file, mode, buffering, encoding, errors, newline, total, and description. The display is not started at this point.
4. Return a context wrapper. On enter, start the Progress, enter the reader, and yield it. On exit, stop the Progress first, then exit the reader.

Module-level wrap_file (file, total, description, display options):
- Build the Progress the same way, obtain the reader from the Progress wrap_file method, and return a context wrapper that yields a binary reader.

Progress.open (file, mode defaulting to 'r', buffering, encoding, errors, newline, total, task_id, description):
1. Normalize mode by sorting its letters. Accept only the normalized values 'r', 'rt', and 'br'. Any other value raises ValueError that names the mode. Validate before any file is opened or any task is created.
2. Buffering is forwarded to the byte handle's open unchanged, except for the two values with special meaning:
   - Binary mode: a buffering value of 1 emits a RuntimeWarning saying the default buffer size is used, and the handle is opened with the default buffering. Every other value, including 0 and values greater than 1, is forwarded unchanged.
   - Text mode: buffering 0 is an error. Buffering 1 requests line buffering on the text wrapper, and the byte handle is opened with the default buffering. Every other value, including values greater than 1, is forwarded unchanged to the byte handle's open. Do not discard it.
3. Total: if none is given, obtain the size in bytes with a file-system stat call on the path, before any task is created. Do not catch, wrap, or re-word errors from this call. A missing path raises the same OSError subclass that the builtin open raises. This error is not a ValueError.
4. Task: if task_id is None, add a task with description and total. Otherwise update that task's total to the resolved total. Progress.open does not start the Progress.
5. Open the path in binary mode with the resolved buffering. Wrap the handle in a reader that owns it.
6. Return value: when the mode string is exactly 'r' or 'rt', wrap the reader in a text wrapper with encoding, errors, newline, and line buffering, and return the wrapper. For every other accepted spelling, including 'rb', 'br', and 'tr', return the binary reader.

Progress.wrap_file (file, total optional, task_id optional, description):
1. Resolve total. An explicit total wins. Otherwise, if task_id is given, read that task's stored total while holding the Progress lock, and use the stored value unchanged (it may be a float; do not convert it to an integer). If the resolved value is still missing, raise ValueError before any task is created or updated.
2. If task_id is None, add a task with description and the resolved total. Otherwise update that task's total to the resolved total.
3. Return a binary reader that wraps file as a caller-owned handle.

Reader behavior (all readers):
- Byte accounting: each read operation advances the task by the number of bytes actually returned. This covers read, readline, readinto, readlines (the sum of the line lengths), and iteration (the length of each yielded line).
- readinto: call the handle's own readinto on the caller's buffer and advance the task by the count that call returns. Do not read into a temporary buffer and copy, because a buffer the handle rejects must fail before any bytes are consumed.
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
- A task total may be a float, because track() accepts float totals. The feature reads and writes totals without narrowing them.
- The text wrapper, when used, is the standard library text wrapper around the reader. It is not a separate type introduced by this feature.

## API contracts
- Public names: the module-level open and wrap_file in rich.progress, and the open and wrap_file methods on Progress. Nothing else is public. The reader class and the context wrapper are private, with underscore-prefixed names.
- Module-level open, positional parameters in this order: file (str, path-like, or bytes); mode, default 'r'; buffering, default -1; encoding, optional; errors, optional; newline, optional. Keyword-only parameters after these: total (optional integer count of bytes); description, default 'Reading...'; auto_refresh, default true; console, optional; transient, default false; get_time, optional; refresh_per_second, default 10; style, default 'bar.back'; complete_style, default 'bar.complete'; finished_style, default 'bar.finished'; pulse_style, default 'bar.pulse'; disable, default false.
  - Returns a context manager. It yields a text reader for 'r' and 'rt', and a binary reader for the binary modes.
- Module-level wrap_file: file (binary file-like object); total (required integer count of bytes, may be given by keyword). Keyword-only parameters after total: description, auto_refresh, console, transient, get_time, refresh_per_second, style, complete_style, finished_style, pulse_style, disable, with the same defaults as open. Returns a context manager that yields a binary reader.
- Progress.open: file, mode default 'r', buffering default -1, encoding, errors, newline. Keyword-only after these: total (optional integer count of bytes), task_id (optional), description default 'Reading...'. Returns a binary reader for binary modes, or a text wrapper for 'r' and 'rt'. It does not return a context manager; the caller uses the result in a with statement.
- Progress.wrap_file: file (binary file-like object); total (optional integer count of bytes); keyword-only task_id (optional) and description default 'Reading...'. Returns a binary reader.
- Return annotations: every public return is annotated with the standard interface types. Use the text interface for text results, the binary file interface for binary results, and a context manager of either for the module-level functions. The reader class and the context wrapper must never be named in any public annotation or overload.
- Reader parameter types (for the reader class, which is private but is checked by the repository's type checker):
  - read and readlines take a size or hint integer defaulting to -1.
  - readline takes a size integer defaulting to -1. This narrows the base class's optional size, so the override must be marked as in Implementation constraints.
  - readinto takes a buffer typed as the union of bytearray, memoryview, and mmap. It has no return annotation and is marked as in Implementation constraints.
  - write takes its argument typed as Any and raises the unsupported-operation error.
- The reader class inherits from both the standard raw I/O base class and the binary file interface type, so that type checkers and the text wrapper accept it.
- Public total parameters are integer counts of bytes. A total read from an existing task is passed through as stored and may be a float; it is never converted to an integer.
- Type-level overloads: binary modes map to the binary file interface and text modes map to the text interface, for both open entry points.

## Module architecture
- All code changes are in rich/progress.py. Place the private reader class and context wrapper with the other progress helpers. Place the module-level functions beside track(). Place the Progress methods in the Progress class next to track().
- Progress.open and Progress.wrap_file own the file, total, and task logic. The module-level functions only build a Progress with the display options and delegate. They must not duplicate file handling.
- Progress.wrap_file reads the task's stored total only while holding the Progress lock, as the other task reads in the class do.
- The reader uses only the public Progress methods for advancing and updating. It must not read or write Progress internals such as the task table or its lock.
- The context wrapper alone owns the ordering of start and stop.

## Implementation constraints
- Implement every read-side method explicitly on the reader: read, readline, readinto, readlines, iteration, seek, and tell. Do not add a catch-all attribute forwarder that can bypass byte accounting or let writes through. Other attributes come from the base classes.
- Forward references: the module does not use postponed annotation evaluation. Any annotation that names Progress, or any other class defined later in the module, must be a quoted string annotation. Check every annotation in the module-level helper functions and in the reader class for this, including helpers placed before the Progress class. An unquoted forward reference fails at import time.
- Type-checker suppressions: do not suppress type errors in general. Fix the declared type first. Add a suppression only at the constructs where the reference suppresses the same error, and only with the same error categories:
  - The reader's readinto: suppress the untyped-definition and override error categories, because the reference leaves its return unannotated and overrides the base method with a narrower buffer type.
  - The reader's readline: suppress the override error category, because of the narrowed size type.
  - The call to the handle's readinto inside the reader: suppress the attribute error category, because the handle's declared type does not expose readinto.
  - The return of the module-level open, which wraps the context wrapper in the overloaded return type: suppress the return-value and type-variable error categories.
  No other suppression is permitted.
- Do not start the Progress inside open or wrap_file.
- Do not catch exceptions from the size lookup or from opening the handle; let them propagate.
- track() and existing Progress behavior must not change.

## Dependencies
- Standard library only: io, os, sys, warnings, typing, mmap (for the readinto buffer type only), and contextlib if needed. Existing rich imports in progress.py are reused. Do not add new rich module imports.
- No new third-party packages and no project metadata changes.
- Literal, if imported, uses the same version-gated import pattern as the other rich modules.

## Naming
- Public: open and wrap_file, both module-level and as Progress methods. The name read is not a public name for this feature.
- Private: the reader class, the context wrapper, and any type alias or type variable introduced for this feature. Each has a leading underscore. No public alias is exported.
- Parameter names: file, mode, buffering, encoding, errors, newline, total, task_id, description, and the display options spelled exactly as in track() and Progress.__init__.
- Mode values are the strings 'r', 'rt', and 'rb'.

## Validation
- Mode: must normalize to 'r', 'rt', or 'br'. Validated before any file is opened or any task is created.
- Buffering: validated as described under Workflows and Error handling. Only 0 in text mode and 1 in binary mode are interpreted by the feature; every other value is passed through to the handle's open.
- Total: path input defaults to the file size, and errors from that lookup propagate unchanged (see Error handling). File-like input requires an explicit total or a task whose stored total is set.
- task_id: when supplied, it refers to an existing task. Use the Progress's existing task lookup behavior.

## Error handling
- Invalid mode: ValueError whose message includes the offending value.
- Text mode with buffering 0: ValueError.
- Binary mode with buffering 1: emit RuntimeWarning stating that line buffering is not supported in binary mode and the default buffer size is used. Continue with default buffering.
- No other buffering value is rejected in either mode. Values other than the two above propagate to the handle's open, which decides whether they are valid.
- File-like input with no total and no task total: ValueError whose message says that total must be specified. Raised before any task is created or updated.
- Path input whose size cannot be obtained (for example a missing file): the OSError from the size lookup propagates unchanged, so a missing file raises FileNotFoundError as the builtin open does. Do not wrap it in ValueError and do not re-word it. The ValueError rule above does not apply to path input.
- write on a reader: raise the standard unsupported-operation error naming 'write'.
- Exceptions raised by the underlying handle propagate unchanged. Do not swallow them.
- An error before the module-level context is entered leaves no display running. An error inside the context stops the display and exits the reader, then propagates.

## Documentation
- docs/source/progress.rst: add two subsections, "Reading from a file" and "Reading from a file-like object", as subsections of the existing "Advanced usage" section, placed after "Customizing" and before "Multiple Progress". Underline them with the tilde character used for the other subsections of Advanced usage. Do not use the hyphen underline, which marks top-level sections.
- The file-path subsection covers Progress.open with a path, the default text mode compared with 'rb', and that the default total is the file size. The file-like subsection covers Progress.wrap_file: binary only, total required unless a task with a total is given, and the reader does not close the wrapped file.
- Every documentation example names each module it uses in an import before the first use of that module.
- Use only the names open and wrap_file in the documentation.
- Docstrings for the four public entry points and the reader use the Google style with Args, Returns, and Raises sections, matching track(). Describe total as a count of bytes, and state the default description.
- CHANGELOG.md: add one entry under the Unreleased section's Added heading. Use the bullet form of the neighboring entries, including a pull request link in the same URL form, with pull request number 1759.

## Maintainability
- Format with black at its default line length of 88. Order imports as isort does with the black profile. Within the standard library block, plain imports come before from-imports.
- Keep file-handling logic in one place (Progress.open and Progress.wrap_file).
- Keep two blank lines before any module-level statement that follows a class.

## Reliability
- The display starts on context entry and always stops on context exit, including when the body raises.
- Exiting a reader closes a reader-owned handle and leaves a caller-owned handle open.

## Compatibility
- Purely additive. Existing names, track(), Progress, Task, and column classes keep their behavior.
- Use syntax no newer than the project's declared minimum Python version.
- rich.progress must import without error on every declared Python version. Because postponed annotation evaluation is not assumed, annotations that name Progress or any later-defined class must be quoted, as stated under Implementation constraints.

## Behavioral acceptance criteria
- Module-level open on a path with default mode returns text: read() returns a str equal to the file contents, and after the with block the reader reports closed.
- Explicit mode 'r' behaves the same way.
- Mode 'rb' returns bytes.
- Progress.open on a path with no total sets the task total to the file size in bytes.
- Module-level open and Progress.open on a missing path with no total raise FileNotFoundError (an OSError), not ValueError, and create no task.
- Module-level wrap_file on a caller-owned binary file returns bytes. After the context exits, the reader reports closed, the caller's file is still open, and the caller's own with block closes it.
- Progress.wrap_file with an existing task that has a total, and no total argument, reads correctly, the task's completed value equals the bytes read, and a float stored total is not truncated.
- Progress.wrap_file with an existing task that has no total, and no total argument, raises ValueError and creates or updates no task.
- Each read path (read, readline, readinto, readlines, iteration) advances completed by exactly the number of bytes returned.
- seek to a position p sets completed to p. tell returns the handle's position.
- write raises the unsupported-operation error.
- File-like input with no total and a task without a total raises ValueError, and no display is started.
- Invalid mode raises ValueError. Text mode with buffering 0 raises ValueError.
- Binary mode with buffering 1 emits RuntimeWarning, and reading still succeeds.
- A text-mode open with a buffering value greater than 1 passes that value to the byte handle's open; it is not silently replaced by the default.
- Importing rich.progress succeeds on the declared minimum Python version.

## Test requirements
- Add tests to tests/test_progress.py in the file's existing style: each test annotated to return None, temporary files removed in a finally block, and a Console writing to an in-memory stream with forced terminal output as existing tests do.
- Insert the new tests before the existing script-entry block at the end of tests/test_progress.py, not after it.
- Cover at least: module-level open with default mode, module-level open with explicit 'r', module-level wrap_file with a caller-owned file, Progress.wrap_file reusing an existing task's total, a missing path with no total raising FileNotFoundError, and Progress.wrap_file with a task lacking a total raising ValueError.
- Cover the behavioral acceptance criteria where practical.
- New test code follows the repo's line-length limit.
