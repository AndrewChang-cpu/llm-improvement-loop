# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance, equal to the scale factor method at z = 0 as a dimensionless Quantity.

## Scope
- In scope: astropy/cosmology/flrw/base.py, astropy/cosmology/flrw/tests/test_base.py, docs/changes/cosmology/14931.api.rst.
- Out of scope: the Cosmology class in core.py, registration, Parameter definitions, constructor signatures, serialization, other packages.

## Data model
- FLRW already defines the scale factor method, a(z) = 1/(1+z), returning a float for scalar input.
- scale_factor0 is derived, not stored: not a Parameter, constructor argument, or serialization field. Each access evaluates the scale factor method at z = 0, with no caching.
- A dimensionless Quantity has unit astropy.units.one. A plain float does not qualify.

## API contracts
- scale_factor0 is a read-only property taking no arguments, visible on FLRW and all subclasses.
- It returns a scalar dimensionless Quantity equal to the scale factor method at z = 0. Comparison to 1 and numpy.allclose against that method must work.
- The scale factor method's name, parameters, and return types are unchanged. Its errors propagate unchanged. The change is additive.

## Module architecture
- In the FLRW base module, move the existing scale factor method unchanged into a new private mixin class _ScaleFactorMixin, placed immediately before FLRW, so exactly one definition exists.
- The mixin holds scale_factor0 and the scale factor method. The FLRW base list is the Cosmology base class followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. It must not hard-code 1.0, so subclass overrides are respected.

## Implementation constraints
- Add no new imports. Use only existing astropy.units and the existing redshift conversion helper.
- Test modules may use only names they already import, since an added import breaks the import ordering check.
- Do not modify the Cosmology class in core.py or the subclass registration hook.

## Naming
- Follow the *0 suffix convention (critical_density0, Ogamma0, Onu0). The name a0 denotes a(0), which equals 1.

## Documentation
- The docstring summarizes scale_factor0 as the scale factor at redshift 0. The extended description gives a = a0/(1+z), notes a0 = 1, and says writing a0 explicitly avoids ambiguity.
- The changelog fragment states scale_factor0 was added, is the scale factor at redshift 0, and is defined to be 1.0.

## Test requirements
- Add test_scale_factor0 after the total density parameter test. Its docstring names the method under test. It checks the Quantity type, unit, value 1, and numpy.allclose agreement with the scale factor method at z = 0.
- Add test_scale_factor, parametrized over the existing valid redshift list (scalars, lists, arrays, table columns, redshift Quantities). It checks the method equals 1/(1+z). Convert the redshift to a plain numeric array first, since lists and redshift Quantities fail under direct arithmetic. Compute the expected value without the redshift helper.
- Use the existing cosmology test fixture.
