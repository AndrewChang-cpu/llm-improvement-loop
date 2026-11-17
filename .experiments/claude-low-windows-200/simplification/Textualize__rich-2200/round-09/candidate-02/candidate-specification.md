Terminal window title setting

## Scope
- Applications set the title through the Console's existing control path.
- Out of scope: reading or restoring the title, sanitizing text, configuration, the Windows wrapper.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Title control: a SET_WINDOW_TITLE control whose parameter is the title text.
- Title sequence: ESC, "]0;", title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text. If not a terminal, the method buffers nothing and returns false. Otherwise it buffers a title control and returns true.
2. At flush, a legacy Windows console writing to a standard stream calls set-title once per title control, in order.
3. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Add one enum member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- A title control code is the type followed by the title text. The control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title, one positional parameter: title. Returns true when the control was written, false when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title, one parameter: title. Returns a Control whose segment text is the title sequence, with no style and one title control code in its control list. Pass that code as one two-item argument; separate arguments fail at runtime.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: escape bytes.
- Console module: set_window_title beside show_cursor, no Windows calls.
- Windows renderer: one new legacy dispatch branch.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing control values or output; write title text unmodified.
- Do not catch or convert wrapper exceptions, including the under-255-character assertion.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; terminals may reset it; true means only the control was written.
- Control classmethod docstring: summary and title Args entry.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test (forced terminal, skipped on legacy Windows): set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Place tests in existing modules; format with Black, 88 characters.
