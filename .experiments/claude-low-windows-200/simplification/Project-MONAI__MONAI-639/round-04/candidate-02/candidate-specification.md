# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies the same callable to each listed key of a mapping.
- Register both in the existing transform packages, using the short-alias convention for the dictionary form, and document both.

## Scope
- Included: Lambda in the vanilla utility module, Lambdad in the dictionary utility module, the LambdaD and LambdaDict aliases, documentation, and tests.
- Excluded: sequences of callables, per-key functions, output validation, and changes to existing classes or aliases.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect the return value.
- A callable that is also iterable is still one callable and is used whole.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, unchanged.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func, which performs the callability check. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input with the built-in dict type, as other dictionary transforms do. For each configured key in order, it replaces that value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is not modified. A missing configured key raises the mapping's lookup error, uncaught.

## Data model
- Lambda holds only the callable.
- Lambdad holds the normalized key tuple from the MapTransform base and one internal Lambda.

## API contracts
- Lambda (vanilla utility module): one required parameter, func, annotated Callable, with no default. Calling it takes one positional argument, img, and returns what func returns for it.
- Lambdad (dictionary utility module): keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Calling it takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. Do not edit the package initializer.

## Module architecture
- Lambda is appended at the end of the vanilla module and subclasses the Transform base.
- Lambdad sits after the ConcatItemsd class and before the alias block, separated by two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in its original order.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, including an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, because Transform defines none.
- Existing lines must not change, except: add Lambda to the existing array import list, add Callable to the existing typing import, and append one new alias line after the ConcatItemsD alias line. Whitespace-only edits count as changes. Keep the single space on each side of each equals sign in the IdentityD alias line, since removing them breaks flake8's E225 rule.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length. Add no third-party packages.

## Naming
- Class names are Lambda and Lambdad.
- LambdaD and LambdaDict use the same chained-assignment form as the other dictionary aliases, with single spaces around the equals sign.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Lambdad validates func only by constructing its internal Lambda.
- Before finishing, compare each modified file with its original. Apart from the edits listed above, every original line must remain unchanged.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError instead, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- Missing input keys and exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section documenting its parameters.
- Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in the Vanilla Transforms section, before SplitChannel, and a Lambdad entry in the Dictionary-based Transforms section, after ConcatItemsd and before Transform Adaptors. Each follows its neighbors' pattern.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- Keys may be given as a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes. Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass the shared NumpyImageTestCase2D base, and carry the repository license header and main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable.
- Pass a keys view only when the mapping's sole entry is the image. A keys view includes every entry, and slicing a non-array entry such as a string raises TypeError, a test defect.
- To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key.
- The slicing callable slices only the spatial axes, leaving the leading batch and channel axes whole. Slicing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result against the same slice computed directly from the test image.
