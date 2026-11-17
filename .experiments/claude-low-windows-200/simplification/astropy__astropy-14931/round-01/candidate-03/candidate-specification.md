# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW cosmology instance.
- The value is the existing scale factor evaluated at z = 0, returned as a dimensionless astropy Quantity, so it always agrees with the scale factor method.

## Scope
- In scope: the FLRW base module (astropy/cosmology/flrw/base.py), the FLRW tests (astropy/cosmology/flrw/tests/test_base.py), and one new changelog fragment (docs/changes/cosmology/14931.api.rst).
- Out of scope: the generic Cosmology base class and its registration logic, Parameter definitions, constructor signatures, serialization/io, and other packages.

## Assumptions
- The FLRW class already defines a scale factor method that takes a redshift and returns a float for scalar input. It is the single existing definition, a(z) = 1/(1+z).
- astropy.units is already imported in the FLRW base module.

## Terminology
- Scale factor a(z) = 1/(1+z); a0 denotes a(0), which equals 1 under the standard convention.
- Dimensionless Quantity: an astropy Quantity whose unit is astropy.units.one. A plain Python float does not satisfy this term.

## Workflows
- A user reads scale_factor0 on any FLRW instance, including flat subclasses, with no arguments and receives a dimensionless Quantity equal to 1.
- Calls to the existing scale factor method keep their current behavior for scalar and array redshifts.

## Data model
- scale_factor0 is derived. It is not stored on the instance, not a Parameter, not a constructor argument, and not a serialization field.
- Each access evaluates the scale factor method at z = 0.

## API contracts
- Name: scale_factor0, a read-only property taking no arguments, visible on FLRW and all its subclasses.
- Return type: a scalar astropy Quantity with unit one. Its numeric value equals the scale factor method at z = 0.
- A bare float is not acceptable.
- The scale factor method's name, parameters, and return types (float for scalar input, array for array input) remain unchanged.

## Module architecture
- In the FLRW base module, add a private mixin class named _ScaleFactorMixin, defined immediately before the FLRW class.
- The mixin contains scale_factor0 and the scale factor method. Move the existing scale factor method into the mixin unchanged, so exactly one definition exists.
- The FLRW class's base list is the Cosmology base class followed by the mixin.
- scale_factor0 obtains its numeric value by calling the scale factor method with z = 0 and wraps that result as a dimensionless Quantity. It does not restate the literal 1.

## Implementation constraints
- Do not hard-code 1.0 or any other constant in scale_factor0. Derive it through the scale factor method so overrides are respected.
- Add no new imports to either modified module. The test module must use only names it already imports, because an added import breaks the repository's import ordering check.
- Do not modify the generic Cosmology class in core.py or the subclass registration hook.
- The mixin stays private and is not exported from the package.

## Dependencies
- No new packages, modules, or external libraries. Only the existing astropy.units import and the existing redshift conversion helper are used.

## Naming
- Public name: scale_factor0, following the *0 suffix convention of critical_density0, Ogamma0, and Onu0.
- Private mixin name: _ScaleFactorMixin.

## Validation
- scale_factor0 takes no input and performs no validation of its own.
- Redshift validation of the scale factor method is unchanged.

## Error handling
- No new exceptions. Errors from the scale factor method propagate unchanged.

## Logging
- Not applicable; no logging is added.

## Documentation
- scale_factor0 has a docstring with a one-line summary stating it is the scale factor at redshift 0, followed by an extended description: the scale factor is a = a0/(1+z); the common convention sets a0 = 1; using a0 explicitly in calculations avoids ambiguity. Match the docstring style of neighboring properties.
- Add the changelog fragment docs/changes/cosmology/14931.api.rst. It states that the scale_factor0 property was added to Cosmology objects, that it is the scale factor at redshift 0, and that it is defined to be 1.0.
- Omit pull-request process text such as mentions or pings.

## Performance
- No caching. Each access costs one evaluation of the scale factor method.

## Security
- Not applicable.

## Reliability
- scale_factor0 equals the scale factor method at z = 0 for every FLRW subclass, including subclasses that override the scale factor method.

## Usability
- The unit-aware return composes with astropy units. Comparisons to 1 and numpy.allclose against the scale factor method at z = 0 must work.

## Maintainability
- Keep exactly one definition of the scale factor. scale_factor0 must not duplicate its formula or constant.

## Compatibility
- The change is additive. No existing public attribute or method is removed or changed in behavior, and moving the scale factor method into the mixin does not change subclass behavior.

## Operations
- The change applies as a patch to the original snapshot.
- Edits are limited to the three files listed under Scope.

## Behavioral acceptance criteria
- For every FLRW subclass instance: scale_factor0 is an astropy Quantity; its unit is astropy.units.one; its value is 1; and numpy.allclose against the scale factor method at z = 0 holds.
- For each valid redshift in the existing test redshift list, including every entry type (scalar numbers, plain Python lists, numpy arrays, table columns, and redshift-unit Quantities), the scale factor method returns 1/(1+z), compared on numeric values. The test must pass for all entry types.

## Test requirements
- Add test_scale_factor0 to the FLRW test class in astropy/cosmology/flrw/tests/test_base.py, after the test for the total density parameter. It checks the Quantity type, the unit, the value equal to 1, and agreement with the scale factor method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking that the scale factor method equals 1/(1+z). Convert the parametrized redshift to a plain numeric array first, then evaluate 1 divided by (1 plus that array). Do not apply arithmetic directly to the raw parametrized value, since plain lists and redshift-unit Quantities fail under direct arithmetic. Do not compute the expected value with the implementation's redshift helper; the oracle must be independent.
- Use the existing cosmology test fixture.
- The changelog fragment must be present.
