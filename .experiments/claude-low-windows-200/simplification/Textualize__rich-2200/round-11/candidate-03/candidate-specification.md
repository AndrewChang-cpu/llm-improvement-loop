Terminal window title setting

## Scope
- Applications set the window title through the Console's control path.
- Out of scope: reading or restoring the title, sanitizing text, configuration.

## Workflows
1. The Console method buffers a title control only when the show_cursor terminal check is true.
2. At flush, legacy Windows calls set-title once per title control, in order.
3. Other render paths emit the sequence as text; control segments drop when not a terminal.

## Data model
- Add SET_WINDOW_TITLE to the control type enum after existing values.
- A title control is SET_WINDOW_TITLE plus title text; the control code union must admit it.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written, false when not a terminal. Never returns None or raises.
- Control classmethod title: one parameter, title. Returns a Control with the title sequence as text, no style, and one title control code as a single two-item argument.
- Legacy renderer: pass a title control code's second item as the sole argument to set-title.

## Module architecture
- Console module: set_window_title beside show_cursor, no Windows calls.
- Segment and control modules: enum member, union, escape bytes.
- Windows renderer: one legacy dispatch branch.

## Implementation constraints
- Follow the parameterized-control if/elif pattern. Add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring: no title restoration; true means only the control was written.
- Control classmethod docstring: summary and title Args entry.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a title control.
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black at 88 characters.
