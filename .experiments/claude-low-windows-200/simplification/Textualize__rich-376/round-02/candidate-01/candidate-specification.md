## Goals

Provide a public Console method, out, for low-level text output. Its positional objects are written as plain text, with an optional basic style and highlighting enabled by default. It does not pretty-print, wrap, crop, apply markup, or replace emoji codes. It is a thin alternative to print for callers who want raw text.

## Scope

In scope:
- One new public method on the Console class in the console module, placed next to print, with a docstring.
- A CHANGELOG entry under Unreleased, in the existing Added list.
- A "Low level output" section in the Console documentation page, after the logging section.
- Tests in the existing console test module.

Out of scope:
- Any change to the behavior, signature, or defaults of print, log, control, or other existing methods.
- New rendering paths, output types, or Console state.

## Assumptions

- Console.print already accepts the options out needs (style, highlight, emoji, markup, no_wrap, overflow, crop, end), so out delegates to it.
- Existing print behavior is the reference for how each option is interpreted.

## Terminology

- Raw output: each positional object converted with normal string conversion (not pretty-printing or repr-style formatting), joined by the separator.
- Console default: the Console's highlight setting from its constructor, on by default. It applies when a per-call highlight value is None.
- Render hook: a callback registered on the Console that print runs over its renderables before rendering. out output must pass through these hooks.

## Workflows

1. The caller invokes out with zero or more objects and optional sep, end, style, and highlight values.
2. out converts each object to a string and joins them with the separator. With no objects, the raw output is the empty string.
3. out calls the Console's print exactly once, with the raw output as its only object. It passes style, highlight, and end through, and fixes emoji and markup off, no-wrap on, overflow to ignore, and crop off.
4. Because the call goes through print, render hooks run, the buffer is used, and output is flushed or captured like any other print output.
5. out returns nothing.

Note: out always supplies one string to print, so a call with no objects still writes the end string. It does not trigger print's blank-line path.

## Data model

- No new data structures, classes, or fields. out holds no pending output; the existing buffer and flush behavior is used unchanged.

## API contracts

- out is a public instance method of Console.
- Positional parameters: zero or more arbitrary objects.
- sep: a string, default a single space, placed between converted objects.
- end: a string, default a newline.
- style: a style name or Style object, default none.
- highlight: default true. True forces highlighting even when the Console disabled it. False turns highlighting off. None defers to the Console default. The default must be true, not none.
- Parameter names sep, end, style, and highlight match print's names.
- The method returns nothing.
- The docstring must state highlight's actual default (true).

## Module architecture

- out belongs in the Console class of the console module, grouped with print and control.
- out is a thin layer: build the raw output, then delegate to print. It must not write to the buffer or output file directly, nor create a second rendering path.
- Rendering, highlighting, buffering, and render-hook handling stay in the existing print pipeline. out only chooses the fixed options.
- out must not depend on any new module or helper.

## Implementation constraints

- Add no imports. Annotation names (Any, Union, Style) are already available in the console module.
- Do not change print's or control's signature or behavior.
- Keep the code compatible with the Python versions the project supports.
- Add no third-party or internal packages, and change no packaging, lock, or requirements files.

## Naming

- Method name: out. Parameters: objects, sep, end, style, highlight.
- The basic functional test must be named exactly test_out. Additional tests use the test_out prefix plus the aspect they check (for example markup, emoji, highlight, or render hook).

## Validation and error handling

- out adds no validation or coercion. Objects are converted with normal string conversion; sep and end are used as given. Beyond what print does, add no type checks.
- Exceptions raised while converting an object propagate unchanged. No new error types, retries, or silent fallbacks.
- out does not log anything and adds no logging calls.

## Documentation

- The docstring describes low-level behavior: no pretty printing, no wrapping, no markup, optional highlighting, basic style. It documents sep, end, style, and highlight with actual defaults (highlight true).
- The Console documentation page gets a "Low level output" section after the logging section. It explains that out is a lower-level alternative to print and log, lists what it does and does not do, and mentions highlighting and basic style.
- The CHANGELOG gets one bullet under Unreleased, Added: "Added Console.out", matching neighboring entries.

## Compatibility

- Purely additive. Existing print, log, and control behavior and defaults are unchanged.

## Behavioral acceptance criteria

- Several objects with a separator and end string write the converted objects joined by the separator, then the end string, with no wrapping at a narrow width. Example in prose: with width 10, five copies of "foo bar" joined by "." and ended with "X" produce "foo bar.foo bar.foo bar.foo bar.foo barX".
- Markup-like text (square brackets containing style names) and emoji codes are written literally.
- Containers are written as string conversion, not pretty-printed.
- Output is not cropped to the console width.
- Default highlight applies highlighting even when the Console disabled it. None defers to the Console setting. False applies no highlighting.
- A style is applied as print applies it.
- Render hooks run for out output as they do for print output.
- out returns no value.

## Test requirements

- Add tests to the existing console test module next to the print style test. Do not change or remove existing tests.
- Include test_out covering separator, end, and no-wrap behavior at a fixed narrow width.
- Plain-text assertions use a Console writing to an in-memory stream with fixed width, not forced into terminal mode, asserting the captured plain text.
- Escape-sequence assertions must construct the Console with color system "truecolor", as existing style tests do. Forcing terminal mode alone is not enough, and results must not depend on TERM, COLORTERM, or NO_COLOR. Do not assert escape bytes unless traced through print with cropping disabled. Prefer plain-text assertions or verify styles another traced way.
- With highlighting enabled in a terminal-capable console, do not assert substrings containing characters the default highlighter styles (brackets, braces, quotes, numbers, slashes), since styling splits them. Use a non-terminal console or disable highlighting for those.
- Cover at least: separator and end with wrapping suppressed; markup and emoji literal; style accepted; highlight for default, none, and false where checkable as plain text.
- New test imports (for example the render hook base class) go at the top of the test module with existing imports, not inside functions.
