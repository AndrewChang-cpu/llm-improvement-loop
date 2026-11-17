# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW cosmology instance.

## Scope
- In scope: astropy/cosmology/flrw/base.py, astropy/cosmology/flrw/tests/test_base.py, and docs/changes/cosmology/14931.api.rst.
- Out of scope: the generic Cosmology class in core.py, registration logic, Parameter definitions, constructor signatures, serialization, and other packages.
- Assume the FLRW class already defines the scale factor method a(z) = 1/(1+z), returning a float for scalar input, and that astropy.units is imported in the FLRW base module.

## Terminology
- a0 denotes a(0), which equals 1 under the standard convention.
- Dimensionless Quantity: an astropy Quantity with unit astropy.units.one. A plain float does not qualify.

## Data model
- scale_factor0 is derived, not stored. It is not a Parameter, constructor argument, or serialization field. Each access evaluates the scale factor method at z = 0, with no caching.

## API contracts
- scale_factor0: a read-only property taking no arguments, visible on FLRW and all subclasses.
- Returns a scalar dimensionless Quantity equal to the scale factor method at z = 0. Comparisons to 1 and numpy.allclose against that method must work.
- The scale factor method's name, parameters, and return types are unchanged.

## Module architecture
- Move the existing scale factor method, unchanged, into a new private mixin _ScaleFactorMixin placed immediately before the FLRW class, so exactly one definition exists.
- The mixin holds scale_factor0 and the scale factor method. FLRW's bases are Cosmology followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides are respected.

## Implementation constraints
- Add no new imports or packages. Use only existing astropy.units and the existing redshift conversion helper.
- Test modules may use only names they already import, because an added import breaks the import ordering check.
- Do not modify the Cosmology class in core.py or the subclass registration hook.

## Naming
- Follow the *0 suffix convention of critical_density0, Ogamma0, and Onu0.

## Error handling
- scale_factor0 takes no input and performs no validation. Errors from the scale factor method propagate unchanged.

## Documentation
- One-line docstring summary: the scale factor at redshift 0. Extended description: a = a0/(1+z), noting the convention a0 = 1 and that writing a0 explicitly avoids ambiguity.
- Changelog fragment: scale_factor0 has been added to Cosmology objects, is the scale factor at redshift 0, and is defined to be 1.0. No pull-request process text.

## Compatibility
- Additive change. No existing public attribute or method is removed or changes behavior, including for subclasses.

## Behavioral acceptance criteria
- For every FLRW subclass instance, including those overriding the scale factor method, scale_factor0 is a Quantity with unit one, equals 1, and matches the scale factor method at z = 0 under numpy.allclose.
- For each valid redshift in the existing test list (scalars, lists, arrays, table columns, redshift Quantities), the scale factor method returns 1/(1+z) numerically.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. Check Quantity type, unit, value 1, and agreement with the method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking the method equals 1/(1+z). Convert redshift to a plain numeric array first, since lists and redshift Quantities fail under direct arithmetic. Compute the expected value without the implementation's redshift helper.
- Use the existing cosmology test fixture.
