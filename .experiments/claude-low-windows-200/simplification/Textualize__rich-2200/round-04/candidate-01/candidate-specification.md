Terminal window title setting

## Goals
- Let applications set the window title through the Console's existing control path.
- On ANSI-capable terminals, emit the OSC 0 title sequence. On legacy Windows consoles, the legacy renderer calls the wrapper's set-title method.

## Scope
- In scope: the control type, Control classmethod, Console method, renderer branch, CHANGELOG entry, and tests below.
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, configuration options, and the Windows wrapper.

## Assumptions
- Legacy Windows detection and the standard-stream check at buffer flush already exist; leave them unchanged.
- The wrapper already provides a set-title method. Reuse it.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Standard stream: an output stream the legacy render path can address directly.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, a right bracket, the digit zero, a semicolon, the title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, as show_cursor does, not the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment through the existing control path and return true.
3. At buffer flush on a legacy Windows console writing to a standard stream, the legacy renderer calls the wrapper's set-title method once per title control, in buffer order, with the title text.
4. Other render paths emit the title sequence as segment text. Control segments are dropped when output is not a terminal. True means the sequence was written, not that the title changed.

## Data model
- Control type enumeration: add exactly one member, SET_WINDOW_TITLE, after the highest existing value. Do not renumber existing members.
- Control code: a tuple of control type followed by parameters. A title control code is the type followed by the title text.
- The declared union must admit a control type followed by text and type-check under mypy; existing shapes stay admitted.

## API contracts
- Console method set_window_title: one positional text parameter named title; returns a boolean. True when the title control was written; False, with nothing written, when the console is not a terminal. Never raises for non-terminal consoles.
- Control classmethod title: one text parameter named title; returns a Control whose segment text is the title sequence, whose style is none, and whose control list holds exactly one title control code.
- Construction rule: pass the title control to the Control constructor as one two-item argument (type and text). Separate positional arguments fail at runtime.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, read the title from the second item and pass it as the only argument to the wrapper's set-title method.
- Naming: enum member SET_WINDOW_TITLE; Console method set_window_title; Control classmethod title, matching bell, home, and alt_screen.

## Module architecture
- Segment module: enum member and control code union.
- Control module: formatting table entry and classmethod. Escape bytes live only here.
- Console module: set_window_title beside show_cursor and set_alt_screen. It delegates to the control path, with no Windows calls or legacy checks.
- Windows renderer module: one new branch in the legacy dispatch. Win32 wrapper: unchanged.
- Imports point downward only, with no cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain, reading the title from the two-item form as other parameterized controls do.
- Gate the Console method only on the terminal check. Add no console-level guard for legacy consoles.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Add no imports; reuse the names the renderer already imports.

## Validation
- Write the title text unmodified, as in the reference. Add no type checks, trimming, or escaping.
- Non-terminal consoles, including recording and redirected output, never buffer a title sequence. Legacy title calls happen only on the standard-stream path.

## Error handling
- Do not catch or convert exceptions from the wrapper's set-title method; its length assertion (under 255 characters) propagates.
- Add no new exception types and no logging.

## Documentation
- Console docstring: Google style with summary, Args, and Returns. Note that Rich cannot restore the previous title, so it persists after exit; some shells reset it per command, most do not; some terminals need configuration or lack support; other software may overwrite it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased bullet under an Added heading (create it above Fixed if missing), describing the change and linking pull request 2200, in the existing format.

## Test requirements
- Console test (all platforms): forced terminal output, empty environment. Skip the assertion on legacy Windows; otherwise assert set_window_title("hello") writes the title sequence and returns true.
- Control test: Control.title("hello") yields a segment equal to the title sequence, no style, and a control list holding the title type paired with "hello".
- Renderer test (Windows only): mocked wrapper; a segment with one title control holding "Hello, world!" calls set-title exactly once with that text.
- Put tests in the existing test modules, Black-formatted at 88 characters.
