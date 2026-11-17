## Goals

- Let an uncertainty object of one `NDUncertainty` subclass be explicitly converted into another subclass through a public conversion method, using variance as the common intermediate representation. This mirrors the coordinate subsystem, where Cartesian is the common path.
- Supported classes are the three variance-convertible subclasses: StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Unsupported classes are those without conversion hooks, such as UnknownUncertainty and test doubles that lack the hooks.
- The feature motivation is issue #11862. That reference is context only; it does not change any requirement.

## Scope

In scope:
- One public conversion method on the `NDUncertainty` base class.
- Private per-class conversion hooks on StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Tests in the existing nddata uncertainty test module.
- A towncrier changelog fragment for the nddata package.

Out of scope:
- Changing the constructor's type check.
- Changing implicit conversion in arithmetic propagation.
- Changing any `_convert_uncertainty` method or override.
- NDData, I/O, and transport layers.

## Assumptions

- An uncertainty's array may be None (the default), and its unit may be None. Both are valid states that conversion must handle.
- Conversion is elementwise arithmetic: squaring, square root, and reciprocal, with unit exponents of 2, 1/2, and -1. Floating-point results are not guaranteed to be bit-exact, so tests that compare transformed float values may use approximate comparison.
- Mixed uncertainty types remain rejected everywhere except the explicit conversion method.

## Terminology

- **Variance-convertible class**: a subclass that provides both the to-variance hook and the from-variance hook.
- **Unsupported class**: a subclass lacking either hook.
- **Target class**: the class passed to the conversion method as its single argument.
- **Intermediate variance**: a VarianceUncertainty produced from the source and consumed to build the target.

## Workflows

Conversion via the public method on a source instance, with a target class argument, must proceed as follows:

1. Look up the to-variance hook on the source instance by attribute lookup. If absent, raise TypeError naming the source type as not supporting conversion.
2. Look up the from-variance hook on the target class by attribute lookup. If absent, raise TypeError naming the target class as not supporting conversion from another type.
3. Call the to-variance hook to obtain a variance uncertainty, then call the target's from-variance hook with it and return the result.

Rules:
- Always route through variance, including when source and target are the same class. Do not add a same-class shortcut that bypasses the capability check. An unsupported class converted to itself must raise TypeError.
- Variance-to-variance conversion returns the same variance uncertainty object.
- StdDev to variance: square the array; the unit becomes the unit squared.
- Variance to StdDev: take the square root of the array; the unit becomes the unit raised to 1/2.
- InverseVariance to variance: take the reciprocal of the array; the unit becomes the reciprocal of the unit.
- Variance to InverseVariance: take the reciprocal of the array; the unit becomes the reciprocal of the unit.
- If the array is None, the converted array is None. If the unit is None, the converted unit is None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## Data model

- The feature adds no stored state to any uncertainty class.
- A conversion result is a new instance of the target class, except variance-to-variance, which returns the same object. A newly built result has no parent data association. Because the variance-to-variance case returns the existing object, that object keeps whatever parent association it already has.
- Units follow the exponent rules above, so the converted unit is always consistent with the converted array.

## API contracts

- Public method name: `represent_as`, defined on the `NDUncertainty` base class. It takes one positional parameter named `other_uncert`, which is the target `NDUncertainty` subclass. It returns an instance of that subclass.
- The return contract is: an instance of the target class, or, for variance-to-variance, the same object that was called. Do not state or imply in the public contract that the result has no parent association or that conversion is exact.
- Private hook on each variance-convertible class: an instance method named `_convert_to_variance` that returns a VarianceUncertainty.
- Private hook on each variance-convertible class: a class method named `_convert_from_variance` that accepts a VarianceUncertainty and returns an instance of the class.
- Hook discovery must use attribute lookup, so that a class without a hook is unsupported. The `NDUncertainty` base class must not define default hooks; a base default would make every class look supported and would raise the wrong exception type.
- Public exception contract: unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, for both the same-class and cross-class cases.

## Module architecture

- All changes belong in `astropy/nddata/nduncertainty.py`.
- Orchestration (capability checks and dispatch through variance) lives on the `NDUncertainty` base class. Per-class math lives on the subclasses' hooks.
- The `NDUncertainty` constructor's uncertainty-type check must remain unchanged. Mismatched types still raise IncompatibleUncertaintiesException on construction.
- Do not change `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method. Propagation behavior must be identical to the original.
- Conversion is explicit only. It must not be invoked implicitly from construction or arithmetic.

## Implementation constraints

- Place `represent_as` on the `NDUncertainty` base class after the abstract propagation methods.
- Use attribute lookup, not a registry or a chain of type checks, to discover hooks.
- Add no new imports. Use the module's existing numpy and unit facilities.
- Each hook must explicitly map a None array to None and a None unit to None.
- Give `represent_as` a numpydoc docstring with Parameters, Returns, and Raises sections. The Raises section documents TypeError.
- Do not reuse the propagation exception for conversion errors.

## Dependencies

- No new packages, modules, or configuration changes. The feature uses only numpy and astropy units already used by the module.

## Naming

- Public method: `represent_as`. Its parameter: `other_uncert`.
- Hooks: `_convert_to_variance` (instance) and `_convert_from_variance` (class method). Use these exact names so the registration mechanism is consistent.
- Changelog fragment: named with the pull request number 12057 (the task identifier), type `feature`, inside `docs/changes/nddata/`. Do not use 11862, which is the issue number.

## Validation

- Capability validation of both source and target happens inside `represent_as` before any array math.
- Do not add extra argument-type validation beyond what the attribute lookup provides.

## Error handling

- Unsupported source: raise TypeError with a message naming the source type and stating it does not support conversion to another uncertainty type.
- Unsupported target: raise TypeError with a message naming the target class and stating it does not support conversion from another uncertainty type.
- Do not catch and re-raise numpy errors for None arrays; handle None explicitly.
- Keep the constructor and propagation error behavior unchanged.

## Logging

- No logging is required or added.

## Documentation

- Add the towncrier fragment `docs/changes/nddata/12057.feature.rst` describing conversion between uncertainty types via variance.
- The reference also updates the nddata usage docs and the 5.1 what's-new page. These are recommended. If a versionadded note is added, use 5.1 because 5.0 is already released.
- Keep existing docstrings accurate. The `_convert_uncertainty` docstring and the `NDUncertainty` class-level Raises section must still describe the unchanged behavior.
- The `represent_as` docstring describes the returned instance type and the TypeError conditions. It must not state that the result has no parent NDData association (false for the variance-to-variance case, which returns the same object) and must not describe the conversion as exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid unnecessary copies beyond those needed to build the result.

## Security

- No security-relevant behavior is introduced.

## Reliability

- Conversion must never crash on None arrays or None units. A None array converts to a None array.
- Implicit mixed-type arithmetic must keep its original behavior and must not silently convert operands.

## Usability

- Users call one documented method to convert types. Error types are predictable: TypeError for unsupported conversion.

## Maintainability

- Keep each class's conversion formulas only in its hooks. Do not duplicate conversion math in the propagation path.

## Compatibility

- Existing constructor behavior is preserved: constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- Existing arithmetic behavior is preserved: StdDevUncertainty's override still raises for non-StdDev operands, and Variance and InverseVariance propagation behavior is unchanged.
- The public API changes only by addition.

## Operations

- No operational or deployment behavior changes.

## Behavioral acceptance criteria

- Converting a supported uncertainty to its own class returns an object with equal array values and an equal unit.
- Converting a VarianceUncertainty to VarianceUncertainty returns the same object, so its values and unit are unchanged. For example, a unit of adu stays adu and is not squared, and its array is not square-rooted or otherwise transformed.
- StdDev to Variance squares the values and squares the unit. Variance to StdDev takes the square root and the unit to the 1/2 power. For example, a VarianceUncertainty with unit m squared converted to StdDevUncertainty has unit m, not m to the 1/2 power. InverseVariance to Variance uses the reciprocal of the values and the reciprocal of the unit.
- Unit-only examples: a VarianceUncertainty with unit m and a None array converted to VarianceUncertainty keeps unit m. The same object converted to InverseVariance has unit m to the power -1. An InverseVariance with unit m and a None array converted to VarianceUncertainty has unit m to the power -1, not m to the power -2.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to a different supported class via variance produces a result of the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class raises TypeError.
- Converting between an unsupported class and a supported class, in either direction, raises TypeError.
- Converting a supported uncertainty whose array is None returns a result whose array is None, with no error. A unit-only uncertainty keeps its converted unit.
- Constructing a VarianceUncertainty from a StdDevUncertainty still raises IncompatibleUncertaintiesException.
- Mixed-type arithmetic that was rejected before remains rejected.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's existing parametrized style and imports. Add any missing numpy testing import needed for approximate comparisons.
- Cover: supported self-conversion for StdDev, Variance, and InverseVariance; conversion to variance and back from variance; unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected array values per class, for each direction. StdDevUncertainty to variance squares the values; variance to StdDevUncertainty takes the square root. InverseVariance to variance and variance to InverseVariance each take the reciprocal. A VarianceUncertainty to VarianceUncertainty conversion is the identity: the expected values equal the input values, and no square or square root is applied. Do not apply one class's transform to an input of a different class.
- Expected units: derive every expected unit by applying the pair's unit rule to the unit the test itself constructs, using the unit rules above. Do not reuse a unit or exponent from a different pair or class. For example, an InverseVariance built with unit m converts to variance with unit m to the power -1, and a VarianceUncertainty built with unit m converts to variance with unit m. The square root of a squared unit is the original unit, and the variance-to-variance case keeps its unit unchanged.
- To check that a freshly converted result has no parent association, expect access to its parent_nddata to raise MissingDataAssociationException, as the existing tests do. Do not compare parent_nddata to None, because the getter raises instead of returning None.
- Recommended: add a test for a None-array uncertainty conversion returning None array.

