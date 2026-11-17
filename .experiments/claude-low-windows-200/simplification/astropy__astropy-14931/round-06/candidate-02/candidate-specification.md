# Specification: scale_factor0 for FLRW
## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW instance.
## Scope
- In scope: flrw/base.py, flrw/tests/test_base.py, docs/changes/cosmology/14931.api.rst.
- Out of scope: core.py's Cosmology class, registration, Parameters, constructors, serialization, other packages.
## Assumptions
- FLRW already defines the scale factor method a(z) = 1/(1+z), returning a float for scalar input.
## Data model
- scale_factor0 is derived, not stored: not a Parameter, constructor argument, or serialized field. Each access evaluates the scale factor method at z = 0, without caching.
- Dimensionless means unit astropy.units.one; a plain float does not qualify.
## API contracts
- scale_factor0 is a read-only property with no arguments, visible on FLRW and all subclasses.
- It returns a scalar dimensionless Quantity equal to the scale factor method at z = 0.
- The scale factor method keeps its name, parameters, and return types; its errors propagate, and scale_factor0 performs no validation.
## Module architecture
- In flrw/base.py, move the existing scale factor method unchanged into a new private mixin, _ScaleFactorMixin, placed immediately before FLRW, so exactly one definition exists.
- FLRW's bases are Cosmology followed by the mixin. The mixin is not exported.
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0, so overrides apply.
## Implementation constraints
- Add no imports; use only existing astropy.units and the existing redshift conversion helper.
- Test modules may use only names they already import, since an added import breaks the import ordering check.
- Do not modify core.py's Cosmology class or the subclass registration hook.
## Naming
- Follow the *0 suffix convention (critical_density0, Ogamma0, Onu0); a0 denotes a(0) = 1.
## Documentation
- Docstring: summary "scale factor at redshift 0"; extended text gives a = a0/(1+z), notes a0 = 1, and says writing a0 explicitly avoids ambiguity.
- Changelog fragment: scale_factor0 added to Cosmology objects, the scale factor at redshift 0, defined as 1.0. No pull-request process text.
## Compatibility
- Additive; no existing public API changes behavior.
## Test requirements
- test_scale_factor0, added to the FLRW test class after the total density parameter test: checks Quantity type, unit, value 1, and numpy.allclose agreement with the scale factor method at z = 0. Use the existing cosmology fixture.
- test_scale_factor, parametrized over the existing valid redshift list (scalars, lists, arrays, table columns, redshift Quantities): checks the method equals 1/(1+z). Convert redshift to a plain numeric array first, since lists and Quantities fail under arithmetic; compute the expected value without the helper.
