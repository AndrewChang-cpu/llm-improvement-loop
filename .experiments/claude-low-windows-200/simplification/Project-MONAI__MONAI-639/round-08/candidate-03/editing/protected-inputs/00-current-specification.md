# Lambda transforms (vanilla and dictionary)

## Scope
- Included: both classes in their utility transforms modules, the LambdaD and LambdaDict aliases, documentation, and tests.
- Excluded: changes to existing classes, sequences of callables, per-key functions, output validation.
- func receives the whole input for Lambda, or one item for Lambdad, and returns the transformed value.

## Workflows
- Lambda construction checks callability and stores func; calling it returns func applied to the input.
- Lambdad construction validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy with the built-in dict type, not copy.copy. For each key in order, it replaces the value with the internal Lambda's result, leaving the caller's mapping unchanged.

## API contracts
- Lambda's constructor takes one required func parameter, annotated Callable with no default. Its call takes one positional argument, img, and returns func's result.
- Lambdad's constructor takes keys (KeysCollection) and func (Callable, required), usable as keyword arguments. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key; lists or tuples of callables are unsupported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level package through existing star exports; the package initializer stays unchanged.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits between ConcatItemsd and the alias block, separated by two blank lines on each side. It subclasses MapTransform and delegates to one internal Lambda.
- LambdaD and LambdaDict are appended to the end of the contiguous alias block (IdentityD through ConcatItemsD) in its chained-assignment form, leaving original order intact.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Do not classify func by iterability. Lambdad never iterates func or splits it per key. Pass any callable, even an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, which does not exist.
- Add no parameters beyond the API contracts and no third-party packages.
- Change no existing lines except as listed under Validation, including the IdentityD alias line whitespace.
- New and changed lines must pass flake8 and black.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only through its internal Lambda.
- Diff each modified file against its original. In the dictionary module, only the typing import line may disappear, and only the Lambda import, the Callable name, the Lambdad class, and the new alias line may be added.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from MapTransform. Missing input keys and func exceptions propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example using an array input and a slicing callable, and an Args section.
- The reference page gets a Lambda entry in Vanilla Transforms before SplitChannel, and a Lambdad entry after ConcatItemsd and before Transform Adaptors, following neighbors' pattern.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view. An iterable callable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the license header and main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable.
- Use a keys view only when the image is the sole entry (slicing a string entry raises TypeError). Test unlisted-entry preservation with keys naming only the image.
- The slicing callable slices only spatial axes, keeping batch and channel axes whole, so results are non-empty. Compare each result with the same slice of the test image.
