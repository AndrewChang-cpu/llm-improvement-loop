Terminal window title setting

## Scope
- Applications change the window title through the Console's existing control path. Reading, restoring, sanitizing, configuration, and the Windows wrapper class are out of scope.

## Terminology
- Terminal: a Console whose terminal check (the one show_cursor uses) is true.
- Title control: a control of type SET_WINDOW_TITLE whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
- If the terminal check fails, set_window_title buffers nothing and returns false. Otherwise it buffers a title control and returns true.
- At buffer flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in order.
- Other render paths emit the title sequence as text; control segments drop when output is not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- A title control code is the type followed by the title text. The control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written, false when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title: one parameter, title. Returns a Control whose segment text is the title sequence, with no style and one title control code in its control list. Pass that code as one two-item argument; separate arguments fail at runtime.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Put set_window_title beside show_cursor in Console, with no Windows calls or legacy checks. Segment holds the enum and union; Control holds the escape bytes.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions, including the under-255-character assertion.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; terminals may reset it; true means only that the control was written.
- Control classmethod docstring: summary and Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment with no style and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Black formatting at 88 characters.
