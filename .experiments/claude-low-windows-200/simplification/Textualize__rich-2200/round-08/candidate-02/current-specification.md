Terminal window title setting

## Scope
- Applications change the window title through the Console, reusing the existing control path.
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, configuration, and the Windows wrapper class. Keep legacy detection unchanged.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, not the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: buffer a title control through the existing control path and return true.
3. At buffer flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in order.
4. Other render paths emit the title sequence as text; control segments drop when output is not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- A title control code is the type followed by the title text. The control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title; returns a boolean. True means the control was written; False, with nothing written, when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title: one parameter, title; returns a Control whose segment text is the title sequence, with no style, and whose control list holds one title control code. Pass that code as one two-item argument; separate arguments fail at runtime.
- Format entry: for the title type, the text formatter returns the title sequence.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: formatting entry and classmethod; escape bytes live only here.
- Console module: set_window_title beside show_cursor; no Windows calls or legacy checks.
- Windows renderer: one new branch in the legacy dispatch. Win32 wrapper unchanged.

## Implementation constraints
- Follow the parameterized-control pattern in the existing if/elif chain. Add no imports.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Change no existing control values or output.
- Write title text unmodified: no type checks, trimming, or escaping.

## Error handling
- Do not catch or convert wrapper set-title exceptions, including its under-255-character assertion. Add no exception types or logging.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; terminals may reset or overwrite it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test, all platforms: forced terminal; skip on legacy Windows. Assert set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; assert set-title is called exactly once with "Hello, world!" for a rendered title control.
- Put tests in existing modules; format with Black at 88 characters.
