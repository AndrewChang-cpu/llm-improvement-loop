Terminal window title setting

## Scope
- Applications set the title through the existing Console control path.
- Out of scope: reading or restoring the title, sanitizing text, configuration.

## Workflows
1. The Console method buffers a title control only if the show_cursor terminal check passes, returning that result.
2. At flush, a legacy Windows console calls set-title once per title control, in order.
3. Other render paths emit the title sequence as text; control segments drop when not a terminal.

## Data model
- Append SET_WINDOW_TITLE to the control type enum; renumber nothing.
- A title control is SET_WINDOW_TITLE followed by the title text; the control code union must admit it.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, BEL (0x07).

## API contracts
- Console method set_window_title: one positional parameter, title. Returns true if the control was written, false if not a terminal; never None, never raises. True does not mean the title changed.
- Control classmethod title: one parameter, title. Returns a Control whose segment is the title sequence, with no style and one title control code. Pass the code as one two-item argument, not two arguments.
- Legacy renderer: pass the code's second item as the sole argument to set-title.

## Module architecture
- Console module: set_window_title beside show_cursor; no Windows calls.

## Implementation constraints
- Follow the existing parameterized-control if/elif pattern. Add no imports.
- Register the type in the formatting table, enum, union, and renderer dispatch; omissions are defects.
- Change no existing control values or output. Write title text unmodified. Do not catch wrapper exceptions.

## Documentation
- Console docstring: Rich cannot restore the title; true means only the control was written.
- Control classmethod docstring: summary and title Args entry.
- CHANGELOG: Unreleased Added bullet linking pull request 2200.

## Test requirements
- Console test: forced terminal, skipped on legacy Windows; set_window_title("hello") writes the sequence, returns true.
- Control test: Control.title("hello") yields one unstyled sequence segment and a title control pairing "hello".
- Renderer test (Windows only): mocked wrapper; set-title called once with "Hello, world!".
- Format with Black at 88 characters.
