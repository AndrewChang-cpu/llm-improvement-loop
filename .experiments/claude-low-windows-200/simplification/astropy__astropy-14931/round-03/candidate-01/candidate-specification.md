# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.
- Its value equals the scale factor method evaluated at z = 0, as a dimensionless astropy Quantity.

## Scope
- In scope: astropy/cosmology/flrw/base.py, astropy/cosmology/flrw/tests/test_base.py, and the new changelog fragment docs/changes/cosmology/14931.api.rst.
- Out of scope: the generic Cosmology class and registration logic in core.py, Parameter definitions, constructor signatures, serialization, and other packages.

## Assumptions
- The FLRW class already defines the scale factor method, a(z) = 1/(1+z), returning a float for scalar input.
- astropy.units is already imported in the FLRW base module.

## Terminology
- a0 denotes a(0), which equals 1 under the standard convention.
- A dimensionless Quantity has unit astropy.units.one. A plain float does not qualify.

## Workflows
- A user reads scale_factor0 on any FLRW instance, including flat subclasses, with no arguments and receives a dimensionless Quantity equal to 1.

## Data model
- scale_factor0 is derived, not stored. It is not a Parameter, constructor argument, or serialization field. Each access evaluates the scale factor method at z = 0, with no caching.

## API contracts
- scale_factor0 is a read-only property taking no arguments, visible on FLRW and all subclasses.
- It returns a scalar Quantity with unit one whose value equals the scale factor method at z = 0. Comparisons to 1 and numpy.allclose against that method must work.
- The scale factor method's name, parameters, and return types are unchanged.
- scale_factor0 follows the *0 suffix convention of critical_density0, Ogamma0, and Onu0.

## Module architecture
- Add a private mixin class _ScaleFactorMixin immediately before the FLRW class. Move the existing scale factor method into it unchanged in logic, so exactly one definition exists.
- The FLRW bases are the Cosmology base class followed by the mixin. The mixin stays private and is not exported.
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides are respected.

## Implementation constraints
- Add no new imports. Use only existing astropy.units and the existing redshift conversion helper.
- The test module may use only names it already imports, since an added import breaks the import ordering check.
- Do not modify the Cosmology class in core.py or its subclass registration hook.

## Validation and errors
- scale_factor0 takes no input and performs no validation. Errors from the scale factor method propagate unchanged; no new exceptions are added.

## Documentation
- scale_factor0 has a one-line docstring summary stating it is the scale factor at redshift 0. The extended description gives a = a0/(1+z), notes the common convention a0 = 1, and says writing a0 explicitly avoids ambiguity. Match neighboring properties' style.
- Add docs/changes/cosmology/14931.api.rst stating that scale_factor0 has been added to Cosmology objects, is the scale factor at redshift 0, and is defined to be 1.0. Include no pull-request process text.

## Compatibility
- The change is additive. No existing public attribute or method is removed or changes behavior, including for FLRW subclasses. Edits are limited to the three files in Scope.

## Acceptance criteria
- For every FLRW subclass instance, including subclasses overriding the scale factor method: scale_factor0 is an astropy Quantity with unit one, equals 1, and numpy.allclose against the scale factor method at z = 0 holds.
- For each valid redshift in the existing test list, the scale factor method returns 1/(1+z) numerically.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. It checks Quantity type, unit, value 1, and agreement with the scale factor method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking the scale factor method equals 1/(1+z). Convert the parametrized redshift to a plain numeric array first, then compute 1 divided by (1 plus that array); plain lists and redshift-unit Quantities fail under direct arithmetic. Do not use the implementation's redshift helper for the expected value.
- Use the existing cosmology test fixture.
