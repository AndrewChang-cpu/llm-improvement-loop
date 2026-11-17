Terminal window title setting

## Goals
- Let applications set the window title through the Console, reusing the existing control path.
- ANSI terminals receive the OSC 0 sequence; legacy Windows consoles call the wrapper's set-title method.

## Scope
- Out of scope: reading or restoring the title, sanitizing text, changing existing controls, configuration options, and the Windows wrapper class.

## Assumptions
- Legacy Windows detection and the buffer-flush standard-stream check stay unchanged.
- The wrapper already provides set-title; reuse it.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Standard stream: an output stream the legacy render path can address directly.
- Title control: a control of type SET_WINDOW_TITLE whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, ignoring the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: buffer a title control segment and return true.
3. At buffer flush, a legacy Windows console writing to a standard stream passes the buffer to the legacy renderer, which calls set-title once per title control, in order.
4. Other render paths emit the title sequence as text; control segments are dropped when output is not a terminal.

## Data model
- Control type enum: add exactly one member, SET_WINDOW_TITLE, after the highest existing value; renumber nothing.
- Control code: a type followed by parameters; a title control code is the type then the title text.
- The control code union must admit title control codes and pass mypy under the repository configuration.

## API contracts
- Console method set_window_title: one parameter, title; returns a boolean. True when the control was written; False, with nothing written, when not a terminal. Never raises for non-terminal consoles. True means written, not that the title changed.
- Control classmethod title: one parameter, title; returns a Control whose segment text is the title sequence, no style, and whose control list holds one title control code.
- Pass the title control to Control as one two-item argument; separate positional arguments fail at runtime.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, pass the second item as the sole argument to set-title.

## Module architecture
- Segment module: enum member and union. Control module: formatting entry and classmethod; escape bytes live only here.
- Console module: set_window_title beside show_cursor and set_alt_screen; no Windows calls or legacy checks.
- Windows renderer: one new branch in the legacy dispatch. Win32 wrapper unchanged. No import cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain, following the parameterized-control pattern.
- Register the type in formatting table, enum and union, and renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Add no imports; reuse names the renderer already imports.
- Write title text unmodified: no type checks, trimming, or escaping.

## Error handling
- Do not catch or convert wrapper set-title exceptions, including its under-255-character assertion. Add no exception types or logging.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; shells may reset it, terminals may need configuration or lack support, other software may overwrite it.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased bullet under Added (create above Fixed if missing) linking pull request 2200.

## Test requirements
- Console test, all platforms: forced terminal output, empty environment; skip the assertion on legacy Windows. Otherwise assert set_window_title("hello") writes the sequence and returns true.
- Control test: Control.title("hello") yields the sequence, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; render a title control with "Hello, world!"; assert set-title is called exactly once with that text.
- Put tests in existing modules, Black-formatted at 88 characters.
