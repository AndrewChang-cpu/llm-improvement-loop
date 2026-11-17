# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.

## Scope
- In scope: flrw/base.py, flrw/tests/test_base.py, docs/changes/cosmology/14931.api.rst.
- Out of scope: the Cosmology class in core.py, registration logic, Parameters, constructor signatures, serialization, other packages.

## Data model
- scale_factor0 is derived, not stored: it is not a Parameter, constructor argument, or serialization field. Each access evaluates the existing scale factor method, a(z) = 1/(1+z), at z = 0 without caching.
- Dimensionless means unit astropy.units.one. A plain float does not qualify.

## API contracts
- scale_factor0 is a read-only property taking no arguments, visible on FLRW and all subclasses.
- It returns a scalar dimensionless Quantity equal to the scale factor method at z = 0.
- The scale factor method keeps its name, parameters, and return types. Its errors propagate; scale_factor0 performs no validation.

## Module architecture
- In the FLRW base module, move the existing scale factor method unchanged into a new private mixin, _ScaleFactorMixin, placed immediately before the FLRW class, so exactly one definition exists.
- The FLRW base list is the Cosmology base class followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method at z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides apply.

## Implementation constraints
- Add no new imports. Use only existing astropy.units and the existing redshift conversion helper.
- Test modules may use only names they already import, because an added import breaks the import ordering check.
- Do not modify the Cosmology class in core.py or the subclass registration hook.

## Naming
- Follow the *0 suffix convention of critical_density0, Ogamma0, and Onu0. The name a0 denotes a(0), which equals 1.

## Documentation
- The docstring gives a one-line summary (scale factor at redshift 0) and an extended description of a = a0/(1+z), noting a0 = 1.
- The changelog fragment states that scale_factor0 was added to Cosmology objects and is the scale factor at redshift 0, defined to be 1.0. Omit pull-request process text.

## Compatibility
- The change is additive; no existing public attribute or method changes behavior.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. It checks the Quantity type, unit, value 1, and numpy.allclose agreement with the scale factor method at z = 0.
- Add test_scale_factor, parametrized over the existing valid redshift list. It checks the method equals 1/(1+z), converting the redshift to a plain numeric array first and computing the expected value without the redshift helper.
- Use the existing cosmology test fixture.
