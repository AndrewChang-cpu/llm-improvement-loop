# Lambda transforms (vanilla and dictionary)

## Scope
- Included: Lambda and Lambdad in their utility transforms modules, the LambdaD and LambdaDict aliases, documentation, and tests.
- Excluded: changes to existing classes or aliases, callable sequences, per-key functions, output validation.

## Workflows
- Lambda construction checks callability, then stores func. Calling Lambda returns func applied to the input.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func, which checks callability. Empty or non-hashable keys fail before func is checked.
- Calling Lambdad makes a shallow copy with the built-in dict type. For each key in order, it replaces the value with the internal Lambda's result and returns the copy, leaving the caller's mapping unchanged.

## API contracts
- Lambda's constructor takes one required func parameter, annotated Callable with no default. Its call takes one positional argument, img, and returns func's result.
- Lambdad's constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. Lists or tuples of callables are not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports, which stay unchanged.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits between ConcatItemsd and the alias block, with two blank lines on each side. It subclasses MapTransform and holds the normalized keys and one internal Lambda.
- LambdaD and LambdaDict are appended after the existing alias block, in the same chained-assignment form.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, even an iterable one, whole to Lambda.
- Lambda must not call the base initializer, which does not exist.
- Add no parameters beyond the API contracts and no third-party packages. Existing lines change only as listed under Validation.
- New and changed lines must pass flake8 and black under the repository configuration.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only through its internal Lambda.
- Diff each modified file against its original. Only the typing import line may disappear. Only the Lambda import, the Callable name, the Lambdad class, and the new alias line may be added. The IdentityD alias line keeps its whitespace.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base. Missing input keys and func's exceptions propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambdad documents keys by referring to the MapTransform base, and func.
- Examples use an array input and a slicing callable, stating only values the code produces.
- The reference page gets a Lambda entry in Vanilla Transforms before SplitChannel, and a Lambdad entry after ConcatItemsd and before Transform Adaptors.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view. An iterable callable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the license header and standard main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable. The slicing callable slices only spatial axes, keeping batch and channel axes whole, so results are non-empty; compare results with the same slice of the test image.
- Use a keys view only when the image is the sole entry; otherwise slicing a string entry raises TypeError. Test unlisted-entry preservation with explicit keys naming only the image.
