## Goals

- Allow explicit conversion between supported `NDUncertainty` subclasses through variance, mirroring the coordinate subsystem's Cartesian path.
- Supported classes: StdDevUncertainty, VarianceUncertainty, InverseVariance. Unsupported classes, such as UnknownUncertainty and test doubles, lack conversion hooks.
- Issue #11862 is context only.

## Scope

In scope: one public conversion method on `NDUncertainty`; private per-class hooks on the three supported classes; tests in the existing nddata uncertainty test module; a towncrier changelog fragment.

Out of scope: the constructor type check, implicit conversion in arithmetic propagation, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- An array or unit may be None; both are valid and must be handled.
- Conversion is elementwise: squaring, square root, or reciprocal, with unit exponents 2, 1/2, or -1. Float results are not bit-exact, so tests may compare approximately.

## Terminology

- **Variance-convertible class**: provides both the to-variance and from-variance hooks. **Unsupported class**: lacks either.

## Workflows

Converting a source instance to a target class:

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type as not supporting conversion.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class as not supporting conversion from another uncertainty type.
3. Call the to-variance hook, pass the result to the target's from-variance hook, and return its result.

Rules:
- Always route through variance, including same-class conversion, so an unsupported class converted to itself raises TypeError. Do not add a same-class shortcut that skips the capability check.
- Variance-to-variance returns the same object.
- StdDev to variance: square the array and the unit.
- Variance to StdDev: take the square root of the array and raise the unit to 1/2.
- InverseVariance to variance, and variance to InverseVariance: take the reciprocal of the array and invert the unit.
- A None array or None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## Data model

- Add no stored state to any uncertainty class.
- A conversion result is a new target-class instance with no parent data association, except variance-to-variance, which returns the same object and keeps its parent association.

## API contracts

- Public method `represent_as` on `NDUncertainty`. It takes one positional parameter, `other_uncert`, the target subclass, and returns an instance of that subclass (the same object for variance-to-variance).
- Hook `_convert_to_variance`: instance method on each variance-convertible class, returning a VarianceUncertainty.
- Hook `_convert_from_variance`: class method on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup, so a class without a hook is unsupported. The base class must not define default hooks, because a default would make every class look supported.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, whether same-class or cross-class.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`.
- The base class holds orchestration (capability checks and dispatch through variance). Per-class math lives in the hooks.
- The constructor type check stays unchanged; mismatched types still raise IncompatibleUncertaintiesException on construction.
- Do not change `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method. Propagation behavior must remain identical.
- Conversion runs only when called explicitly, never from construction or arithmetic.

## Implementation constraints

- Place `represent_as` after the abstract propagation methods on the base class.
- Discover hooks by attribute lookup, not a registry or a chain of type checks.
- Each hook explicitly maps a None array to None and a None unit to None. Do not catch and re-raise numpy errors.
- Validate capabilities on both source and target inside `represent_as` before any array math. Add no other argument-type validation.
- `represent_as` has a numpydoc docstring with Parameters, Returns, and Raises sections; Raises documents TypeError.

## Dependencies

- No new packages, modules, imports, or configuration changes. Use the existing numpy and unit facilities.

## Naming

- Changelog fragment `docs/changes/nddata/12057.feature.rst`, using 12057, the task identifier, not 11862, the issue number.

## Error handling

- Unsupported source: TypeError naming the source type as not supporting conversion to another uncertainty type.
- Unsupported target: TypeError naming the target class as not supporting conversion from another uncertainty type.

## Logging

- No logging.

## Documentation

- The towncrier fragment states conversion between uncertainty types via variance.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended; any versionadded note uses 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not mention a missing parent association or call conversion exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid copies beyond those needed for the result.

## Security

- No security-relevant behavior is introduced.

## Reliability

- Conversion never crashes on None arrays or None units. Implicit mixed-type arithmetic keeps its original behavior and never silently converts operands.

## Maintainability

- Keep each class's conversion formulas only in its hooks. Do not duplicate conversion math in the propagation path.

## Compatibility

- StdDevUncertainty's arithmetic override still raises for non-StdDev operands. Variance and InverseVariance propagation is unchanged.
- The public API changes only by addition.

## Operations

- No operational or deployment changes.

## Behavioral acceptance criteria

- Same-class conversion of a supported uncertainty returns equal values and an equal unit. Variance to variance returns the same object, so unit adu stays adu and the array is untouched.
- StdDev to variance squares values and the unit; variance to StdDev takes the square root and raises the unit to 1/2. Example: a VarianceUncertainty with unit m converted to StdDevUncertainty has unit m, not m to the 1/2.
- Unit-only examples: a VarianceUncertainty with unit m and a None array converted to VarianceUncertainty keeps unit m. The same object converted to InverseVariance has unit m to the power -1. An InverseVariance with unit m and a None array converted to VarianceUncertainty has unit m to the power -1, not -2.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to a different supported class produces a result of the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class, or between an unsupported and a supported class in either direction, raises TypeError.
- Constructing a VarianceUncertainty from a StdDevUncertainty still raises IncompatibleUncertaintiesException.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's parametrized style and imports, plus any missing numpy testing import for approximate comparisons.
- Cover supported self-conversion for each supported class, conversion to variance and back, and TypeError for unsupported self-conversion (FakeUncertainty, UnknownUncertainty).
- Expected values follow the rules above. Never apply one class's transform to another class's input. Derive each expected unit by applying the pair's unit rule to the constructed unit.
- For a fresh result, expect access to `parent_nddata` to raise MissingDataAssociationException, as existing tests do. Do not compare it to None, because the getter raises instead of returning None.
