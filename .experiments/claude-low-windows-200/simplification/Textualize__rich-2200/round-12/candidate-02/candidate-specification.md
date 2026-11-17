Terminal window title setting

## Scope
- Out of scope: reading or restoring titles, sanitizing, configuration.

## Workflows
1. Console set_window_title, placed beside show_cursor, buffers a title control only when the show_cursor check passes, returning it.
2. At flush, legacy Windows calls set-title once per title control.
3. Other render paths emit the sequence as text; control segments drop when not a terminal.

## Data model
- Add SET_WINDOW_TITLE to the control type enum after existing values; renumber nothing.
- A title control pairs SET_WINDOW_TITLE with the title text; add it to the control code union.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): returns true when the control was written, false when not a terminal. Never returns None or raises; true does not mean the title changed.
- Control classmethod title(title): returns an unstyled Control whose text is the title sequence, holding one title control code as a two-item argument.
- Legacy renderer: passes the control's second item as the only set-title argument.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern. Add no imports. No Windows calls in Console.
- Register the type in the formatting table, enum, union, and renderer dispatch; omissions are defects.
- Change no existing values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore the title; true means only the control was written.
- Control classmethod docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields an unstyled sequence segment and a "hello" title control.
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Black, 88 characters.
