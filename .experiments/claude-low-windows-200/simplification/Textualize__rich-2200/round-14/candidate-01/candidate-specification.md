Terminal window title setting

## Workflows
1. Legacy Windows flush calls set-title once per title control, in order, using its second item.
2. Other paths emit the sequence as text; non-terminal control segments drop.

## Data model
- Append SET_WINDOW_TITLE to the control type enum without renumbering; a title control pairs it with title text.
- Title sequence: ESC, right bracket, zero, semicolon, title text, BEL (0x07).

## API contracts
- Console set_window_title(title): buffers the control only when show_cursor passes; returns true if written, false if not a terminal. Never raises; true does not mean the title changed. No Windows calls.
- Control title(title): returns an unstyled Control of the title sequence holding one title control.

## Implementation constraints
- Follow the existing if/elif pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch.
- Keep existing output unchanged; write title text unmodified; catch no wrapper exceptions.
- Format with Black at 88 characters.

## Documentation
- Console docstring: Rich cannot restore titles; true means only the control was written.
- Control docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test (forced terminal, skipped on legacy Windows): set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields the unstyled sequence and one title control holding "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
