Terminal window title setting

## Goals
- Let an application change the window title through the Console's existing control path.
- On ANSI terminals, emit the OSC 0 title sequence. On legacy Windows consoles, the legacy renderer calls the wrapper's set-title method.

## Scope
- Out of scope: reading or restoring the title, sanitizing title text, changing existing controls, configuration options, and the Windows wrapper class.

## Assumptions
- Legacy Windows detection and the buffer-flush standard-stream check already exist and stay unchanged.
- The wrapper's existing set-title method is reused.

## Terminology
- Terminal: a Console whose terminal check is true, the check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, right bracket, digit zero, semicolon, title text, then BEL (0x07).

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, not the legacy-windows flag.
   - Not a terminal: buffer nothing and return false.
   - Terminal: add a title control segment through the existing control path and return true.
3. At buffer flush, a legacy Windows console writing to a standard stream calls the set-title method once per title control, in buffer order.
4. Other render paths emit the title sequence as text. Control segments are dropped when output is not a terminal.
5. True means the sequence was written, not that the title changed.

## Data model
- Control type enumeration: add exactly one member, SET_WINDOW_TITLE, with the next integer after the highest existing value.
- Control code: a tuple of type followed by parameters. A title control code has two items: the type, then the title text.
- The control code union must admit title codes and pass mypy.

## API contracts
- Console method set_window_title: one positional text parameter named title; returns a boolean. True when the title control was written; False, with nothing written, when the console is not a terminal. Never raises for non-terminal consoles.
- Control classmethod title: one text parameter named title; returns a Control whose segment text is the title sequence, whose style is none, and whose control list holds exactly one title control code.
- Construction rule: pass the title control as one two-item argument to the Control constructor; separate positional arguments fail.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, read the title from the second item and pass it as the only argument to the set-title method.

## Module architecture
- Segment module: enum member and control code union.
- Control module: formatting table entry and classmethod. Escape bytes live only here.
- Console module: set_window_title beside show_cursor and set_alt_screen, delegating to the control path with no Windows calls or legacy checks.
- Windows renderer module: one new branch in the legacy dispatch. Win32 wrapper unchanged. No import cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain, following the parameterized-control pattern.
- Gate the Console method only on the terminal check. No console-level guard for legacy consoles.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Change no existing control values or output. Add no imports; reuse names the renderer already imports.
- Write title text unmodified. No type checks, trimming, or escaping.

## Error handling
- Do not catch or convert wrapper exceptions, including the under-255-character length assertion. Add no exception types or logging.
- Non-terminal consoles never receive a title sequence. On legacy consoles, the title call happens only on the standard-stream render path.

## Documentation
- Console docstring (Google style): Rich cannot restore the previous title; some shells reset titles per command, but most do not; some terminals need configuration or lack title support; other software may overwrite it; true means only that the control was written.
- Control classmethod docstring: summary and an Args entry for title.
- CHANGELOG: one Unreleased bullet under an Added heading (created above Fixed if missing) describing the change and linking pull request 2200, in the existing format.

## Test requirements
- Console test (all platforms): forced terminal output, empty environment. Skip the assertion on legacy Windows. Otherwise assert set_window_title("hello") writes the title sequence and returns true.
- Control test: Control.title("hello") yields the title sequence segment, no style, and a control list pairing the title type with "hello".
- Renderer test (Windows only): mocked wrapper; render a title control with "Hello, world!"; assert set-title is called once with that text.
- Put tests in existing test modules, Black-formatted at 88 characters.
