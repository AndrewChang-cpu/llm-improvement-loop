## Goals

- Allow explicit conversion between supported `NDUncertainty` subclasses through variance, mirroring the coordinate subsystem's Cartesian path.
- Supported classes: StdDevUncertainty, VarianceUncertainty, InverseVariance. Unsupported classes lack conversion hooks, such as UnknownUncertainty and test doubles.

## Scope

In scope:
- One public conversion method on `NDUncertainty`.
- Private per-class hooks on StdDevUncertainty, VarianceUncertainty, and InverseVariance.
- Tests in the existing nddata uncertainty test module.
- A towncrier changelog fragment.

Out of scope: the constructor type check, implicit conversion in arithmetic propagation, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- An array or unit may be None; both are valid.
- Conversion is elementwise: squaring, square root, or reciprocal, with unit exponents 2, 1/2, or -1. Float results are not bit-exact, so tests may compare approximately.

## Terminology

- **Variance-convertible class**: provides both hooks. **Unsupported class**: lacks either hook.
- **Target class**: the class passed to the conversion method.

## Workflows

Converting a source instance to a target class:

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class.
3. Call the to-variance hook, pass the result to the target's from-variance hook, and return its result.

Rules:
- Always route through variance, including same-class conversion. Do not add a same-class shortcut that skips the capability check, so an unsupported class converted to itself raises TypeError.
- Variance-to-variance returns the same object.
- StdDev to variance: square the array; square the unit.
- Variance to StdDev: take the square root; raise the unit to 1/2.
- InverseVariance to or from variance: take the reciprocal; invert the unit.
- A None array converts to None; a None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## API contracts

- Public method `represent_as` on `NDUncertainty`. It takes one positional parameter, `other_uncert`, the target subclass, and returns an instance of that subclass (the same object for variance-to-variance).
- Hook `_convert_to_variance`: instance method on each variance-convertible class, returning a VarianceUncertainty.
- Hook `_convert_from_variance`: class method on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup, so a class without a hook is unsupported. The base class must not define default hooks.
- A new result is a new target-class instance with no parent data association. Variance-to-variance keeps its parent association.
- Unsupported conversion raises TypeError, never IncompatibleUncertaintiesException, in same-class and cross-class cases.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`. Add no stored state and no new imports.
- Orchestration (capability checks and dispatch through variance) lives on the base class. Per-class math lives only in the hooks.
- The constructor type check stays unchanged; mismatched types still raise IncompatibleUncertaintiesException on construction.
- Do not change `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method.
- Conversion is explicit only, never run from construction or arithmetic.

## Implementation constraints

- Place `represent_as` after the abstract propagation methods on the base class.
- Discover hooks by attribute lookup, not a registry or type checks.
- Check capabilities on both source and target inside `represent_as` before any array math. Add no argument-type validation beyond attribute lookup.
- Each hook explicitly maps a None array to None and a None unit to None. Do not catch and re-raise numpy errors.
- `represent_as` has a numpydoc docstring with Parameters, Returns, and Raises sections; Raises documents TypeError.
- Conversion is elementwise and linear in array size. Avoid copies beyond those needed for the result.

## Naming

- Method `represent_as`, parameter `other_uncert`, hooks `_convert_to_variance` (instance) and `_convert_from_variance` (class method).
- Changelog fragment `docs/changes/nddata/12057.feature.rst`. Use 12057, the task identifier, not 11862.

## Error handling

- Unsupported source: TypeError naming the source type, stating it does not support conversion to another uncertainty type.
- Unsupported target: TypeError naming the target class, stating it does not support conversion from another uncertainty type.

## Documentation

- The towncrier fragment states conversion between uncertainty types via variance.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended. Any versionadded note uses 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not mention parent associations or call conversion exact.

## Reliability and compatibility

- Conversion never crashes on None arrays or None units. Implicit mixed-type arithmetic keeps its original behavior and never silently converts operands.
- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands. Variance and InverseVariance propagation is unchanged.
- The public API changes only by addition. No new packages, configuration changes, or operational changes.

## Behavioral acceptance criteria

- Same-class conversion of a supported uncertainty returns equal values and an equal unit. Variance to variance returns the same object, so unit adu stays adu.
- Examples: a VarianceUncertainty with unit m converted to StdDevUncertainty has unit m, not m to the 1/2. An InverseVariance with unit m converted to VarianceUncertainty has unit m to the power -1, not -2. A VarianceUncertainty with unit m converted to InverseVariance has unit m to the power -1.
- A VarianceUncertainty with unit m and a None array converted to VarianceUncertainty keeps unit m.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to a different supported class produces a result of the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class raises TypeError. Converting between an unsupported and a supported class, in either direction, raises TypeError.
- A supported uncertainty with a None array converts to a None array without error.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's parametrized style and imports. Add any missing numpy testing import needed for approximate comparisons.
- Cover: supported self-conversion for StdDev, Variance, and InverseVariance; conversion to variance and back; unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected values: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance take the reciprocal in either direction; variance to variance is the identity. Never apply one class's transform to another class's input.
- Derive each expected unit by applying the pair's unit rule to the unit the test constructs.
- For a fresh result, expect access to `parent_nddata` to raise MissingDataAssociationException, as existing tests do. Do not compare it to None.
