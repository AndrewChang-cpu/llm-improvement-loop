Terminal window title setting

## Goals
- Let an application request a window title change through the Console, using the same control path as the existing cursor and screen controls.
- On ANSI terminals, emit the OSC 0 title sequence. On legacy Windows consoles, the renderer calls the wrapper's set-title method.
- Return a boolean saying whether the title control was written to the output buffer.

## Scope
- In scope: one control type, one Control classmethod, one Console method, one renderer branch, one CHANGELOG entry, and the tests under Test requirements.
- Out of scope: reading or restoring the title; sanitizing title text; changing existing control types or their output; changes to the Windows wrapper class.
- Contributor checklists, pull-request type selections, review notes, and mentions of individuals must not appear in the specification or code comments.

## Assumptions
- Legacy Windows detection and the standard-stream check at buffer flush already exist and stay unchanged.
- The wrapper already provides a set-title method. Reuse it.
- Other software may overwrite the title at any time.

## Terminology
- Terminal: a Console whose terminal check is true, the same check show_cursor uses.
- Legacy Windows console: a Console whose legacy-windows flag is set.
- Title control: a control whose type is SET_WINDOW_TITLE and whose parameter is the title text.
- Title sequence: ESC, a right bracket, the digit zero, a semicolon, the title text, then BEL (0x07). This is OSC 0 with a BEL terminator.

## Workflows
1. The application calls the Console method with title text.
2. The method checks only the terminal check, not the legacy-windows flag, matching show_cursor.
   - Not a terminal: buffer nothing and return false.
   - Terminal: build a title control, add its segment to the buffer through the existing control path, and return true.
3. At buffer flush, if the console is a legacy Windows console and the output is a standard stream, the buffer goes to the legacy renderer. For each title control, in buffer order, the renderer calls the wrapper's set-title method once with the title text.
4. On other render paths, the segment carries the title sequence as its text and follows ordinary render rules.
5. True means the sequence was written, not that the title changed.

## Data model
- Control type enumeration: add exactly one member, SET_WINDOW_TITLE, with the next integer after the highest existing value. Do not renumber existing members.
- Control code: a tuple whose first item is the control type and whose remaining items are parameters. The title control code has two items: the type, then the title text.
- The declared union of control code shapes must also admit a control type followed by text, and must type-check under the repository's mypy configuration.
- Store the title text exactly as given.

## API contracts
- Console method set_window_title: one positional text parameter named title; returns a boolean. True when the title control was written; false, with nothing written, when the console is not a terminal. Never returns nothing and never raises for non-terminal consoles.
- Control classmethod title: one text parameter named title; returns a Control whose segment text is the title sequence, whose style is none, and whose control list holds exactly one title control code.
- Construction rule: pass the title control to the Control constructor as one two-item argument. Separate positional arguments fail at runtime, because each is read as a bare type or a control code.
- Format entry: for the title type, the text formatter takes the title text and returns the title sequence.
- Legacy renderer: for a title control code, read the title from the second item and call the wrapper's set-title method with it as the only argument.

## Module architecture
- Segment module: enum member and control code union.
- Control module: formatting table entry and classmethod. Escape bytes live only here.
- Console module: set_window_title beside show_cursor and set_alt_screen. It delegates to the control path, with no Windows calls or legacy checks.
- Windows renderer module: one new branch in the legacy dispatch.
- Win32 wrapper: unchanged. Dependencies point downward only: Console to Control to Segment; renderer to wrapper and Segment. No upward imports or cycles.

## Implementation constraints
- Add the renderer branch to the existing if/elif chain over control types. Follow the parameterized-control pattern: interpret the two-item form, then read the parameter.
- Gate the Console method only on the terminal check. Add no console-level guard for legacy consoles.
- Register the type in all three places: formatting table, enum and union, renderer dispatch. Omitting one is a defect.
- Do not change existing control values or output. No Windows-specific logic in the Console or Control modules.

## Dependencies
- No new imports. Reuse the typing names and control types the renderer already imports.
- The wrapper's set-title method asserts the title is shorter than 255 characters. Inherit this; do not duplicate it.

## Naming
- Enum member SET_WINDOW_TITLE; Console method set_window_title with parameter title; Control classmethod title, matching bell, home, and alt_screen.

## Validation
- No type or content checks, trimming, or escaping. Write the title text unmodified, as in the reference.

## Error handling
- Writing to a non-terminal is not an error: return false.
- Do not catch or convert exceptions from the wrapper's set-title method; its length assertion propagates on legacy consoles.
- Add no new exception types and no logging.

## Documentation
- Console docstring: Google style, summary line, Args and Returns. State that Rich cannot restore the previous title, so it persists after exit; that some shells reset titles around each command and most do not; that some terminals need configuration or lack title support; that other software may overwrite it; and that true means only that the control was written.
- Control classmethod docstring: summary line and an Args entry for title.
- CHANGELOG: one bullet under Unreleased, under an Added heading (create it above Fixed if missing). Describe changing the terminal window title, link pull request 2200, and follow the existing bullet format.

## Reliability
- When the console is not a terminal, including recording and redirected output, no title sequence may enter the buffer.
- On legacy consoles, the title call happens only on the standard-stream render path. Redirected legacy output must not reach it.

## Maintainability
- Use the existing extension mechanism: enum, formatting table, union, renderer dispatch. No parallel path or legacy-only Console branch.

## Compatibility
- Existing control types, their escape output, and other renderer behavior are unchanged. Widening the union is additive.

## Behavioral acceptance criteria
- Non-legacy terminal: set_window_title with "hello" writes exactly the title sequence for "hello" and returns true.
- Non-terminal, including recording and redirected output: writes nothing and returns false.
- Control.title with "hello": segment text is the title sequence, no style, and a control list holding exactly one title control code with the title type and "hello".
- Legacy renderer given one title code with "hello": calls set-title exactly once with "hello" and makes no other terminal call for that code.

## Test requirements
- Console test (all platforms): forced terminal output, empty environment. If the console is legacy Windows, return without asserting. Otherwise assert set_window_title("hello") writes the title sequence for "hello" and returns true.
- Control test: Control.title("hello") yields a segment equal to the title sequence, no style, and a control list holding exactly the title type paired with "hello".
- Renderer test (Windows only; skip elsewhere): mocked wrapper; render one segment whose control list holds a title control with "Hello, world!"; assert set-title is called exactly once with that text.
- Put tests in the existing Console, Control, and Windows renderer test modules, following their patterns. Format added test code with black at 88 characters, keeping one-line statements on one line. No other test changes.
