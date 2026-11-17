## Goals

- Let an uncertainty of one `NDUncertainty` subclass be explicitly converted into another through a public method, using variance as the common intermediate representation, as the coordinate subsystem does with Cartesian.
- Supported classes are StdDevUncertainty, VarianceUncertainty, and InverseVariance. Unsupported classes lack conversion hooks, such as UnknownUncertainty and test doubles.
- Issue #11862 is context only.

## Scope

In scope:
- One public conversion method on `NDUncertainty`.
- Private per-class hooks on StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Tests in the existing nddata uncertainty test module.
- A towncrier fragment for the nddata package.

Out of scope:
- The constructor type check, implicit conversion in arithmetic, `_convert_uncertainty` and its override, `_propagate_*` methods, NDData, I/O, and transport layers.

## Assumptions

- An uncertainty's array (default None) and unit (may be None) are both valid states that conversion must handle.
- Conversion is elementwise: squaring, square root, and reciprocal, with unit exponents 2, 1/2, and -1. Float results are not guaranteed bit-exact, so tests may compare approximately.
- Mixed uncertainty types stay rejected everywhere except the explicit conversion method.

## Terminology

- **Variance-convertible class**: a subclass providing both hooks.
- **Unsupported class**: a subclass lacking either hook.
- **Target class**: the class passed to the conversion method.
- **Intermediate variance**: the VarianceUncertainty produced from the source and consumed to build the target.

## Workflows

Conversion on a source instance with a target class argument proceeds as follows:

1. Look up the to-variance hook on the source by attribute lookup. If absent, raise TypeError naming the source type as not supporting conversion.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class as not supporting conversion from another type.
3. Call the to-variance hook to get a variance uncertainty, pass it to the target's from-variance hook, and return the result.

Rules:
- Always route through variance, including same-class conversion. Do not add a same-class shortcut that skips the capability check. An unsupported class converted to itself raises TypeError.
- Variance to variance returns the same object.
- StdDev to variance: square the array; unit squared.
- Variance to StdDev: square root of the array; unit raised to 1/2.
- InverseVariance to variance, and variance to InverseVariance: reciprocal of the array; reciprocal of the unit.
- A None array converts to None. A None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## Data model

- No stored state is added to any uncertainty class.
- A conversion result is a new instance of the target class, except variance-to-variance, which returns the same object and keeps its existing parent association. A newly built result has no parent association.
- The converted unit always follows the exponent rules above.

## API contracts

- Public method `represent_as`, defined on `NDUncertainty`. It takes one positional parameter, `other_uncert`, the target `NDUncertainty` subclass, and returns an instance of that subclass (or the same object for variance-to-variance).
- Do not state in the public contract that the result has no parent association or that conversion is exact.
- Private instance method `_convert_to_variance` on each variance-convertible class, returning a VarianceUncertainty.
- Private class method `_convert_from_variance` on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup, so a class without a hook is unsupported. `NDUncertainty` must not define default hooks, since a base default would make every class look supported and raise the wrong exception.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, for both same-class and cross-class cases.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`.
- Capability checks and variance dispatch live on the `NDUncertainty` base class. Per-class math lives in the hooks.
- The constructor's uncertainty-type check stays unchanged, so mismatched types still raise IncompatibleUncertaintiesException on construction.
- Conversion is explicit only. It is never invoked from construction or arithmetic.

## Implementation constraints

- Place `represent_as` on `NDUncertainty` after the abstract propagation methods.
- Use attribute lookup, not a registry or type-check chain, to find hooks.
- Add no new imports. Use the module's existing numpy and unit facilities.
- Each hook explicitly maps a None array to None and a None unit to None.
- Give `represent_as` a numpydoc docstring with Parameters, Returns, and Raises (documenting TypeError) sections.
- Do not reuse the propagation exception for conversion errors.

## Dependencies

- No new packages, modules, or configuration changes.

## Naming

- Method `represent_as`; parameter `other_uncert`.
- Hooks `_convert_to_variance` (instance) and `_convert_from_variance` (class method), with these exact names.
- Changelog fragment named for pull request 12057 (the task identifier), not issue 11862.

## Validation

- Capability checks on both source and target happen inside `represent_as` before any array math.
- Add no argument-type validation beyond attribute lookup.

## Error handling

- Unsupported source: TypeError naming the source type and stating it does not support conversion to another uncertainty type.
- Unsupported target: TypeError naming the target class and stating it does not support conversion from another uncertainty type.
- Handle None arrays explicitly. Do not catch and re-raise numpy errors.
- Constructor and propagation error behavior stays unchanged.

## Logging

- No logging is required or added.

## Documentation

- Add `docs/changes/nddata/12057.feature.rst` describing conversion between uncertainty types via variance.
- Recommended: update the nddata usage docs and the 5.1 what's-new page. If a versionadded note is added, use 5.1, since 5.0 is released.
- Existing docstrings, including `_convert_uncertainty` and the `NDUncertainty` Raises section, must stay accurate for unchanged behavior.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not claim the result lacks a parent association, which is false for variance-to-variance, and must not call conversion exact.

## Performance

- Conversion is elementwise and linear in array size. Avoid copies beyond those needed to build the result.

## Security

- No security-relevant behavior is introduced.

## Reliability

- Conversion never crashes on None arrays or None units.
- Implicit mixed-type arithmetic keeps its original behavior and never silently converts operands.

## Usability

- Users call one documented method. Unsupported conversion always raises TypeError.

## Maintainability

- Keep each class's conversion formulas only in its hooks. Do not duplicate conversion math in propagation.

## Compatibility

- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands. Variance and InverseVariance propagation is unchanged.
- The public API changes only by addition.

## Operations

- No operational or deployment behavior changes.

## Behavioral acceptance criteria

- Converting a supported uncertainty to its own class returns equal array values and an equal unit. Variance to variance returns the same object unchanged: unit adu stays adu, and values are not transformed.
- StdDev to Variance squares values and units. Variance to StdDev takes the square root and unit power 1/2. For example, a VarianceUncertainty with unit m squared converted to StdDevUncertainty has unit m, not m to the 1/2.
- InverseVariance to Variance uses reciprocal values and the reciprocal unit.
- Unit-only examples: a VarianceUncertainty with unit m and None array converted to VarianceUncertainty keeps unit m. Converted to InverseVariance, it has unit m to the -1. An InverseVariance with unit m and None array converted to VarianceUncertainty has unit m to the -1, not m to the -2.
- Round trips through variance return the original values and unit for each supported class.
- A supported class converted to another supported class produces an instance of the target class.
- Converting FakeUncertainty or UnknownUncertainty to its own class raises TypeError.
- Converting between an unsupported and a supported class, in either direction, raises TypeError.
- A supported uncertainty with a None array converts to a None array without error. A unit-only uncertainty keeps its converted unit.
- Constructing a VarianceUncertainty from a StdDevUncertainty still raises IncompatibleUncertaintiesException.
- Mixed-type arithmetic that was rejected before remains rejected.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py` in the file's parametrized style, with any missing numpy testing import needed for approximate comparisons.
- Cover: supported self-conversion for StdDev, Variance, and InverseVariance; conversion to variance and back; TypeError for self-conversion of FakeUncertainty and UnknownUncertainty.
- Expected arrays: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance take the reciprocal in each direction; variance to variance is the identity. Do not apply one class's transform to another class's input.
- Derive each expected unit by applying the pair's unit rule to the unit the test constructs. Do not reuse a unit or exponent from another pair.
- To check that a fresh result has no parent association, expect `parent_nddata` access to raise MissingDataAssociationException, as existing tests do. Do not compare it to None, since the getter raises.
- Recommended: test that a None-array conversion returns a None array.
