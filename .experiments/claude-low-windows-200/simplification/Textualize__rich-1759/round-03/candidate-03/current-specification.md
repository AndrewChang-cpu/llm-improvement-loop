## Goals
- Let callers show progress while bytes are read from a file, so a long consumer such as a JSON or CSV parser can report how far through its input it is.
- Provide two public module-level functions in rich.progress, open and wrap_file, and two Progress methods with the same names. The module-level functions manage their own display. The Progress methods attach a reader to an existing Progress and task.
- Expose no other public name. No public read function or method is added.

## Scope
- In scope: rich/progress.py; tests/test_progress.py; docs/source/progress.rst; CHANGELOG.md.
- Out of scope: track(), Progress rendering, Task fields, column classes, and rich/__init__.py exports.
- Edits are additive. Do not delete or alter existing code.

## Assumptions
- Target the declared Python versions (3.6.2 and newer) and use only syntax available on them.
- typing_extensions is declared for Python below 3.9. Import Literal from it only in the version-gated way other rich modules do.
- File-like input supplies total unless the task already has one. No total is inferred for file-like objects.
- Bytes are the unit for total and completed.

## Terminology
- Path input: a str, path-like object, or bytes naming a file to open.
- File-like input: an already-open binary file object supplied by the caller.
- Reader: the private object returned to callers. It wraps a binary handle and advances a task as bytes are consumed.
- Reader-owned handle: a handle opened from a path. Closing the reader closes it. A caller-owned handle, from a file-like input, stays open.
- Normalized mode: the letters of the mode string sorted alphabetically. Runtime-accepted normalized values are 'r', 'rt', and 'br'; any other is rejected. Normalization drives validation and buffering only.
- Typed mode literals: exactly 'r' and 'rt' (text) and 'rb' (binary). Only these may appear in any annotation, overload, alias, or docstring type description.
- Untyped spellings: 'br' and 'tr'. The runtime accepts them, but they are not typed literals and must not be documented as supported modes.
- Return classification: the mode string as given decides the return type. Exactly 'r' or 'rt' returns a text wrapper. Every other accepted spelling, including 'rb', 'br', and 'tr', returns the binary reader. This test uses the literal string, not the normalized value.
- Buffering classification: decided by the normalized mode. Normalized 'br' uses binary buffering rules; normalized 'r' or 'rt' uses text rules. So 'tr' follows text buffering rules yet returns the binary reader.
- Context wrapper: a private helper returned by the module-level functions. It starts and stops the Progress and enters and exits the reader.
- Text wrapper: the standard library text wrapper placed around a reader.

## Workflows
Module-level open (file, mode, buffering, encoding, errors, newline, total, description, display options):
1. Build columns as track() does: a description text column only when description is non-empty, a bar column carrying the style options, a byte-count download column, and a time-remaining column.
2. Create a Progress from those columns and the display options. The refresh rate falls back to 10 when the given value is falsy.
3. Ask that Progress for a reader through its open method, passing file, mode, buffering, encoding, errors, newline, total, and description. Do not start the display.
4. Return a context wrapper. On enter, start the Progress, enter the reader, and yield it. On exit, stop the Progress first, then exit the reader.

Module-level wrap_file (file, total, description, display options): build the Progress the same way, obtain the reader from the Progress wrap_file method, and return a context wrapper that yields a binary reader. It takes no task argument.

Progress.open (file, mode default 'r', buffering, encoding, errors, newline, total, task_id, description):
1. Normalize mode. Reject any normalized value other than 'r', 'rt', or 'br' with a ValueError naming the mode.
2. Apply buffering rules for the normalized mode:
   - Normalized 'br': buffering 1 emits a RuntimeWarning saying the default buffer size is used, and the handle is opened with default buffering. Every other value, including 0 and values above 1, is forwarded unchanged to the handle's open.
   - Normalized 'r' or 'rt': buffering 0 raises ValueError. Buffering 1 requests line buffering on the text wrapper, and the byte handle uses default buffering. Every other value, including values above 1, is forwarded unchanged to the byte handle's open.
   - Steps 1 and 2 run before any file is opened, size lookup is made, or task is created.
3. Total: if none is given, obtain the size in bytes with a file-system stat call on the path. Do not catch, wrap, or re-word its errors. A missing path raises the same OSError subclass the builtin open raises, not ValueError.
4. Task: if task_id is None, add a task with description and total. Otherwise update that task's total to the resolved total. Do not start the Progress.
5. Open the path in binary mode with the resolved buffering and wrap the handle in a reader that owns it.
6. Return: if the mode string as given is exactly 'r' or 'rt', wrap the reader in a text wrapper using encoding, errors, newline, and line buffering. Otherwise return the binary reader.

Progress.wrap_file (file, total, task_id, description):
1. Resolve total. An explicit total wins. Otherwise, if task_id is given, read that task's stored total while holding the Progress lock and use it unchanged; it may be a float and must not be converted to an integer. If still missing, raise ValueError before any task is created or updated.
2. If task_id is None, add a task with description and the resolved total. Otherwise update that task's total to the resolved total.
3. Return a binary reader wrapping file as a caller-owned handle.

## Reader behavior
- Byte accounting: each read operation advances the task by the bytes actually returned. This covers read, readline, readlines (sum of line lengths), and iteration (length of each yielded line).
- readinto: call the handle's own readinto on the caller's buffer and advance by the count it returns. Do not read into a temporary buffer and copy, so a buffer the handle rejects fails before any bytes are consumed.
- seek(offset, whence): delegate to the handle. On success, set the task's completed value to the returned absolute position through the Progress public update operation, and return that position.
- tell: return the handle's position. Keep no separate counter.
- readable, seekable, fileno, isatty: delegate. writable: false. write: raise the standard unsupported-operation error naming 'write'.
- close: close the handle only if the reader owns it, and always mark the reader closed. The closed property reports that marker, not the handle's state.
- Entering the reader enters the handle and returns the reader. Exiting calls close.
- Iteration returns the reader itself; each step yields the next line of the handle.
- The wrapped handle is a public attribute named handle.

Lifecycle: open and wrap_file never start the live display. The display starts only when the module-level context is entered, and always stops on exit, including when the body raises. An error before entering leaves nothing started.

## Data model
- Reader state: the wrapped handle, the owning Progress, the task identifier, an owns-handle flag, and a closed marker. The byte position comes from the handle.
- Task state: use the existing total and completed fields. The feature adds no fields to Task or Progress and stores nothing outside memory.
- Totals may be floats, since track() accepts float totals. Read and write them without narrowing.

## API contracts
- Public names: module-level open and wrap_file in rich.progress, and open and wrap_file methods on Progress. The reader class and context wrapper are private, with underscore-prefixed names.
- Module-level open. Positional parameters in order: file (str, path-like, or bytes); mode, default 'r'; buffering, default -1; encoding, optional; errors, optional; newline, optional. Keyword-only after these: total (optional integer byte count); description, default 'Reading...'; auto_refresh, default true; console, optional; transient, default false; get_time, optional; refresh_per_second, default 10; style, default 'bar.back'; complete_style, default 'bar.complete'; finished_style, default 'bar.finished'; pulse_style, default 'bar.pulse'; disable, default false. Returns a context manager yielding a text reader for 'r' and 'rt', and a binary reader for every other accepted mode.
- Module-level wrap_file: file (binary file-like object); total (required integer byte count, may be given by keyword). Keyword-only after total: description, auto_refresh, console, transient, get_time, refresh_per_second, style, complete_style, finished_style, pulse_style, disable, with the same defaults as open. No task parameter. Returns a context manager yielding a binary reader.
- Progress.open: file, mode default 'r', buffering default -1, encoding, errors, newline. Keyword-only after these: total (optional integer byte count), task_id (optional), description default 'Reading...'. Returns a text wrapper for 'r' and 'rt', otherwise a binary reader. It is not a context manager.
- Progress.wrap_file: file (binary file-like object); total (optional integer byte count); keyword-only task_id (optional) and description default 'Reading...'. Returns a binary reader.
- Mode parameter types: the typed mode parameter of each open entry point is exactly 'r', 'rt', and 'rb'. Map 'rb' to the binary file interface and 'r' and 'rt' to the text interface, with one overload per group where the entry point is overloaded.
- Return annotations use standard interface types: the text interface for text results, the binary file interface for binary results, and a context manager of either for module-level functions. The reader class and context wrapper must never be named in any public annotation or overload.
- Reader types (private, but checked by the type checker): read and readlines take a size or hint integer defaulting to -1. readline takes a size integer defaulting to -1, which narrows the base optional size. readinto takes a buffer typed as the union of bytearray, memoryview, and mmap, with no return annotation. write takes an argument typed Any and has an integer return annotation matching the base contract, not None; it always raises.
- The reader inherits from both the standard raw I/O base class and the binary file interface type, so type checkers and the text wrapper accept it.

## Module architecture
- All changes are in rich/progress.py. Place the private reader class and context wrapper with the other progress helpers, the module-level functions beside track(), and the Progress methods in the Progress class next to track().
- Progress.open and Progress.wrap_file own all file, total, and task logic. Module-level functions only build a Progress with the display options and delegate.
- Progress.wrap_file reads the stored task total only while holding the Progress lock, as other task reads in the class do.
- The reader uses only public Progress methods for advancing and updating. It must not read or write Progress internals such as the task table or its lock.
- The context wrapper alone owns the ordering of start and stop.

## Implementation constraints
- Implement every read-side method explicitly on the reader: read, readline, readinto, readlines, iteration, seek, and tell. Do not add a catch-all attribute forwarder, which could bypass byte accounting or let writes through. Other attributes come from the base classes.
- Return classification tests the mode string as given against 'r' and 'rt'. Do not use the sorted value: sorted 'tr' is 'rt', yet the reference returns the binary reader for it. Buffering uses the normalized value. Keep the two decisions separate.
- Forward references: the module does not use postponed annotation evaluation. Any annotation naming Progress or another class defined later must be a quoted string, including in helpers placed before Progress and in the reader class.
- Type-checker suppressions: fix declared types first. Add a suppression only where the reference suppresses the same error, using the same category:
  - Reader readinto: untyped-definition and override categories, because the reference leaves its return unannotated and narrows the buffer type.
  - Reader readline: override category, because of the narrowed size type.
  - Call to the handle's readinto inside the reader: attribute category, because the handle's declared type does not expose readinto.
  - Return of module-level open that wraps the context wrapper in the overloaded return type: return-value and type-variable categories.
  No other suppression is permitted.
- Do not start the Progress inside open or wrap_file. Do not catch exceptions from the size lookup or from opening the handle.
- track() and existing Progress behavior must not change.

## Dependencies and naming
- Standard library only: io, os, sys, warnings, typing, mmap (for the readinto buffer type only), and contextlib if needed. Reuse existing rich imports in progress.py. Add no new rich module imports, third-party packages, or project metadata changes.
- Public: open and wrap_file only. read is not a public name for this feature. Private names (reader class, context wrapper, any alias or type variable) have a leading underscore and no public alias is exported.
- Parameter names: file, mode, buffering, encoding, errors, newline, total, task_id, description, and the display options spelled exactly as in track() and Progress.__init__.

## Error handling
- Invalid mode: ValueError whose message includes the offending value.
- Normalized 'r' or 'rt' (including the literal 'tr') with buffering 0: ValueError.
- Normalized 'br' (including the literal 'rb') with buffering 1: RuntimeWarning stating that line buffering is not supported in binary mode and the default buffer size is used. Continue with default buffering.
- File-like input with no total and no task total: ValueError whose message says total must be specified, raised before any task is created or updated.
- Path input whose size cannot be obtained, such as a missing file: the OSError propagates unchanged, so a missing file raises FileNotFoundError as the builtin open does.
- write on a reader: the standard unsupported-operation error naming 'write'.
- Exceptions from the underlying handle propagate unchanged. An error inside the context stops the display, exits the reader, then propagates.

## Documentation
- docs/source/progress.rst: under the existing "Advanced usage" section, add subsections "Reading from a file" and "Reading from a file-like object" after "Customizing" and before "Multiple Progress". Underline them with tildes, as the other Advanced usage subsections do.
- The file-path subsection covers Progress.open with a path, the default text mode compared with 'rb', and that the default total is the file size.
- The file-like subsection covers Progress.wrap_file: binary only, total required unless a task with a total is given, and the reader does not close the wrapped file. The task clause applies only to Progress.wrap_file, not the module-level wrap_file.
- Every example imports each module it uses before first use. Use only the names open and wrap_file.
- Docstrings for the four public entry points and the reader use Google style with Args and Returns, matching track(). Progress.open and Progress.wrap_file also have a Raises section. Describe total as a byte count and state the default description.
- CHANGELOG.md: one bullet under the Unreleased section's Added heading, in the form of neighboring entries, with a pull request link for number 1759.

## Maintainability
- Format with black at line length 88. Order imports as isort does with the black profile; within the standard library block, plain imports precede from-imports.
- Keep file-handling logic only in Progress.open and Progress.wrap_file.
- Keep two blank lines before any module-level statement that follows a class.

## Compatibility
- Purely additive. Existing names, track(), Progress, Task, and column classes keep their behavior.
- Use syntax no newer than the declared minimum Python version. rich.progress must import on every declared version.

## Acceptance criteria
- Module-level open on a path with default mode returns text: read() returns the file's contents as str, and after the with block the reader reports closed. Mode 'rb' returns bytes.
- Progress.open on a path with no total sets the task total to the file size in bytes.
- Module-level open and Progress.open on a missing path with no total raise FileNotFoundError and create no task.
- Module-level wrap_file on a caller-owned binary file returns bytes. After the context exits, the reader reports closed, and the caller's file is still open.
- Progress.wrap_file with an existing task that has a float total and no total argument reads correctly, completed equals the bytes read, and the total is not truncated.
- Progress.wrap_file with an existing task that has no total, and no total argument, raises ValueError and creates or updates no task.
- Each read path (read, readline, readinto, readlines, iteration) advances completed by exactly the bytes returned. seek to position p sets completed to p; tell returns the handle's position.
- write raises the unsupported-operation error.
- File-like input with no total and a task without a total raises ValueError, and no display is started.
- Mode 'r' or 'rt' with buffering 0 raises ValueError. Mode 'rb' with buffering 1 emits RuntimeWarning, and reading still succeeds.
- A text-mode open with buffering above 1 passes that value to the byte handle's open.
- Mode 'tr' is accepted, applies the text buffering rules, and returns the binary reader.
- Typed mode parameters list only 'r', 'rt', and 'rb'. Neither 'br' nor 'tr' appears in any annotation, overload, or alias.
- Importing rich.progress succeeds on the declared minimum Python version.

## Test requirements
- Add tests to tests/test_progress.py in the file's existing style: each test annotated to return None, temporary files removed in a finally block, and a Console writing to an in-memory stream with forced terminal output.
- Insert new tests before the existing script-entry block at the end of the file.
- Cover at least: module-level open with default mode; open with explicit 'r'; module-level wrap_file with a caller-owned file; Progress.wrap_file reusing an existing task's total; a missing path with no total raising FileNotFoundError; Progress.wrap_file with a task lacking a total raising ValueError. Cover the other acceptance criteria where practical, within the repo's line-length limit.
