## Goals
- When the Quantity constructor receives a structured value (an array or record-like input whose dtype has named fields), no unit is supplied (unit is None), and the input carries no unit of its own, the resulting quantity's unit is a StructuredUnit that mirrors the value's dtype. Every leaf of that structured unit is the class's default unit (the class attribute named _default_unit, which is dimensionless for Quantity).
- The feature exists so that structured data gets a unit whose structure matches the data, instead of a single dimensionless unit for a structured array.

## Scope
- In scope: the default-unit decision inside Quantity construction; one private helper that builds a StructuredUnit from a unit and a record dtype; the changelog fragment; tests for the new behavior.
- Out of scope: any change to unstructured inputs, to explicitly supplied units, to inputs that carry their own unit, and to StructuredUnit's public interface.
- Process items from the original draft (sign-off, maintainer checklist, TODO boxes, milestone and label reminders) are not requirements and must not be implemented.

## Assumptions
- The default unit for a subclass is read from its _default_unit attribute at construction time. Base Quantity uses a dimensionless unit; SpecificTypeQuantity sets it to none.
- The feature is a prerequisite for later structured-unit work; that context needs no implementation.

## Terminology
- Default unit: the value of the class attribute _default_unit used when no unit is given.
- Record dtype: a numpy dtype with named fields; any field may itself be a record dtype (nested).
- Structured unit: a StructuredUnit whose fields correspond to the fields of a record dtype.
- Leaf: a non-record field of a dtype, which maps to a single unit inside the structured unit.

## Workflows
1. Keep the existing unit and value resolution unchanged. Introduce a flag that is set to true only when unit is None and the input has no unit attribute, at the point where the class default unit is taken. Otherwise the flag stays false.
2. Convert the input to an array using the existing dtype, copy, order, and ndmin handling.
3. After that conversion, if the flag is true and the resulting array's dtype has named fields, replace both the requested unit and the value unit with a structured unit built from the default unit and the array's dtype. Base this decision on the converted array's dtype, not on the input's dtype attribute, so that lists or tuples of record elements are also covered.
4. Continue with the existing checks (numeric-kind validation, float defaulting, subclass selection, view, and unit assignment) unchanged. Non-structured arrays follow the existing path with no new behavior.

## Data model
- The structured unit has one entry per dtype field, in dtype order, with the same field names.
- A field that is itself a record produces a nested structured unit with the same nesting depth.
- A non-record field produces a leaf equal to the class default unit.
- Nested field names follow the existing StructuredUnit convention: a nested level is represented by a name paired with a tuple of its sub-names, not flattened.

## API contracts
- The Quantity constructor signature and public attributes do not change. With unit None and structured input, quantity.unit becomes a StructuredUnit.
- The private helper accepts a unit (a regular unit or an already-structured unit) and a record dtype, and returns a StructuredUnit.
- If the unit passed in is already a StructuredUnit, the helper returns it unchanged; the caller guarantees it matches the dtype.
- Otherwise the helper builds the structure recursively over the dtype's named fields, placing the same unit at every leaf.
- The helper is private (leading underscore) and must be reachable by that name from the quantity module namespace, because the tests import it from there.

## Module architecture
- The helper is defined in the structured module, next to the StructuredUnit class and the existing dtype-name helper. It must not be defined in the quantity module.
- The quantity module imports the helper from the structured module alongside the existing StructuredUnit import and calls it only from the Quantity construction path.
- The structured module must not import the quantity module.
- The decision to use the default unit remains in the Quantity construction method, where the default-unit logic already lives.

## Implementation constraints
- Do not hardcode a dimensionless unit for structured leaves. Pass the class default unit (the value taken from the class attribute) into the helper.
- Do not add a second recursive dtype walk in the quantity module. The only dtype recursion for this feature lives in the helper.
- Recursion descends only into record fields and places the unit at non-record fields.
- Type annotations in the structured module must remain valid on Python versions below 3.10 (defer annotation evaluation).
- Do not add third-party or new internal dependencies.

## Dependencies
- The quantity module already depends on the structured module; the new import adds a name to that existing dependency and creates no new module edge or cycle.

## Naming
- The helper name describes building a structured unit like a dtype, with a leading underscore to mark it private.
- The changelog fragment is named by the pull request number.

## Error handling
- When the class default unit is none (for example SpecificTypeQuantity), constructing a structured quantity with unit None must raise TypeError through the existing unit-construction path (the unit path rejects a none unit). Do not add a silent fallback to a dimensionless unit, and do not catch and suppress this error.

## Documentation
- Add a changelog fragment at the units sub-package changelog directory, named with the pull request number and the type api, because the change alters the public behavior of the constructor. Write one full sentence stating that constructing a Quantity from a structured array with unit None now gives a default unit structured like the input data, using double backticks for code.
- The helper has a numpy-style docstring with a summary, a Parameters section (unit and dtype, with their meaning), and a Returns section naming the StructuredUnit return.

## Compatibility
- Explicit units, inputs that carry their own unit, and all unstructured inputs keep their current behavior.
- The change to unit None with structured input is intentional and must be recorded in the api changelog fragment.

## Behavioral acceptance criteria
- Base Quantity given a structured array with nested record fields and unit None: the values are unchanged, and the unit is a StructuredUnit whose field structure matches the dtype with dimensionless leaves.
- A list or tuple of record elements with unit None produces a structured unit, matching the array form.
- A Quantity subclass whose default unit is a non-dimensionless unit produces leaves in that unit for structured input with unit None.
- A subclass whose default unit is none raises TypeError for structured input with unit None.
- Explicit units and inputs carrying their own unit produce the same results as before.

## Test requirements
- Add a test to the structured-unit test module: construct from the existing nested fixture with unit None; assert the values equal the input; assert the unit equals the structured unit built by the helper from the default unit and the fixture dtype; and assert the unit equals an explicitly written nested structured unit of dimensionless leaves.
- Expected field names for nested fixtures use the nested convention (name paired with sub-name tuple). Do not assert a flattened tuple where the structure is nested.
- Tests may import the helper by name from the quantity module.
- Add coverage for the subclass default-unit and None-default behaviors listed in the acceptance criteria.
