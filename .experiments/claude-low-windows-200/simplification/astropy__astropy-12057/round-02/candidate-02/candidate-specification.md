## Goals

- Let an `NDUncertainty` subclass be explicitly converted into another supported subclass through a public method, using variance as the common intermediate representation, as the coordinate subsystem does with Cartesian.
- Supported classes are StdDevUncertainty, VarianceUncertainty, and InverseVariance. Classes without conversion hooks, such as UnknownUncertainty and test doubles, are unsupported.
- Issue #11862 is background only and adds no requirement.

## Scope

In scope:
- One public conversion method on the `NDUncertainty` base class.
- Private per-class conversion hooks on StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Tests in the existing nddata uncertainty test module.
- A towncrier changelog fragment for the nddata package.

Out of scope:
- The constructor type check, implicit conversion in arithmetic propagation, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- An uncertainty's array (default None) and unit (possibly None) may each be None. Conversion must handle both.
- Conversion is elementwise: squaring, square root, or reciprocal, with unit exponents 2, 1/2, or -1. Float results are not bit-exact, so tests may compare transformed floats approximately.

## Terminology

- **Variance-convertible class**: a subclass providing both conversion hooks.
- **Unsupported class**: a subclass lacking either hook.
- **Target class**: the class passed to the conversion method.
- **Intermediate variance**: the VarianceUncertainty produced from the source and consumed to build the target.

## Workflows

Converting a source instance to a target class:

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type as unable to convert to another uncertainty type.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class as unable to convert from another uncertainty type.
3. Call the to-variance hook to get an intermediate variance, pass it to the target's from-variance hook, and return the result.

Rules:
- Always route through variance, including same-class conversion. Do not add a same-class shortcut that skips the capability check, so an unsupported class converted to itself raises TypeError.
- Variance-to-variance conversion returns the same object.
- StdDev to variance: square the array; square the unit.
- Variance to StdDev: take the square root of the array; raise the unit to 1/2.
- InverseVariance to variance, and variance to InverseVariance: take the reciprocal of the array; invert the unit.
- A None array converts to None. A None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## Data model

- No stored state is added to any uncertainty class.
- A conversion result is a new instance of the target class with no parent data association, except variance-to-variance, which returns the same object with its existing association.

## API contracts

- Public method `represent_as`, defined on the `NDUncertainty` base class. It takes one positional parameter, `other_uncert`, the target subclass, and returns an instance of that subclass.
- Hook `_convert_to_variance`: an instance method on each variance-convertible class that returns a VarianceUncertainty.
- Hook `_convert_from_variance`: a class method on each variance-convertible class that accepts a VarianceUncertainty and returns an instance of the class.
- Hooks are discovered by attribute lookup, so a class without a hook is unsupported. The base class must not define default hooks, since a default would make every class look supported.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, in same-class and cross-class cases.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`.
- The base class holds orchestration: capability checks and dispatch through variance. Subclass hooks hold the per-class math.
- The constructor type check remains unchanged. Mismatched types still raise IncompatibleUncertaintiesException on construction.
- Do not change `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method. Propagation behavior must stay identical.
- Conversion is explicit only. It must not run implicitly from construction or arithmetic.

## Implementation constraints

- Place `represent_as` on the base class after the abstract propagation methods.
- Discover hooks by attribute lookup, not a registry or a chain of type checks.
- Add no new imports. Use the module's existing numpy and unit facilities.
- Each hook explicitly maps a None array to None and a None unit to None.
- `represent_as` gets a numpydoc docstring with Parameters, Returns, and Raises sections. Raises documents TypeError.
- Do not reuse the propagation exception for conversion errors.

## Dependencies

- No new packages, modules, or configuration changes.

## Naming

- Method `represent_as`, parameter `other_uncert`. Hooks `_convert_to_variance` (instance) and `_convert_from_variance` (class method). Use these exact names.
- Changelog fragment `docs/changes/nddata/12057.feature.rst`. Use 12057, the task identifier, not 11862, the issue number.

## Validation

- Capability checks on both source and target happen inside `represent_as` before any array math.

## Error handling

- Unsupported source or target: TypeError naming the type and stating it cannot convert to or from another uncertainty type, as appropriate.
- Handle None arrays explicitly. Do not catch and re-raise numpy errors.

## Logging

- No logging is required or added.

## Documentation

- Add the towncrier fragment described above.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended. If a versionadded note is added, use 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not say the result lacks a parent NDData association, and must not call the conversion exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid copies beyond those needed to build the result.

## Security

- No security-relevant behavior is introduced.

## Reliability

- Conversion never crashes on None arrays or None units.
- Implicit mixed-type arithmetic keeps its original behavior and never silently converts operands.

## Usability

- Users call one documented method to convert types.

## Maintainability

- Keep conversion formulas only in the hooks. Do not duplicate them in the propagation path.

## Compatibility

- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- Variance and InverseVariance propagation is unchanged. The public API changes only by addition.

## Operations

- No operational or deployment behavior changes.

## Behavioral acceptance criteria

- Converting a supported uncertainty to its own class returns equal values and an equal unit. Variance to variance returns the same object, so a unit of adu stays adu.
- StdDev to variance squares values and squares the unit. Variance to StdDev takes the square root and raises the unit to 1/2. For example, a VarianceUncertainty with unit m converted to StdDevUncertainty has unit m, not m to the 1/2. InverseVariance to variance takes the reciprocal and inverts the unit.
- Unit-only cases: a VarianceUncertainty with unit m and a None array converted to VarianceUncertainty keeps unit m. The same object converted to InverseVariance has unit m to the power -1. An InverseVariance with unit m and a None array converted to VarianceUncertainty has unit m to the power -1, not -2.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to a different supported class via variance produces a result of the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class raises TypeError. Converting between an unsupported and a supported class, in either direction, raises TypeError.
- A supported uncertainty with a None array converts to a None array without error.
- Constructing a VarianceUncertainty from a StdDevUncertainty still raises IncompatibleUncertaintiesException. Mixed-type arithmetic that was rejected before remains rejected.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's parametrized style and imports. Add any missing numpy testing import needed for approximate comparisons.
- Cover: supported self-conversion for StdDev, Variance, and InverseVariance; conversion to variance and back; unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected values per direction: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance take the reciprocal in either direction; variance to variance is the identity. Do not apply one class's transform to an input of a different class.
- Derive each expected unit by applying the pair's unit rule to the unit the test constructs.
- To check that a fresh result has no parent association, expect access to its parent_nddata to raise MissingDataAssociationException, as existing tests do. Do not compare parent_nddata to None.
- Recommended: a test that a None-array uncertainty converts to a None array.
