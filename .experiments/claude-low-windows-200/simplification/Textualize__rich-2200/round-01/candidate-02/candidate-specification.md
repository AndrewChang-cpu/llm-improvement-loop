Terminal window title setting

## Goals
- Let an application request a window title change through the Console, using the same control path as the existing cursor and screen controls.
- On ANSI-capable terminals, emit the OSC 0 title sequence. On legacy Windows consoles, dispatch the title to the existing legacy Windows renderer, which calls the wrapper's set-title method.
- Return a boolean saying whether the title control was written to the output buffer.

## Scope
- In scope: one control type; one Control classmethod; one Console method; one renderer branch; one CHANGELOG entry; the tests under Test requirements.
- Out of scope: reading the title; restoring a previous title; sanitizing title text; changing existing control types or their output; new configuration options; changes to the Windows console wrapper class.
- Contributor checklists, pull-request type selections, review notes, and mentions of individuals must not appear in the specification or in code comments.

## Assumptions
- Legacy Windows detection and the standard-stream check at buffer flush already exist and are correct; this feature does not change them.
- The wrapper already has a set-title method. Reuse it.
- Other software may overwrite the title at any time, so persistence is not guaranteed.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set (Windows without virtual-terminal escape processing).
- Standard stream: an output stream the legacy render path can address directly; checked at buffer flush.
- Title control: a control whose type is the new SET_WINDOW_TITLE member and whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, the title text, then BEL (0x07). This is OSC 0 with a BEL terminator.

## Workflows
1. The application asks the Console to set the title to a text value.
2. The Console method checks only the terminal check. It must not check the legacy-windows flag, matching show_cursor rather than set_alt_screen.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment to the buffer through the existing control path and return true.
3. At buffer flush, if the console is a legacy Windows console and the output is a standard stream, the buffer goes to the legacy renderer. For each title control, in order, the renderer calls the wrapper's set-title method once with the title text.
4. On all other render paths, the segment carries the title sequence as its text and follows ordinary render rules. Control segments are dropped when output is not a terminal.
5. True means the sequence was written. It does not confirm the title changed.

## Data model
- Control type enumeration: add exactly one member, SET_WINDOW_TITLE, with the next integer after the highest existing value. Do not renumber existing members.
- Control code: a tuple whose first item is the control type and whose remaining items are parameters. The title control code has two items: the control type and the title text.
- The declared union of control code shapes must also admit the two-item form of a control type followed by text. Existing shapes stay admitted, and the union must type-check under the repository's mypy configuration.
- Store the title text exactly as given.

## API contracts
- Console method set_window_title: one positional parameter, title, of text type; returns a boolean. Returns true when the title control was written. Returns false, writing nothing, when the console is not a terminal. Never returns nothing and never raises for non-terminal consoles.
- Control classmethod title: one text parameter, title; returns a Control. Its segment text is the title sequence, its style is none, and its control list holds exactly one title control code.
- Construction rule: pass the title control to the Control constructor as a single two-item argument (control type and title text). Do not pass the type and the title as separate positional arguments; the constructor treats each positional argument as a bare control type or a control code, so construction fails at runtime.
- Format entry: for the title control type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer contract: for a title control code, read the title from the second item and call the wrapper's set-title method with it as the only argument.

## Module architecture
- Segment module: enum member and control code union.
- Control module: formatting table entry and the Control classmethod. Escape bytes live only here.
- Console module: set_window_title, placed beside show_cursor and set_alt_screen. It delegates to the control path and contains no Windows API calls and no legacy checks.
- Windows renderer module: one new branch in the legacy render dispatch.
- Win32 console wrapper: unchanged.
- Dependency direction: Console depends on Control, which depends on Segment. The renderer depends on the wrapper and Segment. No upward imports or cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain over control types, beside the other control types, following the parameterized-control pattern: interpret the two-item form, then read the parameter.
- Gate the Console method only on the terminal check. Add no console-level guard for legacy consoles.
- Register the control type in all three places: formatting table, enum and union, and renderer dispatch. Omitting any one is a defect.
- Do not change existing control types' values or output.
- Add no Windows-specific logic to the Console or Control modules.

## Dependencies
- Add no new third-party or standard-library imports. Reuse the typing names and control types the renderer already imports.
- Reuse the wrapper's set-title method, which asserts the title is shorter than 255 characters. Inherit that behavior; do not duplicate it.

## Naming
- Enum member SET_WINDOW_TITLE; Console method set_window_title with parameter title; Control classmethod title, matching bell, home, and alt_screen.

## Validation
- Add no type or content checks to the Console method or Control classmethod. The title is not trimmed, checked, or escaped beyond what is described.

## Error handling
- Writing to a non-terminal console is not an error; return false.
- Do not catch or convert exceptions from the wrapper's set-title method. Its length assertion propagates on legacy consoles. Add no new exception types.

## Logging
- Add no logging.

## Documentation
- Console method docstring: Google style, summary line, Args and Returns sections. State these warnings: Rich cannot reset the title, so it persists after exit; some shells reset titles around each command and most do not; some terminals need configuration or lack title support; other software may overwrite the title; true means only that the control was written.
- Control classmethod docstring: summary line and an Args entry for title.
- CHANGELOG: add one bullet under Unreleased, under an Added heading created above Fixed if missing. The bullet describes changing the terminal window title, links pull request 2200, and follows existing bullet format.

## Security
- Write the title text into the sequence unmodified, as the reference does. Add no stripping or escaping unless ordinary titles stay byte-for-byte identical.

## Reliability
- When the console is not a terminal, including recording or redirected output, no title sequence may enter the buffer. Escape text must never reach pipes, recordings, or exported text.
- On legacy consoles, the title call occurs only on the standard-stream render path. Redirected legacy output must not reach the Windows title call.

## Maintainability
- Use the existing control-type extension mechanism (enum, formatting table, union, renderer dispatch). Create no parallel path or legacy-only Console branch.

## Compatibility
- Existing control types, their escape output, and renderer behavior for other control types are unchanged. Widening the union is additive. Code not calling the new method or classmethod is unaffected.

## Behavioral acceptance criteria
- On a terminal that is not a legacy console, set_window_title with "hello" writes exactly the title sequence for "hello" and returns true.
- On a non-terminal console (including recording and redirected output), it writes nothing and returns false.
- Control.title with "hello" yields a segment whose text is the title sequence, no style, and a control list holding exactly one title control code containing the title control type and "hello".
- Constructing the title control does not raise.
- The legacy renderer, given a segment with one title control code holding "hello", calls the wrapper's set-title method exactly once with "hello" and makes no other terminal call for that code.
- On a legacy Windows console writing to a standard stream, set_window_title results in the set-title call when the buffer renders.

## Test requirements
- Console test (all platforms): create a console with forced terminal output and an empty environment. If it is a legacy Windows console, return without asserting. Otherwise capture set_window_title("hello") output and assert it equals the title sequence for "hello" and the return value is true.
- Control test: Control.title with "hello" produces a segment equal to the title sequence, no style, and a control list containing exactly the title control type paired with "hello".
- Renderer test (Windows only; skip elsewhere): mocked wrapper; render a buffer with one segment whose control list holds a title control with "Hello, world!"; assert set-title was called exactly once with that text.
- Place tests in the existing Console, Control, and Windows renderer test modules, following their patterns.
- All added or changed test code must be black-formatted (line length 88). A literal, call, or list that fits on one line and has no trailing comma forcing expansion must stay on one line.
- No other test changes are required.
