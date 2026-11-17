## Goals
- Let callers pretty print a JSON document supplied as text, with optional syntax highlighting, through three entry points that share one implementation: a Console method, a package-level function that uses the global console, and a renderable that can be passed to the console's print or log methods.
- Printed output is the input re-serialized as multi-line JSON with a configurable indentation (default 4 spaces), so the output is valid JSON.
- Provide a command-line entry point that pretty prints a JSON file.

## Scope
In scope:
- A Console method for printing JSON, placed next to the existing print method.
- A package-level function for printing JSON, placed next to the existing package-level print function and delegating to the global console.
- A JSON renderable in a new json module, including a command-line entry guarded by the main check.
- A JSON highlighter class in the existing highlighter module.
- Six json.* entries in the default theme style table.
- Tests, documentation, and a changelog entry as described below.

Out of scope:
- The reference also changes Console.print so its highlight option is passed into text rendering. Do not implement this. print_json does not depend on it, because the renderable's highlighting is already applied.
- Version bumps, renaming the Unreleased changelog section, and any change to dependency declarations or lock files.

## Assumptions
- The input is one JSON document supplied as text. Pre-parsed Python data is not accepted.
- Colors and attributes come from the console theme. A style name not registered in the theme produces no styling and is not an error.

## Terminology
- JSON renderable: the JSON class in the json module. It holds a highlighted Text and exposes it through the renderable protocol.
- Token group: a named match produced by the JSON highlighter: brace, bool_true, bool_false, null, number, or str.
- Unmatched text: text outside every token group, such as whitespace, newlines, commas, and colons.

## Workflows
1. Console print_json: accepts the JSON text, a keyword-only indent (default 4), and a keyword-only highlight flag (default true). It builds a JSON renderable with those values and sends it to the console's normal print path with default print options. It passes no soft_wrap or other overrides and returns nothing.
2. JSON renderable construction, in this order:
   a. Parse the input text with the standard JSON parser. A parse failure propagates and nothing is printed.
   b. Serialize the parsed data with the standard JSON serializer using the given indent. Keep the serializer's other defaults, including no key sorting.
   c. Choose the JSON highlighter when highlight is true, or the framework's null highlighter when it is false.
   d. Apply the chosen highlighter to the serialized string and keep the Text it returns. Do not rely on mutating an input Text in place.
   e. On that Text, set no-wrap to true and overflow to none, so the console does not wrap the renderable however it is printed or logged.
   f. The renderable's protocol method returns that stored Text.
3. Package-level print_json: takes the same parameters, with the same names, kinds, and defaults, and delegates to the global console's print_json. It returns nothing and writes no output itself.
4. Token matching (JSON highlighter): apply one combined pattern whose alternatives are tried in this order:
   - brace: any one of the bracket characters { } [ ] ( ).
   - literals: the whole words true, false, and null, matched case-sensitively in lowercase only.
   - number: an optional minus sign, one or more digits, an optional fraction, and an optional exponent marked by lowercase e with an optional sign. The match must not be preceded by a word character. A hexadecimal form, a 0x prefix followed by hex digits, is also a number.
   - str: a double-quoted string, optionally preceded by b, not preceded by a backslash or a word character, ending at the first double quote not preceded by a backslash.
   Because the alternatives form one pattern, a str match consumes the whole string, so brackets, digits, and literal words inside a string get no separate styling.
   Each group is styled with the base prefix "json." followed by the group name, such as json.brace or json.str. Unmatched text is left unstyled.
5. Expected rendering of the sample input, an array of four elements (false, true, null, and the string "foo"), with defaults and color enabled:
   - Six lines, followed by the trailing newline the console prints.
   - Line 1 is the opening bracket, styled json.brace.
   - Lines 2 to 5 each have four leading spaces, the element, and a trailing comma except on the last. false, true, and null use their literal styles; "foo" uses json.str. Commas and line breaks are unstyled.
   - Line 6 is the closing bracket, styled json.brace.
6. Highlighting disabled: same plain text and same no-wrap setting, with no token styles.
7. Printing or logging a JSON renderable directly uses the no-wrap setting from step 2e, so its lines are not wrapped. Under default print options the console still crops lines wider than its width. Only soft wrapping keeps such lines whole, and print_json does not enable it.

## Data model
- The JSON renderable keeps one piece of state: the Text built at construction, in a public attribute named text. It does not keep the input string, the parsed data, or the indent and highlight flags.
- The default theme style table gains six keys, placed with the other default styles:
  - json.brace: bold.
  - json.bool_true: bright green, italic.
  - json.bool_false: bright red, italic.
  - json.null: magenta, italic.
  - json.number: cyan, bold, not italic.
  - json.str: green, not italic, not bold.
- No other json.* keys are added. In particular, do not add json.key.

## API contracts
- Console print_json: a Console method taking one required text argument named json, a keyword-only indent (integer, default 4), and a keyword-only highlight (boolean, default true). It returns nothing.
- Package-level print_json: the same names, kinds, and defaults. It returns nothing and is reachable from the package root.
- JSON renderable: the constructor takes json (required text), then indent (integer, default 4) and highlight (boolean, default true), each accepted positionally or by keyword. The finished Text is stored in the public attribute text. The renderable protocol method returns that same stored Text.
- indent is a count of spaces, an integer rather than a string.
- Do not add other public parameters (such as a data argument, serializer pass-through, or an alternative json argument), other public attributes, alternative constructors, or classmethods.
- The package root's list of exported names is unchanged.

## Module architecture
- rich/json.py: new module containing the JSON renderable and the command-line entry guarded by the main check.
- rich/highlighter.py: the JSON highlighter class, added after the repr highlighter as a subclass of the regex highlighter base class.
- rich/default_styles.py: the six json.* entries.
- rich/console.py: Console print_json placed directly after the print method. It imports the JSON renderable inside its body.
- rich/__init__.py: the package-level print_json placed after the package-level print function and before inspect.
- No other modules change.

## Implementation constraints
- Highlight through the existing regex highlighter extension point: a subclass with a base style prefix and a list of patterns, applied through the text's regex-highlight operation. Do not write a custom tokenizer, character scanner, or separate highlighting loop.
- Do not use the repr highlighter or any other highlighter for JSON. Its rules (capitalized True, False, None, URL, path, and call patterns) misfire on JSON.
- Use the value a highlighter call returns, since it returns a new Text and does not guarantee in-place change.
- When highlighting is off, use the framework's null highlighter so both paths share one code path.
- Console print_json must not pass soft_wrap; wrapping is suppressed by the renderable's own Text settings.
- Parsing and serializing belong to the JSON renderable. Console print_json only builds and prints the renderable, and the package-level function only delegates.

## Dependencies
- The JSON renderable uses only the standard library JSON module plus the existing text and highlighter modules. It must not import the console module or the package root.
- Console print_json imports the JSON renderable lazily, inside its body.
- The package-level function uses the existing global console accessor and adds no import.
- No new third-party packages and no changes to dependency declarations.

## Naming
- Public names: print_json (Console method and package-level function), JSON (renderable class in the json module), and JSONHighlighter (highlighter class).
- Highlighter base style prefix: "json.".
- Parameter names: json, indent, and highlight.

## Validation and error handling
- Input validity is checked only by the standard JSON parser. Do not add a type check or custom error message in print_json, Console print_json, or the JSON renderable.
- Invalid JSON: the parser's error propagates unchanged from the Console method, the package-level function, and the constructor. Parsing happens before any output, so nothing partial is printed.
- Command-line file read failure: print to a stderr console a message in the form "Unable to read" followed by the path representation and the error text, then exit with status -1.
- Command-line invalid JSON content: not caught; the error propagates as in the constructor.

## Logging
- No logging is added.

## Documentation
- docs/source/console.rst: insert one "Printing JSON" section between the end of the logging section and the existing "Low level output" heading. It covers the Console print_json method, logging a JSON renderable, the package-level import, and command-line usage. After the edit, the "Low level output" heading must appear exactly once.
- Do not claim JSON output is never wrapped or cropped. State that the renderable disables wrapping, that default printing crops long lines to the console width, and that soft wrapping keeps full lines.
- docs/source/reference/json.rst: new page that auto-documents the rich.json module members.
- docs/source/reference.rst: add the new page to the existing reference toctree.
- CHANGELOG.md: add an entry to the Unreleased section's Added list. Do not rename Unreleased or change the package version.
- Docstrings: Google style with an Args section. Document indent as defaulting to 4.

## Usability
- Command-line entry point: running the json module as a program with a required positional path prints the file's JSON, pretty printed and highlighted, using the JSON renderable with default settings and soft wrapping enabled on print.
- The path is opened as a file. The reference's help text mentions "-" for stdin, but the reference does not implement stdin, so do not claim stdin support.
- Help text summary: "Pretty print json".

## Maintainability
- New source and test code must match the repository's black formatting: double-quoted string literals unless the content contains a double quote. Each import must be used. Before finishing, check new and changed code for unused imports and single-quoted literals the formatter would rewrite.

## Behavioral acceptance criteria
- Console print_json with defaults on the sample input yields the six-line rendering in Workflows step 5, with four-space indentation and a trailing newline.
- The package-level function yields the same plain text as the Console method with the same arguments.
- An indent of two produces two-space indentation. The renderable accepts an explicit indent of four passed positionally and produces four-space indentation.
- Highlighting off yields the same plain text with no token styling.
- Lowercase true, false, and null are styled. Brackets, digits, and literal words inside a string are not styled apart from the string. Commas, colons, spaces, and line breaks carry no JSON style.
- A long single-line JSON value is not wrapped when printed via print_json, when the renderable is printed, or when it is logged. Under default printing it may be cropped to the console width; soft wrapping keeps it whole.
- Invalid JSON raises the parser's error and prints nothing.
- The six json.* keys exist in the default theme.

## Test requirements
- Add a console test: call print_json on the sample input with a truecolor console writing to an in-memory stream, and assert the exact styled output in Workflows step 5.
- Add a package-level print test: call the package-level print_json with the global console captured, and assert the plain four-space output with a trailing newline.
- Do not modify existing tests.
