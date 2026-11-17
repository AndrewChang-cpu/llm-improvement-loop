# Lambda transforms (vanilla and dictionary)

## Scope
- Included: Lambda in the vanilla utility transforms module; Lambdad in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation; tests for both classes. Together they apply one caller-supplied callable to the whole input (Lambda) or to each listed key (Lambdad).
- Excluded: changes to existing classes or aliases; sequences of callables; per-key functions; output validation.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value.
- A callable that is also iterable is still one callable and is used whole.

## Workflows
- Lambda construction checks callability, then stores func. Calling a Lambda returns func applied to the input.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input with the built-in dict type, not copy.copy. For each configured key in order, it replaces that value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is unchanged.

## API contracts
- Lambda takes one required parameter func, annotated Callable, with no default. Its call takes one positional argument named img and returns what func returns for it.
- Lambdad is in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports, so the package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses the Transform base, and holds only the callable.
- Lambdad sits after the ConcatItemsd class and before the alias block, with two blank lines on each side. It subclasses MapTransform, holds the normalized key tuple and one internal Lambda, and delegates to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in original order.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, even an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, since Transform defines none.
- No parameters beyond the API contracts. No new third-party packages.
- Existing lines must not change except the edits listed under Validation; whitespace-only edits count as changes. Keep single spaces around equals signs on the IdentityD alias line (flake8 E225).
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length.
- LambdaD and LambdaDict use the same chained-assignment form as the other dictionary aliases, appended at the end of the alias block.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError for this, and do not wrap the assertion. Lambdad validates func only by constructing its internal Lambda.
- Compare each modified file with its original. The dictionary module may lose only its typing import line. Its only added lines are the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must appear unchanged.

## Error handling
- Empty or non-hashable keys raise ValueError from the MapTransform base. Missing input keys and exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in Vanilla Transforms before SplitChannel, and a Lambdad entry in Dictionary-based Transforms after ConcatItemsd and before Transform Adaptors, each matching its neighbors' heading, underline, and autoclass pattern.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original mapping untouched.
- Keys may be given as a dictionary keys view.
- A callable that is also iterable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the repository license header and standard main guard. Each file covers an identity callable and a slicing callable.
- Use a keys view only when the image is the mapping's sole entry; otherwise a slicing callable reaches a non-array entry such as a string and raises TypeError, a test defect.
- To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key.
- The slicing callable slices only spatial axes, leaving leading batch and channel axes whole, so the result is non-empty. Slicing the size-1 batch axis yields an empty array, which is unacceptable. Compare each result against the same slice computed directly from the test image.
