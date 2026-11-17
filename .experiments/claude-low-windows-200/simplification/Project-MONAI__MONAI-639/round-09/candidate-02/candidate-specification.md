# Lambda transforms (vanilla and dictionary)

## Scope
- Excluded: existing class changes, callable sequences, per-key functions, output validation.

## Workflows
- Lambdad validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys fail before func is checked.
- Calling Lambdad makes a shallow copy as a built-in dict, not via copy.copy; for each key, it replaces the value with the internal Lambda result.

## API contracts
- Lambda's constructor takes one required func parameter (Callable, no default) and returns None. Its call takes one positional img argument and returns func's result.
- Lambdad's constructor takes keys (KeysCollection) and a required func (Callable), usable as keywords, and returns None. Its call takes a data mapping and returns a mapping.
- Lambdad applies one callable to every listed key; lists or tuples of callables are unsupported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes stay reachable through existing star exports.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only func.
- Lambdad sits between ConcatItemsd and the alias block, with two blank lines on each side. It subclasses MapTransform and delegates to one internal Lambda.
- LambdaD and LambdaDict are appended to the alias block (IdentityD through ConcatItemsD) as chained assignments.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Never classify func by iterability. Lambdad never iterates or splits func; any callable, even an iterable one, passes whole to Lambda for every key.
- Lambda must not call a base initializer; it has none.
- Add no parameters beyond the API contracts and no third-party packages.
- Change no existing lines except as listed under Validation, including the IdentityD alias line whitespace.
- New and changed lines must pass flake8 and black.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Diff each modified file against its original. In the dictionary module, remove only the typing import; add only the Lambda import, the Callable name, the Lambdad class, and the new alias line.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from MapTransform. Missing input keys and func exceptions propagate unchanged.

## Documentation
- Each class docstring has a summary line, an array-input example using a slicing callable, and an Args section.
- Lambda goes in Vanilla Transforms before SplitChannel; Lambdad goes after ConcatItemsd and before Transform Adaptors.

## Behavioral acceptance criteria
- Lambda returns identical output for an identity callable and the slice for a slicing callable.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view.

## Test requirements
- Put tests in tests/test_lambda.py and tests/test_lambdad.py, subclassing NumpyImageTestCase2D with the license header and main guard. Each covers identity and slicing callables.
- Use a keys view only when the image is the sole entry (slicing a string raises TypeError). Test unlisted preservation with keys naming only the image.
- The slicing callable slices only spatial axes, keeping batch and channel axes whole so results are non-empty; compare with the same slice of the test image.
