# Lambda transforms (vanilla and dictionary)

## Scope
- Included: both classes, their LambdaD and LambdaDict aliases, docs, and tests.
- Excluded: changes to existing classes, callable sequences, per-key functions, output validation.

## Workflows
- Lambda stores func after checking it is callable; calling it returns func applied to the input.
- Lambdad validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys fail before func is checked.
- Calling a Lambdad makes a shallow copy with the built-in dict type, not copy.copy, then replaces each listed key's value with the internal Lambda's result, leaving the caller's mapping unchanged.

## API contracts
- Lambda's constructor takes one required Callable func, annotated as returning None. Its call takes one positional argument, img, and returns func's result.
- Lambdad's constructor takes keys (KeysCollection) and a required Callable func, usable as keyword arguments, annotated as returning None. Its call takes the data mapping and returns a mapping.
- Lambdad applies one callable to every listed key; lists or tuples of callables are unsupported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are exported through the existing star exports; the package initializer stays unchanged.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits between ConcatItemsd and the alias block, separated by two blank lines on each side. It subclasses MapTransform and delegates to one internal Lambda.
- LambdaD and LambdaDict are appended to the end of the contiguous alias block in chained-assignment form.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Never classify func by iterability. Lambdad never iterates or splits func; pass any callable, even an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, which does not exist.
- Add no parameters beyond the API contracts and no third-party packages.
- Change no existing lines except as listed under Validation, including the IdentityD alias line whitespace.
- New and changed lines must pass flake8 and black.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only through its internal Lambda.
- Diff each modified file against its original. In the dictionary module, only the typing import line may be removed; only the Lambda import, Callable name, Lambdad class, and new alias line may be added.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from MapTransform. Missing input keys and func exceptions propagate unchanged.

## Documentation
- Each class has a docstring with a summary, an array-input slicing example, and an Args section.
- The reference page lists Lambda in Vanilla Transforms before SplitChannel, and Lambdad after ConcatItemsd.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view. An iterable callable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the license header and main guard.
- Each test file covers an identity callable and a slicing callable.
- Use a keys view only when the image is the sole entry, since slicing a string entry raises TypeError. Keys then name only the image, so unlisted-entry preservation is tested.
- The slicing callable slices only spatial axes, keeping batch and channel axes whole, so results are non-empty. Compare each result with the same slice of the test image.
