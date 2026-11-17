## Goals
- When Quantity receives structured data (an array or record-like input whose dtype has named fields), unit is None, and the input has no unit attribute, the quantity's unit is a StructuredUnit mirroring the dtype. Every leaf uses the class default unit (_default_unit; dimensionless for Quantity).
- Structured data thus gets a unit whose structure matches the data, instead of one dimensionless unit.

## Scope
- In scope: the default-unit decision in Quantity construction, one private helper, the changelog fragment, and tests.
- Out of scope: unstructured inputs, explicit units, inputs carrying their own unit, and StructuredUnit's public interface.

## Assumptions
- A subclass's default unit is read from its _default_unit attribute at construction time. Base Quantity uses dimensionless; SpecificTypeQuantity sets it to none.

## Terminology
- Default unit: the value of _default_unit.
- Record dtype: a numpy dtype with named fields; any field may itself be a record dtype.
- Record scalar: a single record element (numpy void value) from indexing or iterating a structured array.
- Leaf: a non-record field, which maps to one unit in the structured unit.

## Workflows
1. Keep existing unit and value resolution unchanged. Set a flag true only when unit is None and the input has no unit attribute, at the point the class default unit is taken.
2. Convert the input to an array with the existing dtype, copy, order, and ndmin handling.
3. If the flag is true and the converted array's dtype has named fields, replace the requested unit and the value unit with a structured unit built from the default unit and that dtype. Use the converted array's dtype, not the input's. A list of record scalars therefore takes this path; a list of plain tuples becomes an unstructured array and keeps the default unit.
4. Continue with the existing checks (numeric-kind validation, float defaulting, subclass selection, view, unit assignment) unchanged.

## Data model
- The structured unit has one entry per dtype field, in dtype order, with the same names.
- A record field produces a nested structured unit; a non-record field produces a leaf equal to the default unit.
- Nesting uses the existing StructuredUnit convention: a name paired with a tuple of sub-names, not flattened.

## API contracts
- The Quantity constructor signature and public attributes do not change. With unit None and structured input, quantity.unit becomes a StructuredUnit.
- The private helper takes a unit and a record dtype and returns a StructuredUnit. If the unit is already a StructuredUnit, it returns it unchanged; the caller guarantees it matches the dtype.
- Otherwise it recurses over the dtype's named fields, descending only into record fields and placing the unit at every non-record field.

## Module architecture
- Define the helper in the structured module, next to StructuredUnit and the existing dtype-name helper, not in the quantity module.
- The quantity module imports it alongside the existing StructuredUnit import and calls it only from the Quantity construction path. The default-unit decision stays in the Quantity construction method.
- The structured module must not import the quantity module. The quantity module already depends on the structured module, so the new import adds no edge or cycle.

## Implementation constraints
- Pass the class default unit into the helper; do not hardcode dimensionless leaves.
- Do not add a second recursive dtype walk in the quantity module.
- Keep annotations in the structured module valid below Python 3.10 (defer annotation evaluation).
- Add no third-party or new internal dependencies.

## Naming
- The helper name has a leading underscore and describes building a structured unit like a dtype. It must be importable from the quantity module namespace, because tests import it from there.
- The changelog fragment is named 13676.

## Error handling
- When the default unit is none (for example SpecificTypeQuantity), structured input with unit None raises TypeError through the existing unit-construction path. Do not add a dimensionless fallback or suppress the error.

## Documentation
- Add exactly one changelog fragment in docs/changes/units/ (relative to the repository root), not docs/changes/, because sub-package changes go in that sub-package's directory. Name it 13676 with type api, since public constructor behavior changes.
- One full sentence: constructing a Quantity from a structured array with unit None now gives a default unit structured like the input data, with double backticks around code. Wrap at about 80 columns.
- The helper has a numpy-style docstring: summary, Parameters (unit and dtype), and a Returns section naming StructuredUnit.

## Compatibility
- Explicit units, inputs carrying their own unit, and unstructured inputs keep current behavior. The unit-None structured change is intentional and recorded in the changelog.

## Behavioral acceptance criteria
- Base Quantity with a nested structured array and unit None: values unchanged; unit is a StructuredUnit matching the dtype with dimensionless leaves.
- A list of record scalars with unit None produces the same structured unit as the array form. A list of plain tuples, including nested tuples, becomes an unstructured array via numpy and keeps the default unit.
- A subclass with a non-dimensionless default unit gives leaves in that unit.
- A subclass whose default unit is none raises TypeError for structured input with unit None.
- Explicit units and inputs carrying their own unit behave as before.

## Test requirements
- Each new test lives in a class whose base provides every fixture attribute it reads. The explicit-unit fixture comes only from the base that also sets up the structured fixtures. The nested-fixture construction test goes in the existing structured Quantity test class, which inherits both.
- Import the helper by name in the existing import block of the test module, following its ordering. Do not import inside a test function.
- Nested-fixture test: construct with unit None; assert values equal the input; assert unit equals the helper's result for the default unit and fixture dtype; assert unit equals an explicitly written nested structured unit of dimensionless leaves. Use nested field names, not flattened tuples.
- List-input tests build input from record scalars (for example, elements of a structured array built from the fixture dtype) so numpy produces a record dtype. Do not build lists from nested plain tuples of the fixture; numpy raises ValueError before unit logic runs. Assert a structured unit only for lists producing a record dtype.
- The None-default test is a regression guard: the unit path already raised TypeError before this change. Keep new-behavior assertions in the nested-fixture test. Assert TypeError for structured input with unit None on a subclass whose default unit is none.
- Cover the subclass default-unit behaviors in the acceptance criteria.
