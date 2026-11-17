Terminal window title setting

## Scope
- Applications set the window title through the Console's existing control path.
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, configuration options, and the Windows wrapper class.
- Legacy Windows detection and the standard-stream check stay unchanged. Reuse the wrapper's set-title.

## Terminology
- Terminal: a Console whose terminal check, the one show_cursor uses, is true.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Title control: a SET_WINDOW_TITLE control whose parameter is the title text.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## Workflows
1. The Console method checks only the terminal check, not the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control through the existing control path and return true.
2. At buffer flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in buffer order.
3. Other render paths emit the title sequence as text. Control segments drop when output is not a terminal.

## Data model
- Add SET_WINDOW_TITLE as the last enum member; renumber nothing.
- A title control code is the type followed by the title text; the control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title(title): returns a boolean. True means the control was written; False, with nothing written, when not a terminal. Never None or raises when not a terminal. True does not mean the title changed.
- Control classmethod title(title): returns a Control whose segment text is the title sequence, with no style, and whose control list holds one title control code.
- Pass the title control to Control as one two-item argument; separate positional arguments fail at runtime.
- Text formatter: for the title type, takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment: enum member and union. Control: formatting entry and classmethod; escape bytes live only here.
- Console: set_window_title beside show_cursor; no Windows calls or legacy checks.
- Windows renderer: one new branch in the legacy dispatch. Win32 wrapper unchanged. No import cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain, like other parameterized controls.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Add no imports; reuse names the renderer already imports.
- Write title text unmodified: no type checks, trimming, or escaping.

## Error handling
- Do not catch or convert wrapper set-title exceptions, including its under-255-character assertion. Add no exception types or logging.

## Documentation
- Console docstring (Google style): Rich cannot restore the title; terminals may reset or ignore it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet (create above Fixed if missing) linking pull request 2200.

## Test requirements
- Console test, all platforms: forced terminal output, empty environment; skip on legacy Windows. Otherwise assert set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; render a title control with "Hello, world!"; assert set-title is called once with that text.
- Put tests in existing modules, Black-formatted.
