Terminal window title setting

## Scope
- Out of scope: reading or restoring titles, sanitizing, configuration.

## Workflows
1. On flush, legacy Windows calls set-title once per title control, in order.
2. Other paths emit the sequence as text; control segments drop when not a terminal.

## Data model
- Add SET_WINDOW_TITLE to the control type enum after existing values, renumbering none.
- Title control: SET_WINDOW_TITLE plus title text, admitted to the control code union.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, BEL (0x07).

## API contracts
- Console method set_window_title(title): returns true when the control is written (show_cursor check passes), false when not a terminal. Never returns None or raises; true does not mean the title changed.
- Control classmethod title(title): returns an unstyled Control of the title sequence, holding one title control as a two-item argument.
- Legacy renderer: the sole set-title argument is the control's second item.

## Implementation constraints
- Console: set_window_title beside show_cursor, no Windows calls. Windows renderer: one legacy branch.
- Segment and control modules: enum member, union, escape bytes.
- Follow the existing parameterized-control if/elif pattern; add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omitting one is a defect.
- Change no existing values or output; write title text unmodified; do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore the title; true means only the control was written.
- Control docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields an unstyled sequence and a matching title control.
- Windows renderer test: mocked wrapper; set-title called once with "Hello, world!".
- Format with Black, 88 characters.
