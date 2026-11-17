## Goals

- Allow explicit conversion between supported `NDUncertainty` subclasses through variance, mirroring the coordinate subsystem's Cartesian path.
- Supported classes: StdDevUncertainty, VarianceUncertainty, InverseVariance. Unsupported classes lack conversion hooks, such as UnknownUncertainty and test doubles.
- A variance-convertible class provides both hooks; an unsupported class lacks either.

## Scope

In scope:
- One public conversion method on `NDUncertainty`.
- Private per-class hooks on the three supported classes.
- Tests in the existing nddata uncertainty test module.
- A towncrier changelog fragment.

Out of scope: the constructor type check, implicit conversion in arithmetic propagation, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- An array or unit may be None; both are valid.
- Conversion is elementwise: squaring, square root, or reciprocal, with unit exponents 2, 1/2, or -1. Results are not bit-exact, so tests may compare approximately.

## Workflows

Converting a source instance to a target class:

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class.
3. Call the to-variance hook, pass the result to the target's from-variance hook, and return its result.

Rules:
- Always route through variance, including same-class conversion. Add no shortcut that skips the capability check.
- Variance-to-variance returns the same object.
- StdDev to variance: square the array and the unit.
- Variance to StdDev: take the square root of the array and raise the unit to 1/2.
- InverseVariance to or from variance: take the reciprocal and invert the unit.
- A None array or None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## API contracts

- Public method `represent_as` on `NDUncertainty`: one positional parameter, `other_uncert`, the target subclass. Returns an instance of that subclass, or the same object for variance-to-variance.
- Hook `_convert_to_variance`: instance method on each variance-convertible class, returning a VarianceUncertainty.
- Hook `_convert_from_variance`: class method on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup. The base class must not define default hooks.
- A new result has no parent data association. Variance-to-variance keeps its parent association.
- Unsupported source raises TypeError naming the source type, stating it does not support conversion to another uncertainty type. Unsupported target raises TypeError naming the target class, stating it does not support conversion from another uncertainty type. Never raise IncompatibleUncertaintiesException for these cases.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`. Add no stored state and no new imports.
- Orchestration (capability checks and dispatch through variance) lives on the base class. Per-class math lives only in the hooks.
- Conversion is explicit only, never run from construction or arithmetic.
- Do not change `NDUncertainty._convert_uncertainty`, the `StdDevUncertainty._convert_uncertainty` override, or any `_propagate_*` method.

## Implementation constraints

- Place `represent_as` after the abstract propagation methods on the base class.
- Check capabilities on both source and target before any array math. Add no argument-type validation beyond attribute lookup.
- Each hook explicitly maps a None array and a None unit to None. Do not catch and re-raise numpy errors.
- `represent_as` has a numpydoc docstring with Parameters, Returns, and Raises sections; Raises documents TypeError.
- Conversion is linear in array size. Avoid copies beyond those needed for the result.

## Documentation

- Add towncrier fragment `docs/changes/nddata/12057.feature.rst` stating conversion between uncertainty types via variance. Use 12057, the task identifier.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended. Any versionadded note uses 5.1, since 5.0 is released.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions only. It must not mention parent associations or call conversion exact.

## Reliability

- Conversion never crashes on None arrays or units. Mixed-type arithmetic keeps its original behavior and never silently converts operands.
- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands.

## Compatibility

- The public API changes only by addition. No new packages or configuration changes.

## Behavioral acceptance criteria

- Same-class conversion of a supported uncertainty returns equal values and an equal unit. Variance to variance returns the same object, so unit adu stays adu.
- A VarianceUncertainty with unit m converted to StdDevUncertainty has unit m, not m to the 1/2. An InverseVariance with unit m converted to VarianceUncertainty has unit m to the power -1, not -2. A VarianceUncertainty with unit m converted to InverseVariance has unit m to the power -1.
- A VarianceUncertainty with unit m and a None array converted to VarianceUncertainty keeps unit m.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to a different supported class produces a result of the target class.
- Converting an unsupported class (FakeUncertainty, UnknownUncertainty) to its own class, or between an unsupported and a supported class in either direction, raises TypeError.
- A supported uncertainty with a None array converts to a None array without error.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's parametrized style and imports. Add any missing numpy testing import needed for approximate comparisons.
- Cover supported self-conversion for StdDev, Variance, and InverseVariance; conversion to variance and back; and unsupported self-conversion raising TypeError for FakeUncertainty and UnknownUncertainty.
- Expected values follow the rules above. Never apply one class's transform to another class's input.
- Derive each expected unit by applying the pair's unit rule to the unit the test constructs.
- For a fresh result, expect access to `parent_nddata` to raise MissingDataAssociationException, as existing tests do. Do not compare it to None.
