Terminal window title setting

## Scope
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, configuration options, and the Windows wrapper class.
- Legacy Windows detection and the buffer-flush standard-stream check stay unchanged.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The Console method checks only the terminal check, not the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment through the existing control path and return true.
2. At buffer flush, a legacy Windows console writing to a standard stream sends the buffer to the legacy renderer, which calls set-title once per title control, in buffer order.
3. Other render paths emit the title sequence as text; control segments are dropped when output is not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- A title control code is the type followed by the title text. The control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title; returns a boolean. True means the control was written; False, with nothing written, when not a terminal. Never returns None or raises for non-terminal consoles. True does not mean the title changed.
- Control classmethod title: one parameter, title; returns a Control whose segment text is the title sequence, no style, and whose control list holds one title control code. Pass the title control as one two-item argument.
- Format entry: for the title type, the text formatter returns the title sequence for the title text.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: formatting entry, classmethod, and escape bytes.
- Console module: set_window_title beside show_cursor; no Windows calls or legacy checks.
- Windows renderer: one new branch in the legacy dispatch. Win32 wrapper unchanged.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain, following the parameterized-control pattern.
- Register the type in formatting table, enum and union, and renderer dispatch; omitting one is a defect.
- Change no existing control values or output. Add no imports.
- Write title text unmodified: no type checks, trimming, or escaping.
- Do not catch or convert wrapper set-title exceptions. Add no exception types or logging.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; shells and terminals may reset, ignore, or overwrite it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test, all platforms: forced terminal output, empty environment; skip on legacy Windows. Otherwise assert set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; render a title control with "Hello, world!"; assert set-title is called exactly once with that text.
- Put tests in existing modules, Black-formatted at 88 characters.
