Terminal window title setting

## Scope
Applications set the window title through the Console's existing control path. Out of scope: reading the title, sanitizing text, changing existing controls, configuration, the Windows wrapper, and legacy detection.

## Terminology
- Terminal: a Console passing the show_cursor terminal check.
- Title control: a control of type SET_WINDOW_TITLE whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, not the legacy-windows flag. Not a terminal: buffer nothing and return false. Terminal: buffer a title control and return true.
3. On flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in order.
4. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Add one control type member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- A title control code is the type followed by the title text; the control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title; returns a boolean. True means the control was written; False, with nothing written, when not a terminal. Never returns None or raises.
- Control classmethod title: one parameter, title; returns a Control whose segment text is the title sequence, with no style, and whose control list holds one title control code. Pass that code as one two-item argument.
- Format entry and legacy renderer: the text formatter returns the title sequence for the title type; the renderer passes the second item of a title control code as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: formatting entry and classmethod; escape bytes only here.
- Console module: set_window_title beside show_cursor; no Windows calls or legacy checks.
- Windows renderer: one branch in legacy dispatch; Win32 wrapper unchanged.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern; add no imports.
- Register the type in all three places (formatting table, enum and union, renderer dispatch); omitting one is a defect.
- Change no existing control values or output. Write title text unmodified.

## Error handling
- Do not catch or convert wrapper set-title exceptions, such as its under-255-character assertion; add no logging.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal; skip on legacy Windows. Assert set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment without style and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; assert set-title is called once with "Hello, world!".
- Put tests in existing modules; format with Black at 88 characters.
