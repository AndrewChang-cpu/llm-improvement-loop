# Specification: scale_factor0 for FLRW cosmologies

## Goals
- Expose the scale factor at redshift 0 as a read-only, unit-aware property on every FLRW cosmology instance.
- The value is the scale factor method evaluated at z = 0, returned as a dimensionless astropy Quantity, so it always agrees with that method.

## Scope
- In scope: the FLRW base module (astropy/cosmology/flrw/base.py), the FLRW tests (astropy/cosmology/flrw/tests/test_base.py), and one new changelog fragment (docs/changes/cosmology/14931.api.rst).
- Out of scope: the generic Cosmology class and its registration logic, Parameter definitions, constructor signatures, serialization, and other packages.

## Assumptions
- The FLRW class already defines the scale factor method, a(z) = 1/(1+z), returning a float for scalar input. astropy.units is already imported in the FLRW base module.

## Terminology
- a0 denotes a(0), which equals 1 under the standard convention.
- Dimensionless Quantity: an astropy Quantity with unit astropy.units.one. A plain float does not qualify.

## Workflows
- Reading scale_factor0 on any FLRW instance, including flat subclasses, returns a dimensionless Quantity equal to 1.
- Existing scale factor method calls keep their current behavior.

## Data model
- scale_factor0 is derived, not stored. It is not a Parameter, constructor argument, or serialization field. Each access evaluates the scale factor method at z = 0.

## API contracts
- Name: scale_factor0, a read-only property taking no arguments, visible on FLRW and all subclasses.
- Return: a scalar astropy Quantity with unit one whose numeric value equals the scale factor method at z = 0. A bare float is not acceptable.
- The scale factor method's name, parameters, and return types are unchanged.

## Module architecture
- In the FLRW base module, add a private mixin class named _ScaleFactorMixin immediately before the FLRW class. Move the existing scale factor method into it unchanged in logic, so exactly one definition exists.
- The mixin contains scale_factor0 and the scale factor method. The FLRW base list is the Cosmology base class followed by the mixin.
- The mixin is not exported from the package.

## Implementation constraints
- scale_factor0 calls the scale factor method with z = 0 and wraps the result as a dimensionless Quantity. Do not hard-code 1.0 or any other constant, so overrides are respected.
- Add no new imports or packages. The test module uses only names it already imports, because an added import breaks the repository's import ordering check.
- Do not modify the generic Cosmology class in core.py or the subclass registration hook.

## Naming
- The public name scale_factor0 follows the *0 suffix convention of critical_density0, Ogamma0, and Onu0.

## Validation
- scale_factor0 takes no input and performs no validation. Redshift validation of the scale factor method is unchanged.

## Error handling
- No new exceptions. Errors from the scale factor method propagate unchanged.

## Documentation
- scale_factor0 has a docstring with a one-line summary stating it is the scale factor at redshift 0, plus an extended description: a = a0/(1+z); the common convention sets a0 = 1; writing a0 explicitly avoids ambiguity. Match neighboring properties' style.
- Add docs/changes/cosmology/14931.api.rst stating that scale_factor0 has been added to Cosmology objects, that it is the scale factor at redshift 0, and that it is defined to be 1.0. Include no pull-request mentions or pings.

## Performance
- No caching. Each access costs one evaluation of the scale factor method.

## Reliability
- scale_factor0 equals the scale factor method at z = 0 for every FLRW subclass, including subclasses that override that method.
- The return composes with astropy units: comparisons to 1 and numpy.allclose against the scale factor method at z = 0 must work.

## Maintainability
- Keep exactly one definition of the scale factor. scale_factor0 must not duplicate the formula or constant.

## Compatibility
- The change is additive. No existing public attribute or method is removed or changes behavior.

## Operations
- The change applies as a patch to the original snapshot and is limited to the three files in Scope.

## Behavioral acceptance criteria
- For every FLRW subclass instance: scale_factor0 is an astropy Quantity with unit astropy.units.one, its value equals 1, and numpy.allclose against the scale factor method at z = 0 holds.
- For each valid redshift in the existing test list, covering scalars, lists, numpy arrays, table columns, and redshift-unit Quantities, the scale factor method returns 1/(1+z), compared on numeric values.

## Test requirements
- Add test_scale_factor0 to the FLRW test class after the total density parameter test. It checks the Quantity type, the unit, the value 1, and agreement with the scale factor method at z = 0. Its docstring names the method under test.
- Add test_scale_factor, parametrized over the existing valid redshift list, checking the scale factor method equals 1/(1+z). Convert the parametrized redshift to a plain numeric array before computing 1 divided by (1 plus that array), since raw lists and redshift-unit Quantities fail under direct arithmetic. The expected value must not use the implementation's redshift helper; it is an independent oracle.
- Use the existing cosmology test fixture.
