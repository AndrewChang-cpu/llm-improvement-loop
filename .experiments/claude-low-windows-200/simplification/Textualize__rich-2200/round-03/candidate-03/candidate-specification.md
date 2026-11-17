Terminal window title setting

## Goals
- Let an application set the window title through the Console, using the existing control path used by the cursor and screen controls.
- On ANSI terminals, emit the OSC 0 title sequence. On legacy Windows consoles, the legacy renderer calls the wrapper's set-title method.

## Scope
- In scope: one control type, Control classmethod, Console method, renderer branch, CHANGELOG entry, and the tests below.
- Out of scope: reading or restoring the title, sanitizing it, changing existing controls or output, new options, and changes to the Windows wrapper class.

## Assumptions
- Legacy Windows detection and the buffer-flush standard-stream check already exist and stay unchanged.
- The wrapper already provides a set-title method. Reuse it.
- Other software may overwrite the title at any time, so persistence is not guaranteed.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set (Windows without virtual-terminal escape processing).
- Standard stream: an output stream the legacy render path can address directly.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, right bracket, zero, semicolon, the title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, not the legacy-windows flag, matching show_cursor.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment through the existing control path and return true.
3. At buffer flush, a legacy Windows console writing to a standard stream sends the buffer to the legacy renderer, which calls the wrapper's set-title method once per title control, in buffer order.
4. Other render paths emit the title sequence as segment text. Control segments are dropped when output is not a terminal.

## Data model
- Control type enumeration: add one member, SET_WINDOW_TITLE, with the next integer after the highest existing value. Do not renumber existing members.
- Control code: a tuple whose first item is the control type and whose remaining items are parameters. The title control code is the type, then the title text.
- The declared control code union must admit a type followed by text and must type-check under the repository's mypy configuration. Existing shapes stay admitted.
- Store the title text exactly as given.

## API contracts
- Console method set_window_title: one positional text parameter named title; returns a boolean. True when the title control was written. False, with nothing written, when the console is not a terminal. Never returns nothing and never raises for non-terminal consoles.
- Control classmethod title: one text parameter named title; returns a Control whose segment text is the title sequence, whose style is none, and whose control list holds exactly one title control code.
- Construction rule: pass the type and text as one two-item tuple to the Control constructor. Separate positional arguments fail at runtime, because the constructor reads each one as a bare type or a control code.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, read the title from the second item and pass it as the only argument to the wrapper's set-title method.

## Naming
- SET_WINDOW_TITLE, set_window_title with parameter title, and title, matching bell, home, and alt_screen.

## Module architecture
- Segment module: enum member and control code union.
- Control module: formatting table entry and classmethod. Escape bytes live only here.
- Console module: set_window_title beside show_cursor and set_alt_screen. It delegates to the control path, with no Windows API calls or legacy checks.
- Windows renderer module: one new branch in the legacy dispatch.
- Imports point downward only: Console to Control to Segment; renderer to wrapper and Segment. No cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain over control types, interpreting the two-item form before reading the parameter.
- Gate the Console method only on the terminal check. Add no console-level guard for legacy consoles.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Do not change existing control values or output. Put no Windows-specific logic in the Console or Control modules.
- No new imports. Reuse the typing names and control types the renderer already imports.

## Validation
- Write the title text unmodified, as in the reference. Add no type checks, trimming, stripping, or escaping.

## Error handling
- Writing to a non-terminal is not an error: return false.
- Do not catch or convert exceptions from set-title. Its length assertion (titles shorter than 255 characters) propagates on legacy consoles.
- Add no new exception types and no logging.

## Documentation
- Console docstring: Google style with summary, Args, and Returns. Note that Rich cannot restore the previous title, so it persists after exit; some shells reset titles per command; some terminals need configuration or lack support; other software may overwrite it; true means only that the control was written.
- Control classmethod docstring: summary line and an Args entry for title.
- CHANGELOG: one bullet under Unreleased's Added heading (create it above Fixed if missing), describing the window title change and linking pull request 2200, in the existing format.

## Reliability
- Non-terminal consoles, including recording and redirected output, must never buffer a title sequence. Redirected legacy output must never reach the set-title call.

## Compatibility
- Existing control types, escape output, and renderer behavior are unchanged. Widening the union is additive.

## Test requirements
- Console test (all platforms): forced terminal output, empty environment. Skip the assertion on legacy Windows. Otherwise assert set_window_title("hello") writes the title sequence for "hello" and returns true.
- Control test: Control.title("hello") yields a segment equal to the title sequence, no style, and a control list with the title type and "hello".
- Renderer test (Windows only; skip elsewhere): mocked wrapper; render one segment with a title control holding "Hello, world!"; assert set-title is called once with that text.
- Put tests in the existing Console, Control, and Windows renderer test modules. Black-format added test code at 88 characters.
- No other test changes.
