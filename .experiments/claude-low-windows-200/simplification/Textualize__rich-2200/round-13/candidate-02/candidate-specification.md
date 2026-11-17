Terminal window title setting

## Scope
- Out of scope: reading, restoring, sanitizing, configuring titles.

## Workflows
1. Console buffers a title control only when the show_cursor check passes, returning that result.
2. Legacy Windows flush calls set-title once per title control, in order.
3. Other paths emit the sequence as text; control segments drop outside terminals.

## Data model
- Append SET_WINDOW_TITLE to the control type enum without renumbering.
- Title controls pair SET_WINDOW_TITLE with title text; the union admits them.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): returns true if the control was written, false when not a terminal; never raises.
- Control title(title): returns an unstyled Control of the title sequence for one title control code.
- Legacy renderer: passes the control's second item as the only set-title argument.

## Implementation constraints
- Put set_window_title beside show_cursor; no Windows calls.
- Follow the existing parameterized-control pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch.
- Change no existing control values or output; write title text unmodified; do not catch wrapper exceptions.
- Format with Black, 88 characters.

## Documentation
- Console docstring: Rich cannot restore titles; true only means the control was written.
- Control docstring: summary and title argument.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test (forced terminal, skipped on legacy Windows): set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields an unstyled sequence and a title control with "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
