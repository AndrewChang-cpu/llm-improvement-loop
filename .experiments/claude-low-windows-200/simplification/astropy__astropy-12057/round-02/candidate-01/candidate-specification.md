## Goals

- Let an `NDUncertainty` subclass be explicitly converted into another subclass through a public method, using variance as the intermediate representation, mirroring the coordinate subsystem's Cartesian path.
- Supported classes: StdDevUncertainty, VarianceUncertainty, InverseVariance. Unsupported classes lack conversion hooks, such as UnknownUncertainty and test doubles.
- The motivation is issue #11862. It is context only.

## Scope

In scope:
- One public conversion method on `NDUncertainty`.
- Private per-class conversion hooks on StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Tests in the existing nddata uncertainty test module.
- A towncrier changelog fragment for nddata.

Out of scope:
- The constructor type check, implicit conversion in propagation, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- The array and the unit may each be None. Both are valid states that conversion must handle.
- Conversion is elementwise. Float results are not bit-exact, so tests may use approximate comparison.
- Mixed uncertainty types stay rejected everywhere except the explicit conversion method.

## Terminology

- **Variance-convertible class**: a subclass providing both hooks. **Unsupported class**: a subclass lacking either hook.
- **Target class**: the class passed to the conversion method.
- **Intermediate variance**: the VarianceUncertainty produced from the source and used to build the target.

## Workflows

Converting a source instance to a target class:

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type as not supporting conversion.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class as not supporting conversion from another type.
3. Call the to-variance hook, pass its result to the target's from-variance hook, and return that result.

Rules:
- Always route through variance, even for same-class conversion. Do not add a same-class shortcut that skips the capability check, so an unsupported class converted to itself raises TypeError.
- Variance to variance returns the same object.
- StdDev to variance: square the array and square the unit.
- Variance to StdDev: take the square root of the array and raise the unit to 1/2.
- InverseVariance to variance, and variance to InverseVariance: take the reciprocal of the array and invert the unit.
- Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit. A None array stays None, and a None unit stays None.
- Capability checks on source and target happen before any array math.

## Data model

- No stored state is added.
- A conversion result is a new target-class instance with no parent data association. The exception is variance to variance, which returns the same object with its existing association.

## API contracts

- `represent_as`: public method on `NDUncertainty` with one positional parameter, `other_uncert`, the target subclass. It returns an instance of that subclass, or the same object for variance to variance.
- `_convert_to_variance`: instance method on each variance-convertible class, returning a VarianceUncertainty.
- `_convert_from_variance`: class method on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup, so a class without a hook is unsupported. The base class must not define default hooks, because defaults would make every class look supported.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, in both same-class and cross-class cases.

## Module architecture

- All code changes go in `astropy/nddata/nduncertainty.py`.
- Orchestration (capability checks, dispatch through variance) lives on the base class. Per-class math lives in the hooks.
- The constructor type check is unchanged. Mismatched construction still raises IncompatibleUncertaintiesException.
- Do not change `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method. Propagation behavior must stay identical.
- Conversion is explicit only. It must never run implicitly from construction or arithmetic.

## Implementation constraints

- Place `represent_as` on the base class after the abstract propagation methods.
- Discover hooks by attribute lookup, not a registry or a chain of type checks.
- Add no imports. Use the module's existing numpy and unit facilities.
- Each hook explicitly maps a None array to None and a None unit to None.
- `represent_as` has a numpydoc docstring with Parameters, Returns, and Raises sections. Raises documents TypeError.
- Do not reuse the propagation exception for conversion errors.

## Naming

- Use these exact names: `represent_as`, `other_uncert`, `_convert_to_variance`, `_convert_from_variance`.
- Changelog fragment: `docs/changes/nddata/12057.feature.rst`. Use 12057, the task identifier, not 11862.

## Error handling

- Unsupported source: TypeError naming the source type and stating it does not support conversion to another uncertainty type.
- Unsupported target: TypeError naming the target class and stating it does not support conversion from another uncertainty type.
- Handle None arrays explicitly. Do not catch and re-raise numpy errors.

## Documentation

- Add the towncrier fragment, stating conversion between uncertainty types via variance.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended. Any versionadded note uses 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including the `_convert_uncertainty` docstring and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not say the result lacks a parent NDData association, and must not call conversion exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid copies beyond those needed for the result.

## Reliability

- Conversion never crashes on None arrays or None units.
- Implicit mixed-type arithmetic keeps its original behavior and never silently converts operands.

## Usability

- Users call one documented method. Unsupported conversion raises TypeError.

## Maintainability

- Keep each class's conversion formulas only in its hooks. Do not duplicate them in the propagation path.

## Compatibility

- Constructing a VarianceUncertainty or StdDevUncertainty from another uncertainty type still raises IncompatibleUncertaintiesException.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands. Variance and InverseVariance propagation is unchanged.
- The public API changes only by addition.

## Behavioral acceptance criteria

- Converting a supported uncertainty to its own class returns equal values and an equal unit. Variance to variance returns the same object, so unit adu stays adu and the array is not transformed.
- StdDev to variance squares values and squares the unit. Variance to StdDev takes the square root and raises the unit to 1/2. For example, a VarianceUncertainty with unit m converted to StdDevUncertainty has unit m to the 1/2.
- Unit-only examples: a VarianceUncertainty with unit m and a None array converted to InverseVariance has unit m to the power -1. An InverseVariance with unit m and a None array converted to VarianceUncertainty has unit m to the power -1, not -2.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to a different supported class produces an instance of the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class raises TypeError. Converting between an unsupported and a supported class, in either direction, raises TypeError.
- A supported uncertainty with a None array converts to a None array without error.
- Mixed-type arithmetic that was rejected before remains rejected.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's parametrized style and imports. Add any numpy testing import needed for approximate comparisons.
- Cover: supported self-conversion for each supported class; conversion to variance and back; unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected values: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance take the reciprocal in either direction; variance to variance is the identity. Do not apply one class's transform to an input of another class.
- Derive each expected unit by applying the pair's unit rule to the test's unit. Do not reuse a unit or exponent from another pair.
- To check that a fresh result has no parent association, expect access to its parent_nddata to raise MissingDataAssociationException, as existing tests do. Do not compare parent_nddata to None, because the getter raises instead of returning None.
- Recommended: a test that a None-array uncertainty converts to a None array.
