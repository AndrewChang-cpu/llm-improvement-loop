## Goals

Provide a public Console method, named out, for low-level text output. Its positional objects are written as plain text. It applies a simple style and, by default, highlighting. It does not pretty-print, wrap, crop, apply markup, or replace emoji codes. The method is a thin, deliberate alternative to print for callers who want raw text.

## Scope

In scope:
- One new public method on the Console class in the console module, placed next to print.
- A docstring for the method.
- A CHANGELOG entry under the Unreleased section, in the existing Added list.
- A "Low level output" section in the Console documentation page, after the logging material, describing out's behavior and when to use it.
- Tests in the existing console test module.

Out of scope:
- Any change to the behavior, signature, or defaults of print, log, control, or other existing methods.
- New rendering paths, new output types, or new Console state.

## Assumptions

- Console.print already accepts the options that out needs (style, highlight, emoji, markup, no_wrap, overflow, crop, end), so out is built by delegating to it.
- "Console default" means the Console's own highlight setting (the constructor argument, which is on by default). It applies only when a per-call highlight value is None.
- Existing print behavior is the reference for how each option is interpreted.

## Terminology

- Raw output: the single string formed by converting each positional object to text with normal string conversion (not pretty-printing or repr-style formatting) and joining the results with the separator.
- Console default: the Console's highlight setting, used when a per-call highlight value is None.
- Render hook: a callback registered on the Console that print runs over its renderables before rendering. Output produced by out must pass through these hooks.
- Pretty printing: rich's structured formatting of containers and objects. out must not apply it.

## Workflows

1. The caller invokes out with zero or more objects and optional separator, end string, style, and highlight values.
2. out converts every object to a string and joins the strings with the separator into raw output. If no objects are given, the raw output is the empty string.
3. out calls the Console's print method exactly once with the raw output as its only object. It passes the style, highlight value, and end string through. It fixes emoji and markup processing off, no-wrap on, overflow set to ignore, and cropping off.
4. Because the call goes through print, output follows the normal path: render hooks run, the buffer is used, and the output is flushed or captured like any other print output.
5. out returns nothing.

Note: because out always supplies one string object to print, a call with no objects still writes the end string. It does not trigger print's blank-line path.

## Data model

- No new data structures, classes, or fields are introduced.
- The Console's existing buffer and flush behavior is used unchanged. out does not hold its own pending output.

## API contracts

- out is a public instance method of Console, with the name out.
- Positional parameters: zero or more arbitrary objects, collected as a variable-length group.
- sep: a string, default a single space. It is placed between converted objects.
- end: a string, default a newline. It is written after the output.
- style: a style name or a Style object, default none (no style applied).
- highlight: a boolean with a default of true. The default must be true, not none. Passing true forces highlighting even when the Console was created with highlighting disabled. Passing false turns highlighting off. Passing none defers to the Console default.
- The method returns nothing.
- The docstring must state the actual default of highlight (true). The docstring must not say the default is none, because the reference code's default is true and the reference code is the source of truth.
- Parameter names must match print's names for the parameters they share (sep, end, style, highlight), so callers can move between print and out without renaming.

## Module architecture

- out belongs in the Console class of the console module, grouped with print and control.
- out must be a thin layer: build the raw output, then delegate to print. It must not write to the Console's buffer or to the output file directly, and it must not create a second rendering or output path.
- Rendering, highlighting, buffering, and render-hook handling stay in the existing print pipeline. out only chooses the fixed options.
- out must not depend on any new module or helper.

## Implementation constraints

- Add no new imports. The type names needed for annotations (Any, Union, Style) are already available in the console module.
- Do not change print's signature or behavior.
- Do not change control's behavior.
- Keep the code compatible with the Python versions the project already supports.

## Dependencies

- No new third-party or internal packages.
- No changes to packaging files, lock files, or requirements files.

## Naming

- Method name: out.
- Parameter names: objects (variable group), sep, end, style, highlight. These mirror print's names.
- Test names follow the existing console test naming, with a test_out prefix.

## Validation

- out adds no validation of its own. Objects are converted with normal string conversion. The separator and end string are used as given.
- Do not add type checks or coercion beyond what print already performs.

## Error handling

- Exceptions raised while converting an object to a string propagate to the caller unchanged.
- No new error types, no catch-and-retry, and no silent fallback are introduced.

## Logging

- out does not log anything. It does not add logging calls.

## Documentation

- The method docstring describes the low-level behavior: no pretty printing, no word wrapping, no markup, optional highlighting, and basic style. It documents sep, end, style, and highlight with their actual defaults (highlight defaults to true).
- The Console documentation page gets a "Low level output" section after the logging section. It explains that out is a lower-level alternative to print and log, lists what it does and does not do, and mentions highlighting and basic style.
- The CHANGELOG gets one bullet under Unreleased, Added: "Added Console.out", in the same style as the neighboring entries.

## Compatibility

- The change is purely additive. Existing print, log, and control behavior is unchanged.
- Existing callers are unaffected because no existing names or defaults change.

## Behavioral acceptance criteria

- A call with several objects, a separator, and an end string writes the converted objects joined by the separator, followed by the end string, with no wrapping at a narrow width. Example expectation in prose: with width 10, five copies of "foo bar" joined by "." and ended with "X" produce "foo bar.foo bar.foo bar.foo bar.foo barX".
- Markup-like text (for example square brackets containing style names) and emoji codes are written literally, not interpreted.
- Output is not pretty-printed: a container object is written as its string conversion, not a formatted structure.
- Output is not cropped to the console width.
- With the default highlight value, highlighting is applied even when the Console was created with highlighting disabled.
- With highlight set to none, the Console's highlight setting decides.
- With highlight set to false, no highlighting is applied.
- A style given to out is applied to the output in the same way print applies it.
- Render hooks registered on the Console run for out output, the same as for print output.
- out returns no value.

## Test requirements

- Add tests to the existing console test module, next to the existing print style test.
- Tests must use a Console that is not a terminal (no forced terminal, no color system) with a fixed width, and must assert against captured plain text.
- Do not assert on escape sequences for styled output unless the expected bytes were traced through the print path with cropping disabled. Prefer asserting plain text or checking that the style is present through a separate, verified means.
- When highlighting is enabled, do not assert a literal substring that contains characters the default highlighter styles (such as brackets, braces, quotes, numbers, or slashes) in a terminal-capable console, because styling splits such text into separate spans. Use a non-terminal console or disable highlighting for those assertions.
- Cover at least: separator and end handling with wrapping suppressed; markup and emoji left literal; style accepted; highlight behavior for the default, none, and false values where it can be checked as plain text.
- The new tests must not change or remove existing tests.
