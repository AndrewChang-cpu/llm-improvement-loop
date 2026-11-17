# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW cosmology instance.
- The value must equal the scale factor method evaluated at z = 0, returned as a dimensionless astropy Quantity.

## Scope
- In scope: the FLRW base module (astropy/cosmology/flrw/base.py), the FLRW tests (astropy/cosmology/flrw/tests/test_base.py), and one new changelog fragment (docs/changes/cosmology/14931.api.rst).
- Out of scope: the generic Cosmology base class and registration logic, Parameter definitions, constructor signatures, serialization, and other packages.

## Assumptions
- The FLRW class already defines the scale factor method, a(z) = 1/(1+z), which returns a float for scalar input.
- astropy.units is already imported in the FLRW base module.

## Terminology
- a0 denotes a(0), which equals 1 under the standard convention.
- Dimensionless Quantity: an astropy Quantity with unit astropy.units.one. A plain float does not qualify.

## Workflows
- A user reads scale_factor0 on any FLRW instance, including flat subclasses, with no arguments and receives a dimensionless Quantity equal to 1.
- Existing scale factor method calls keep their current behavior for scalar and array redshifts.

## Data model
- scale_factor0 is derived, not stored. It is not a Parameter, constructor argument, or serialization field. Each access evaluates the scale factor method at z = 0, with no caching.

## API contracts
- Name: scale_factor0, a read-only property taking no arguments, visible on FLRW and all subclasses.
- Return: a scalar astropy Quantity with unit one, whose value equals the scale factor method at z = 0. Comparisons to 1 and numpy.allclose against that method must work.
- The scale factor method's name, parameters, and return types are unchanged.

## Module architecture
- In the FLRW base module, add a private mixin class named _ScaleFactorMixin immediately before the FLRW class. Move the existing scale factor method into it unchanged in logic, so exactly one definition exists.
- The mixin contains scale_factor0 and the scale factor method. The FLRW base list is the Cosmology base class followed by the mixin.
- scale_factor0 gets its numeric value by calling the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. It must not hard-code 1.0 or any other constant, so overrides are respected.
- The mixin stays private and is not exported from the package.

## Implementation constraints
- Add no new imports or packages. Use only existing astropy.units and the existing redshift conversion helper.
- The test module must use only names it already imports, since an added import breaks the repository's import ordering check.
- Do not modify the generic Cosmology class in core.py or the subclass registration hook.

## Naming
- scale_factor0 follows the *0 suffix convention of critical_density0, Ogamma0, and Onu0.

## Validation and errors
- scale_factor0 takes no input and performs no validation. Errors from the scale factor method propagate unchanged, and no new exceptions are added.

## Documentation
- scale_factor0 has a docstring with a one-line summary stating it is the scale factor at redshift 0. The extended description gives a = a0/(1+z), notes the common convention a0 = 1, and says writing a0 explicitly avoids ambiguity. Match the style of neighboring properties.
- Add docs/changes/cosmology/14931.api.rst stating that the scale_factor0 property has been added to Cosmology objects, that it is the scale factor at redshift 0, and that it is defined to be 1.0. Include no pull-request process text such as mentions or pings.

## Compatibility
- The change is additive. No existing public attribute or method is removed or changes behavior, including for FLRW subclasses. Edits are limited to the three files in Scope, applied as a patch to the original snapshot.

## Acceptance criteria
- For every FLRW subclass instance, including subclasses that override the scale factor method: scale_factor0 is an astropy Quantity with unit astropy.units.one, its value equals 1, and numpy.allclose against the scale factor method at z = 0 holds.
- For each valid redshift in the existing test list, including scalars, plain lists, numpy arrays, table columns, and redshift-unit Quantities, the scale factor method returns 1/(1+z) on numeric values.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. It checks the Quantity type, the unit, the value 1, and agreement with the scale factor method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking that the scale factor method equals 1/(1+z). First convert the parametrized redshift to a plain numeric array, then compute 1 divided by (1 plus that array), since plain lists and redshift-unit Quantities fail under direct arithmetic. Do not use the implementation's redshift helper for the expected value; it must be an independent oracle.
- Use the existing cosmology test fixture.
