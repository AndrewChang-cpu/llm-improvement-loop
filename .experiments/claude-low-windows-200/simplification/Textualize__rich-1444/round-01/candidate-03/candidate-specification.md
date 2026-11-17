## Goals
- Let callers pretty print a JSON document supplied as text, with optional syntax highlighting, through three entry points that share one implementation: a Console method, a package-level function using the global console, and a renderable passed to the console's print or log methods.
- Output is the input re-serialized as multi-line JSON with configurable indentation (default 4 spaces).
- Provide a command-line entry point that pretty prints a JSON file.

## Scope
In scope:
- A Console method next to the existing print method.
- A package-level function next to the existing package-level print function, delegating to the global console.
- A JSON renderable in a new json module, with a command-line entry guarded by the main check.
- A JSON highlighter class in the existing highlighter module.
- Six json.* entries in the default theme style table.
- Tests, documentation, and a changelog entry as described below.

Out of scope:
- The reference's change making Console.print pass its highlight option into text rendering. Do not implement it; print_json does not need it.
- Version bumps, renaming the Unreleased changelog section, and dependency or lock file changes.

## Assumptions
- The input is one JSON document supplied as text, not pre-parsed Python data.
- Colors come from the console theme. A style name not registered in the theme produces no styling and is not an error.

## Terminology
- JSON renderable: the JSON class in the json module. It holds a highlighted Text and exposes it through the renderable protocol.
- Token group: a named match from the JSON highlighter: brace, bool_true, bool_false, null, number, or str.
- Unmatched text: text outside every token group, such as whitespace, line breaks, commas, and colons. It receives no JSON style.

## Workflows
1. Console print_json accepts the JSON text, a keyword-only indent (integer, default 4), and a keyword-only highlight flag (boolean, default true). It builds a JSON renderable with those values and prints it through the console's normal print path with default print options. It passes no soft_wrap or other overrides and returns nothing.
2. JSON renderable construction, in order:
   a. Parse the input with the standard JSON parser. On failure, the parser's error propagates and nothing is printed.
   b. Serialize the parsed data with the standard JSON serializer using the given indent, keeping its other defaults (no key sorting).
   c. Choose the JSON highlighter when highlight is true, or the framework's null highlighter when false.
   d. Apply the chosen highlighter and keep the Text it returns. Do not rely on mutating an input Text in place.
   e. On that Text, set no-wrap to true and overflow to none.
   f. The renderable's protocol method returns that Text.
3. Package-level print_json takes the same parameters with the same names, kinds, and defaults, delegates to the global console's print_json, and returns nothing.
4. Token matching in the JSON highlighter uses one combined pattern whose alternatives are tried in this order:
   - brace: any one of { } [ ] ( ).
   - literals: the whole words true, false, and null, matched case-sensitively in lowercase.
   - number: an optional minus sign, one or more digits, an optional fraction, and an optional exponent with lowercase e and an optional sign. The match must not be preceded by a word character. A hexadecimal form with a 0x prefix followed by hex digits also counts as a number.
   - str: a double-quoted string, optionally preceded by b, not preceded by a backslash or a word character, ending at the first double quote not preceded by a backslash.
   Because the alternatives form one pattern, a str match consumes the whole string, so brackets, digits, and literal words inside it get no separate styling.
   Each token group is styled with "json." followed by the group name, such as json.brace or json.str.
5. Sample: an array of four elements (false, true, null, and "foo") with defaults and color enabled renders as six lines plus the console's trailing newline:
   - Line 1: the opening bracket, styled json.brace.
   - Lines 2 to 5: four leading spaces, the element, and a trailing comma except on the last. false, true, and null use their literal styles; "foo" uses json.str. Commas and line breaks are unstyled.
   - Line 6: the closing bracket, styled json.brace.
6. With highlighting disabled, the plain text and no-wrap setting are the same, and no token styles apply.
7. Printing or logging the renderable directly keeps the no-wrap setting from step 2e, so lines are not wrapped. Under default print options the console still crops lines wider than its width. Only soft wrapping keeps such lines whole, and print_json does not enable it.

## Data model
- The renderable holds one piece of state: the Text built at construction, in the public attribute text. It keeps no input string, parsed data, indent, or highlight flag.
- The default theme style table gains six keys, placed with the other default styles:
  - json.brace: bold.
  - json.bool_true: bright green, italic.
  - json.bool_false: bright red, italic.
  - json.null: magenta, italic.
  - json.number: cyan, bold, not italic.
  - json.str: green, not italic, not bold.
- Add no other json.* keys, such as json.key.

## API contracts
- Console print_json: one required argument json, keyword-only indent (integer, default 4), keyword-only highlight (boolean, default true). Returns nothing.
- Package-level print_json: the same names, kinds, and defaults. Returns nothing and is reachable from the package root.
- JSON renderable: constructor takes json (required text), then indent (integer, default 4) and highlight (boolean, default true), each accepted positionally or by keyword. The finished Text is stored in text, and the renderable protocol method returns that same Text.
- indent is a count of spaces, given as an integer.
- Add no other public parameters, public attributes beyond text, alternative constructors, or classmethods on the renderable.
- The package root's exported-name list is unchanged.

## Module architecture
- rich/json.py: new module with the JSON renderable and the main-guarded command-line entry. It depends only on the highlighter and text modules.
- rich/highlighter.py: JSON highlighter class added after the repr highlighter, as a subclass of the regex highlighter base class.
- rich/default_styles.py: the six json.* entries.
- rich/console.py: Console print_json placed directly after the print method. It imports the JSON renderable inside its body.
- rich/__init__.py: package-level print_json placed after the package-level print function and before inspect.
- No other modules change.

## Implementation constraints
- Highlight through the existing regex highlighter extension point: a subclass with a base style prefix and a list of patterns, applied through the text's regex-highlight operation. Do not write a custom tokenizer, character scanner, or separate highlighting loop.
- Do not use the repr highlighter or any other highlighter for JSON, because its rules (capitalized True/False/None, URL, path, call) misfire on JSON.
- Use the value returned by a highlighter call, since it returns a new Text.
- When highlighting is off, use the null highlighter so both paths share the same code.
- Console print_json must not pass soft_wrap; the renderable's own Text settings suppress wrapping.
- Parsing and serializing belong to the renderable. Console print_json only builds and prints the renderable. The package-level function only delegates.
- Use the standard library JSON module only, with one construction path.

## Dependencies
- The renderable uses only the standard library JSON module and the existing text and highlighter modules. It must not import the console module or the package root.
- Console print_json imports the renderable lazily inside its body.
- The package-level function uses the existing global console accessor and adds no import.
- No new third-party packages and no dependency declaration changes.

## Naming
- Public names: print_json (Console method and package-level function), JSON (renderable class), and JSONHighlighter (highlighter class).
- Base style prefix: "json.". Token group names and theme keys are exactly as listed in Workflows and Data model.
- Parameter names: json, indent, highlight.

## Validation
- Only the standard JSON parser checks input validity. Do not add a type check or custom error message in any entry point.

## Error handling
- Invalid JSON: the parser's error propagates unchanged from the Console method, the package-level function, and the renderable constructor. Parsing precedes any output, so nothing partial is printed.
- Command-line file read failure: print "Unable to read" followed by the path representation and the error text to a stderr console, then exit with status -1.
- Command-line invalid JSON: not caught; the error propagates as in the constructor.

## Documentation
- docs/source/console.rst: insert one "Printing JSON" section between the end of the logging section and the existing "Low level output" heading. Cover the Console print_json method, logging a renderable, the package-level import, and command-line usage. The "Low level output" heading must appear exactly once afterward.
- Do not claim JSON output is never wrapped or cropped. State that the renderable disables wrapping, and that default printing crops long lines to the console width, so soft wrapping is needed to keep them whole.
- docs/source/reference/json.rst: new page auto-documenting the rich.json members.
- docs/source/reference.rst: add the new page to the existing reference toctree.
- CHANGELOG.md: add an entry to the Unreleased section's Added list. Do not rename Unreleased or change the version.
- Docstrings: Google style with an Args section. Document indent as defaulting to 4.

## Usability
- Running the json module as a program with a required positional path prints the file's JSON pretty printed and highlighted, using the renderable with default settings and soft wrapping enabled on print.
- The path is opened as a file. The reference's help text mentions "-" for stdin, but the reference does not implement stdin, so do not claim stdin support.
- Help text summary: "Pretty print json".

## Maintainability
- New and changed code must match the repository's black formatting: double quotes unless the content contains a double quote. Remove unused imports and check for single-quoted literals before finishing.

## Compatibility
- Existing print, log, and output behavior for non-JSON content is unchanged. The theme gains only the six json.* keys, and the exported-name list is unchanged.

## Behavioral acceptance criteria
- Console print_json with defaults on the sample yields the six-line rendering in Workflows step 5, with four-space indentation and a trailing newline.
- The package-level function yields the same plain text as the Console method with the same arguments.
- Indent of two gives two-space indentation. The renderable accepts an explicit indent of four passed positionally and produces four-space indentation.
- With highlighting off, the plain text matches with no token styling.
- Lowercase true, false, and null are styled. Brackets, digits, and literal words inside a string are not styled apart from the string.
- Commas, colons, spaces, and line breaks carry no JSON style.
- A long single-line JSON value is not wrapped when printed via print_json, printed as a renderable, or logged. Under default printing it may be cropped to the console width; soft wrapping keeps it whole.
- Invalid JSON raises the parser's error and prints nothing.
- The six json.* keys exist in the default theme.

## Test requirements
- Console tests: call print_json on the sample with a truecolor console writing to an in-memory stream, and assert the exact styled output from Workflows step 5.
- Package-level print tests: call the package-level print_json with the global console captured, and assert the plain four-space output with a trailing newline.
- Do not modify existing tests. New tests follow the Maintainability formatting rules.
