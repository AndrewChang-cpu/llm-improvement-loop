# Lambda transforms (vanilla and dictionary)

## Scope
- Included: Lambda, Lambdad, the LambdaD and LambdaDict aliases, documentation, and tests.
- Excluded: changing existing classes, callable sequences, per-key functions, output validation.
- func receives the whole input for Lambda, or one item for Lambdad, and returns the transformed value.

## Workflows
- Lambda construction checks callability and stores func. Calling it returns func applied to the input.
- Lambdad construction validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys fail before func is checked.
- Calling a Lambdad makes a shallow copy with the built-in dict type, not copy.copy, then replaces each listed key's value, in order, with the internal Lambda's result.

## API contracts
- Lambda takes one required func parameter, annotated Callable with no default. Its call takes one positional argument, img, and returns func's result.
- Lambdad takes keys (KeysCollection) and func (Callable, required), usable as keyword arguments. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. Lists or tuples of callables are unsupported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level package through existing star exports, which stay unchanged.

## Module architecture
- Lambda is appended to the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits between ConcatItemsd and the alias block, separated by two blank lines. It subclasses MapTransform and delegates to one internal Lambda.
- LambdaD and LambdaDict extend the contiguous alias block in chained-assignment form.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Never classify func by iterability. Lambdad never iterates or splits func; any callable goes whole to Lambda for every key.
- Lambda must not call the base initializer, which does not exist.
- Add no parameters beyond the API contracts and no third-party packages.
- Change no existing lines except those listed under Validation, including the IdentityD alias line whitespace.
- New and changed lines must pass flake8 and black.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only through its internal Lambda.
- Diff each modified file against its original. In the dictionary module, only the typing import line may disappear; the Lambda import, Callable name, Lambdad class, and new alias line may be added.

## Error handling
- A non-callable func raises AssertionError at construction for both classes, unwrapped and never as TypeError or ValueError.
- Empty or non-hashable keys raise ValueError from MapTransform. Missing keys and func exceptions propagate unchanged.

## Documentation
- Each class docstring has a summary, an array-input example with a slicing callable, and an Args section.
- The reference page gets Lambda in Vanilla Transforms before SplitChannel, and Lambdad after ConcatItemsd.

## Acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view. An iterable callable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and include the license header and main guard.
- Each file covers an identity callable and a slicing callable.
- Use a keys view only when the image is the sole entry, since slicing a string entry raises TypeError. Test unlisted-entry preservation with keys naming only the image.
- The slicing callable slices only spatial axes, so results are non-empty. Compare each result with the same slice of the test image.
