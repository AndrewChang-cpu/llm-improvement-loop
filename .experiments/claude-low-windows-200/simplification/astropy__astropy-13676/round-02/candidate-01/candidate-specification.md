## Goals
- When the Quantity constructor receives structured data (an array or record-like input whose dtype has named fields), unit is None, and the input carries no unit, the quantity's unit is a StructuredUnit mirroring the dtype. Every leaf uses the class default unit (the `_default_unit` attribute, dimensionless for Quantity).

## Scope
- In scope: the default-unit decision in Quantity construction, one private helper building a StructuredUnit from a unit and a record dtype, the changelog fragment, and tests.
- Out of scope: unstructured inputs, explicit units, inputs carrying their own unit, and StructuredUnit's public interface.

## Assumptions
- A subclass's default unit is read from `_default_unit` at construction time. Base Quantity uses a dimensionless unit; SpecificTypeQuantity sets it to none.

## Terminology
- Record dtype: a numpy dtype with named fields; any field may itself be a record dtype.
- Record scalar: a single record element (numpy void value) from indexing or iterating a structured array.
- Leaf: a non-record field, which maps to one unit inside the structured unit.

## Workflows
1. Keep existing unit and value resolution unchanged. Set a flag to true only when unit is None and the input has no unit attribute, where the class default unit is taken. Otherwise it stays false.
2. Convert the input to an array using the existing dtype, copy, order, and ndmin handling.
3. If the flag is true and the converted array's dtype has named fields, replace both the requested unit and the value unit with a structured unit built from the default unit and that dtype. Use the converted array's dtype, not the input's dtype attribute, so a list of record scalars behaves like a structured array. A list of plain tuples becomes an unstructured array and keeps the default unit.
4. Continue with the existing checks (numeric-kind validation, float defaulting, subclass selection, view, unit assignment) unchanged.

## Data model
- The structured unit has one entry per dtype field, in dtype order, with the same field names.
- A record field produces a nested structured unit of the same depth. A non-record field produces a leaf equal to the class default unit.
- Nesting uses the existing StructuredUnit convention: a name paired with a tuple of sub-names, not flattened.

## API contracts
- The Quantity constructor signature and public attributes do not change. With unit None and structured input, quantity.unit becomes a StructuredUnit.
- The private helper takes a unit (regular or already structured) and a record dtype, and returns a StructuredUnit.
- If the unit is already a StructuredUnit, return it unchanged; the caller guarantees it matches the dtype.
- Otherwise, build the structure recursively over the dtype's named fields, placing the same unit at every leaf.

## Module architecture
- Define the helper, with a leading underscore, in the structured module next to StructuredUnit and the existing dtype-name helper. Do not define it in the quantity module.
- The quantity module imports the helper by name alongside the existing StructuredUnit import, because tests import it from the quantity module namespace. It calls the helper only from the Quantity construction path. The default-unit decision stays in the Quantity construction method.
- The structured module must not import the quantity module. The new import adds no dependency edge or cycle.

## Implementation constraints
- Do not hardcode a dimensionless unit for leaves; pass the class default unit into the helper.
- Do not add a second recursive dtype walk in the quantity module. The helper alone recurses, descending only into record fields.
- Annotations in the structured module must remain valid below Python 3.10 (defer annotation evaluation).
- Add no third-party or new internal dependencies.

## Naming
- The helper name describes building a structured unit from a dtype, with a leading underscore.
- The changelog fragment is named by the pull request number, 13676.

## Error handling
- When the class default unit is none (for example SpecificTypeQuantity), structured input with unit None must raise TypeError through the existing unit-construction path. Do not add a silent dimensionless fallback or suppress the error.

## Documentation
- Add exactly one changelog fragment in docs/changes/units/ (relative to the repository root), not docs/changes/, since the changelog README places sub-package changes in that sub-package's directory. Name it 13676 with type api, since public constructor behavior changes.
- The fragment is one full sentence stating that constructing a Quantity from a structured array with unit None now gives a default unit structured like the input data, with double backticks around code. Wrap at about 80 columns.
- The helper has a numpy-style docstring: a summary, Parameters (unit and dtype), and a Returns section naming StructuredUnit.

## Compatibility
- Explicit units, inputs carrying their own unit, and all unstructured inputs keep current behavior. The unit-None structured change is intentional and recorded in the changelog.

## Behavioral acceptance criteria
- Base Quantity given a nested structured array with unit None: values unchanged; unit is a StructuredUnit matching the dtype structure with dimensionless leaves.
- A list of record scalars with unit None produces a structured unit matching the array form. A list of plain tuples, including nested tuples, becomes an unstructured array and keeps the default unit.
- A subclass with a non-dimensionless default unit gives leaves in that unit for structured input with unit None.
- A subclass whose default unit is none raises TypeError for structured input with unit None.
- Explicit units and inputs carrying their own unit behave as before.

## Test requirements
- Each new test's class base must provide every fixture attribute it reads. The explicit-unit fixture comes from the base that also sets up the structured unit fixtures, not the plain structured-data base alone. The nested-fixture construction test belongs in the existing structured Quantity test class.
- Import the helper by name in the existing import block at the top of the test module. Do not import inside a test function.
- Nested-fixture test: construct with unit None; assert values equal the input; assert unit equals the helper's result for the default unit and the fixture dtype; assert unit equals an explicitly written nested structured unit of dimensionless leaves. Use nested field names, not a flattened tuple.
- List-input tests build input from record scalars (for example, elements of a structured array built from the fixture dtype) so numpy produces a record dtype. Do not build lists from nested plain tuples of the fixture; numpy raises ValueError before unit logic runs.
- The None-default test is a regression guard, since the unit path already raised TypeError before this change. Keep new-behavior assertions in the nested-fixture test.
- Cover the subclass default-unit behaviors in the acceptance criteria.
