Terminal window title setting

## Scope
- Out of scope: reading, restoring, sanitizing, or configuring titles.

## Workflows
1. Console buffers a title control only when the show_cursor check is true, returning that result.
2. Legacy Windows flush calls set-title once per title control, in order.
3. Other paths emit the sequence as text; control segments drop when not a terminal.

## Data model
- Add SET_WINDOW_TITLE to the control type enum after existing values without renumbering.
- A title control pairs SET_WINDOW_TITLE with the title text; the union admits it.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): returns true when the control was written, false when not a terminal. Never returns None or raises; true does not mean the title changed.
- Control title(title): returns an unstyled Control whose text is the title sequence, taking one title control code.
- Legacy renderer: passes the control's second item as the sole set-title argument.

## Module architecture
- Console module: set_window_title beside show_cursor; no Windows calls.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omissions are defects.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore titles; true means only the control was written.
- Control docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the unstyled sequence segment and a title control pairing "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black at 88 characters.
