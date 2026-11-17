## Goals

- Allow explicit conversion between supported `NDUncertainty` subclasses through variance, mirroring the coordinate subsystem's Cartesian path.
- Supported classes: StdDevUncertainty, VarianceUncertainty, InverseVariance. Unsupported classes (UnknownUncertainty, test doubles) lack conversion hooks. Issue #11862 is context only.

## Scope

In scope: one public conversion method on `NDUncertainty`; private per-class hooks; tests in the existing nddata uncertainty test module; a towncrier fragment. Out of scope: the constructor type check, implicit conversion in arithmetic, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- An array or unit may be None; conversion must handle both.
- Conversion is elementwise, with unit exponents 2, 1/2, or -1. Float results are not bit-exact, so tests may compare approximately.

## Terminology

- **Variance-convertible class**: provides both hooks. **Unsupported class**: lacks either. **Target class**: the class passed to the conversion method.

## Workflows

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type as not supporting conversion.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class as not supporting conversion from another uncertainty type.
3. Call the to-variance hook, pass its result to the target's from-variance hook, and return that result.

Rules:
- Always route through variance, including same-class conversion, so an unsupported class converted to itself raises TypeError. Do not add a same-class shortcut.
- Variance-to-variance returns the same object.
- StdDev to variance: square the array and the unit. Variance to StdDev: take the square root and raise the unit to 1/2.
- InverseVariance to or from variance: take the reciprocal and invert the unit.
- A None array or None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## Data model

- Add no stored state. A conversion result is a new target-class instance with no parent data association, except variance-to-variance, which returns the same object and keeps its parent association.

## API contracts

- Public method `represent_as` on `NDUncertainty`: one positional parameter, `other_uncert`, the target subclass. Returns an instance of that subclass.
- Hook `_convert_to_variance`: instance method on each variance-convertible class, returning a VarianceUncertainty.
- Hook `_convert_from_variance`: class method on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup, so a class without a hook is unsupported. The base class must not define default hooks, since a default would make every class look supported.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, in same-class and cross-class cases.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`.
- The base class holds orchestration (capability checks and variance dispatch); per-class math lives in the hooks and nowhere else.
- Do not change the constructor type check, `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method. Propagation must behave identically.
- Conversion runs only when explicitly requested, never from construction or arithmetic.

## Implementation constraints

- Place `represent_as` after the abstract propagation methods on the base class.
- Discover hooks by attribute lookup, not a registry or type-check chain.
- Add no new imports; use the module's existing numpy and unit facilities. Each hook maps a None array and a None unit to None explicitly.
- `represent_as` has a numpydoc docstring with Parameters, Returns, and Raises sections; Raises documents TypeError.

## Dependencies

- No new packages, modules, or configuration changes.

## Naming

- Changelog fragment `docs/changes/nddata/12057.feature.rst`. Use 12057, the task identifier, not 11862, the issue number.

## Validation

- Check capabilities on both source and target inside `represent_as` before any array math. Add no argument-type validation beyond attribute lookup.

## Error handling

- Unsupported source: TypeError naming the source type as not supporting conversion to another uncertainty type. Unsupported target: TypeError naming the target class as not supporting conversion from another uncertainty type.
- Handle None arrays explicitly. Do not catch and re-raise numpy errors.

## Logging

- No logging.

## Documentation

- The towncrier fragment states conversion between uncertainty types via variance.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended; any versionadded note uses 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not say the result lacks a parent NDData association, and must not call conversion exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid copies beyond those needed for the result.

## Security

- No security-relevant behavior is introduced.

## Reliability

- Conversion never crashes on None arrays or None units. Implicit mixed-type arithmetic keeps its original behavior and never silently converts operands.

## Usability

- Users call one documented method.

## Maintainability

- Do not duplicate conversion math in the propagation path.

## Compatibility

- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException. Mixed types remain rejected everywhere except the explicit conversion method.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands. Variance and InverseVariance propagation is unchanged. The public API changes only by addition.

## Operations

- No operational or deployment changes.

## Behavioral acceptance criteria

- Same-class conversion of a supported uncertainty returns equal values and an equal unit. Variance to variance returns the same object, so unit adu stays adu.
- A VarianceUncertainty with unit m converted to StdDevUncertainty has unit m, not m to the 1/2. An InverseVariance with unit m converted to VarianceUncertainty has unit m to the power -1, not -2.
- A VarianceUncertainty with unit m and a None array converted to VarianceUncertainty keeps unit m. The same object converted to InverseVariance has unit m to the power -1.
- Round-trips through variance return the original values and unit for each supported class. A supported class converted to another supported class produces the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class, or between an unsupported and a supported class in either direction, raises TypeError.
- A supported uncertainty with a None array converts to a None array without error.
- Constructing a VarianceUncertainty from a StdDevUncertainty still raises IncompatibleUncertaintiesException.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py` in the file's parametrized style, adding any missing numpy testing import needed for approximate comparisons.
- Cover supported self-conversion for all three classes, conversion to variance and back, and unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected values: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance take the reciprocal; variance to variance is the identity. Never apply one class's transform to another class's input. Derive each expected unit by applying the pair's unit rule.
- For a fresh result, expect access to `parent_nddata` to raise MissingDataAssociationException, as existing tests do. Do not compare it to None.
