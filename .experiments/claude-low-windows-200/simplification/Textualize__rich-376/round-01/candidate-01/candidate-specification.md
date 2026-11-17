## Goals

Add a public Console method named out for low-level text output. It writes its positional objects as plain text, applies a simple style, and highlights by default. It does not pretty-print, wrap, crop, apply markup, or replace emoji codes. It is a thin alternative to print for callers who want raw text.

## Scope

In scope:
- One new public method on the Console class in the console module, placed next to print.
- A docstring for the method.
- A CHANGELOG entry under Unreleased, in the existing Added list.
- A "Low level output" section in the Console documentation page, after the logging material.
- Tests in the existing console test module.

Out of scope:
- Any change to the behavior, signature, or defaults of print, log, control, or other existing methods.
- New rendering paths, output types, or Console state.

## Assumptions

- Console.print already accepts the options out needs (style, highlight, emoji, markup, no_wrap, overflow, crop, end), so out delegates to it.
- Print's option handling is the reference for how each option is interpreted.

## Terminology

- Raw output: the string formed by converting each positional object with normal string conversion (not pretty-printing or repr-style formatting) and joining the results with the separator.
- Console default: the Console's highlight setting, used when a per-call highlight value is None.
- Render hook: a callback registered on the Console that print runs over its renderables before rendering. Output from out must pass through these hooks.

## Workflows

1. The caller invokes out with zero or more objects and optional separator, end string, style, and highlight values.
2. out converts every object to a string and joins them with the separator. With no objects, the raw output is the empty string.
3. out calls the Console's print method exactly once, with the raw output as its only object. It passes style, highlight, and end through, and fixes emoji and markup processing off, no-wrap on, overflow set to ignore, and cropping off.
4. Output follows the normal print path: render hooks run, the buffer is used, and output is flushed or captured like any other print output.
5. out returns nothing.

Because out always passes one string to print, a call with no objects still writes the end string. It does not trigger print's blank-line path.

## Data model

- No new data structures, classes, or fields.
- The existing buffer and flush behavior is used unchanged. out keeps no pending output of its own.

## API contracts

- out is a public instance method of Console.
- Positional parameters: zero or more arbitrary objects, collected as a variable-length group.
- sep: a string, default a single space, placed between converted objects.
- end: a string, default a newline, written after the output.
- style: a style name or Style object, default none (no style).
- highlight: a boolean defaulting to true, not none. True forces highlighting even when the Console was created with highlighting disabled. False turns highlighting off. None defers to the Console default.
- The method returns nothing.
- The docstring must state that highlight defaults to true. The reference signature default is the source of truth.
- Parameter names sep, end, style, and highlight must match print's names so callers can move between the two without renaming.

## Module architecture

- out belongs in the Console class of the console module, grouped with print and control.
- out is a thin layer: build the raw output, then delegate to print. It must not write to the buffer or output file directly, and must not create a second rendering path.
- Rendering, highlighting, buffering, and render-hook handling stay in the existing print pipeline.

## Implementation constraints

- Add no new imports. Annotation types (Any, Union, Style) are already available in the console module.
- Do not change print's or control's signature or behavior.
- Keep the code compatible with the Python versions the project already supports.

## Dependencies

- No new third-party or internal packages.
- No changes to packaging, lock, or requirements files.

## Naming

- Method name: out. Parameter names: objects (variable group), sep, end, style, highlight.
- The basic functional test must be named exactly test_out. Additional tests use the test_out prefix followed by the aspect they check, such as markup, emoji, highlight, or render hook.

## Validation

- out adds no validation. Objects are converted with normal string conversion, and the separator and end string are used as given.
- Add no type checks or coercion beyond what print already performs.

## Error handling

- Exceptions raised while converting an object to a string propagate unchanged.
- No new error types, catch-and-retry, or silent fallback.

## Logging

- out does not log anything and adds no logging calls.

## Documentation

- The docstring describes the low-level behavior: no pretty printing, no wrapping, no markup, optional highlighting, and basic style. It documents sep, end, style, and highlight with their actual defaults.
- The Console documentation page gets a "Low level output" section after the logging section. It explains that out is a lower-level alternative to print and log, lists what it does and does not do, and mentions highlighting and basic style.
- The CHANGELOG gets one Unreleased Added bullet, "Added Console.out", matching neighboring entries.

## Compatibility

- The change is purely additive. Existing print, log, and control behavior and defaults are unchanged.

## Behavioral acceptance criteria

- Several objects with a separator and end string are written as converted objects joined by the separator, followed by the end string, with no wrapping at a narrow width. Example: at width 10, five copies of "foo bar" joined by "." and ended with "X" produce "foo bar.foo bar.foo bar.foo bar.foo barX".
- Markup-like text (square brackets containing style names) and emoji codes are written literally.
- A container object is written as its string conversion, not a formatted structure.
- Output is not cropped to the console width.
- With the default highlight value, highlighting applies even when the Console was created with highlighting disabled.
- With highlight set to none, the Console's highlight setting decides. With false, no highlighting applies.
- A style given to out is applied the same way print applies it.
- Render hooks registered on the Console run for out output, as they do for print output.
- out returns no value.

## Test requirements

- Add tests to the existing console test module, next to the existing print style test. Do not change or remove existing tests.
- Include test_out, covering separator, end string, and no-wrap behavior at a fixed narrow width.
- Plain-text assertions use a Console writing to an in-memory stream with a fixed width, not forced into terminal mode, and compare captured plain text.
- Assertions on escape sequences must construct the Console with the color system the existing style tests use ("truecolor"). Forcing terminal mode alone is not enough, and results must not depend on TERM, COLORTERM, or NO_COLOR. Do not assert exact escape bytes unless they were traced through the print path with cropping disabled. Prefer plain text, or verify styles another way.
- With highlighting enabled in a terminal-capable console, do not assert literal substrings containing characters the default highlighter styles (brackets, braces, quotes, numbers, slashes), because styling splits them into spans. Use a non-terminal console or disable highlighting for those.
- Cover at least: separator and end with wrapping suppressed; markup and emoji literal; style accepted; highlight default, none, and false where checkable as plain text.
- New imports, such as a render hook base class, go at the top of the test module with the existing imports, not inside a test function.
