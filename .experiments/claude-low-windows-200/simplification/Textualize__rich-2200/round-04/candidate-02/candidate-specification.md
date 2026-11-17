Terminal window title setting

## Goals
- Let an application change the window title through the Console, using the same control path as the existing cursor and screen controls.
- On ANSI-capable terminals, emit the OSC 0 title sequence. On legacy Windows consoles, the legacy renderer calls the wrapper's set-title method.

## Scope
- In scope: one control type, one Control classmethod, one Console method, one renderer branch, one CHANGELOG entry, and the tests below.
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, new configuration options, and changing the Windows wrapper.

## Assumptions
- Legacy Windows detection and the standard-stream check at buffer flush already exist and stay unchanged.
- The wrapper already provides a set-title method. Reuse it.
- Other software may overwrite the title at any time.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, a right bracket, the digit zero, a semicolon, the title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, matching show_cursor rather than set_alt_screen.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment through the existing control path and return true.
3. At buffer flush, a legacy Windows console writing to a standard stream sends the buffer to the legacy renderer, which calls the wrapper's set-title method once per title control, in buffer order, with the title text.
4. Other render paths emit the title sequence as segment text. Control segments are dropped when output is not a terminal.
5. True means the sequence was written, not that the title changed.

## Data model
- Control type enumeration: add exactly one member, SET_WINDOW_TITLE, after the highest existing value. Do not renumber existing members.
- Control code: a tuple whose first item is the control type and whose remaining items are parameters. A title control code has two items: the type and the title text.
- The declared union of control code shapes must admit a control type followed by text and type-check under the repository's mypy configuration. Existing shapes stay admitted.

## API contracts
- Console method set_window_title: one positional text parameter named title; returns a boolean. True when the title control was written; False, with nothing written, when the console is not a terminal. Never returns nothing and never raises for non-terminal consoles.
- Control classmethod title: one text parameter named title; returns a Control whose segment text is the title sequence, whose style is none, and whose control list holds exactly one title control code.
- Construction rule: pass the title control to the Control constructor as one two-item argument. Separate positional arguments fail at runtime.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, read the title from the second item and pass it as the only argument to the wrapper's set-title method.

## Module architecture
- Segment module: enum member and control code union.
- Control module: formatting table entry and classmethod. Escape bytes live only here.
- Console module: set_window_title beside show_cursor and set_alt_screen. It delegates to the control path and has no Windows API calls or legacy checks.
- Windows renderer module: one new branch in the legacy dispatch. Win32 wrapper: unchanged.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain over control types, following the parameterized-control pattern.
- Gate the Console method only on the terminal check. Add no console-level guard for legacy consoles.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Add no imports.

## Validation
- Write the title text unmodified. Add no type checks, trimming, or escaping.
- Non-terminal consoles, including recording and redirected output, never buffer a title sequence. On legacy consoles, the title call happens only on the standard-stream path.

## Error handling
- Do not catch or convert exceptions from the wrapper's set-title method. Its length assertion (under 255 characters) propagates. Add no new exception types.

## Logging
- Add no logging.

## Documentation
- Console docstring: Google style with summary, Args, and Returns. State that Rich cannot restore the previous title, so it persists after exit; that some shells reset titles per command; that some terminals need configuration or lack title support; that other software may overwrite it; and that true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one bullet under Unreleased, under an Added heading (create it above Fixed if missing), describing the change and linking pull request 2200, in the existing format.

## Test requirements
- Console test (all platforms): forced terminal output, empty environment. Skip the assertion on legacy Windows. Otherwise assert set_window_title("hello") writes the title sequence for "hello" and returns true.
- Control test: Control.title("hello") yields a segment equal to the title sequence, no style, and a control list holding the title type paired with "hello".
- Renderer test (Windows only): mocked wrapper; render one segment whose control list holds a title control with "Hello, world!"; assert set-title is called exactly once with that text.
- Put tests in the existing test modules, Black-formatted at 88 characters. No other test changes.
