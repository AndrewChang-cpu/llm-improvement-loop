# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input.
- Provide a dictionary transform applying that callable to each listed key, with an alias and a reference page entry.

## Scope
- Included: Lambda in the vanilla utility transforms module; Lambdad in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation; tests for both classes.
- Excluded: changes to existing classes or aliases, sequences of callables, per-key functions, output validation.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value.

## Workflows
- Lambda construction checks callability, then stores func. Calling a Lambda returns func applied to the input, unchanged.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func, which checks callability. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input with the built-in dict type, not copy.copy. For each configured key in order, it replaces that key's value with the internal Lambda's result and returns the copy. The caller's mapping is unchanged.

## API contracts
- Lambda's constructor takes one required parameter, func, annotated Callable, with no default. Its call takes one positional argument, img, and returns func's result for it.
- Lambdad's constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports, so the package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses the existing Transform base, and holds only the callable.
- Lambdad sits after ConcatItemsd and before the alias block, with two blank lines on each side. It subclasses MapTransform, holds the normalized key tuple and one internal Lambda, and delegates to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in its original order. LambdaD and LambdaDict are appended at its end in the same chained-assignment form, with single spaces around equals signs.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, including an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Add no parameters beyond the API contracts and no third-party packages.
- Existing lines must not change, except the two import edits and the appended alias line. Whitespace-only edits count as changes, including on the IdentityD alias line.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only by constructing its internal Lambda.
- Before finishing, diff each modified file against its original. In the dictionary module, only the typing import line may disappear. Only the Lambda import entry, the Callable name, the Lambdad class, and the new alias line may be added. Every other original line must be unchanged.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base. Missing input keys and exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in the Vanilla Transforms section before SplitChannel, and a Lambdad entry in the Dictionary-based Transforms section after ConcatItemsd and before Transform Adaptors, matching neighbors' heading and autoclass pattern.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original mapping untouched. Keys may be a dictionary keys view. A callable that is also iterable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the repository license header and standard main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable.
- Use a keys view only when the image is the sole entry; otherwise slicing a string entry raises TypeError, a test defect.
- To test preservation of unlisted entries, pass explicit keys naming only the image.
- The slicing callable slices only spatial axes, keeping leading batch and channel axes whole, so results are non-empty. Compare each result against the same slice computed directly from the test image.
