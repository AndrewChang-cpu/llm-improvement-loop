# Lambda transforms (vanilla and dictionary)

## Workflows
- Lambdad validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys fail before func is checked.
- Calling Lambdad makes a built-in dict shallow copy, replacing each listed key's value with the internal Lambda's result. The caller's mapping stays unchanged.

## API contracts
- Lambda: constructor takes one required func (annotated Callable, no default), returns None. Call takes one positional argument, img, and returns func's result.
- Lambdad: constructor takes keys (KeysCollection) and func (Callable, required), accepted as keywords, returns None. Call takes the data mapping and returns a mapping.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Existing top-level star exports expose both classes; the package initializer is unchanged.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits between ConcatItemsd and the alias block, separated by two blank lines. It subclasses MapTransform and delegates to one internal Lambda.
- LambdaD and LambdaDict are appended to the end of the alias block in chained-assignment form.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Never classify func by iterability. Lambdad never iterates or splits func; any callable, even an iterable one, passes whole to Lambda. Lists or tuples of callables are unsupported.
- Lambda must not call the base initializer, which does not exist.
- Add no parameters beyond the API contracts and no third-party packages.
- Change no existing lines except those under Validation, including the IdentityD alias line whitespace.
- New and changed lines must pass flake8 and black.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Diff each modified file against its original. The dictionary module may only remove the typing import and add the Lambda import, Callable name, Lambdad class, and new alias line.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from MapTransform. Missing input keys and func exceptions propagate unchanged.

## Documentation
- Each class docstring has a summary line, an array-input example with a slicing callable, and an Args section.
- Lambda goes before SplitChannel; Lambdad goes after ConcatItemsd and before Transform Adaptors.

## Behavioral acceptance criteria
- Lambda returns the same value for an identity callable and the slice for a slicing callable.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the license header and main guard. Each covers an identity and a slicing callable.
- Use a keys view only when the image is the sole entry, since slicing a string entry raises TypeError. Keys naming only the image test unlisted-entry preservation.
- The slicing callable slices only spatial axes, so results are non-empty. Compare results with the same slice of the test image.
