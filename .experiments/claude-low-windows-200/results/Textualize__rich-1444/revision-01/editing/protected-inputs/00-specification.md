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
- Tests, documentation, and a changelog entry as described in the Test requirements and Documentation sections.

Out of scope:
- The reference also changes Console.print so its highlight option is passed into text rendering. Do not implement this as part of the feature. print_json does not depend on it, because it prints a renderable whose highlighting is already applied.
- Version bumps and renaming the Unreleased changelog section to a release number.
- Any change to dependency declarations or lock files.

## Assumptions
- The input is one JSON document supplied as text. The feature does not accept pre-parsed Python data.
- Colors and attributes come from the console theme. A style name that is not registered in the theme produces no styling and is not an error.

## Terminology
- JSON renderable: the JSON class in the json module. It holds a highlighted Text and exposes that Text through the renderable protocol.
- Token group: a named match produced by the JSON highlighter: brace, bool_true, bool_false, null, number, or str.
- Unmatched text: text not covered by any token group, such as whitespace, newlines, commas, and colons. Unmatched text receives no JSON style.

## Workflows
1. Console print_json: accepts the JSON text, an indent value (keyword-only integer, default 4), and a highlight flag (keyword-only boolean, default true). It builds a JSON renderable with those values and sends it to the console's normal print path with default print options. It does not pass soft_wrap or other overrides. It returns nothing.
2. JSON renderable construction, in this order:
   a. Parse the input text with the standard JSON parser. If parsing fails, the parser's error propagates and nothing is printed.
   b. Serialize the parsed data with the standard JSON serializer using the given indent. Keep the serializer's other defaults (no key sorting).
   c. Choose the JSON highlighter when highlight is true, or the framework's null highlighter when it is false.
   d. Apply the chosen highlighter to the serialized string and keep the Text it returns. Do not rely on mutating an input Text in place.
   e. On that Text, set no-wrap to true and overflow to none, so the renderable is not wrapped or cropped by the console however it is printed or logged.
   f. The renderable's protocol method returns that stored Text.
3. Package-level print_json: takes the same parameters with the same names, kinds, and defaults, and delegates to the global console's print_json with those values. It returns nothing and does not write output itself.
4. Token matching (JSON highlighter): apply one combined pattern whose alternatives are tried in this order:
   - brace: any one of the bracket characters { } [ ] ( ).
   - literals: the whole words true, false, and null, matched case-sensitively in lowercase only.
   - number: an optional minus sign, one or more digits, an optional fraction, and an optional exponent marked by lowercase e with an optional sign; the match must not be preceded by a word character. A hexadecimal form with a 0x prefix followed by hex digits is also a number.
   - str: a double-quoted string, optionally preceded by b, that is not preceded by a backslash or a word character and ends at the first double quote not preceded by a backslash.
   Because the alternatives are one pattern, a str match consumes the whole string, so brackets, digits, and literal words inside a string get no separate token styling.
   Each token group is styled with the base style prefix "json." followed by the group name, for example json.brace or json.str. Unmatched text is left unstyled.
5. Expected rendering of the sample input (an array of four elements: false, true, null, and the string "foo") with defaults and color enabled:
   - Six lines, followed by a trailing newline printed by the console.
   - Line 1 is the opening bracket, styled as json.brace.
   - Lines 2 to 5 each contain four leading spaces, the element, and a trailing comma except the last. false, true, and null use their literal styles; "foo" uses the string style. The commas and line breaks are unstyled.
   - Line 6 is the closing bracket, styled as json.brace.
6. Highlighting disabled: the output has the same plain text and the same no-wrap setting, and no token styles are applied.
7. Printing or logging a JSON renderable directly through the console's print or log methods uses the same no-wrap setting from step 2e, so long lines are not wrapped.

## Data model
- The JSON renderable holds exactly one piece of state: the Text built at construction. It does not keep the input string, the parsed data, or the indent and highlight flags after construction.
- The default theme style table gains six keys, placed with the other default styles:
  - json.brace: bold.
  - json.bool_true: bright green, italic.
  - json.bool_false: bright red, italic.
  - json.null: magenta, italic.
  - json.number: cyan, bold, not italic.
  - json.str: green, not italic, not bold.
- No other json.* keys are added. In particular, do not add a json.key entry.

## API contracts
- Console print_json: a method on Console. It takes one required text argument named json, a keyword-only indent (integer, default 4), and a keyword-only highlight (boolean, default true). It returns nothing.
- Package-level print_json: the same argument names, kinds, and defaults as the Console method. It returns nothing and is reachable as a name in the package root.
- JSON renderable: the constructor takes json (required text), then indent (integer, default 4, accepted positionally or by keyword), then highlight (boolean, default true, accepted positionally or by keyword). It exposes only the renderable protocol method, which returns the stored Text.
- indent is a count of spaces. It is an integer, not a string.
- Do not add extra public parameters (such as a data argument, serializer option pass-through, or an optional json argument), and do not add alternative constructors or classmethods to the JSON renderable.
- The package root's list of exported names is left unchanged.

## Module architecture
- rich/json.py: a new module containing the JSON renderable and the command-line entry guarded by the main check. It depends only on the highlighter and text modules.
- rich/highlighter.py: the JSON highlighter class is added in this module, after the repr highlighter, as a subclass of the regex highlighter base class.
- rich/default_styles.py: the six json.* entries are added to the default style table.
- rich/console.py: Console print_json is placed directly after the print method. It imports the JSON renderable inside its body.
- rich/__init__.py: the package-level print_json function is placed after the package-level print function and before inspect.
- No other modules change.

## Implementation constraints
- Highlighting must use the existing regex highlighter extension point: a subclass with a base style prefix and a list of patterns, applied through the text's regex-highlight operation. Do not write a custom tokenizer, character scanner, or separate highlighting loop in the JSON module.
- Do not use the repr highlighter or any other highlighter for JSON. Its rules (capitalized True/False/None, URL, path, and call patterns) misfire on JSON content.
- Use the value returned by a highlighter call. The highlighter returns a new Text and does not guarantee in-place change of the input.
- When highlighting is off, use the framework's null highlighter so both paths share the same code.
- Console print_json must not pass soft_wrap; wrapping is suppressed by the renderable's own Text settings.
- Formatting (parse and serialize) belongs to the JSON renderable. Console print_json only builds the renderable and prints it. The package-level function only delegates.
- Use the standard library JSON module only. Do not add a second construction path.

## Dependencies
- The JSON renderable uses only the standard library JSON module plus the existing text and highlighter modules. It must not import the console module or the package root.
- Console print_json imports the JSON renderable lazily inside its body, not at module load.
- The package-level function uses the existing global console accessor and adds no new import.
- No new third-party packages and no changes to dependency declarations.

## Naming
- Public names: print_json (Console method and package-level function), JSON (renderable class in the json module), and JSONHighlighter (highlighter class in the highlighter module).
- Highlighter base style prefix: "json.".
- Token group names and theme keys are exactly those listed in Workflows and Data model.
- Parameter names: json, indent, and highlight.

## Validation
- Input validity is checked only by the standard JSON parser. Do not add a separate type check or a custom error message in print_json, Console print_json, or the JSON renderable.
- indent is used as an integer count of spaces.

## Error handling
- Invalid JSON: the parser's error propagates unchanged from the Console method, the package-level function, and the JSON renderable constructor. Parsing happens before any output, so no partial output is printed.
- Command-line file read failure: print a message to a stderr console in the form "Unable to read" followed by the path representation and the error text, then exit with status -1.
- Command-line invalid JSON content: not caught; the error propagates as in the constructor.

## Logging
- No logging is added.

## Documentation
- docs/source/console.rst: add a "Printing JSON" section after the logging section and before the low-level output section. It covers the Console print_json method, logging a JSON renderable, the package-level import, and the command-line usage.
- docs/source/reference/json.rst: new page that auto-documents the rich.json module members.
- CHANGELOG.md: add an entry under the existing Unreleased section's Added list. Do not rename Unreleased and do not change the package version.
- Docstrings: Google style with an Args section. indent is documented as defaulting to 4.

## Usability
- Command-line entry point: running the json module as a program with a required positional path argument prints the file's JSON pretty printed and highlighted, using the same JSON renderable with default settings and soft wrapping enabled on print.
- The path argument is opened as a file. The reference's help text mentions "-" for stdin, but the reference does not implement stdin; do not claim stdin support.
- The help text summary is "Pretty print json".

## Compatibility
- Existing print, log, and output behavior for non-JSON content is unchanged.
- The default theme table gains only the six json.* keys.
- The package root's exported-name list is unchanged.

## Behavioral acceptance criteria
- Console print_json with defaults on the sample input yields the six-line rendering described in Workflows, with each element indented by four spaces and a trailing newline.
- The package-level function yields the same plain text as the Console method with the same arguments.
- indent=2 changes the indentation to two spaces. JSON(text, 4) is accepted and uses four spaces.
- highlight=False yields the same plain text with no token styling.
- Lowercase true, false, and null are styled. Brackets, digits, and literal words inside a string are not styled separately from the string.
- Commas, colons, spaces, and line breaks carry no JSON style.
- A long single-line JSON value is not wrapped when printed via print_json, console print of a JSON renderable, or console log of a JSON renderable.
- Invalid JSON raises the parser's error and prints nothing.
- The six json.* keys exist in the default theme.

## Test requirements
- Add a test to the console tests: call print_json on the sample input with a truecolor console writing to an in-memory stream, and assert the exact styled output described in Workflows step 5.
- Add a test to the package-level print tests: call the package-level print_json with the global console captured, and assert the plain four-space output with a trailing newline.
- Do not modify existing tests.
