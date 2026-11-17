# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.

## Scope
- In scope: flrw/base.py, flrw/tests/test_base.py, docs/changes/cosmology/14931.api.rst.
- Out of scope: core.py's Cosmology class, registration, Parameters, constructors, serialization.

## Assumptions
- FLRW already defines the scale factor method, a(z) = 1/(1+z), returning a float for scalar input.

## Data model
- scale_factor0 is derived, not stored: not a Parameter, constructor argument, or serialized field. Each access evaluates the scale factor method at z = 0, without caching.
- Dimensionless means unit astropy.units.one; a plain float does not qualify.

## API contracts
- scale_factor0 is a read-only property with no arguments, visible on FLRW and all subclasses. It returns a scalar dimensionless Quantity equal to the scale factor method at z = 0.
- The scale factor method keeps its name, parameters, and return types. Its errors propagate; scale_factor0 adds no validation.

## Module architecture
- Move the existing scale factor method unchanged into a new private mixin, _ScaleFactorMixin, placed immediately before the FLRW class, so exactly one definition exists.
- The FLRW base list is the Cosmology base class followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides are respected.

## Implementation constraints
- Add no imports. Use only existing astropy.units and the existing redshift conversion helper.
- Test modules may use only names they already import, since an added import breaks the import ordering check.
- Do not modify the Cosmology class or the subclass registration hook.

## Naming
- Follow the *0 suffix convention (critical_density0, Ogamma0, Onu0). The name a0 denotes a(0), which equals 1.

## Documentation
- Docstring: one-line summary, then an extended description giving a = a0/(1+z) with a0 = 1, noting that writing a0 explicitly avoids ambiguity.
- Changelog fragment: scale_factor0 was added to Cosmology objects, is the scale factor at redshift 0, and is defined as 1.0.

## Compatibility
- Additive change; no existing public attribute or method changes behavior.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. Check the Quantity type, unit, value 1, and numpy.allclose agreement with the scale factor method at z = 0. Its docstring names that method.
- Add test_scale_factor, parametrized over the existing valid redshift list (scalars, lists, arrays, table columns, redshift Quantities). Check the method equals 1/(1+z), computing the expected value without the redshift helper, after converting the redshift to a plain numeric array.
- Use the existing cosmology test fixture.
