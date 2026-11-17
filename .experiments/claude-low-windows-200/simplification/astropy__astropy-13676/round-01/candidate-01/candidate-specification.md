## Goals
- When the Quantity constructor receives a structured value (an array or record-like input whose dtype has named fields), no unit is supplied (unit is None), and the input carries no unit of its own, the resulting quantity's unit is a StructuredUnit mirroring the value's dtype. Every leaf is the class's default unit (the class attribute _default_unit, dimensionless for Quantity).
- Structured data thus gets a unit whose structure matches the data, instead of one dimensionless unit.

## Scope
- In scope: the default-unit decision inside Quantity construction; one private helper building a StructuredUnit from a unit and a record dtype; the changelog fragment; tests.
- Out of scope: unstructured inputs, explicitly supplied units, inputs carrying their own unit, and StructuredUnit's public interface.
- Process items from the original draft (sign-off, checklists, TODO boxes, milestone and label reminders) are not requirements.

## Assumptions
- The default unit for a subclass is read from its _default_unit attribute at construction time. Base Quantity uses a dimensionless unit; SpecificTypeQuantity sets it to none.
- Later structured-unit work depends on this feature; it needs no implementation here.

## Terminology
- Default unit: the value of _default_unit, used when no unit is given.
- Record dtype: a numpy dtype with named fields; any field may itself be a record dtype (nested).
- Record scalar: a single element of a structured array (a numpy void value), as obtained by indexing or iterating. Its dtype is a record dtype.
- Structured unit: a StructuredUnit whose fields correspond to the fields of a record dtype.
- Leaf: a non-record field, which maps to one unit inside the structured unit.

## Workflows
1. Keep existing unit and value resolution unchanged. Set a flag to true only when unit is None and the input has no unit attribute, at the point where the class default unit is taken. Otherwise the flag stays false.
2. Convert the input to an array using the existing dtype, copy, order, and ndmin handling.
3. If the flag is true and the converted array's dtype has named fields, replace both the requested unit and the value unit with a structured unit built from the default unit and that dtype. Decide on the converted array's dtype, not the input's dtype attribute. A list of record scalars therefore takes this path. A list of plain tuples, including nested tuples, becomes an unstructured array and keeps the default unit.
4. Continue with the existing checks (numeric-kind validation, float defaulting, subclass selection, view, unit assignment) unchanged. Unstructured arrays follow the existing path.

## Data model
- The structured unit has one entry per dtype field, in dtype order, with the same field names.
- A record field produces a nested structured unit, preserving nesting depth.
- A non-record field produces a leaf equal to the class default unit.
- Nested levels follow the existing StructuredUnit convention: a name paired with a tuple of sub-names, not flattened.

## API contracts
- The Quantity constructor signature and public attributes do not change. With unit None and structured input, quantity.unit becomes a StructuredUnit.
- The private helper takes a unit (regular or already structured) and a record dtype, and returns a StructuredUnit.
- If the unit passed in is already a StructuredUnit, the helper returns it unchanged; the caller guarantees it matches the dtype.
- Otherwise the helper builds the structure recursively over the dtype's named fields, placing the same unit at every leaf.
- The helper name has a leading underscore and must be importable by that name from the quantity module namespace, because tests import it from there.

## Module architecture
- Define the helper in the structured module, next to the StructuredUnit class and the existing dtype-name helper. Do not define it in the quantity module.
- The quantity module imports the helper alongside the existing StructuredUnit import and calls it only from the Quantity construction path.
- The structured module must not import the quantity module.
- The default-unit decision stays in the Quantity construction method, where that logic lives.

## Implementation constraints
- Pass the class default unit (from the class attribute) into the helper; do not hardcode a dimensionless unit for leaves.
- Do not add a second recursive dtype walk in the quantity module. The only dtype recursion lives in the helper, which descends only into record fields and places the unit at non-record fields.
- Type annotations in the structured module must remain valid below Python 3.10 (defer annotation evaluation).
- Add no third-party or new internal dependencies.

## Dependencies
- The quantity module already depends on the structured module; the new import adds a name to that edge and creates no new module edge or cycle.

## Naming
- The helper name describes building a structured unit from a dtype, with a leading underscore.
- The changelog fragment is named by the pull request number, 13676.

## Error handling
- When the class default unit is none (for example SpecificTypeQuantity), structured input with unit None must raise TypeError through the existing unit-construction path. Do not add a silent dimensionless fallback or catch and suppress the error.

## Documentation
- Add exactly one changelog fragment in docs/changes/units/ (relative to the repository root), not the top-level docs/changes/, because the changelog README requires sub-package changes in that sub-package's directory. Name it 13676 with type api, since the change alters public constructor behavior.
- Its content is one full sentence stating that constructing a Quantity from a structured array with unit None now gives a default unit structured like the input data, using double backticks for code. Wrap at about 80 columns, like the existing fragments.
- The helper has a numpy-style docstring: a summary, a Parameters section (unit and dtype with meanings), and a Returns section naming the StructuredUnit return.

## Compatibility
- Explicit units, inputs carrying their own unit, and all unstructured inputs keep current behavior.
- The change for unit None with structured input is intentional and recorded in the api changelog fragment.

## Behavioral acceptance criteria
- Base Quantity with a nested structured array and unit None: values unchanged; unit is a StructuredUnit matching the dtype structure with dimensionless leaves.
- A list of record scalars with unit None produces a structured unit matching the array form. A list of plain tuples (including nested) is converted by numpy to an unstructured array and keeps the default unit.
- A subclass whose default unit is non-dimensionless produces leaves in that unit for structured input with unit None.
- A subclass whose default unit is none raises TypeError for structured input with unit None.
- Explicit units and inputs carrying their own unit behave as before.

## Test requirements
- Each new test sits in a class whose base provides every fixture attribute the test reads. The explicit-unit fixture comes only from the base that also sets up the structured unit fixtures; do not rely on the plain structured-data base alone. The nested-fixture construction test belongs in the existing structured Quantity test class, which already inherits both the nested data fixture and the explicit structured unit fixtures.
- Import the helper at the top of the test module, in the existing import block, following its ordering. Do not import inside a test function. Tests may import it by name from the quantity module.
- Nested-fixture test: construct with the nested fixture and unit None; assert values equal the input; assert the unit equals the structured unit built by the helper from the default unit and the fixture dtype; and assert it equals an explicitly written nested structured unit of dimensionless leaves.
- Use the nested naming convention for nested field names; do not assert a flattened tuple where structure is nested.
- List-input tests must build input from record scalars (for example, elements of a structured array built from the fixture dtype) so numpy produces a structured dtype. Do not build list input from nested plain tuples: numpy raises ValueError before unit logic runs. Assert a structured unit only for list inputs that produce a record dtype.
- The None-default test is a regression guard: the unit path already raised TypeError before this change, so keep the new-behavior assertions in the nested-fixture test. Assert TypeError for structured input with unit None on a subclass whose default unit is none.
- Add coverage for the subclass default-unit behaviors in the acceptance criteria.
