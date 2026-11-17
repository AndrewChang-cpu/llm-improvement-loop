Terminal window title setting

## Scope
- Applications change the window title through the Console's existing control path.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Title control: a SET_WINDOW_TITLE control whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, BEL (0x07).

## Workflows
1. The application calls the Console method with title text. The method buffers a title control only when the terminal check is true, and returns that result.
2. At flush, legacy Windows calls set-title once per title control, in order.
3. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Control type enum: add one member, SET_WINDOW_TITLE, after existing values; renumber nothing.
- A title control code is the type plus the title text. The control code union must admit it and pass mypy.

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written, false when not a terminal. Never returns None or raises.
- Control classmethod title: one parameter, title. Returns a Control of the title sequence, unstyled, with one title control code. Pass the code as one two-item argument; separate arguments fail at runtime.
- Legacy renderer: pass the code's second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: escape bytes.
- Console module: set_window_title beside show_cursor; no Windows calls.
- Windows renderer: one new branch in the legacy dispatch.

## Implementation constraints
- Follow the parameterized-control if/elif pattern. Add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title, terminals may reset it, and true means only the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a title control holding "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black, 88 columns.
