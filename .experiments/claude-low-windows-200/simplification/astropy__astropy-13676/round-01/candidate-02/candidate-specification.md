## Goals
- When the Quantity constructor receives structured input (an array or record-like input whose dtype has named fields), unit is None, and the input carries no unit, the quantity's unit is a StructuredUnit mirroring the dtype. Every leaf uses the class default unit (class attribute _default_unit, dimensionless for Quantity).
- Structured data thereby gets a unit matching its structure rather than one dimensionless unit.

## Scope
- In scope: the default-unit decision in Quantity construction; one private helper building a StructuredUnit from a unit and a record dtype; the changelog fragment; tests.
- Out of scope: unstructured inputs, explicitly supplied units, inputs carrying their own unit, and StructuredUnit's public interface.
- Process items from the original draft (sign-off, checklists, TODO boxes, milestone and label reminders) are not requirements.

## Assumptions
- A subclass's default unit is read from its _default_unit at construction time. Base Quantity uses dimensionless; SpecificTypeQuantity sets none.

## Terminology
- Default unit: the value of _default_unit used when no unit is given.
- Record dtype: a numpy dtype with named fields; fields may be nested record dtypes.
- Record scalar: a single element of a structured array (numpy void), whose dtype is a record dtype.
- Structured unit: a StructuredUnit whose fields correspond to a record dtype's fields.
- Leaf: a non-record field, which maps to one unit.

## Workflows
1. Keep existing unit and value resolution unchanged. Set a flag true only when unit is None and the input has no unit attribute, at the point where the class default unit is taken; otherwise false.
2. Convert the input to an array using existing dtype, copy, order, and ndmin handling.
3. If the flag is true and the converted array's dtype has named fields, replace the requested unit and value unit with a structured unit built from the default unit and that dtype. Decide from the converted array's dtype, not the input's dtype attribute. A list of record scalars therefore takes this path; a list of plain tuples becomes an unstructured array and keeps the default unit.
4. Continue existing checks (numeric-kind validation, float defaulting, subclass selection, view, unit assignment) unchanged.

## Data model
- The structured unit has one entry per dtype field, in dtype order, with the same field names.
- A record field produces a nested structured unit of the same depth.
- A non-record field produces a leaf equal to the default unit.
- Nested names follow the existing StructuredUnit convention: a name paired with a tuple of sub-names, not flattened.

## API contracts
- Quantity constructor signature and public attributes are unchanged. With unit None and structured input, quantity.unit becomes a StructuredUnit.
- The private helper takes a unit (regular or already structured) and a record dtype, and returns a StructuredUnit.
- If the unit is already a StructuredUnit, return it unchanged; the caller guarantees it matches the dtype.
- Otherwise build recursively over the dtype's named fields, placing the same unit at every leaf.
- The helper's name has a leading underscore and must be importable by that name from the quantity module namespace, since tests import it there.

## Module architecture
- Define the helper in the structured module, next to StructuredUnit and the existing dtype-name helper, not in the quantity module.
- The quantity module imports it alongside the existing StructuredUnit import and calls it only from the Quantity construction path.
- The structured module must not import the quantity module.
- The default-unit decision stays in the Quantity construction method.

## Implementation constraints
- Do not hardcode a dimensionless unit for leaves; pass the class default unit into the helper.
- No second recursive dtype walk in the quantity module; the only dtype recursion lives in the helper.
- Recursion descends only into record fields and places units at non-record fields.
- Annotations in the structured module must remain valid below Python 3.10 (defer annotation evaluation).
- Add no third-party or new internal dependencies.

## Dependencies
- The quantity module already imports the structured module; the new import adds a name to that edge and creates no new module edge or cycle.

## Naming
- The helper name describes building a structured unit from a dtype, with a leading underscore.
- The changelog fragment is named by PR number 13676.

## Error handling
- When the default unit is none (for example SpecificTypeQuantity), structured input with unit None must raise TypeError through the existing unit-construction path. Do not add a silent dimensionless fallback or catch and suppress the error.

## Documentation
- Add exactly one changelog fragment in docs/changes/units/ (the units sub-package directory, not top-level docs/changes/), named by PR 13676 with type api, since the constructor's public behavior changes.
- Its content is one full sentence stating that constructing a Quantity from a structured array with unit None now gives a default unit structured like the input data, using double backticks for code. Wrap at about 80 columns like existing fragments.
- The helper has a numpy-style docstring: summary, Parameters (unit and dtype), and Returns naming the StructuredUnit.

## Compatibility
- Explicit units, inputs with their own unit, and all unstructured inputs keep current behavior. The unit-None structured change is intentional and recorded in the changelog.

## Behavioral acceptance criteria
- Base Quantity given a nested structured array with unit None: values unchanged; unit is a StructuredUnit matching the dtype structure with dimensionless leaves.
- A list of record scalars with unit None produces a structured unit matching the array form. A list of plain (including nested) tuples becomes an unstructured array and keeps the default unit.
- A subclass with a non-dimensionless default unit gives structured input leaves in that unit.
- A subclass with default unit none raises TypeError for structured input with unit None.
- Explicit units and inputs with their own unit behave as before.

## Test requirements
- Each new test's class base must provide every fixture attribute the test reads. The explicit-unit fixture comes only from the base that also sets up the structured unit fixtures; do not rely on the plain structured-data base alone.
- Put the nested-fixture construction test in the existing structured Quantity test class, which already inherits both the nested data fixture and the explicit structured unit fixtures.
- Import the helper by name in the top-level import block, following module ordering; never inside a test function.
- Nested construction test: construct from the nested fixture with unit None; assert values equal the input; assert unit equals the helper's result for the default unit and fixture dtype; assert unit equals an explicitly written nested structured unit of dimensionless leaves.
- Use the nested naming convention for expected field names; do not assert flattened tuples for nested structure.
- List-input tests must build input from record scalars (for example, elements of a structured array from the fixture dtype) so numpy yields a record dtype. Do not build lists from nested plain tuples: numpy raises ValueError before unit logic. Assert a structured unit only for list inputs producing a record dtype.
- The None-default TypeError test is a regression guard (the path already raised before the change); keep new-behavior assertions in the nested-fixture test.
- Add coverage for the subclass default-unit behaviors in the acceptance criteria.
