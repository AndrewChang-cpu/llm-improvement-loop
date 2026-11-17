## Goals

Add a public Console method, out, for low-level text output. Its positional objects are written as plain text with a basic style and, by default, highlighting. It does not pretty-print, wrap, crop, apply markup, or replace emoji codes. It is a thin alternative to print for callers who want raw text.

## Scope

In scope:
- One new public method on Console in the console module, placed next to print, with a docstring.
- A CHANGELOG bullet under Unreleased, Added.
- A "Low level output" section in the Console documentation page, after the logging material.
- Tests in the existing console test module.

Out of scope:
- Any change to the behavior, signature, or defaults of print, log, control, or other methods.
- New rendering paths, output types, or Console state.

## Assumptions

- Console.print already accepts style, highlight, emoji, markup, no_wrap, overflow, crop, and end, so out delegates to it.
- Print's behavior is the reference for how each option is interpreted.

## Terminology

- Raw output: each positional object converted with normal string conversion (not pretty-printing or repr-style formatting), joined by the separator.
- Console default: the Console's highlight setting from its constructor, on by default. It applies when a per-call highlight value is None.
- Render hook: a callback registered on the Console that print runs over its renderables before rendering.

## Workflows

1. The caller invokes out with zero or more objects and optional sep, end, style, and highlight values.
2. out builds raw output from the objects and separator. With no objects, raw output is the empty string.
3. out calls the Console's print exactly once, passing raw output as the only object, plus style, highlight, and end. It fixes emoji and markup off, no-wrap on, overflow to ignore, and crop off.
4. Because the call goes through print, render hooks run, and buffering, flushing, and capture behave as for print.
5. out returns nothing.

Note: a call with no objects still passes one string to print, so it writes the end string and does not take print's blank-line path.

## Data model

- No new data structures, classes, or fields. out holds no pending output.

## API contracts

- out is a public instance method of Console.
- Parameters: zero or more arbitrary objects (variadic); sep, a string defaulting to a single space; end, a string defaulting to a newline; style, a style name or Style object, defaulting to none; highlight, defaulting to true.
- highlight true forces highlighting even when the Console disabled it. False turns it off. None defers to the Console default. The default is true, not none.
- Parameter names match print's so callers can move between them.
- Returns nothing.
- The docstring states highlight's default as true.

## Module architecture

- out goes in the Console class of the console module, grouped with print and control.
- out is a thin layer: build raw output, then delegate to print. It must not write to the buffer or output file directly or create a second rendering path.
- Rendering, highlighting, buffering, and render-hook handling stay in the existing print pipeline.
- out must not depend on any new module or helper.

## Implementation constraints

- Add no imports. Annotation names (Any, Union, Style) are already available in the console module.
- Do not change print's or control's signature or behavior.
- Stay compatible with the project's supported Python versions.
- Add no third-party or internal packages; change no packaging, lock, or requirements files.

## Naming

- Method name: out. Parameters: objects, sep, end, style, highlight.
- The basic functional test must be named exactly test_out. Other tests use the test_out prefix plus the aspect checked, for example markup, emoji, highlight, or render hook.

## Validation

- None added. Objects use normal string conversion; sep and end are used as given. No type checks or coercion beyond what print performs.

## Error handling

- Exceptions raised while converting an object propagate unchanged. No new error types, retries, or fallbacks.

## Logging

- out does not log and adds no logging calls.

## Documentation

- The docstring describes low-level behavior: no pretty printing, no wrapping, no markup, optional highlighting, basic style. It documents sep, end, style, and highlight with actual defaults.
- The Console documentation page gets a "Low level output" section after the logging section. It explains that out is a lower-level alternative to print and log, lists what it does and does not do, and mentions highlighting and basic style.
- CHANGELOG: one Unreleased, Added bullet, "Added Console.out", matching neighboring entries.

## Compatibility

- Purely additive. Existing print, log, and control behavior and defaults are unchanged.

## Behavioral acceptance criteria

- Several objects with a separator and end write the converted objects joined by the separator, then the end, with no wrapping at a narrow width. Example: at width 10, five copies of "foo bar" joined by "." and ended with "X" produce "foo bar.foo bar.foo bar.foo bar.foo barX".
- Markup-like text and emoji codes are written literally.
- Containers are written as string conversion, not pretty-printed.
- Output is not cropped to the console width.
- Default highlight applies highlighting even when the Console disabled it. None defers to the Console. False applies none.
- A style is applied as print applies it.
- Render hooks run for out output as for print output.
- out returns no value.

## Test requirements

- Add tests to the existing console test module next to the print style test. Do not change or remove existing tests.
- test_out covers separator, end, and no-wrap at a fixed narrow width.
- Plain-text assertions use a Console writing to an in-memory stream with fixed width, not forced into terminal mode.
- Escape-sequence assertions construct the Console with color system "truecolor", as existing style tests do. Forcing terminal mode alone is not enough, and results must not depend on TERM, COLORTERM, or NO_COLOR. Do not assert escape bytes unless traced through print with cropping disabled. Prefer plain-text assertions.
- With highlighting enabled in a terminal-capable console, do not assert substrings containing characters the default highlighter styles (brackets, braces, quotes, numbers, slashes), since styling splits them. Use a non-terminal console or disable highlighting for those.
- Cover at least: separator and end with wrapping suppressed; markup and emoji literal; style accepted; highlight default, None, and false where checkable as plain text.
- New test imports, such as a render hook base class, go at the top of the test module.
