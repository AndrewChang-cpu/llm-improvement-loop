Terminal window title setting

## Scope
- Out of scope: reading or restoring titles, sanitizing, configuration.

## Workflows
1. The Console method buffers a title control only when the show_cursor terminal check is true, returning that result.
2. At buffer flush, legacy Windows calls set-title once per title control, in order.
3. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Add SET_WINDOW_TITLE to the control type enum after existing values; renumber nothing.
- A title control pairs SET_WINDOW_TITLE with the title text, admitted by the control code union.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, BEL (0x07).

## API contracts
- Console method set_window_title(title): returns true when the control was written, false when not a terminal. Never returns None or raises. True does not mean the title changed.
- Control classmethod title(title): returns an unstyled Control whose text is the title sequence and holds one title control code as a single two-item argument.
- Legacy renderer: pass the control's second item as the sole set-title argument.

## Module architecture
- Console module: set_window_title beside show_cursor; no Windows calls.
- Segment and control modules: enum member, union, escape bytes.
- Windows renderer: one new legacy dispatch branch.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern. Add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore the title; true means only the control was written.
- Control classmethod docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the unstyled sequence segment and a title control pairing "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black at 88 characters.
