# Lambda transforms (vanilla and dictionary)

## Scope
- Excluded: changes to existing classes, callable sequences, per-key functions, output validation.

## Workflows
- Lambdad validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys fail before func is checked.
- Calling Lambdad makes a shallow copy with the built-in dict type, not copy.copy. For each key in order, it replaces the value with the internal Lambda's result, leaving the caller's mapping unchanged.

## API contracts
- Lambda's constructor takes one required func parameter, annotated Callable with no default, and returns None. Its call takes one positional argument, img, and returns func's result.
- Lambdad's constructor takes keys (KeysCollection) and func (Callable, required), usable as keyword arguments, and returns None. Its call takes the data mapping and returns a mapping.
- Lambdad applies one callable to every listed key; lists or tuples of callables are unsupported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes stay reachable through existing top-level star exports; the package initializer is unchanged.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits between ConcatItemsd and the alias block, separated by two blank lines on each side. It subclasses MapTransform and delegates to one internal Lambda.
- LambdaD and LambdaDict are appended to the end of the alias block (IdentityD through ConcatItemsD) in chained-assignment form.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Never classify func by iterability. Lambdad never iterates or splits func; any callable, even an iterable one, passes whole to Lambda for every key.
- Lambda must not call the base initializer, which does not exist.
- Add no parameters beyond the API contracts and no third-party packages.
- Change no existing lines except as listed under Validation, including the IdentityD alias line whitespace.
- New and changed lines must pass flake8 and black.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Diff each modified file against its original. In the dictionary module, only the typing import may be removed; only the Lambda import, the Callable name, the Lambdad class, and the new alias line may be added.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from MapTransform. Missing input keys and func exceptions propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an array-input example using a slicing callable, and an Args section.
- Lambda goes in Vanilla Transforms before SplitChannel; Lambdad goes after ConcatItemsd and before Transform Adaptors.

## Behavioral acceptance criteria
- Lambda returns the same value for an identity callable and the slice for a slicing callable.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the license header and main guard. Each file covers an identity callable and a slicing callable.
- Use a keys view only when the image is the sole entry, since slicing a string entry raises TypeError. Test unlisted-entry preservation with keys naming only the image.
- The slicing callable slices only spatial axes, keeping batch and channel axes whole, so results are non-empty. Compare results with the same slice of the test image.
