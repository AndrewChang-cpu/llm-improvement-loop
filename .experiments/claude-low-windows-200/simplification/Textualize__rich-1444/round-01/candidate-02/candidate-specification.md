## Goals
- Let callers pretty print a JSON document supplied as text, with optional syntax highlighting, through three entry points sharing one implementation: a Console method, a package-level function using the global console, and a renderable passed to the console's print or log methods.
- Output is the input re-serialized as multi-line JSON with configurable indentation (default 4 spaces), so the output is valid JSON.
- Provide a command-line entry point that pretty prints a JSON file.

## Scope
In scope:
- A Console method for printing JSON, placed after the print method.
- A package-level function delegating to the global console, placed after the package-level print function.
- A JSON renderable in a new json module, with a command-line entry guarded by the main check.
- A JSON highlighter class in the highlighter module.
- Six json.* entries in the default theme style table.
- Tests, documentation, and a changelog entry as described below.

Out of scope:
- The reference also changes Console.print so its highlight option reaches text rendering. Do not implement this. print_json does not need it, because the renderable's highlighting is already applied.
- Version bumps and renaming the Unreleased changelog section.
- Changes to dependency declarations or lock files.

## Assumptions
- The input is one JSON document supplied as text. Pre-parsed Python data is not accepted.
- Colors and attributes come from the console theme. An unregistered style name produces no styling and is not an error.

## Terminology
- JSON renderable: the JSON class in the json module. It holds a highlighted Text and exposes it through the renderable protocol.
- Token group: a named match from the JSON highlighter: brace, bool_true, bool_false, null, number, or str.
- Unmatched text: text outside every token group, such as whitespace, newlines, commas, and colons. It receives no JSON style.

## Workflows
1. Console print_json: accepts the JSON text, a keyword-only indent (default 4), and a keyword-only highlight flag (default true). It builds a JSON renderable with these values and sends it through the console's normal print path with default print options. It passes no soft_wrap or other overrides and returns nothing.
2. JSON renderable construction, in this order:
   a. Parse the input with the standard JSON parser. On failure the parser's error propagates and nothing is printed.
   b. Serialize the parsed data with the standard JSON serializer using the given indent, keeping its other defaults (no key sorting).
   c. Choose the JSON highlighter when highlight is true, or the framework's null highlighter when false.
   d. Apply the chosen highlighter to the serialized string and keep the Text it returns. Do not rely on in-place mutation.
   e. Set no-wrap to true and overflow to none on that Text, so the console does not wrap the renderable however it is printed or logged.
   f. The renderable's protocol method returns that stored Text.
3. Package-level print_json: takes the same parameters with the same names, kinds, and defaults, delegates to the global console's print_json, and returns nothing.
4. Token matching (JSON highlighter): one combined pattern whose alternatives are tried in this order:
   - brace: any one of { } [ ] ( ).
   - literals: the whole words true, false, and null, matched case-sensitively in lowercase.
   - number: an optional minus sign, one or more digits, an optional fraction, and an optional exponent marked by lowercase e with an optional sign. The match must not be preceded by a word character. A hexadecimal form with a 0x prefix followed by hex digits also counts as a number.
   - str: a double-quoted string, optionally preceded by b, not preceded by a backslash or a word character, ending at the first double quote not preceded by a backslash.
   Because this is one pattern, a str match consumes the whole string, so brackets, digits, and literal words inside a string get no separate styling.
   Each group is styled with the base prefix "json." plus the group name, such as json.brace or json.str. Unmatched text stays unstyled.
5. Expected rendering of the sample input, an array of four elements false, true, null, and "foo", with defaults and color enabled:
   - Six lines, followed by the trailing newline the console prints.
   - Line 1 is the opening bracket, styled json.brace.
   - Lines 2 to 5 each have four leading spaces, the element, and a trailing comma except on the last. false, true, and null use their literal styles; "foo" uses the string style. Commas and line breaks are unstyled.
   - Line 6 is the closing bracket, styled json.brace.
6. Highlighting disabled: the same plain text and no-wrap setting, with no token styles.
7. Printing or logging a JSON renderable directly uses the no-wrap setting from step 2e, so its lines are not wrapped. Under default print options the console still crops lines wider than the console width. Only soft wrapping keeps such lines whole, and print_json does not enable it.

## Data model
- The JSON renderable holds one piece of state: the Text built at construction, in a public attribute named text. It does not keep the input string, parsed data, indent, or highlight flag.
- The default theme style table gains six keys, placed with the other default styles:
  - json.brace: bold.
  - json.bool_true: bright green, italic.
  - json.bool_false: bright red, italic.
  - json.null: magenta, italic.
  - json.number: cyan, bold, not italic.
  - json.str: green, not italic, not bold.
- No other json.* keys are added. In particular, no json.key entry.

## API contracts
- Console print_json: a Console method with one required argument json, a keyword-only indent (integer, default 4), and a keyword-only highlight (boolean, default true). Returns nothing.
- Package-level print_json: the same argument names, kinds, and defaults. Returns nothing and is reachable as a name in the package root.
- JSON renderable: the constructor takes json (required text), then indent (integer, default 4) and highlight (boolean, default true), each accepted positionally or by keyword. The finished Text is stored in the public attribute text. The renderable protocol method returns that same stored Text.
- indent is a count of spaces, given as an integer.
- Add no other public parameters (such as a data argument, serializer pass-through, or optional json argument), no public attributes beyond text, and no alternative constructors or classmethods.
- The package root's exported-name list is unchanged.

## Module architecture
- rich/json.py: new module with the JSON renderable and the main-guarded command-line entry. It depends only on the highlighter and text modules.
- rich/highlighter.py: the JSON highlighter class, added after the repr highlighter, as a subclass of the regex highlighter base class.
- rich/default_styles.py: the six json.* entries.
- rich/console.py: Console print_json placed directly after the print method, importing the JSON renderable inside its body.
- rich/__init__.py: the package-level print_json placed after the package-level print function and before inspect.
- No other modules change.

## Implementation constraints
- Highlight through the existing regex highlighter extension point: a subclass with a base style prefix and a list of patterns, applied through the text's regex-highlight operation. Do not write a custom tokenizer, character scanner, or separate highlighting loop.
- Do not use the repr highlighter or any other highlighter for JSON, since its capitalized True/False/None, URL, path, and call rules misfire on JSON.
- Use the value a highlighter call returns, since it returns a new Text.
- When highlighting is off, use the framework's null highlighter so both paths share the same code.
- Console print_json must not pass soft_wrap. Wrapping is suppressed by the renderable's own Text settings.
- Parsing and serializing belong to the JSON renderable. Console print_json only builds and prints the renderable, and the package-level function only delegates.
- Use only the standard library JSON module, with a single construction path.

## Dependencies
- The JSON renderable uses only the standard library JSON module and the existing text and highlighter modules. It must not import the console module or the package root.
- Console print_json imports the JSON renderable lazily, inside its body.
- The package-level function uses the existing global console accessor and adds no import.
- No new third-party packages and no dependency declaration changes.

## Naming
- Public names: print_json (Console method and package-level function), JSON (renderable class), and JSONHighlighter (highlighter class).
- Base style prefix: "json.". Token group names and theme keys are exactly those in Workflows and Data model.
- Parameter names: json, indent, and highlight.

## Validation
- Input validity is checked only by the standard JSON parser. Do not add a type check or custom error message in any entry point.
- indent is used as an integer count of spaces.

## Error handling
- Invalid JSON: the parser's error propagates unchanged from the Console method, the package-level function, and the renderable constructor. Parsing happens before any output, so nothing partial is printed.
- Command-line file read failure: print to a stderr console "Unable to read", then the path representation and the error text, then exit with status -1.
- Command-line invalid JSON: not caught; the error propagates as in the constructor.

## Logging
- No logging is added.

## Documentation
- docs/source/console.rst: insert one "Printing JSON" section between the end of the logging section and the existing "Low level output" heading. It covers the Console print_json method, logging a JSON renderable, the package-level import, and command-line usage. After the edit, "Low level output" must appear exactly once.
- Do not claim JSON output is never wrapped or cropped. State that the renderable disables wrapping, that default printing crops long lines to the console width, and that soft wrapping keeps full lines.
- docs/source/reference/json.rst: new page auto-documenting the rich.json module members.
- docs/source/reference.rst: add the new page to the existing reference toctree.
- CHANGELOG.md: add an entry to the Unreleased section's Added list. Do not rename Unreleased or change the version.
- Docstrings: Google style with an Args section. Document indent as defaulting to 4.

## Usability
- Command-line entry: running the json module as a program with a required positional path prints the file's JSON pretty printed and highlighted, using the renderable with default settings and soft wrapping enabled on print.
- The path is opened as a file. The reference's help text mentions "-" for stdin, but stdin is not implemented; do not claim stdin support.
- The help summary is "Pretty print json".

## Maintainability
- New and changed code must match the repository's black formatting: double-quoted string literals unless the content contains a double quote. Each import must be used. Before finishing, check for unused imports and single-quoted literals.

## Compatibility
- Existing print, log, and output behavior for non-JSON content is unchanged.
- The default theme table gains only the six json.* keys, and the package root's exported-name list is unchanged.

## Behavioral acceptance criteria
- Console print_json with defaults on the sample input yields the six-line rendering in Workflows, each element indented four spaces, with a trailing newline.
- The package-level function yields the same plain text as the Console method with the same arguments.
- An indent of two produces two-space indentation. A renderable constructed with indent four passed positionally produces four-space indentation.
- Highlighting off yields the same plain text with no token styling.
- Lowercase true, false, and null are styled. Brackets, digits, and literal words inside a string are not styled separately from the string.
- Commas, colons, spaces, and line breaks carry no JSON style.
- A long single-line JSON value is not wrapped when printed via print_json, when the renderable is printed, or when it is logged. Under default printing it may be cropped to the console width; soft wrapping keeps it whole.
- Invalid JSON raises the parser's error and prints nothing.
- The six json.* keys exist in the default theme.

## Test requirements
- Console tests: call print_json on the sample input with a truecolor console writing to an in-memory stream, and assert the exact styled output in Workflows step 5.
- Package-level print tests: call the package-level print_json with the global console captured, and assert the plain four-space output with a trailing newline.
- Do not modify existing tests. Test code follows the Maintainability rules.
