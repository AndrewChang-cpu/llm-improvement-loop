Terminal window title setting

## Goals
- Let an application request a terminal window title change through the Console, using the same control path as the existing cursor and screen controls.
- On ANSI-capable terminals, emit the OSC 0 title sequence. On legacy Windows consoles, dispatch the title to the existing legacy Windows renderer, which calls the wrapper's set-title method.
- Return a boolean saying whether the title control was written to the output buffer.

## Scope
- In scope: one new control type; one Control classmethod; one Console method; one renderer branch; one CHANGELOG entry; the tests under Test requirements.
- Out of scope: reading the title; restoring a previous title; sanitizing title text; changing existing control types or their output; new configuration options; changes to the Windows console wrapper.
- Contributor checklists, pull-request type selections, review notes, and mentions of individuals must not appear in the specification or code comments.

## Assumptions
- Legacy Windows detection and the standard-stream check at buffer flush already exist and stay unchanged.
- The legacy Windows wrapper already provides a set-title method. Reuse it.
- Other software may overwrite the title at any time, so persistence is not guaranteed.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set, meaning Windows without virtual-terminal (VT) escape processing.
- Standard stream: an output stream the legacy render path can address directly. The render path checks this at buffer flush.
- Title control: a control whose type is the new SET_WINDOW_TITLE member and whose parameter is the title text.
- Title sequence: ESC, a right bracket, the digit zero, a semicolon, the title text, and BEL (0x07). This is OSC 0 with a BEL terminator.

## Workflows
1. The application asks the Console to set the window title to a text value.
2. The Console method checks only whether the console is a terminal. It must not check the legacy-windows flag, matching show_cursor rather than set_alt_screen.
   - If not a terminal: buffer nothing and return false.
   - If a terminal: build a title control from the text, add its segment to the buffer through the existing control path, and return true.
3. At buffer flush, if the console is a legacy Windows console and the output is a standard stream, the buffer goes to the legacy renderer. For each title control, in buffer order, the renderer calls the wrapper's set-title method once with the title text.
4. On all other render paths, the title segment carries the title sequence as its text and follows the ordinary render rules. Control segments are dropped when output is not a terminal.
5. A true result means the sequence was written. It does not confirm the title changed.

## Data model
- Control type enumeration: add exactly one member, SET_WINDOW_TITLE, with the next integer after the highest existing value. Do not renumber existing members.
- Control code: a tuple whose first item is the control type and whose remaining items are parameters. The title control code is two items: the control type, then the title text.
- The declared union of control code shapes must also admit a control type followed by text, while keeping existing shapes. It must type-check under the repository's mypy configuration.
- Store the title text exactly as given. No transformation at the data level.

## API contracts
- Console method: named set_window_title, one positional text parameter named title, returns a boolean. Returns true when the title control was written to the buffer; returns false for non-terminal consoles, writing nothing. It must never return nothing and must not raise for non-terminal consoles.
- Control classmethod: named title, one text parameter named title, returns a Control. Its segment text is the title sequence, its style is none, and its control list holds exactly one title control code.
- Construction rule: pass the title control to the Control constructor as a single two-item argument. Passing the type and title as separate positional arguments fails at runtime, because each positional argument is read as a bare control type or a control code.
- Format entry: for the title control type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer contract: for a title control code, read the title text from the code's second item and call the wrapper's set-title method with it as the only argument.

## Module architecture
- Segment module: the enum member and the control code union.
- Control module: the formatting table entry and the Control classmethod. Escape bytes live only here.
- Console module: set_window_title, beside show_cursor and set_alt_screen. It delegates to the control path and contains no Windows API calls and no legacy checks.
- Windows renderer module: one new branch in the legacy render dispatch.
- Win32 console wrapper: unchanged; its set-title method is reused.
- Dependencies point one way: Console depends on Control, which depends on Segment. The renderer depends on the wrapper and Segment. No upward imports or cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain over control types, beside the other control types. Follow the parameterized-control pattern: interpret the two-item form, then read the parameter.
- Gate the Console method only on the terminal check. Add no legacy-windows guard and no console-level false return for legacy consoles; the renderer handles that path.
- Register the new type in all three places: the formatting table, the enum and union, and the legacy renderer dispatch. Omitting any one is a defect.
- Do not change existing control type values or output.
- Add no Windows-specific logic to the Console or Control modules.

## Dependencies
- Add no new third-party or standard-library imports. Reuse the typing names and control types the renderer already imports.
- Reuse the wrapper's set-title method, which asserts the title is shorter than 255 characters. Do not duplicate that check.

## Naming
- Enum member: SET_WINDOW_TITLE. Console method: set_window_title, with parameter title. Control classmethod: title, matching the short style of bell, home, and alt_screen.

## Validation
- Add no type or content checks to the Console method or Control classmethod. The title is not trimmed, checked, or escaped beyond what is described here.

## Error handling
- Writing to a non-terminal console is not an error. Return false.
- Do not catch or convert exceptions from the wrapper's set-title method. Its length assertion propagates on legacy consoles.
- Introduce no new exception types.

## Logging
- Add no logging.

## Documentation
- The Console method docstring follows the repository's Google style, with a summary line and Args and Returns sections. It must state: Rich cannot restore the previous title, so the title persists after exit; some shells reset titles before and after each command and most do not; some terminals need configuration or do not support titles; other software may overwrite the title; and true means only that the control was written.
- The Control classmethod docstring has a summary line and an Args entry for title.
- CHANGELOG: add one bullet under Unreleased, under an Added heading created above the Fixed heading if missing. The bullet describes the ability to change the terminal window title, links to pull request 2200, and follows the existing format.

## Security
- Write the title text into the escape sequence unmodified, as the reference does. Add no stripping or escaping unless ordinary titles stay byte-for-byte identical.

## Reliability
- When the console is not a terminal, including recording and redirected output, no title sequence may enter the buffer. Escape text must never reach pipes, recordings, or exported text.
- On legacy consoles, the title call occurs only on the standard-stream render path. Redirected legacy output never reaches the Windows title call.

## Compatibility
- Existing control types, their escape output, and other legacy renderer behavior are unchanged. Widening the union is additive. Code that does not call the new method or classmethod is unaffected.

## Behavioral acceptance criteria
- On a terminal that is not a legacy console, set_window_title with "hello" writes exactly the title sequence for "hello" and returns true.
- On a non-terminal console (including recording and redirected output), set_window_title writes nothing and returns false.
- Control.title with "hello" yields a segment whose text is the title sequence, with no style, and whose control list holds exactly one title control code containing the title control type and "hello".
- Constructing the title control does not raise.
- The legacy renderer, given a segment with one title control code holding "hello", calls the wrapper's set-title method exactly once with "hello" and makes no other terminal call for that code.
- On a legacy Windows console writing to a standard stream, set_window_title results in the set-title call when the buffer renders.

## Test requirements
- Console test (all platforms): create a console with forced terminal output and an empty environment. If it is a legacy Windows console, return without asserting. Otherwise capture set_window_title("hello") output and assert it equals the title sequence for "hello" and the return value is true.
- Control test: Control.title with "hello" produces a segment equal to the title sequence, no style, and a control list containing exactly the title control type paired with "hello".
- Renderer test (Windows only; skip elsewhere): use a mocked wrapper, render a buffer with one segment whose control list holds a title control with "Hello, world!", and assert set-title was called exactly once with that text.
- Place tests in the existing Console, Control, and Windows renderer test modules, following their patterns.
- All added or changed test code must be black-formatted (88-character limit). Literals, calls, or lists that fit on one line must stay on one line, with no trailing comma forcing expansion.
- No other test changes are required.
