# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.

## Scope
- In scope: flrw/base.py, flrw/tests/test_base.py, docs/changes/cosmology/14931.api.rst.
- Out of scope: Cosmology in core.py, registration, Parameters, constructor signatures, serialization, other packages.

## Data model
- scale_factor0 is derived, not stored: not a Parameter, constructor argument, or serialization field. Each access evaluates the existing scale factor method, a(z) = 1/(1+z), at z = 0 without caching.
- Dimensionless means unit astropy.units.one; a plain float does not qualify.

## API contracts
- scale_factor0 is a read-only property taking no arguments, visible on FLRW and all subclasses.
- It returns a scalar dimensionless Quantity equal to the scale factor method at z = 0.
- The scale factor method keeps its name, parameters, and return types. Its errors propagate; scale_factor0 performs no validation.

## Module architecture
- Move the existing scale factor method unchanged into a new private mixin, _ScaleFactorMixin, placed immediately before the FLRW class.
- The FLRW base list is the Cosmology base class followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method at z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides apply.

## Implementation constraints
- Add no new imports; use existing astropy.units and the existing redshift conversion helper.
- Test modules may use only names they already import; an added import breaks the import ordering check.
- Do not modify the Cosmology class in core.py or the subclass registration hook.

## Naming
- Follow the *0 suffix convention of critical_density0, Ogamma0, and Onu0; a0 denotes a(0), which equals 1.

## Documentation
- The docstring gives a one-line summary and an extended description of a = a0/(1+z), noting a0 = 1.
- The changelog fragment says scale_factor0 was added to Cosmology objects as the scale factor at redshift 0, defined as 1.0.

## Compatibility
- The change is additive; no existing public behavior changes.

## Test requirements
- Add test_scale_factor0 after the total density parameter test, checking the Quantity type, unit, value 1, and numpy.allclose agreement with the scale factor method at z = 0.
- Add parametrized test_scale_factor over the existing valid redshifts, checking the method equals 1/(1+z) computed from a plain numeric array without the redshift helper.
- Use the existing cosmology test fixture.
