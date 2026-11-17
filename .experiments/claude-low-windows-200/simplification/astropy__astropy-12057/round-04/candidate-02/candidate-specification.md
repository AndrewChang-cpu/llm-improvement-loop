## Goals

- Allow explicit conversion between supported `NDUncertainty` subclasses through variance, mirroring the coordinate subsystem's Cartesian path.
- Supported classes: StdDevUncertainty, VarianceUncertainty, InverseVariance. Unsupported classes, such as UnknownUncertainty and test doubles, lack conversion hooks.

## Scope

In scope: one public conversion method on `NDUncertainty`; private per-class hooks on the three supported classes; tests in the existing nddata uncertainty test module; a towncrier changelog fragment.

Out of scope: the constructor type check, implicit conversion in arithmetic propagation, `_convert_uncertainty` and its overrides, and the NDData, I/O, and transport layers.

## Assumptions

- An array or unit may be None; both are valid.
- Conversion is elementwise: squaring, square root, or reciprocal, with unit exponents 2, 1/2, or -1. Results are floats, so tests may compare approximately.

## Terminology

- **Variance-convertible class**: provides both hooks. **Unsupported class**: lacks either hook.
- **Target class**: the class passed to the conversion method.

## Workflows

Converting a source instance to a target class:

1. Look up the to-variance hook on the source instance. If absent, raise TypeError naming the source type.
2. Look up the from-variance hook on the target class. If absent, raise TypeError naming the target class.
3. Call the to-variance hook, pass the result to the target's from-variance hook, and return its result.

Rules:
- Always route through variance, including same-class conversion, so unsupported classes raise TypeError even converted to themselves. Add no same-class shortcut.
- Variance-to-variance returns the same object.
- StdDev to variance: square the array; square the unit.
- Variance to StdDev: take the square root; raise the unit to 1/2.
- InverseVariance to or from variance: take the reciprocal; invert the unit.
- A None array or None unit converts to None. Compute the unit independently of the array, so a unit-only uncertainty keeps its converted unit.

## API contracts

- Public method `represent_as` on `NDUncertainty` takes one positional parameter, `other_uncert`, the target subclass, and returns an instance of it (the same object for variance-to-variance).
- Hook `_convert_to_variance`: instance method on each variance-convertible class, returning a VarianceUncertainty.
- Hook `_convert_from_variance`: class method on each variance-convertible class, accepting a VarianceUncertainty and returning an instance of the class.
- Discovery uses attribute lookup. The base class defines no default hooks.
- A new result has no parent data association. Variance-to-variance keeps its parent association.
- Unsupported conversion raises TypeError, naming the offending class and never IncompatibleUncertaintiesException.

## Module architecture

- All code changes belong in `astropy/nddata/nduncertainty.py`. Add no stored state and no new imports.
- Capability checks and variance dispatch live on the base class. Per-class math lives only in the hooks.
- The constructor type check stays unchanged; mismatched types still raise IncompatibleUncertaintiesException on construction.
- Do not change `_convert_uncertainty`, its `StdDevUncertainty` override, or any `_propagate_*` method.
- Conversion runs only when explicitly requested, never from construction or arithmetic.

## Implementation constraints

- Place `represent_as` after the abstract propagation methods on the base class.
- Check both source and target capabilities before any array math. Add no argument-type validation beyond attribute lookup.
- Each hook maps a None array to None and a None unit to None. Do not catch and re-raise numpy errors.
- `represent_as` has a numpydoc docstring with Parameters, Returns, and Raises sections; Raises documents TypeError.
- Conversion is linear in array size. Avoid copies beyond those needed for the result.

## Naming

- Method `represent_as`, parameter `other_uncert`, hooks `_convert_to_variance` and `_convert_from_variance`.
- Changelog fragment `docs/changes/nddata/12057.feature.rst`, using the task identifier 12057.

## Documentation

- The towncrier fragment states conversion between uncertainty types via variance.
- Updating the nddata usage docs and the 5.1 what's-new page is recommended. Any versionadded note uses 5.1.
- Keep existing docstrings accurate, including `_convert_uncertainty` and the class-level Raises section.
- The `represent_as` docstring describes the returned type and TypeError conditions. It must not mention parent associations or call conversion exact.

## Compatibility

- Conversion never crashes on None arrays or units. Mixed-type arithmetic keeps its original behavior and never silently converts operands.
- Constructing a VarianceUncertainty or StdDevUncertainty from a different uncertainty type still raises IncompatibleUncertaintiesException.
- StdDevUncertainty's arithmetic override still raises for non-StdDev operands. The public API changes only by addition.

## Acceptance criteria

- Same-class conversion of a supported uncertainty returns equal values and unit. Variance to variance returns the same object, so unit adu stays adu.
- Unit examples: VarianceUncertainty with unit m to StdDevUncertainty gives unit m, not m to the 1/2. InverseVariance with unit m to VarianceUncertainty gives unit m to the power -1, not -2. VarianceUncertainty with unit m to InverseVariance gives unit m to the power -1.
- Round-trips through variance return the original values and unit for each supported class.
- A supported class converted to another supported class produces the target class.
- Unsupported classes (FakeUncertainty, UnknownUncertainty) raise TypeError when converted to their own class or to or from a supported class.
- A supported uncertainty with a None array converts to a None array without error.

## Test requirements

- Add tests to `astropy/nddata/tests/test_nduncertainty.py`, using the file's parametrized style. Add any missing numpy testing import needed for approximate comparisons.
- Cover supported self-conversion for all three classes, conversion to variance and back, and unsupported self-conversion raising TypeError.
- Expected values: StdDev to variance squares; variance to StdDev takes the square root; InverseVariance and variance take the reciprocal in either direction; variance to variance is the identity. Never apply one class's transform to another class's input.
- Derive each expected unit by applying the pair's unit rule to the constructed unit.
- For a fresh result, expect access to `parent_nddata` to raise MissingDataAssociationException, as existing tests do. Do not compare it to None.
