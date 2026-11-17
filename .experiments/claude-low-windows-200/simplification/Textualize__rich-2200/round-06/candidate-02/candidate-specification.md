Terminal window title setting

## Goals
- Let applications set the window title through the Console, reusing the existing control path; ANSI terminals get the OSC 0 sequence and legacy Windows consoles call set-title.

## Scope
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, configuration options, and the Windows wrapper class.

## Assumptions
- Legacy Windows detection and the buffer-flush standard-stream check stay unchanged; reuse the wrapper's set-title.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Standard stream: an output stream the legacy render path can address directly.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, ignoring the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment through the existing control path and return true.
3. At buffer flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in buffer order.
4. Other render paths emit the title sequence as text; control segments drop when output is not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- Control code: type followed by parameters; for titles, the type then the title text.
- The control code union admits title control codes; mypy passes under the repository configuration.

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written; false, with nothing written, when not a terminal. Never returns None or raises for non-terminal consoles. True means written, not that the title changed.
- Control classmethod title: one parameter, title; returns a Control with the title sequence as segment text, no style, and exactly one title control code in its control list.
- Construction: pass the title control to Control as one two-item argument; separate positional arguments fail at runtime.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Control: formatting entry and classmethod; escape bytes only here.
- Console: set_window_title beside show_cursor and set_alt_screen, delegating with no Windows calls or legacy checks.
- Windows renderer: one new branch in the legacy dispatch; wrapper unchanged; no import cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain, mirroring parameterized controls.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Add no imports; reuse names the renderer already imports.
- Write title text unmodified: no type checks, trimming, or escaping.

## Error handling
- Do not catch or convert wrapper set-title exceptions, including its under-255-character assertion; add no exception types or logging.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; shells, terminals, and other software may reset or overwrite it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased bullet under Added (create above Fixed if missing) linking pull request 2200.

## Test requirements
- Console test, all platforms: forced terminal output, empty environment; skip on legacy Windows; otherwise assert set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields a segment equal to the sequence, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; render a title control with "Hello, world!"; expect exactly one set-title call with that text.
- Put tests in existing modules, Black-formatted at 88 characters.
