## Goals

Provide a public Console method, named out, for low-level text output. Its positional objects are written as plain text, with a simple style and, by default, highlighting. It does not pretty-print, wrap, crop, apply markup, or replace emoji codes. It is a thin alternative to print for callers who want raw text.

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
- Existing print behavior is the reference for how each option is interpreted.

## Terminology

- Raw output: the string formed by converting each positional object with normal string conversion (not pretty-printing or repr-style formatting) and joining the results with the separator.
- Console default: the Console's highlight setting, set by its constructor argument (on by default). It applies only when a per-call highlight value is None.
- Render hook: a callback registered on the Console that print runs over its renderables before rendering. Output from out must pass through these hooks.

## Workflows

1. The caller invokes out with zero or more objects and optional sep, end, style, and highlight values.
2. out converts each object to a string and joins them with sep. With no objects, the raw output is the empty string.
3. out calls the Console's print exactly once, with the raw output as its only object. It passes style, highlight, and end through, and fixes emoji and markup off, no_wrap on, overflow to ignore, and crop off.
4. Because the call goes through print, render hooks run and the buffer, flush, and capture behave as for any print output.
5. out returns nothing.

Because out always supplies one string object, a call with no objects still writes the end string. It does not trigger print's blank-line path.

## Data model

No new data structures, classes, or fields. out uses the Console's existing buffer and flush behavior unchanged and holds no pending output of its own.

## API contracts

- out is a public instance method of Console.
- Positional parameters: zero or more arbitrary objects, collected as a variable-length group.
- sep: a string, default a single space, placed between converted objects.
- end: a string, default a newline, written after the output.
- style: a style name or Style object, default none.
- highlight: a boolean defaulting to true. Passing true forces highlighting even when the Console was created with highlighting disabled. Passing false turns it off. Passing none defers to the Console default.
- The method returns nothing.
- The docstring must state that highlight defaults to true, not none. The reference signature and behavior are the source of truth.
- The names sep, end, style, and highlight must match print's names so callers can move between print and out without renaming.

## Module architecture

- out belongs in the Console class of the console module, grouped with print and control.
- out is a thin layer: it builds the raw output, then delegates to print. It must not write to the buffer or output file directly, and must not create a second rendering or output path.
- Rendering, highlighting, buffering, and render-hook handling stay in the existing print pipeline. out only chooses the fixed options.
- out must not depend on any new module or helper.

## Implementation constraints

- Add no new imports. The annotation types (Any, Union, Style) are already available in the console module.
- Do not change print's or control's signature or behavior.
- Keep the code compatible with the Python versions the project already supports.

## Dependencies

- No new third-party or internal packages.
- No changes to packaging, lock, or requirements files.

## Naming

- Method name: out. Parameters: objects (variable group), sep, end, style, highlight, matching print.
- The basic functional test must be named exactly test_out. Additional tests use the test_out prefix plus the aspect checked, such as markup, emoji, highlight, or render hook.

## Validation

out adds no validation. Objects are converted with normal string conversion, and sep and end are used as given. Add no type checks or coercion beyond what print performs.

## Error handling

Exceptions raised while converting an object to a string propagate unchanged. Introduce no new error types, retries, or silent fallbacks.

## Logging

out does not log anything and adds no logging calls.

## Documentation

- The docstring describes the low-level behavior: no pretty printing, wrapping, or markup; optional highlighting; basic style. It documents sep, end, style, and highlight with their actual defaults.
- The Console documentation page gets a "Low level output" section after the logging section. It explains that out is a lower-level alternative to print and log, lists what it does and does not do, and mentions highlighting and basic style.
- The CHANGELOG gets one bullet under Unreleased, Added: "Added Console.out", matching the neighboring entries.

## Compatibility

The change is purely additive. No existing names or defaults change, so existing print, log, and control callers are unaffected.

## Behavioral acceptance criteria

- Several objects with a separator and end string are written as converted objects joined by the separator, then the end string, with no wrapping at a narrow width. Example: with width 10, five copies of "foo bar" joined by "." and ended with "X" produce "foo bar.foo bar.foo bar.foo bar.foo barX".
- Markup-like text (for example brackets containing style names) and emoji codes are written literally.
- A container object is written as its string conversion, not a pretty-printed structure.
- Output is not cropped to the console width.
- With the default highlight value, highlighting applies even when the Console was created with highlighting disabled.
- With highlight none, the Console's highlight setting decides. With highlight false, no highlighting applies.
- A style given to out is applied the same way print applies it.
- Render hooks run for out output, as for print output.
- out returns no value.

## Test requirements

- Add tests to the existing console test module, next to the existing print style test. Do not change or remove existing tests.
- Include a test named exactly test_out covering separator, end string, and no-wrap behavior at a fixed narrow width.
- Plain-text assertions use a Console writing to an in-memory stream with a fixed width, not forced into terminal mode, and assert against the captured plain text.
- Assertions on escape sequences (styled or highlighted output) must construct the Console with the explicit color system "truecolor", as the existing style tests do. Forcing terminal mode alone is not enough, and such assertions must not depend on TERM, COLORTERM, or NO_COLOR. Do not assert styled escape bytes unless traced through the print path with cropping disabled. Prefer plain-text assertions or verify style by another traced means.
- With highlighting enabled in a terminal-capable console, do not assert literal substrings containing characters the default highlighter styles (brackets, braces, quotes, numbers, slashes), since styling splits them into spans. Use a non-terminal console or disable highlighting for those.
- Cover at least: separator and end handling with wrapping suppressed; markup and emoji left literal; style accepted; highlight default, none, and false, where checkable as plain text.
- Any import a new test needs, such as a render hook base class, goes at the top of the test module with the existing imports, not inside a test function.
