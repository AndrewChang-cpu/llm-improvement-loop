Window title setting

## Scope
- Out of scope: reading, restoring, sanitizing, or configuring titles.

## Workflows
1. Console buffers a title control only when show_cursor is true, returning its result.
2. Legacy Windows flush calls set-title once per title control, in order.
3. Other paths emit the sequence as text; control segments drop without a terminal.

## Data model
- Add SET_WINDOW_TITLE to the control type enum.
- Union admits title controls: SET_WINDOW_TITLE plus title text.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): returns true when written, false when not a terminal. Never returns None or raises.
- Control title(title): returns an unstyled Control wrapping one title control, with the title sequence as text.
- Legacy renderer: passes the control's second item as the sole set-title argument.
- Place set_window_title beside show_cursor, with no Windows calls.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern; add no imports.
- Register the type in formatting table, enum, union, and renderer dispatch.
- Change no existing control values or output; write title text unmodified; do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore titles; true only means the control was written.
- Control docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking PR 2200.

## Test requirements
- Console test (forced terminal, skipped on legacy Windows): set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the unstyled sequence and a title control with "hello".
- Renderer test (Windows only, mocked wrapper): set-title called once with "Hello, world!".
- Format with Black at 88 characters.
