Terminal window title setting

## Goals
- Let an application request a change of the terminal window title through the Console, using the same control path as the existing cursor and screen controls.
- Make the request effective on ANSI-capable terminals by emitting the OSC 0 title sequence, and on legacy Windows consoles by dispatching the title to the existing legacy Windows renderer, which calls the wrapper's set-title method.
- Report through a boolean result whether the title control was written to the output buffer.

## Scope
- In scope: one new control type; one classmethod on the Control class that builds the title control; one Console method; one new branch in the legacy Windows renderer; one CHANGELOG entry; the tests listed under Test requirements.
- Out of scope: reading the title; resetting or restoring a previous title; sanitizing or transforming title text; changing existing control types, their values, or their output; new configuration options; changes to the Windows console wrapper class.
- Contributor checklists, pull-request type selections, review-process notes, and mentions of individuals are not part of the feature and must not appear in the specification or in code comments.

## Assumptions
- Legacy Windows detection, and the standard-stream check that selects the legacy render path at buffer flush, already exist and are correct. This feature does not change them.
- The legacy Windows wrapper already provides a method that sets the console title. It is reused, not reimplemented.
- Other software (the shell, a prompt, the terminal itself) may overwrite the title at any time, so the feature does not guarantee that a title persists.

## Terminology
- Terminal: a Console for which the terminal check is true. This is the same check that show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set, meaning Windows without virtual-terminal (VT) escape processing.
- Standard stream: an output stream that the legacy render path can address directly. The render path checks this at buffer flush.
- Title control: a control code whose type is the new SET_WINDOW_TITLE member and whose parameter is the title text.
- Title sequence: the escape sequence consisting of the ESC character, a right bracket, the digit zero, a semicolon, the title text, and the BEL character (code 0x07). This is OSC 0 with a BEL terminator.

## Workflows
1. The application asks the Console to set the window title to a text value.
2. The Console method checks only whether the console is a terminal. It must not check the legacy-windows flag. This matches show_cursor, not set_alt_screen.
   - If the console is not a terminal: buffer nothing and return false.
   - If it is a terminal: build a title control from the text, add its segment to the buffer through the existing control path, and return true.
3. At buffer flush, if the console is a legacy Windows console and the output file is a standard stream, the buffer goes to the legacy renderer. For each title control, in buffer order, the renderer calls the wrapper's set-title method once, passing the title text.
4. On all other render paths, the title segment carries the title sequence as its text and follows the ordinary render rules. Control segments are dropped when the output is not a terminal.
5. A true result means the sequence was written to the buffer. It does not confirm that the title changed.

## Data model
- Control type enumeration: add exactly one member, named SET_WINDOW_TITLE, with the next integer after the highest existing value. Do not renumber existing members.
- Control code: a control code is a tuple whose first item is the control type and whose remaining items are parameters. The title control code is a two-item form: the control type followed by the title text.
- The declared union of allowed control code shapes must also admit the two-item form of a control type followed by text. Existing shapes stay admitted. The union must type-check under the repository's mypy configuration.
- The title text is stored in the control code exactly as given. No transformation is applied at the data level.

## API contracts
- Console method: name set_window_title; one positional parameter named title that is text; returns a boolean. Returns true when the title control was written to the buffer. Returns false when the console is not a terminal, and in that case nothing is written. It must never return nothing, and it must not raise for non-terminal consoles.
- Control classmethod: name title; one text parameter named title; returns a Control. The Control's segment text is the title sequence, its style is none, and its control list holds exactly one title control code.
- Construction rule: a title control must be passed to the Control constructor as a single two-item argument (control type and title text). Do not pass the control type and the title as two separate positional arguments. The constructor treats each positional argument as either a bare control type or a control code, so a bare text argument is misread as a sequence of codes and construction fails at runtime.
- Format entry: for the title control type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer contract: for a title control code, read the title text from the second item of the code and call the wrapper's set-title method with that text as its only argument.

## Module architecture
- Segment module: holds the enum member and the control code union.
- Control module: holds the formatting table entry and the Control classmethod. Escape bytes live only here.
- Console module: holds the set_window_title method, placed beside show_cursor and set_alt_screen. It delegates to the control path and contains no Windows API calls and no legacy checks.
- Windows renderer module: holds the one new branch in the legacy render dispatch, which is where Windows-side handling of control types belongs.
- Win32 console wrapper: unchanged. Its existing set-title method is reused.
- Dependency direction: Console depends on Control, which depends on Segment. The renderer depends on the wrapper and Segment. No module may import upward or create a cycle.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain over control types, placed with the other control types, and follow the pattern of the parameterized controls: interpret the code in its two-item form, then read the parameter.
- Gate the Console method only on the terminal check. Do not gate it on the legacy-windows flag, and do not add any console-level guard that returns false for legacy consoles. The legacy path is handled by the renderer.
- Register the new control type in all three places: the formatting table, the enum and union, and the legacy renderer dispatch. Omitting any one of them is a defect.
- Do not change the values or output format of any existing control type.
- Do not add Windows-specific logic to the Console or Control modules.

## Dependencies
- Introduce no new third-party or standard-library imports. The renderer already imports the typing names and control types it needs; reuse them.
- Reuse the wrapper's existing set-title method. It asserts that the title is shorter than 255 characters. Inherit that behavior; do not duplicate it.

## Naming
- Enum member: SET_WINDOW_TITLE.
- Console method: set_window_title, with a parameter named title.
- Control classmethod: title, matching the short classmethod style of bell, home, and alt_screen.
- Test names follow the existing test-file naming pattern (see Test requirements).

## Validation
- Do not add type checks or content checks to the Console method or to the Control classmethod. The title is not trimmed, checked, or escaped beyond what is described above.

## Error handling
- Writing to a non-terminal console is not an error. Return false.
- Do not catch or convert exceptions raised by the wrapper's set-title method. Its length assertion propagates on legacy consoles.
- Do not introduce new exception types.

## Logging
- Add no logging.

## Documentation
- The Console method docstring follows the repository's Google style, with a summary line and Args and Returns sections. It must state these warnings: Rich provides no way to reset the title to its previous value, so the title persists after the application exits; some shells reset titles before and after each command and most do not; some terminals need configuration changes or do not support titles; other software may overwrite the title; and a true result means only that the control was written, not that the title changed.
- The Control classmethod docstring has a summary line and an Args entry for title.
- CHANGELOG: add one bullet under the Unreleased section, under an Added heading. Create that heading above the Fixed heading if it is missing. The bullet describes the ability to change the terminal window title, links to pull request 2200, and follows the existing bullet format.

## Security
- The title text is written into the escape sequence unmodified, as in the reference implementation. Do not add stripping or escaping unless it leaves ordinary titles byte-for-byte unchanged.

## Reliability
- When the console is not a terminal, including when recording is enabled or output is redirected, no title sequence may enter the buffer. Escape text must never reach pipes, recordings, or exported text through this method.
- On legacy consoles, the title call must occur only on the standard-stream render path. Redirected legacy output must not reach the Windows title call.

## Maintainability
- Use the existing control-type extension mechanism: the enum, the formatting table, the union, and the legacy renderer dispatch. Do not create a parallel path or a legacy-only branch in the Console.

## Compatibility
- Existing control types, their escape output, and the legacy renderer behavior for other control types are unchanged.
- Widening the control code union is additive.
- Code that does not call the new method or classmethod is unaffected.

## Behavioral acceptance criteria
- On a terminal that is not a legacy console, set_window_title with the text "hello" writes exactly the title sequence for "hello" and returns true.
- On a console that is not a terminal (including recording and redirected output), set_window_title writes nothing and returns false.
- Control.title with "hello" yields a segment whose text is the title sequence, with no style, and whose control list holds exactly one title control code containing the title control type and "hello".
- Constructing the title control does not raise.
- The legacy renderer, given a segment carrying one title control code with "hello", calls the wrapper's set-title method exactly once with "hello" and makes no other terminal call for that code.
- On a legacy Windows console writing to a standard stream, set_window_title results in the set-title call when the buffer is rendered.

## Test requirements
- Console test (all platforms): create a console with forced terminal output and an empty environment. If the console is a legacy Windows console, return without asserting. Otherwise capture the output of set_window_title with the text "hello", and assert that the captured text equals the title sequence for "hello" and that the return value is true.
- Control test: assert that Control.title with "hello" produces a segment equal to the title sequence text, no style, and a control list containing exactly the title control type paired with "hello".
- Renderer test (Windows only; skip on other platforms): use a mocked wrapper, render a buffer containing one segment whose control list holds a title control with the text "Hello, world!", and assert that the set-title method was called exactly once with that text.
- Place the tests in the existing test modules for the Console, Control, and Windows renderer, following their current patterns.
- Formatting: all test code added or changed for this feature must be black-formatted under the repository's configuration (default line length of 88 characters). A literal, call, or list that fits on one line within that limit and has no trailing comma that forces expansion must be written on one line, not split across lines.
- No other test changes are required by this feature.
