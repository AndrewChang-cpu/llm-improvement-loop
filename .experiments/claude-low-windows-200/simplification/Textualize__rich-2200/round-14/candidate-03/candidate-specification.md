Terminal window title setting

## Workflows
1. Console buffers a title control only when show_cursor passes.
2. Legacy Windows flush calls set-title once per title control.
3. Other paths emit the sequence as text; control segments drop when not a terminal.

## Data model
- Append SET_WINDOW_TITLE to the control type enum without renumbering.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): returns true when written, false when not a terminal; never raises. No Windows calls.
- Control title(title): returns an unstyled Control whose text is the title sequence, carrying one title control with the title text.
- Legacy renderer: passes the control's second item to set-title.

## Implementation constraints
- Follow the existing if/elif control pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch.
- Change no existing values or output; write title text unmodified; catch no wrapper exceptions.
- Format with Black at 88 characters.

## Documentation
- Console docstring: Rich cannot restore titles; true means only the control was written.
- Control docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test (forced terminal, skipped on legacy Windows): set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the unstyled sequence and a title control holding "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
