# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.
- Its value equals the scale factor method evaluated at z = 0, returned as a dimensionless astropy Quantity.

## Scope
- In scope: astropy/cosmology/flrw/base.py, astropy/cosmology/flrw/tests/test_base.py, and the new changelog fragment docs/changes/cosmology/14931.api.rst.
- Out of scope: the generic Cosmology class and registration logic, Parameter definitions, constructor signatures, serialization, and other packages.

## Assumptions
- FLRW already defines the scale factor method, a(z) = 1/(1+z), returning a float for scalar input.
- astropy.units is already imported in the FLRW base module.

## Terminology
- a0 denotes a(0), which equals 1 under the standard convention.
- Dimensionless Quantity: an astropy Quantity with unit astropy.units.one. A plain float does not qualify.

## Workflows
- Reading scale_factor0 on any FLRW instance, including flat subclasses, with no arguments returns a dimensionless Quantity equal to 1.
- Existing scale factor method calls keep their current behavior for scalar and array redshifts.

## Data model
- scale_factor0 is derived, not stored. It is not a Parameter, constructor argument, or serialization field.

## API contracts
- scale_factor0: a read-only property taking no arguments, visible on FLRW and all subclasses.
- Returns a scalar astropy Quantity with unit one whose value equals the scale factor method at z = 0. A bare float is not acceptable.
- The scale factor method's name, parameters, and return types are unchanged.

## Module architecture
- In the FLRW base module, add a private mixin class named _ScaleFactorMixin immediately before the FLRW class. Move the existing scale factor method into it unchanged in logic, so exactly one definition exists.
- The FLRW bases are the Cosmology base class followed by the mixin. The mixin is not exported from the package.
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity.

## Implementation constraints
- Do not hard-code 1.0 or any other constant in scale_factor0; derive it through the scale factor method so overrides are respected.
- Add no new imports. The test module uses only names it already imports, since an added import breaks the repository's import ordering check.
- Do not modify the generic Cosmology class in core.py or its subclass registration hook. Add no new packages or libraries.

## Naming
- The name scale_factor0 follows the *0 suffix convention of critical_density0, Ogamma0, and Onu0.

## Validation
- scale_factor0 takes no input and performs no validation. Redshift validation of the scale factor method is unchanged.

## Error handling
- No new exceptions. Errors from the scale factor method propagate unchanged.

## Documentation
- scale_factor0 has a one-line docstring stating it is the scale factor at redshift 0, plus an extended description: a = a0/(1+z); the common convention sets a0 = 1, and writing a0 explicitly avoids ambiguity.
- Add docs/changes/cosmology/14931.api.rst stating that scale_factor0 was added to Cosmology objects, is the scale factor at redshift 0, and is defined to be 1.0. Include no pull-request text such as mentions or pings.

## Performance
- No caching. Each access costs one evaluation of the scale factor method.

## Usability
- The result composes with astropy units: comparisons to 1 and numpy.allclose against the scale factor method at z = 0 must work.

## Compatibility
- The change is additive. No existing public attribute or method is removed or changes behavior, including for subclasses. Edits are limited to the three files in Scope, applied as a patch to the original snapshot.

## Behavioral acceptance criteria
- For every FLRW subclass instance: scale_factor0 is an astropy Quantity with unit astropy.units.one, its value equals 1, and numpy.allclose against the scale factor method at z = 0 holds.
- For each valid redshift in the existing test list (scalars, plain lists, numpy arrays, table columns, redshift-unit Quantities), the scale factor method returns 1/(1+z), compared on numeric values.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. It checks the Quantity type, unit, value 1, and agreement with the scale factor method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking the scale factor method equals 1/(1+z). Convert the parametrized redshift to a plain numeric array before computing 1 divided by (1 plus that array), since plain lists and redshift-unit Quantities fail under direct arithmetic. Do not use the implementation's redshift helper for the expected value; it must be an independent oracle.
- Use the existing cosmology test fixture.
