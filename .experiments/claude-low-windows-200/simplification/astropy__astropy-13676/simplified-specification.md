## Goals
- When the Quantity constructor receives structured data (an array or record-like input whose dtype has named fields), unit is None, and the input carries no unit, the quantity's unit is a StructuredUnit mirroring the dtype. Every leaf uses the class default unit (the class attribute _default_unit, dimensionless for Quantity).
- Structured data then gets a unit whose structure matches the data, instead of one dimensionless unit.

## Scope
- In scope: the default-unit decision in Quantity construction, one private helper building a StructuredUnit from a unit and a record dtype, the changelog fragment, and tests.
- Out of scope: unstructured inputs, explicit units, inputs carrying their own unit, and StructuredUnit's public interface.
- Process items in the original draft (sign-off, checklists, TODO boxes, milestone and label reminders) are not requirements.

## Assumptions
- A subclass's default unit is read from its _default_unit attribute at construction time. Base Quantity uses a dimensionless unit; SpecificTypeQuantity sets it to none.

## Terminology
- Default unit: the value of _default_unit, used when no unit is given.
- Record dtype: a numpy dtype with named fields; any field may itself be a record dtype.
- Record scalar: a single record element (numpy void value) from indexing or iterating a structured array; its dtype is a record dtype.
- Structured unit: a StructuredUnit whose fields correspond to a record dtype's fields.
- Leaf: a non-record field, which maps to one unit inside the structured unit.

## Workflows
1. Keep existing unit and value resolution unchanged. Set a flag to true only when unit is None and the input has no unit attribute, at the point where the class default unit is taken. Otherwise it stays false.
2. Convert the input to an array with the existing dtype, copy, order, and ndmin handling.
3. If the flag is true and the converted array's dtype has named fields, replace both the requested unit and the value unit with a structured unit built from the default unit and that dtype. Base this on the converted array's dtype, not the input's dtype attribute. A list of record scalars therefore takes the same path as a structured array. A list of plain tuples becomes an unstructured array and keeps the default unit.
4. Continue with the existing checks (numeric-kind validation, float defaulting, subclass selection, view, unit assignment) unchanged.

## Data model
- The structured unit has one entry per dtype field, in dtype order, with the same field names.
- A record field produces a nested structured unit of the same depth.
- A non-record field produces a leaf equal to the class default unit.
- Nested levels use the existing StructuredUnit convention: a name paired with a tuple of sub-names, not flattened.

## API contracts
- The Quantity constructor signature and public attributes do not change. With unit None and structured input, quantity.unit becomes a StructuredUnit.
- The private helper takes a unit (regular or already structured) and a record dtype, and returns a StructuredUnit.
- If the unit is already a StructuredUnit, return it unchanged; the caller guarantees it matches the dtype.
- Otherwise build the structure recursively over the dtype's named fields, placing the same unit at every leaf.
- The helper name has a leading underscore and must be importable by that name from the quantity module namespace, because tests import it from there.

## Module architecture
- Define the helper in the structured module, next to StructuredUnit and the existing dtype-name helper. Do not define it in the quantity module.
- The quantity module imports the helper alongside the existing StructuredUnit import and calls it only from the Quantity construction path.
- The structured module must not import the quantity module.
- The default-unit decision stays in the Quantity construction method.

## Implementation constraints
- Do not hardcode a dimensionless unit for leaves; pass the class default unit into the helper.
- Do not add a second recursive dtype walk in the quantity module; the only recursion lives in the helper, which descends only into record fields and places the unit at non-record fields.
- Annotations in the structured module must remain valid below Python 3.10 (defer annotation evaluation).
- Add no third-party or new internal dependencies.

## Dependencies
- The quantity module already depends on the structured module; the new import adds no module edge or cycle.

## Naming
- The helper name describes building a structured unit like a dtype, with a leading underscore.
- The changelog fragment is named by the pull request number, 13676.

## Error handling
- When the class default unit is none (for example SpecificTypeQuantity), structured input with unit None must raise TypeError through the existing unit-construction path. Do not add a silent dimensionless fallback or catch and suppress the error.

## Documentation
- Add exactly one changelog fragment in docs/changes/units/ (relative to the repository root), not docs/changes/, because the changelog README places sub-package changes in that sub-package's directory. Name it 13676 with type api, since public constructor behavior changes.
- The fragment is one full sentence stating that constructing a Quantity from a structured array with unit None now gives a default unit structured like the input data, with double backticks around code. Wrap at about 80 columns like existing fragments.
- The helper has a numpy-style docstring: a summary, Parameters (unit and dtype with meanings), and a Returns section naming StructuredUnit.

## Compatibility
- Explicit units, inputs carrying their own unit, and all unstructured inputs keep current behavior. The unit-None structured change is intentional and recorded in the changelog.

## Behavioral acceptance criteria
- Base Quantity given a nested structured array with unit None: values unchanged; unit is a StructuredUnit matching the dtype structure with dimensionless leaves.
- A list of record scalars with unit None produces a structured unit matching the array form. A list of plain tuples, including nested tuples, is converted by numpy to an unstructured array and keeps the default unit.
- A subclass with a non-dimensionless default unit gives leaves in that unit for structured input with unit None.
- A subclass whose default unit is none raises TypeError for structured input with unit None.
- Explicit units and inputs carrying their own unit behave as before.

## Test requirements
- Each new test lives in a class whose base provides every fixture attribute the test reads. The explicit-unit fixture comes only from the base that also sets up the structured unit fixtures; do not rely on the plain structured-data base alone. The nested-fixture construction test belongs in the existing structured Quantity test class, which already inherits both fixtures.
- Import the helper by name at the top of the test module in the existing import block, following its ordering. Do not import inside a test function.
- Nested-fixture test: construct with unit None; assert values equal the input; assert unit equals the helper's result for the default unit and the fixture dtype; assert unit equals an explicitly written nested structured unit of dimensionless leaves.
- Use the nested naming convention for expected field names; do not assert a flattened tuple where structure is nested.
- List-input tests must build input from record scalars (for example, elements of a structured array built from the fixture dtype) so numpy produces a record dtype. Do not build lists from nested plain tuples of the fixture; numpy raises ValueError before unit logic runs. Assert a structured unit only for list inputs producing a record dtype.
- The None-default test is a regression guard: the unit path already raised TypeError before this change. Keep new-behavior assertions in the nested-fixture test. Assert TypeError for structured input with unit None on a subclass whose default unit is none.
- Cover the subclass default-unit behaviors in the acceptance criteria.
