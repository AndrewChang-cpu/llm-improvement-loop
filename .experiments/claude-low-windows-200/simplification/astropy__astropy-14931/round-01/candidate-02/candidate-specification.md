# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW cosmology instance.
- The value is the existing scale factor evaluated at z = 0, returned as a dimensionless astropy Quantity, so it always agrees with the scale factor method.

## Scope
- In scope: astropy/cosmology/flrw/base.py, astropy/cosmology/flrw/tests/test_base.py, and the new changelog fragment docs/changes/cosmology/14931.api.rst.
- Out of scope: the generic Cosmology base class and its registration logic, Parameter definitions, constructor signatures, serialization/io, and other packages.

## Assumptions
- FLRW already defines a scale factor method taking a redshift and returning a float for scalar input; it is the single definition, a(z) = 1/(1+z).
- astropy.units is already imported in the FLRW base module.

## Terminology
- a(z) = 1/(1+z); a0 denotes a(0), which equals 1 under the standard convention.
- Dimensionless Quantity: an astropy Quantity with unit astropy.units.one. A plain float does not satisfy this.

## Workflows
- A user reads scale_factor0 on any FLRW instance, including flat subclasses, with no arguments and receives a dimensionless Quantity equal to 1.
- Calls to the scale factor method keep their current behavior for scalar and array redshifts.

## Data model
- scale_factor0 is derived: not stored on the instance, not a Parameter, not a constructor argument, not a serialization field.
- Each access evaluates the scale factor method at z = 0.

## API contracts
- Name: scale_factor0, a read-only property taking no arguments, visible on FLRW and all subclasses.
- Return: a scalar astropy Quantity with unit one whose numeric value equals the scale factor method at z = 0. A bare float is not acceptable.
- The scale factor method's name, parameter, and return types (float for scalar input, array for array input) are unchanged.

## Module architecture
- In the FLRW base module, add a private mixin class _ScaleFactorMixin immediately before the FLRW class.
- The mixin holds scale_factor0 and the scale factor method. Move the existing scale factor method out of the FLRW class body into the mixin without changing its logic, so exactly one definition exists.
- The FLRW base list is the Cosmology base class followed by the mixin.
- scale_factor0 obtains its numeric value by calling the scale factor method with z = 0 and wraps that result as a dimensionless Quantity. It must not restate the literal 1.

## Implementation constraints
- Do not hard-code 1.0 or any other constant in scale_factor0; derive it through the scale factor method so overrides are respected.
- Add no new imports to either modified module. Do not add an import line to the test module, since that breaks the repository's import ordering check; use only names it already imports.
- Do not modify the generic Cosmology class in core.py or its subclass registration hook.
- The mixin stays private and is not exported.

## Dependencies
- No new packages or modules. Use only existing astropy.units and the existing redshift conversion helper.

## Naming
- Public name scale_factor0 follows the *0 suffix convention of critical_density0, Ogamma0, and Onu0.
- Private mixin name: _ScaleFactorMixin.

## Validation
- scale_factor0 takes no input and performs no validation of its own. Redshift validation of the scale factor method is unchanged.

## Error handling
- No new exceptions. Errors from the scale factor method propagate unchanged.

## Logging
- Not applicable.

## Documentation
- scale_factor0 has a docstring with a one-line summary stating it is the scale factor at redshift 0, then an extended description: the scale factor is a = a0/(1+z); the common convention sets a0 = 1; using a0 explicitly in code avoids ambiguity. Match neighboring property docstrings.
- Add docs/changes/cosmology/14931.api.rst stating that the scale_factor0 property was added to Cosmology objects, that it is the scale factor at redshift 0, and that it is defined to be 1.0.
- Omit pull-request process text such as mentions or pings.

## Performance
- No caching. Each access costs one scale factor evaluation.

## Security
- Not applicable.

## Reliability
- scale_factor0 equals the scale factor method at z = 0 for every FLRW subclass, including subclasses that override the method.

## Usability
- The unit-aware return composes with astropy units; comparison to 1 and numpy.allclose against the method at z = 0 must work.

## Maintainability
- Keep one definition of the scale factor; scale_factor0 must not duplicate the formula or constant.

## Compatibility
- Additive change. No existing public attribute or method is removed or changed in behavior, including FLRW subclass behavior after the move into the mixin.

## Operations
- The change must apply as a patch to the original snapshot, limited to the three files in Scope.

## Behavioral acceptance criteria
- For every FLRW subclass instance: scale_factor0 is an astropy Quantity with unit astropy.units.one, value 1, and numpy.allclose against the scale factor method at z = 0.
- For each valid redshift in the existing test list, covering every entry type (scalar numbers, plain Python lists, numpy arrays, table columns, redshift-unit Quantities), the scale factor method returns 1/(1+z) on numeric values.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. It checks Quantity type, unit, value 1, and agreement with the scale factor method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking the method equals 1/(1+z). First convert the parametrized redshift to a plain numeric array, then compute 1 divided by (1 plus that array). Do not apply arithmetic to the raw value, since plain lists and redshift Quantities fail under direct arithmetic. Do not use the implementation's redshift helper for the expected value; it must be an independent oracle.
- Use the existing cosmology test fixture.
