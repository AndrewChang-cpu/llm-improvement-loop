## Goals

- Let an uncertainty of one `NDUncertainty` subclass be explicitly converted into another subclass through a public method, using variance as the common intermediate representation.
- Supported classes: StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Unsupported classes: those lacking conversion hooks, such as UnknownUncertainty and test doubles.
- Issue #11862 is background context only; it adds no requirement.

## Scope

In scope:
- One public conversion method on `NDUncertainty`.
- Private per-class conversion hooks on StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Tests in the existing nddata uncertainty test module.
- A towncrier changelog fragment.

Out of scope:
- The constructor type check.
- Implicit conversion in arithmetic propagation.
- `_convert_uncertainty` and its override.
- NDData, I/O, and transport layers.

## Assumptions

- An array may be None (the default), and a unit may be None. Conversion must handle both.
- Conversion is elementwise: squaring, square root, or reciprocal, with unit exponents 2, 1/2, or -1. Float results are not bit-exact, so tests comparing transformed floats may use approximate comparison.
- Mixed uncertainty types stay rejected everywhere except the explicit conversion method.

## Terminology

- **Variance-convertible class**: a subclass providing both the to-variance and from-variance hooks.
- **Unsupported class**: a subclass lacking either hook.
- **Target class**: the class passed to the conversion method.
- **Intermediate variance**: the VarianceUncertainty produced from the source and consumed to build the target.

## Workflows

Conversion on a source instance with a target class proceeds as follows:

1. Look up the source's to-variance hook by attribute lookup. If absent, raise TypeError naming the source type.
2. Look up the target class's from-variance hook by attribute lookup. If absent, raise TypeError naming the target class.
3. Call the to-variance hook to get a variance uncertainty, pass it to the target's from-variance hook, and return the result.

Rules:
- Always route through variance, including same-class conversion. Do not add a same-class shortcut that skips the capability check. An unsupported class converted to itself raises TypeError.
- Variance-to-variance returns the same object.
- StdDev to variance: square the array; square the unit.
- Variance to StdDev: take the square root of the array; raise the unit to 1/2.
- InverseVariance to variance, and variance to InverseVariance: take the reciprocal of the array; take the reciprocal of the unit.
- A None array converts to None. A None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## Data model

- No stored state is added to any uncertainty class.
- A conversion returns a new instance of the target class, except variance-to-variance, which returns the same object. A new result has no parent data association; the existing object keeps whatever association it has.
- Converted units follow the exponent rules, so unit and array stay consistent.

## API contracts

- Public method `represent_as` on `NDUncertainty`. It takes one positional parameter, `other_uncert`, the target subclass, and returns an instance of that subclass (or the same object for variance-to-variance). Do not state that the result is exact or lacks a parent association.
- Private instance hook `_convert_to_variance` on each variance-convertible class, returning a VarianceUncertainty.
- Private class-method hook `_convert_from_variance` on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Hooks are discovered by attribute lookup, so a class without a hook is unsupported. `NDUncertainty` must not define default hooks; a base default would make every class look supported and raise the wrong exception.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, in both same-class and cross-class cases.

## Module architecture

- All changes go in `astropy/nddata/nduncertainty.py`.
- Orchestration (capability checks and dispatch through variance) lives on the `NDUncertainty` base class. Per-class math lives in the hooks.
- The constructor's uncertainty-type check stays unchanged; mismatched types still raise IncompatibleUncertaintiesException on construction.
- Do not change `NDUncertainty._convert_uncertainty`, the StdDev override, or any `_propagate_*` method. Propagation behavior must match the original.
- Conversion is explicit only. It must not run from construction or arithmetic.

## Implementation constraints

- Place `represent_as` after the abstract propagation methods.
- Discover hooks by attribute lookup, not a registry or a type-check chain.
- Add no new imports; use the module's existing numpy and unit facilities.
- Each hook maps a None array to None and a None unit to None explicitly.
- `represent_as` gets a numpydoc docstring with Parameters, Returns, and Raises sections; Raises documents TypeError.
- Do not reuse the propagation exception for conversion errors.

## Dependencies

- No new packages, modules, or configuration changes.

## Naming

- Method `represent_as`; parameter `other_uncert`; hooks `_convert_to_variance` (instance) and `_convert_from_variance` (class method). Use these exact names.
- Changelog fragment: `docs/changes/nddata/12057.feature.rst`. Use 12057, the pull request number, not 11862, the issue number.

## Validation

- Capability checks for both source and target happen inside `represent_as` before any array math.
- Add no argument-type validation beyond what attribute lookup provides.

## Error handling

- Unsupported source: TypeError naming the source type and stating it does not support conversion to another uncertainty type.
- Unsupported target: TypeError naming the target class and stating it does not support conversion from another uncertainty type.
- Handle None arrays explicitly; do not catch and re-raise numpy errors.
- Constructor and propagation error behavior stays unchanged.

## Logging

- No logging is added.

## Documentation

- Add the towncrier fragment describing conversion between uncertainty types via variance.
- Recommended: update the nddata usage docs and the 5.1 what's-new page. If a versionadded note is added, use 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the `NDUncertainty` class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not claim the result has no parent association or that conversion is exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid copies beyond those needed to build the result.

## Security

- No security-relevant behavior is introduced.

## Reliability

- Conversion never crashes on None arrays or units; a None array converts to None.
- Implicit mixed-type arithmetic keeps its original behavior and must not silently convert operands.

## Usability

- Users call one documented method. Unsupported conversion raises TypeError.

## Maintainability

- Keep conversion formulas only in the hooks; do not duplicate them in the propagation path.

## Compatibility

- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands; Variance and InverseVariance propagation is unchanged.
- The public API changes only by addition.

## Operations

- No operational or deployment behavior changes.

## Behavioral acceptance criteria

- Converting a supported uncertainty to its own class returns equal array values and an equal unit.
- VarianceUncertainty to VarianceUncertainty returns the same object, unchanged. A unit of adu stays adu; the array is not transformed.
- StdDev to Variance squares values and unit. Variance to StdDev takes the square root and unit to the 1/2 power, so a variance with unit m squared becomes a StdDev with unit m. InverseVariance to Variance uses the reciprocal of values and unit.
- Unit-only cases: a Variance with unit m and None array converted to Variance keeps unit m; converted to InverseVariance it has unit m to the power -1. An InverseVariance with unit m and None array converted to Variance has unit m to the power -1, not -2.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to another supported class produces the target class.
- Converting an unsupported class to its own class raises TypeError (FakeUncertainty, UnknownUncertainty).
- Converting between an unsupported and a supported class, in either direction, raises TypeError.
- A supported uncertainty with a None array returns a None array without error; a unit-only uncertainty keeps its converted unit.
- Constructing a VarianceUncertainty from a StdDevUncertainty still raises IncompatibleUncertaintiesException.
- Mixed-type arithmetic that was rejected before remains rejected.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py` in the file's parametrized style, with any missing numpy testing import needed for approximate comparisons.
- Cover: supported self-conversion for each class; conversion to variance and back; unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected values: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance each take the reciprocal in the other direction; variance to variance is the identity. Do not apply one class's transform to another class's input.
- Expected units: derive each from the pair's unit rule applied to the unit the test constructs. Do not reuse a unit or exponent from another pair. Example: InverseVariance with unit m converts to variance with unit m to the power -1; the variance-to-variance case keeps its unit.
- To check a freshly converted result has no parent, expect access to `parent_nddata` to raise MissingDataAssociationException, as existing tests do. Do not compare it to None; the getter raises.
- Recommended: a test that a None-array uncertainty converts to a None array.
