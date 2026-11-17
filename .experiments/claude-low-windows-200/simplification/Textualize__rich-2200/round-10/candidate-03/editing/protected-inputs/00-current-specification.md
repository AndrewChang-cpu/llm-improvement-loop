Terminal window title setting

## Scope
- Applications change the window title through the Console, using the existing control path.
- Out of scope: reading or restoring the title, sanitizing text, and configuration.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Title control: a control of type SET_WINDOW_TITLE whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks the terminal check. It buffers a title control only when true, and returns that result.
3. At buffer flush, a legacy Windows console calls set-title once per title control, in order.
4. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after existing values; renumber nothing.
- A title control code is the type followed by the title text; the control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written, false when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title: one parameter, title. Returns a Control whose segment text is the title sequence, with no style and one title control code. Pass that code as one two-item argument; separate arguments fail at runtime.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: escape bytes.
- Console module: set_window_title beside show_cursor; no Windows calls.
- Windows renderer: one new branch in the legacy dispatch.

## Implementation constraints
- Follow the parameterized-control pattern in the existing if/elif chain. Add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; terminals may reset it; true means only the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal; skip on legacy Windows; set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black at 88 characters.
