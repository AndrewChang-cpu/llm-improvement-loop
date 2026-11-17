## Goals

- Add a string format for `TimeDelta` named `quantity_str`. It represents a physical time delta as an optionally signed sequence of components: years (`yr`), days (`d`), hours (`hr`), minutes (`min`), and seconds (`s`). It is meant to be human-readable and usable in configuration files and command-line options.
- Make strings in this form valid `TimeDelta` input without an explicit format. Bare-string construction is the primary usage, so construction without a format must succeed for these strings.
- Provide output subformats `multi`, `yr`, `d`, `hr`, `min`, and `s` through the existing output-subformat mechanism, with `precision` applied to the selected subformat.
- Make `precision`, `in_subfmt`, `out_subfmt`, and `copy` keyword-only arguments of `TimeDelta` construction. Their names and relative order follow the `Time` initializer, but that initializer takes these arguments positionally. The keyword-only marker is new for `TimeDelta` only and must not be described as existing for `Time`.
- Rationale: ISO 8601 durations depend on a calendar reference date, so they cannot express a physical delta that is independent of the start date. The units of this format are physical, not calendar.

## Scope

In scope:
- The new format class in the time formats module, with its registration and public export.
- `TimeDelta` construction: format resolution, the new keyword-only arguments, and where the numeric-without-unit warning is raised.
- The shared format-resolution routine used by both `Time` and `TimeDelta`, limited to the changes listed under Workflows and Error handling.
- The `subfmt` keyword of `TimeDelta.to_value`.
- The precision range for delta formats.
- Tests, changelog fragments, and documentation.

Out of scope:
- Arithmetic and comparison behavior of `TimeDelta`.
- Calendar-aware semantics. Years are never calendar years.
- Registering the new format for `Time`.
- Parsing ISO 8601 durations, and components other than the five listed units.
- Changing how unitless numeric strings are guessed. They keep their existing behavior (see Compatibility).
- Glob-pattern resolution of subformat names (see Terminology).

## Assumptions

- Units are physical: 1 yr = 365.25 d (the astropy `yr` unit), 1 d = 24 hr, 1 hr = 60 min, 1 min = 60 s. Leap seconds are not handled.
- Values are held in a two-part representation: `jd1` (whole days) and `jd2` (fraction of a day), both float64. The fractional part is kept in `jd2`, so fractional seconds survive large spans. For example, 1e8 days plus 1.0123456789012345 s keeps the fractional seconds. The format must not be described as losing precision at the level of total seconds.
- The `precision` setting controls only the number of printed digits.

## Terminology

- Component: a non-negative decimal number, followed by optional whitespace and then a unit name from {yr, d, hr, min, s}.
- Unit names are lowercase and case-sensitive.
- Subformat: an output selector. `multi` is the multi-component form. `yr`, `d`, `hr`, `min`, and `s` are single-unit forms. `*` is the wildcard default and resolves to `multi`.
- Subformat pattern: a requested subformat string that the existing subformat-validation mechanism matches against the declared names with shell-style glob rules. Matching decides only whether the request is valid. The new format does not replace a pattern with a matched name; it passes the requested string on as the output selector (see Workflows). Glob patterns are not a supported output selector for this format, and no behavior is specified for them.
- Multi output: output containing only the non-zero components among d, hr, min, and s.
- TimeUnique format: a format class marked as TimeUnique. It can be identified from its input without an explicit format name. The shared guessing routine consults these classes, and only these classes.
- Numeric without unit: a numeric input with no unit attribute. This includes numeric strings and bytes with no unit (for example "1.0" or "2.5"), which the numeric delta format reads as days.

## Workflows

Construction of a `TimeDelta` from a non-TimeDelta value:
1. Accept the value, optional `val2`, optional `format`, optional `scale`, and the keyword-only `precision`, `in_subfmt`, `out_subfmt`, and `copy`.
2. If the value is already a `TimeDelta`, keep the existing replicate path unchanged.
3. If `format` is given, it must be a string (TypeError otherwise) and must name a registered delta format (ValueError otherwise). Resolve it through the same single-candidate path as step 4, so that a failure in that class is wrapped as described under Error handling.
4. If `format` is absent, the shared format-resolution routine (the same routine `Time` uses; see Module architecture) runs. First, reject zero-size input (both `val` and `val2`, if present, have size zero) with a ValueError. Then try every registered TimeUnique delta format in registration order: jd, datetime, quantity_str. The first class that accepts the input wins.
   - The guessing order is the only selection mechanism. The routine must not add any input-type filter of its own (for example, excluding string input from a class). Whether a class accepts an input is decided by its own input validation.
   - `TimeDelta` must not keep a special-case default-format method.
   - Expected outcomes: a `datetime.timedelta` resolves to the datetime format; a Quantity resolves to jd; a plain numeric without unit resolves to jd; a numeric string or bytes without unit (for example "1.0") resolves to jd, which reads it as days; a string in quantity_str form (for example "2.5hr") resolves to quantity_str, because jd rejects it.
5. Instantiate the chosen class with `val`, `val2`, `scale`, `precision`, `in_subfmt`, and `out_subfmt`. Pass `precision` None through unchanged so the format applies its own default. An unspecified `in_subfmt` or `out_subfmt` on `TimeDelta` is resolved to `*` as before.
6. After construction, if no format was given, the input has no unit, and the resolved format is numeric (including numeric strings and bytes resolved to jd), emit the missing-unit warning described under Logging.

Output:
- `value` returns the output in the current `out_subfmt`.
- `to_value` with a format, or with a `subfmt` keyword and no format, uses the current format and the given subformat.
- Subformat resolution, in the output path of the new format:
  - The requested `out_subfmt` (or the `subfmt` keyword of `to_value`) is resolved through the base format class's existing subformat coercion helper (see Module architecture). That helper applies the existing subformat-validation mechanism that `TimeNumeric` formats use for output.
  - If the helper accepts the request, the requested string is used unchanged as the output selector. A glob pattern is not resolved to a concrete name (see Terminology).
  - If the helper rejects the request, it yields the wildcard `*`, which means multi. The output path must not fail on it.
  - Public setters for `out_subfmt` and `in_subfmt` reject names that the existing mechanism rejects, with ValueError.
  - No separate name list or name-matching logic may be added to the format class for this purpose. Matching is not done by string comparison against a private unit list.
- Once resolved, `*` and `multi` produce multi output, and each other concrete name produces single-unit output.
- For a negative total, compute the output from the absolute value and prefix the whole output with a single "-".

Multi output:
- Split the two-part total into whole days, whole hours, whole minutes, and remaining seconds (see Implementation constraints).
- Round the seconds to `precision` first. Then carry: if the rounded seconds reach 60, move 60 s into one minute; a minute count reaching 60 moves into hours; an hour count reaching 24 moves into days. Carries happen after rounding.
- Days, hours, and minutes are integers. Seconds are the rounded number.
- Emit only the non-zero components, in the order d, hr, min, s, separated by one space. Years are never emitted in multi output; the day count absorbs them.
- If all components are zero, the output is the text "0.0s".
- Expected results: 1 yr gives "365d 6hr"; 2.5 hr gives "2hr 30min"; 60 s gives "1min"; 1 s gives "1.0s"; 3e7 s gives "347d 5hr 20min"; 3.000001e7 s gives "347d 5hr 20min 10.0s".

Single-unit output:
- Convert the total to the resolved unit using astropy's day-based unit conversion (yr = 365.25 d, d, hr, min, s).
- Round to `precision`. Render the rounded number in the default shortest float text, followed by the unit name, with the sign prefix.
- Do not pad trailing zeros beyond what float text produces; whole numbers keep ".0".
- Expected results for a total of 30000010 s: yr "0.951yr", d "347.222d", hr "8333.336hr", min "500000.167min", s "30000010.0s". The multi result is "347d 5hr 20min 10.0s".

## Data model

Per element, the internal state is `jd1` (float64, whole days) and `jd2` (float64, fraction of a day), normalized with the standard day-fraction split.

Input grammar (pseudocode, to be implemented as one full-match pattern):

    delta      := ws* [sign] ws* ( yr-part )? ( d-part )? ( hr-part )? ( min-part )? ( s-part )? ws*
    yr-part    := number ws* "yr" ws*        (and likewise for d, hr, min, s; the order is fixed)
    number     := digits [if "." [digits]] | "." digits, optionally followed by an exponent ("e" or "E", optional sign, digits)

- The whole string must match. At least one component is required, and the string must contain at least one character that is neither a sign nor whitespace.
- The sign is optional and appears once, at the start. It applies to the whole delta.
- Each component appears at most once, in the order yr, d, hr, min, s. Whitespace between components and between a number and its unit is optional.
- Accepted examples: "1s", "1min", "2.5hr", "3e7s", "3.e7s", "  100.0 d1.0123456789012345 s ", "2yr 3d 4hr 5min 6.789s", "-1yr 2d 23hr 10min 5.6s".
- Rejected examples: the empty string, whitespace only, a sign only, "1.0" (no unit), "1.0s 2.0s", "1.0s 2.0", "1.0s 2min" (out of order), "++1.0s", "2min +1s", "2d -1s", "1sec".

Parsing steps for one element:
- Match the whole string against the grammar. A non-match is an error.
- Missing components are zero. Apply the sign to all components.
- Whole days = yr × 365.25 + d (exact for integer inputs). Fraction = hr/24 + min/1440 + s/86400.
- Normalize into `jd1` and `jd2` with the standard day-fraction split. Do not compute a single total-seconds float.

Precision (per format instance):
- Default is 3 when the value is None. The precision setter maps None to the format's default, so None is accepted both at construction and when the property is set.
- Delta formats accept integers from -99 to 99 inclusive. `Time` formats keep 0 to 9.
- Negative values round to tens (for example, 21.123456789012345 s at precision -1 gives "20.0s").
- Precision applies to every subformat, including the single-unit ones and the seconds of multi output.

`in_subfmt`: stored and validated against the subformat names. Parsing does not depend on it.

## API contracts

- `TimeDelta` construction: `val`, `val2`, `format`, and `scale` remain positional. `precision` (default None), `in_subfmt` (default None, which the format resolves to the wildcard `*`), `out_subfmt` (default None, resolved the same way), and `copy` (default False) are keyword-only on the construction entry point that performs initialization. `copy` must not be accepted positionally there.
- `TimeDelta.__new__` keeps the original parameter list exactly as it is in the original code: the same positional-or-keyword parameters, including `location` (default None) and `copy`, with no keyword-only marker added. Do not remove `location`, and do not add a bare-star separator. Only the initialization entry point changes, and the values are applied at initialization.
- `TimeDelta.to_value`, in the order the checks are applied:
  - No arguments: TypeError with the existing "missing required format or unit argument" message.
  - Allowed keyword names are format, subfmt, unit, and equivalencies. Any other keyword raises TypeError naming it.
  - A `format` keyword, or a first positional argument that is None or a registered delta format, delegates to the base implementation.
  - A `subfmt` keyword with no format and no positional argument outputs in the current format with that subformat. Any other keyword passed with it (for example `unit` or `equivalencies`) is forwarded to the base `to_value` signature, which does not accept it, so the call raises TypeError. This is a TypeError even though the keyword is in the allowlist; it is not a ValueError.
  - A `subfmt` keyword together with a positional argument that is not a format raises ValueError.
  - Otherwise the first positional argument is parsed as a unit, as before.
- Format class: name "quantity_str"; class `TimeDeltaQuantityString`; a delta-format subclass that is also TimeUnique; subformats in the order multi, yr, d, hr, min, s. Its output method accepts an optional parent and an optional output subformat, and returns an array of text (masked when the input is masked). Its `value` property returns the output of that method.
- Input validation for the format class: a non-empty array whose dtype is not string (unicode or bytes) is rejected. A zero-size array of any dtype is accepted and produces a zero-size result. A present `val2` is rejected.
- `TimeDeltaJD` gains the TimeUnique marking. Its signature does not change.
- `TimeDelta.FORMATS` lists sec, jd, datetime, quantity_str, in that order.

## Module architecture

- Parsing and rendering belong in the new format class in the time formats module. `TimeDelta` must not parse strings itself.
- Subformat selection for output belongs to the format layer's existing subformat handling: the validation mechanism that `TimeNumeric` formats use to resolve `out_subfmt`, together with the base format class's existing coercion helper, which returns the requested subformat when that validation accepts it and otherwise returns the wildcard `*`. The output path of the new class must obtain its output selector by calling that coercion helper. It must not wrap the validation mechanism in its own try/except fallback, and it must not add a parallel coercion or selection path.
- Format guessing belongs to the shared format-resolution routine in the time core module, which is used by both `Time` and `TimeDelta`. That routine owns the zero-size check, the candidate list (TimeUnique formats in registry order), the pseudo-format fallback for `Time` only, and the aggregated error message. The routine must not contain format-specific or input-type-specific exclusions. Candidate acceptance is decided by TimeUnique membership and each format's own input validation.
- The TimeDelta-specific default-format method (which returns datetime for timedelta objects and jd for everything else) is removed. Its behavior comes from TimeUnique guessing.
- The keyword plumbing for `precision`, `in_subfmt`, and `out_subfmt`, and the numeric-without-unit check, belong to `TimeDelta` construction in the core time module. The numeric-without-unit check uses the resolved format class and applies to string input as well.
- Registration uses the existing subclass-registration mechanism: declare the format name on the class. Do not create a separate registry.
- Each subformat entry of the new class uses the same tuple shape as the other delta format classes (a name followed by placeholder entries), not a bare two-element pair.
- The subformat handling for `subfmt` in `to_value` belongs in `TimeDelta.to_value`.

## Implementation constraints

- Keep two-part storage end to end. Do not convert the total to a single seconds float before splitting. Use the existing two-sum helper to split the total into whole days and a remainder for output.
- Do not add a parallel unit table. Single-unit conversion uses astropy's day-based unit conversion, and the unit name passed to it is the requested subformat string accepted by the existing subformat-validation mechanism.
- Check the requested subformat through the existing subformat-validation mechanism, and map `*` to multi, before any unit lookup.
- Pass a precision of None through to the format.
- Perform the numeric-without-unit check after construction, using the chosen format.
- The zero-size rejection is a guessing rule of the shared format-resolution routine only. The format class itself does not reject zero-size arrays; parsing and output of zero-size arrays produce zero-size results.
- Do not change `TimeDelta` arithmetic or scale handling, or the output of the existing sec, jd, and datetime formats.
- Do not change the case-sensitivity of format-name lookup beyond the existing behavior.

## Dependencies

- Add no third-party or project dependencies. Use the regular-expression module, numpy, astropy units, and the day-fraction and two-sum helpers already used by the time formats module.

## Naming

- Class name: `TimeDeltaQuantityString`. Format name: "quantity_str". Subformat names: exactly multi, yr, d, hr, min, s.
- Add the class to the formats module's public export list, next to the other delta format classes.
- Keyword names `precision`, `in_subfmt`, `out_subfmt`, and `copy` are unchanged.

## Validation

- Input arrays use string dtypes, either unicode or bytes. Bytes are decoded as ASCII before parsing, and byte input is accepted.
- A non-empty non-string array raises TypeError. Empty arrays are accepted.
- Each element must fully match the grammar in Data model.
- `val2` must be absent. A present `val2` raises ValueError.
- `precision` must be None (meaning the format default) or an integer within the range for the format class.
- `in_subfmt` and `out_subfmt` are validated against the subformat names (including the glob-matching rule in Terminology) when they are set.
- Ordering when a format class is constructed directly: the base initializer sets `precision`, `in_subfmt`, and `out_subfmt` before it checks the input values. A None subformat is not a subformat name and raises ValueError from that subformat validation, so a non-string array passed to the format class with None subformats raises ValueError, not the non-string TypeError. The non-string TypeError is reached only when both subformats are valid strings (for example "*"). `TimeDelta` resolves unspecified subformats to `*` before instantiating the format, so the TypeError applies there without this caveat.
- The `to_value` keyword allowlist is enforced.
- The scale check is the existing delta-scale check.

## Error handling

- `format` is not a string: TypeError, "format must be a string". This applies to `Time` and `TimeDelta`.
- `format` names no registered format: ValueError, "Format <name> is not one of the allowed formats <sorted names>".
- Explicit format fails: ValueError, "Input values did not match the format class <name>:", then the platform line separator (`os.linesep`, as the original code uses), then "<ErrorClass>: <message>". Chain the original error. This is a ValueError for every format, including quantity_str; do not raise TypeError for an explicit-format failure.
- No format, and guessing fails for all candidates: ValueError, "Input values did not match any of the formats where the format keyword is optional:", then a literal newline character (not the platform line separator), then one line per candidate in the form "- '<name>': <error>", with lines separated by a literal newline character.
- Unit-conversion errors propagate immediately, unwrapped.
- Zero-size input with no format, for `Time` and `TimeDelta` alike: ValueError, "cannot guess format from input values with zero-size array". Time([]) must keep raising this error.
- An element that does not match the grammar: ValueError, "Time delta '<text>' does not match quantity_str format".
- Non-string input: TypeError, "Input values for quantity_str class must be strings". This is raised when the subformat arguments are valid strings. When the format class is constructed directly with None subformats, the subformat ValueError is raised first (see Validation).
- `val2` provided: ValueError, "quantity_str objects do not accept a val2 but you provided <val2>".
- `precision` out of range: ValueError, "precision attribute must be an int between <min> and <max>", using the limits for the format class.
- Unknown `to_value` keyword: TypeError, "TimeDelta.to_value() got an unexpected keyword argument '<name>'".
- `subfmt` with a positional argument that is not a format: ValueError, "cannot specify 'subfmt' and positional argument that is not a valid format".
- `subfmt` keyword combined with a `unit` or `equivalencies` keyword and no format: TypeError, raised by the base signature. Do not wrap it or convert it to ValueError.

## Logging

- Missing-unit warning: category TimeDeltaMissingUnitWarning, text "Numerical value without unit or explicit format passed to TimeDelta, assuming days".
- Emit it once per construction, only when no format was given, the input has no unit, and the resolved format is numeric. This includes numeric strings and bytes that resolve to jd (for example "1.0" or "2.5"); they warn exactly like numeric arrays. Do not emit it for inputs with a unit, for inputs that resolve to quantity_str or datetime, or when a format was given.
- No other logging.

## Documentation

- `TimeDelta` class docstring: document the `precision`, `in_subfmt`, and `out_subfmt` parameters. Update the listed FORMATS output to include quantity_str, in the order given in API contracts.
- `to_value` docstring: list the built-in TimeDelta format names, including quantity_str.
- Format class docstring: describe the grammar in prose and the units. Include the calendar note: adding one year to 2000-01-01 00:00:00 gives 2000-12-31 06:00:00. Describe the subformats, and state that the default output is not finalized (see Compatibility).
- Docstring examples are doctests. In the format class docstring and the TimeDelta docstring, each example's expected text must equal exactly what printing the value produces, meaning the str form, not the repr form. Do not put quotation marks in expected output unless the printed text itself contains them. Show each value by printing it, one value per example.
- Documentation index for time: add a quantity_str row to the TimeDelta format table, widening the table to fit. Add a short section on the format and its subformats that references the class.
- Release notes: in the existing in-development whatsnew page for the current development series (docs/whatsnew/6.0.rst), in its existing sections, add all of the following. Do not create a new version page and do not add a new toctree entry.
  - A bullet in the page's highlights list that references a new labelled section for the format.
  - A labelled section with a title for the quantity_str format. It describes the format, its grammar in prose, the units, and the subformats.
  - A warning note that the default output format is not yet finalized and may change in version 6.1, and that the input format is stable, referencing issue 15485.
  - The keyword-only construction change, stated accurately (see the changelog rule below).
- Changelog fragments under docs/changes/time/, named with pull request number 15264: one feature fragment and one api fragment. The api fragment states the previous positional order (val, val2, format, scale, copy) and the new order with the keyword-only group after scale. It must not say that Time's arguments are already keyword-only, because the `Time` initializer takes precision, in_subfmt, out_subfmt, and copy positionally. The whatsnew wording follows the same rule.
- Keep existing attribute docstrings directly after their attribute definitions. Do not move a docstring so that it documents a different attribute.

## Maintainability

- Code lines are at most 88 characters, which satisfies the repository's black and ruff settings.
- The repository's ruff configuration selects all rules and enforces the pre-commit ruff hook on every commit. Write membership negation as "x not in y", never as "not x in y" (rule E713). Other ruff rules are not exempted by this change.
- The TimeDelta default-format method is removed, not kept as dead code.
- Remove any import that the change leaves unused (for example, the datetime timedelta name in the core time module once the default-format method is gone). The repository's lint configuration does not exempt non-__init__ modules from unused-import checks. The existing os import in the core time module is still used for the platform line separator in the explicit-format error, so it stays; do not remove it and do not replace the platform line separator in existing messages with a literal newline.
- Each name is imported in exactly one import statement per module. Do not import the same name twice in a module, even in a separate statement. The repository's ruff/pyflakes configuration flags a redefined import (F811), and a duplicate import fails the lint check.

## Compatibility

- `TimeDelta` construction: `copy` becomes keyword-only on the initialization path. `val`, `val2`, `format`, and `scale` remain positional. `TimeDelta.__new__` keeps its original signature, including `location`. The api changelog fragment records the keyword-only change accurately (see Documentation).
- Numeric, datetime, and sec output is unchanged. Existing precision defaults are unchanged. The TimeDelta precision range widens to -99 through 99.
- Format guessing for TimeDelta now includes every TimeUnique delta format, and jd is now TimeUnique. quantity_str is one of those guessed formats.
- Numeric input without a unit still means days, with the warning. Numeric strings and bytes without a unit (for example "1.0") are still accepted as days with the warning, as in the original code. Only strings in the quantity_str grammar are newly accepted without a format.
- `Time` guessing considers all TimeUnique formats in registry order, with the astropy_time pseudo-format last. Its failure message wording changes to the multi-line list. A non-string `format` on `Time` raises TypeError. Zero-size input with no format still raises ValueError for `Time`.
- `TimeDelta.FORMATS` gains quantity_str. The private default-format method is removed.

## Behavioral acceptance criteria

- Bare strings in the grammar construct a `TimeDelta` without a format and produce these multi outputs: "1s" gives "1.0s"; "1min" gives "1min"; "2.5hr" gives "2hr 30min"; "3.000001e7s" gives "347d 5hr 20min 10.0s"; "3.e7s" and "3e7s" give "347d 5hr 20min"; "1.0123456789012345s" gives "1.012s"; "  100.0 d1.0123456789012345 s " gives "100d 1.012s"; "2yr 3d 4hr 5min 6.789s" gives "733d 16hr 5min 6.789s"; "2.5yr 3.5d 4.5hr 5.5min 6.789s" gives "916d 19hr 35min 36.789s".
- A leading "+" gives the same output as no sign. A leading "-" gives the same output prefixed with "-", and the total is negated.
- "1yr 3.6d" with subformat d gives "368.85d". "-1yr 2d 23hr 10min 5.6s" with subformat d gives "-368.215d".
- A 40-hour delta gives "1d 16hr" in multi, "1.667d" with out_subfmt "d" and also with the subfmt keyword "d", and "1.666666667d" with subformat d at precision 9.
- Invalid strings in Data model raise ValueError. With an explicit format, the message contains "Input values did not match the format class quantity_str". Without a format, the guessing message is raised.
- "100.0d 1.0123456789012345s" at precision 9 gives "100d 1.012345679s". "21.123456789012345s" gives "21.123s" by default, "20.0s" at precision -1, and "21.123456789012s" at precision 12. Setting precision to 100 raises ValueError naming the range -99 to 99.
- For a total of 30000010 s, every single-unit subformat gives the values in Workflows, and the multi output gives "347d 5hr 20min 10.0s". The same results apply through `to_value` with a subfmt keyword and no format, and through a Quantity of 30000010.0 s with an explicit format and subfmt.
- "100.0d 1.0123456789012345s" at precision 9 with out_subfmt d gives "100.000011717d".
- Overflow: "1d 23hr 59min 59.9999s" gives "2d" by default and "1d 23hr 59min 59.9999s" at precision 9. "1d 23hr 58min 59.9999s" gives "1d 23hr 59min". "1d 23hr 59min 60.0001s" gives "2d", and "2d 0.0001s" at precision 9.
- A zero delta ("0d") gives "0.0s".
- "100000000d 1.0123456789012345s" has `jd1` equal to 100000000, and `jd2` times 86400 approximately equal to 1.0123456789012345.
- `TimeDelta("1s", "2s")` raises ValueError about `val2`.
- Byte-string input is parsed as ASCII.
- `TimeDelta("1.0")` and `TimeDelta("2.5")` without a format each give a one-day-per-unit numeric TimeDelta (1 day, 2.5 days) and emit the missing-unit warning. The same numeric string with an explicit format, or a numeric value with a unit, gives no warning.
- A numeric value without unit and without a format gives a numeric TimeDelta and the missing-unit warning. A `datetime.timedelta` resolves to the datetime format.
- `to_value` with an unknown keyword raises TypeError. `to_value` with a unit as a positional argument and a subfmt keyword raises ValueError. `to_value` with a `unit` keyword and a `subfmt` keyword and no format raises TypeError. `to_value` with "sec" and a unit keyword still raises TypeError.
- A rejected out_subfmt or in_subfmt value set on a TimeDelta raises ValueError. A rejected subfmt passed to `to_value` produces multi output rather than an error.
- `TimeDelta.FORMATS` lists sec, jd, datetime, quantity_str.
- `Time` with a non-string format raises TypeError, "format must be a string".
- `Time([])` with no format raises ValueError (zero-size guessing message), unchanged from the original.

## Test requirements

- Add tests to astropy/time/tests/test_delta.py. Cover the following:
  - Basic parsing and multi output, with sign variants.
  - Precision, including negative values, values above 9, and None meaning the default.
  - Invalid strings, both with an explicit format and through guessing. An explicit-format failure is asserted as ValueError, not TypeError.
  - Each output subformat through out_subfmt, through `to_value` with a subfmt keyword, and from a Quantity. Do not test glob patterns (see Terminology).
  - The two-part internal precision check.
  - A zero value.
  - Overflow carry.
  - Non-string input and `val2` errors. For non-string input, either construct the format class directly with valid subformat strings such as `*`, or go through `TimeDelta` with an explicit quantity_str format (where unspecified subformats resolve to `*`). Do not assert TypeError for a direct construction that passes None subformats; that case raises ValueError first (see Validation).
  - `to_value` keyword validation: an unknown keyword raises TypeError naming it, and a `unit` keyword combined with a `subfmt` keyword and no format raises TypeError.
  - The FORMATS list.
  - Unitless numeric strings ("1.0", "2.5") without a format: parsed as days and warned, both through the warning check and the value check.
- Any regular expression passed to a match argument, or otherwise containing backslash escapes, must be a raw string literal. A non-raw literal with an invalid escape (for example a backslash before an opening parenthesis) raises a DeprecationWarning at compile time. The repository's pytest configuration sets warnings to errors, so the whole test module would fail to collect, including pre-existing tests.
- Update astropy/time/tests/test_basic.py. Replace the old "No time format was given" assertion with the new guessing message. Add a TypeError test for a non-string format on `Time`. Keep the existing assertion that `Time([])` raises ValueError. The explicit-format assertions keep the platform line separator (`os.linesep`) in their expected text, as the original tests do; only the guessing-message assertion changes to the new message form.
- Update astropy/time/tests/test_quantity_interaction.py. A positional unit with a subfmt keyword must raise ValueError with the new message, not TypeError.
- Run the time test suite. The docstring doctests in the format class and in TimeDelta must pass as doctests, with their expected output written as described under Documentation.
- Lint: the changed modules must pass the repository's ruff configuration, including the E713 membership rule described under Maintainability.
