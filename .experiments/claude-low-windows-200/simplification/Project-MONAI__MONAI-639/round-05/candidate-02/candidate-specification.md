# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform applying one caller-supplied callable to its input.
- Provide a dictionary transform applying that callable to each listed key, with the short-alias convention and a reference page entry.

## Scope
- Included: Lambda in the vanilla utility transforms module; Lambdad in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation; tests for both classes.
- Excluded: changes to existing classes or aliases; sequences of callables; per-key functions; output validation.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect the return value. A callable that is also iterable is still one callable, used whole.

## Workflows
- Lambda construction checks callability, then stores func. Calling a Lambda returns func applied to the input, unchanged.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func, which performs the callability check. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad shallow-copies the input into a built-in dict (not copy.copy). For each configured key in order, it replaces that value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is unmodified. A missing key raises the mapping's lookup error, uncaught. Keys may be a dictionary keys view.

## API contracts
- Lambda's constructor takes one required parameter, func, annotated Callable, with no default. Its call takes one positional argument, img, and returns func's result for it.
- Lambdad lives in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None. Lambdad applies one callable to every listed key; a list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through existing star exports; the package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses the Transform base, and holds only the callable.
- Lambdad sits after the ConcatItemsd class and before the alias block, separated by two blank lines on each side. It subclasses MapTransform, holds the normalized key tuple and one internal Lambda, and delegates to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in original order. LambdaD and LambdaDict follow the same chained-assignment form, appended at the end with single spaces around the equals sign.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, including an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, because Transform defines none.
- Add no parameters beyond the API contracts and no new third-party packages.
- Existing lines must not change, except the two import edits and the appended alias line. Whitespace-only edits count as changes. Keep single spaces around equals signs on the IdentityD line (flake8 E225).
- New and changed lines must pass flake8 under the repository configuration and black at the configured line length.

## Validation and error handling
- Lambda asserts that func is callable, with the message "func must be callable". A non-callable func raises AssertionError at construction for both classes; do not raise TypeError or ValueError, and do not wrap the assertion.
- Lambdad validates func only by constructing its internal Lambda. Empty or non-hashable keys raise ValueError from the MapTransform base. Missing input keys and exceptions raised by func propagate unchanged.
- Before finishing, compare each modified file with its original. In the dictionary module, only the typing import line may disappear. Added lines are limited to the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must appear unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func. Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in the Vanilla Transforms section before SplitChannel, and a Lambdad entry in the Dictionary-based Transforms section after ConcatItemsd and before Transform Adaptors, following neighbors' heading, underline, and autoclass pattern.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the repository license header and standard main guard.
- Lambda and Lambdad tests each cover an identity callable (output equals input) and a slicing callable (output equals the same slice computed from the test image).
- The slicing callable slices only spatial axes, keeping batch and channel axes whole, so the result is non-empty. Slicing the size-1 batch axis yields an empty array, which is unacceptable.
- Pass a keys view only when the image is the mapping's sole entry; otherwise a non-array entry such as a string raises TypeError, a test defect.
- To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key.
