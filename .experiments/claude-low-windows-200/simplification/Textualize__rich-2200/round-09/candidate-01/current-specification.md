Terminal window title setting

## Scope
- Applications change the window title through the Console, using the existing control path.
- Out of scope: reading or restoring the title, sanitizing text, configuration, and the Windows wrapper class.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Title control: a control of type SET_WINDOW_TITLE whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check. If not a terminal, it buffers nothing and returns false. Otherwise it buffers a title control through the existing control path and returns true.
3. At buffer flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in order.
4. Other render paths emit the title sequence as text; control segments drop when output is not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- A title control code is the type followed by the title text. The control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written, false when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title (formatting entry: title type returns the title sequence): one parameter, title. Returns a Control with the title sequence as segment text, no style, and one title control code in its control list. Pass that code as one two-item argument; separate arguments fail at runtime.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: holds escape bytes.
- Console module: set_window_title beside show_cursor; no Windows calls or legacy checks.
- Windows renderer: one new branch in the legacy dispatch.

## Implementation constraints
- Follow the parameterized-control pattern in the existing if/elif chain. Add no imports.
- Register the type in formatting table, enum and union, and renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Write title text unmodified.

## Error handling
- Do not catch or convert wrapper exceptions, including the under-255-character assertion.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; terminals may reset it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal; skip on legacy Windows; set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Put tests in existing modules; format with Black at 88 characters.
