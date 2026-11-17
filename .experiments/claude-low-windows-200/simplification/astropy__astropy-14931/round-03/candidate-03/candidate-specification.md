# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW cosmology instance.
- The value equals the scale factor method evaluated at z = 0, as a dimensionless astropy Quantity (unit one; a plain float does not qualify).

## Scope
- In scope: the FLRW base module (astropy/cosmology/flrw/base.py), the FLRW tests (astropy/cosmology/flrw/tests/test_base.py), and one changelog fragment (docs/changes/cosmology/14931.api.rst).
- Out of scope: the generic Cosmology base class, registration logic, Parameter definitions, constructor signatures, serialization, and other packages.

## Assumptions
- The FLRW class already defines the scale factor method, a(z) = 1/(1+z), returning a float for scalar input.

## Terminology
- a0 denotes a(0), which equals 1 under the standard convention.

## Workflows
- A user reads scale_factor0 on any FLRW instance, including flat subclasses, and receives a dimensionless Quantity equal to 1.
- Existing scale factor method calls keep their behavior for scalar and array redshifts.

## Data model
- scale_factor0 is derived, not stored. It is not a Parameter, constructor argument, or serialization field. Each access evaluates the scale factor method at z = 0, with no caching.

## API contracts
- scale_factor0: a read-only property taking no arguments, visible on FLRW and all subclasses.
- Return: a scalar astropy Quantity with unit one whose value equals the scale factor method at z = 0. Comparisons to 1 and numpy.allclose against that method must work.
- The scale factor method's name, parameters, and return types are unchanged.

## Module architecture
- In the FLRW base module, add a private mixin class _ScaleFactorMixin immediately before the FLRW class. Move the existing scale factor method into it unchanged in logic, so exactly one definition exists.
- The FLRW base list is the Cosmology base class followed by the mixin. The mixin is not exported from the package.
- scale_factor0 gets its numeric value by calling the scale factor method with z = 0 and wraps it as a dimensionless Quantity. It must not hard-code 1.0, so overrides are respected.

## Implementation constraints
- Add no new imports or packages. Use only existing astropy.units and the existing redshift conversion helper.
- The test module must use only names it already imports, since an added import breaks the import ordering check.
- Do not modify the generic Cosmology class in core.py or the subclass registration hook.

## Naming
- Follow the *0 suffix convention of critical_density0, Ogamma0, and Onu0.

## Validation
- scale_factor0 takes no input and performs no validation. Errors from the scale factor method propagate unchanged.

## Documentation
- The scale_factor0 docstring has a one-line summary stating it is the scale factor at redshift 0. The extended description gives a = a0/(1+z), notes the convention a0 = 1, and says writing a0 explicitly avoids ambiguity.
- The changelog fragment states that scale_factor0 has been added to Cosmology objects, is the scale factor at redshift 0, and is defined to be 1.0. It includes no pull-request mentions or pings.

## Compatibility
- The change is additive. No existing public attribute or method is removed or changes behavior, including for subclasses. Apply edits only to the three files in Scope, as a patch to the original snapshot.

## Behavioral acceptance criteria
- For every FLRW subclass instance, including subclasses overriding the scale factor method: scale_factor0 is an astropy Quantity with unit astropy.units.one, equals 1, and numpy.allclose against the method at z = 0 holds.
- For each valid redshift in the existing test list, the scale factor method returns 1/(1+z) on numeric values.

## Test requirements
- Add test_scale_factor0 after the total density parameter test in the FLRW test class. It checks the Quantity type, unit, value 1, and agreement with the method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking that the method equals 1/(1+z). Convert the redshift to a plain numeric array first, since lists and redshift-unit Quantities fail under direct arithmetic. The expected value must not use the implementation's redshift helper; it is an independent oracle.
- Use the existing cosmology test fixture.
