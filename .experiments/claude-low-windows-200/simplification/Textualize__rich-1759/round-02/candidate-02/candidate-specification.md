## Goals
- Let callers show progress while bytes are read from a file, such as in a long JSON or CSV parser.
- Provide two public module-level functions in rich.progress, open and wrap_file, and two Progress methods with the same names. The module-level functions create and manage their own display. The Progress methods attach a reader to an existing Progress and task.
- Add no other public name, including no public read function or method.

## Scope
- In scope: rich/progress.py (private reader class, private context wrapper, two module-level functions, two Progress methods); tests/test_progress.py; docs/source/progress.rst; CHANGELOG.md.
- Out of scope: track(), Progress rendering, Task fields, column classes, and rich/__init__.py exports.
- Edits are additive. Do not delete or alter existing code.

## Assumptions
- Target the declared minimum Python (3.6.2) and use only syntax available on it.
- typing_extensions is declared for Python below 3.9. Import Literal from it only as other rich modules do, for interpreters older than 3.8.
- File-like input must supply total unless the task already has one. No total is inferred for file-like objects.
- Bytes are the unit for total and completed.

## Terminology
- Path input: a str, path-like object, or bytes naming a file to open.
- File-like input: an already-open binary file object supplied by the caller.
- Reader: the object callers receive. It wraps a binary handle and advances a task as bytes are consumed. The class is private.
- Reader-owned handle: a handle the feature opened from a path; closing the reader closes it.
- Caller-owned handle: a file-like input; closing the reader must not close it.
- Normalized mode: the letters of the mode string sorted alphabetically. Runtime-accepted normalized values are 'r', 'rt', and 'br'; any other is rejected. Normalization drives validation and buffering only.
- Typed mode literals: exactly 'r' and 'rt' (text) and 'rb' (binary). Only these may appear in any annotation, overload, alias, or docstring type description.
- Accepted-but-untyped spellings: 'br' and 'tr'. The runtime accepts them, but they are not typed literals and must not be documented as supported modes.
- Return classification: decided by the mode string as given. Exactly 'r' or 'rt' returns a text wrapper; every other accepted spelling, including 'rb', 'br', and 'tr', returns the binary reader.
- Buffering classification: decided by the normalized mode. Normalized 'br' uses binary rules; normalized 'r' or 'rt' uses text rules. So 'tr' follows text buffering rules yet returns the binary reader.

## Workflows
Module-level open (file, mode, buffering, encoding, errors, newline, total, description, display options):
1. Build columns as track() does, with the same description, bar, byte-count, and time-remaining columns, and the given style options.
2. Create a Progress from those columns and the display options. A falsy refresh rate falls back to 10.
3. Ask that Progress for a reader through its open method, passing file, mode, buffering, encoding, errors, newline, total, and description. Do not start the display.
4. Return a context wrapper. On enter, start the Progress, enter the reader, and yield it. On exit, stop the Progress first, then exit the reader.

Module-level wrap_file (file, total, description, display options): build the Progress the same way, obtain the reader from the Progress wrap_file method, and return a context wrapper yielding a binary reader.

Progress.open (file, mode default 'r', buffering, encoding, errors, newline, total, task_id, description):
1. Normalize mode. Reject any normalized value other than 'r', 'rt', or 'br' with a ValueError naming the mode. Validate before any file is opened, any size lookup is made, or any task is created.
2. Apply buffering rules for the normalized mode, also before any file is opened or task created:
   - Normalized 'br': buffering 1 emits a RuntimeWarning saying the default buffer size is used, and the handle is opened with default buffering. Every other value, including 0 and values above 1, is forwarded unchanged to the handle's open.
   - Normalized 'r' or 'rt': buffering 0 raises ValueError. Buffering 1 requests line buffering on the text wrapper, and the byte handle uses default buffering. Every other value, including values above 1, is forwarded unchanged to the byte handle's open.
3. Total: if none is given, obtain the size in bytes with a file-system stat call on the path, before any task is created. Do not catch, wrap, or re-word its errors.
4. Task: if task_id is None, add a task with description and total. Otherwise update that task's total to the resolved total. Do not start the Progress.
5. Open the path in binary mode with the resolved buffering and wrap the handle in a reader that owns it.
6. Return: if the mode string as given is exactly 'r' or 'rt', wrap the reader in a text wrapper using encoding, errors, newline, and line buffering. Otherwise return the binary reader.

Progress.wrap_file (file, total, task_id, description):
1. Resolve total. An explicit total wins. Otherwise, if task_id is given, read that task's stored total while holding the Progress lock and use it unchanged; it may be a float and must not be converted to an integer. If still missing, raise ValueError before any task is created or updated.
2. If task_id is None, add a task with description and the resolved total. Otherwise update that task's total to the resolved total.
3. Return a binary reader wrapping file as a caller-owned handle.

Reader behavior:
- Byte accounting: each read operation advances the task by the bytes actually returned. This covers read, readline, readlines (sum of line lengths), and iteration (length of each yielded line).
- readinto: call the handle's own readinto on the caller's buffer and advance by the count returned. Do not read into a temporary buffer and copy, so a buffer the handle rejects fails before any bytes are consumed.
- seek(offset, whence): delegate to the handle. On success, set the task's completed value to the returned absolute position through the Progress public update operation, and return that position.
- tell: return the handle's position. Keep no separate counter.
- readable, seekable, fileno, isatty: delegate. writable: false. write: raise the standard unsupported-operation error naming 'write'.
- close: close the handle only if the reader owns it, and always mark the reader closed. The closed property reports that marker, not the handle's state.
- Entering the reader enters the handle and returns the reader. Exiting calls close.
- Iteration returns the reader itself; each step yields the next line of the handle.
- The wrapped handle is a public attribute named handle.

## Data model
- Reader state: the wrapped handle, the owning Progress, the task identifier, a flag saying whether the reader owns the handle, and a closed marker. The byte position comes from the handle.
- Task state: use the existing total and completed fields. Add no fields to Task or Progress and store nothing outside memory.
- Totals may be floats, since track() accepts float totals. Read and write them without narrowing.

## API contracts
- Public names: open and wrap_file in rich.progress, and open and wrap_file methods on Progress. The reader class and context wrapper are private, underscore-prefixed.
- Module-level open. Positional parameters in order: file (str, path-like, or bytes); mode, default 'r'; buffering, default -1; encoding, optional; errors, optional; newline, optional. Keyword-only after these: total (optional byte count); description, default 'Reading...'; auto_refresh, default true; console, optional; transient, default false; get_time, optional; refresh_per_second, default 10; style, default 'bar.back'; complete_style, default 'bar.complete'; finished_style, default 'bar.finished'; pulse_style, default 'bar.pulse'; disable, default false. Returns a context manager yielding a text reader for 'r' and 'rt', and a binary reader for every other accepted mode.
- Module-level wrap_file: file (binary file-like object); total (required byte count, may be given by keyword). Keyword-only after total: description, auto_refresh, console, transient, get_time, refresh_per_second, style, complete_style, finished_style, pulse_style, disable, with the same defaults as open. No task parameter. Returns a context manager yielding a binary reader.
- Progress.open: file, mode default 'r', buffering default -1, encoding, errors, newline. Keyword-only after these: total (optional byte count), task_id (optional), description default 'Reading...'. Returns a text wrapper for 'r' and 'rt', otherwise a binary reader. Not a context manager; callers use the result in a with statement.
- Progress.wrap_file: file (binary file-like object); total (optional byte count); keyword-only task_id (optional) and description default 'Reading...'. Returns a binary reader.
- Mode parameter types: exactly 'r', 'rt', and 'rb'. Map 'rb' to the binary file interface and 'r' and 'rt' to the text interface, with one overload per group where an entry point is overloaded.
- Return annotations use standard interface types: text interface for text results, binary file interface for binary results, and a context manager of either for module-level functions. The reader class and context wrapper must never be named in any public annotation or overload.
- Reader types (private, but checked by the type checker): read and readlines take a size or hint integer defaulting to -1. readline takes a size integer defaulting to -1, narrowing the base optional size. readinto takes a buffer typed as the union of bytearray, memoryview, and mmap, with no return annotation. write takes an argument typed Any, has an integer return annotation matching the base contract, and always raises.
- The reader inherits from both the standard raw I/O base class and the binary file interface type, so type checkers and the text wrapper accept it.

## Module architecture
- All changes are in rich/progress.py. Place the private reader class and context wrapper with the other progress helpers, the module-level functions beside track(), and the Progress methods in the Progress class next to track().
- Progress.open and Progress.wrap_file own the file, total, and task logic. Module-level functions only build a Progress with the display options and delegate; they do not duplicate file handling.
- The reader uses only public Progress methods for advancing and updating, and reads stored totals only while holding the Progress lock, as other task reads do. It must not touch Progress internals such as the task table or its lock.
- The context wrapper alone owns the ordering of start and stop.

## Implementation constraints
- Implement every read-side method explicitly on the reader: read, readline, readinto, readlines, iteration, seek, and tell. No catch-all attribute forwarder, which could bypass byte accounting or let writes through. Other attributes come from the base classes.
- Return classification tests the mode string as given. Do not use the sorted value: sorted 'tr' is 'rt', yet the reference returns the binary reader for it. Buffering uses the normalized value. Keep the two decisions separate.
- Forward references: the module does not use postponed annotation evaluation. Any annotation naming Progress or another class defined later must be a quoted string, including in helpers placed before Progress and in the reader class.
- Type-checker suppressions: fix declared types first. Add a suppression only where the reference suppresses the same error, using the same category:
  - Reader readinto: untyped-definition and override categories.
  - Reader readline: override category.
  - Call to the handle's readinto inside the reader: attribute category.
  - Return of module-level open wrapping the context wrapper in the overloaded return type: return-value and type-variable categories.
  No other suppression is permitted.
- Do not start the Progress inside open or wrap_file. Do not catch exceptions from the size lookup or from opening the handle.
- track() and existing Progress behavior must not change.

## Dependencies
- Standard library only: io, os, sys, warnings, typing, mmap (for the readinto buffer type only), and contextlib if needed. Reuse existing rich imports in progress.py. Add no new rich module imports, third-party packages, or project metadata changes.
- Literal, if imported, uses the same version-gated import pattern as other rich modules.

## Naming
- Public: open and wrap_file, both module-level and as Progress methods. read is not a public name for this feature.
- Private: reader class, context wrapper, and any alias or type variable introduced, each with a leading underscore. Export no public alias.
- Parameter names: file, mode, buffering, encoding, errors, newline, total, task_id, description, and display options spelled exactly as in track() and Progress.__init__.

## Validation
- Mode: the normalized value must be 'r', 'rt', or 'br', checked before any file is opened, size lookup made, or task created.
- Buffering: as under Workflows and Error handling. Only 0 under text rules and 1 under binary rules are interpreted; every other value goes to the handle's open.
- Total: path input defaults to the file size, and lookup errors propagate. File-like input requires an explicit total or a task whose stored total is set.
- task_id: when supplied, it refers to an existing task, found through the Progress's existing task lookup.

## Error handling
- Invalid mode: ValueError whose message includes the offending value.
- Normalized 'r' or 'rt' (including the literal 'tr') with buffering 0: ValueError.
- Normalized 'br' (including the literal 'rb') with buffering 1: RuntimeWarning stating that line buffering is not supported in binary mode and the default buffer size is used. Continue with default buffering.
- File-like input with no total and no task total: ValueError whose message says total must be specified, raised before any task is created or updated.
- Path input whose size cannot be obtained, such as a missing file: the OSError propagates unchanged, so a missing file raises FileNotFoundError.
- write on a reader: the standard unsupported-operation error naming 'write'. Exceptions from the underlying handle propagate unchanged.
- An error before the context is entered leaves no display running. An error inside the context stops the display, exits the reader, then propagates.

## Documentation
- docs/source/progress.rst: under the existing "Advanced usage" section, add subsections "Reading from a file" and "Reading from a file-like object" after "Customizing" and before "Multiple Progress", underlined with tildes.
- The file-path subsection covers Progress.open with a path, the default text mode compared with 'rb', and that the default total is the file size.
- The file-like subsection covers Progress.wrap_file: binary only, total required unless a task with a total is given, and the reader does not close the wrapped file. The task clause applies only to Progress.wrap_file.
- Every example imports each module it uses before first use. Use only the names open and wrap_file.
- Docstrings for the four public entry points and the reader use Google style with Args and Returns, matching track(). Progress.open and Progress.wrap_file also have a Raises section. Describe total as a byte count and state the default description.
- CHANGELOG.md: one bullet under the Unreleased section's Added heading, in the form of neighboring entries, with a pull request link for number 1759.

## Maintainability
- Format with black at line length 88. Order imports as isort does with the black profile; within the standard library block, plain imports precede from-imports.
- Keep file-handling logic only in Progress.open and Progress.wrap_file. Keep two blank lines before any module-level statement that follows a class.

## Reliability
- The display starts on context entry and always stops on exit, including when the body raises.
- Exiting a reader closes a reader-owned handle and leaves a caller-owned handle open.
- open and wrap_file never start the live display; an error before entering leaves nothing to clean up.

## Compatibility
- Purely additive. Existing names, track(), Progress, Task, and column classes keep their behavior.
- Use syntax no newer than the declared minimum Python version. rich.progress must import on every declared version.

## Behavioral acceptance criteria
- Module-level open on a path returns str from read() with default or 'r' mode, and bytes with 'rb'. After the with block the reader reports closed.
- Progress.open on a path with no total sets the task total to the file size in bytes.
- Module-level open and Progress.open on a missing path with no total raise FileNotFoundError and create no task.
- Module-level wrap_file on a caller-owned binary file returns bytes. After exit the reader reports closed, and the caller's file stays open until the caller closes it.
- Progress.wrap_file with an existing task that has a total, and no total argument, reads correctly; completed equals the bytes read; a float stored total is not truncated.
- Progress.wrap_file with an existing task lacking a total, and no total argument, raises ValueError and creates or updates no task.
- Each read path (read, readline, readinto, readlines, iteration) advances completed by exactly the bytes returned.
- seek to position p sets completed to p; tell returns the handle's position; write raises the unsupported-operation error.
- File-like input with no total and a task without a total raises ValueError, and no display is started.
- Invalid mode raises ValueError. Mode 'r' or 'rt' with buffering 0 raises ValueError.
- Mode 'rb' with buffering 1 emits RuntimeWarning, and reading still succeeds.
- A text-mode open with buffering above 1 passes that value to the byte handle's open.
- Mode 'tr' is accepted, applies text buffering rules, and returns the binary reader.
- Typed mode parameters list only 'r', 'rt', and 'rb'. Neither 'br' nor 'tr' appears in any annotation, overload, or alias.
- Importing rich.progress succeeds on the declared minimum Python version.

## Test requirements
- Add tests to tests/test_progress.py in the file's existing style: each test annotated to return None, temporary files removed in a finally block, and a Console writing to an in-memory stream with forced terminal output. Insert them before the existing script-entry block.
- Cover at least: module-level open with default mode; open with explicit 'r'; module-level wrap_file with a caller-owned file; Progress.wrap_file reusing an existing task's total; a missing path with no total raising FileNotFoundError; Progress.wrap_file with a task lacking a total raising ValueError. Cover other acceptance criteria where practical, within the repo's line-length limit.
