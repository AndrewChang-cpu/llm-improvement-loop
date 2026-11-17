Terminal window title setting

## Scope
- Applications change the window title through the Console's existing control path.
- Out of scope: reading or restoring the title, sanitizing text, configuration.

## Workflows
1. The Console method buffers a title control only when the terminal check, the same check show_cursor uses, is true, and returns that result.
2. At buffer flush, a legacy Windows console calls set-title once per title control, in order.
3. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Control type enum: add SET_WINDOW_TITLE after existing values; renumber nothing.
- A title control is the SET_WINDOW_TITLE type followed by the title text; the control code union must admit it.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, BEL (0x07).

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true when the control was written, false when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title: one parameter, title. Returns a Control with the title sequence as segment text, no style, and one title control code, passed as a single two-item argument; separate arguments fail at runtime.
- Legacy renderer: pass a title control code's second item as the sole argument to set-title.

## Module architecture
- Console module: set_window_title beside show_cursor; no Windows calls.
- Segment module and control module: enum member, union, and escape bytes.
- Windows renderer: one new branch in the legacy dispatch.

## Implementation constraints
- Follow the parameterized-control pattern in the existing if/elif chain. Add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore the previous title; true means only the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the sequence segment, no style, and a title control pairing "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black at 88 characters.
