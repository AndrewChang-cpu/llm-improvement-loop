Terminal window title setting

## Workflows
1. Console buffers a title control only when show_cursor passes.
2. Legacy Windows flush calls set-title once per title control, in order.
3. Other paths emit the sequence as text; non-terminal output drops control segments.

## Data model
- Append SET_WINDOW_TITLE to the control type enum; do not renumber.
- A title control pairs SET_WINDOW_TITLE with title text and joins the union.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): returns true when the control was written, false when not a terminal; never raises.
- Control title(title): returns an unstyled Control holding the sequence and one title control.
- Legacy renderer: passes the control's second item as set-title argument.

## Implementation constraints
- Follow the parameterized-control pattern; add no imports; change no existing output.
- Register the type in the formatting table, enum, union, and renderer dispatch.
- Write title unmodified; catch no wrapper exceptions; use Black at 88 characters.

## Documentation
- Console docstring: Rich cannot restore titles; true means only the control was written.
- Control docstring: summary and title Args.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test (forced terminal, skipped on legacy Windows): set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the unstyled sequence and a title control holding "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
