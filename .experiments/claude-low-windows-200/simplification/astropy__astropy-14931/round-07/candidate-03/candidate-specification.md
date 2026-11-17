# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.

## Scope
- In scope: flrw/base.py, flrw/tests/test_base.py, docs/changes/cosmology/14931.api.rst.
- Out of scope: the Cosmology class, registration logic, Parameters, constructor signatures, serialization, other packages.

## Data model
- scale_factor0 is derived, not stored, and is not a Parameter, constructor argument, or serialization field. Each access evaluates a(z) = 1/(1+z) at z = 0 through the existing scale factor method, uncached.
- Dimensionless means unit astropy.units.one; a plain float does not qualify.

## API contracts
- scale_factor0 is a read-only property taking no arguments, visible on FLRW and all subclasses.
- It returns a scalar dimensionless Quantity equal to the scale factor method at z = 0.
- The scale factor method keeps its name, parameters, and return types; its errors propagate and scale_factor0 adds no validation.

## Module architecture
- Move the existing scale factor method unchanged into a new private mixin, _ScaleFactorMixin, placed immediately before FLRW so exactly one definition exists.
- The FLRW base list is Cosmology followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method at z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides apply.

## Implementation constraints
- Add no new imports; use existing astropy.units and the existing redshift conversion helper.
- Test modules use only existing imports, since added imports break the import ordering check.
- Do not modify the Cosmology class in core.py or the subclass registration hook.

## Naming
- Follow the *0 suffix convention of critical_density0, Ogamma0, and Onu0; a0 denotes a(0), which equals 1.

## Documentation
- The docstring gives a one-line summary and extends it with a = a0/(1+z), noting a0 = 1.
- The changelog fragment states scale_factor0 was added as the scale factor at redshift 0, equal to 1.0. Omit pull-request text.

## Compatibility
- The change is additive; no existing public behavior changes.

## Test requirements
- Add test_scale_factor0 after the total density parameter test, checking Quantity type, unit, value 1, and numpy.allclose agreement with the scale factor method at z = 0.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking the method equals 1/(1+z) from a plain numeric array, without the redshift helper.
- Use the existing cosmology test fixture.
