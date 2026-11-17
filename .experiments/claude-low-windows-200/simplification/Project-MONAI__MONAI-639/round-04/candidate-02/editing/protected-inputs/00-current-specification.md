# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies that same callable to each listed key of a mapping.
- Register both in the existing transform packages, using the short-alias convention for the dictionary form, and document both on the transforms reference page.

## Scope
- Included: Lambda in the vanilla utility transforms module; Lambdad in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation; tests for both classes.
- Excluded: changes to existing classes or aliases; sequences of callables; per-key functions; output validation.
- The change is purely additive. No existing class, function, signature, or alias changes behavior.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect the return value.
- A callable that is also iterable is still one callable and is used whole.

## Terminology
- Vanilla transform: operates on a single input value rather than a mapping.
- Dictionary transform: a MapTransform that touches only its configured keys.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, unchanged: no copy and no type conversion.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func, which performs the callability check. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input mapping using the built-in dict type, as the other dictionary transforms do; copy.copy is not used. For each configured key in order, it replaces that key's value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is not modified. A missing configured key raises the mapping's lookup error, uncaught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the normalized key tuple from the MapTransform base and one internal Lambda, and no other state.

## API contracts
- Lambda is in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated Callable, with no default. Its call takes one positional argument named img and returns what func returns for it.
- Lambdad is in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla module and subclasses the existing Transform base.
- Lambdad sits after the ConcatItemsd class and before the alias block, separated by two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in its original order.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Any callable, including an iterable one, is passed whole to Lambda for every key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Do not add parameters beyond those in the API contracts.
- Existing lines must not change. The only edits to existing dictionary-module lines are adding Lambda to the existing array import list and adding Callable to the existing typing import. The only other change is appending one new alias line after the ConcatItemsD alias line.
- Whitespace-only edits count as changes. The IdentityD alias line keeps the single space on each side of each equals sign; removing them breaks flake8's E225 rule.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length. No new third-party packages are needed.

## Naming
- Class names are Lambda and Lambdad.
- LambdaD and LambdaDict use the same chained-assignment form as the other dictionary aliases, appended at the end of the alias block with single spaces around the equals sign.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Lambdad validates func only by constructing its internal Lambda.
- Before finishing, compare each modified file with its original. In the dictionary module, the only original line that may disappear is the typing import line. The only added lines are the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must appear unchanged.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError for this, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- Missing input keys and exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in the Vanilla Transforms section, before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section, after ConcatItemsd and before the Transform Adaptors heading. Each follows the heading-and-underline and autoclass pattern of its neighbors.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- Keys may be given as a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes. Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass the shared NumpyImageTestCase2D base, and carry the repository license header and standard main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable.
- Pass a keys view only when the mapping's sole entry is the image. A keys view includes every entry, and a slicing callable on a non-array entry such as a string raises TypeError, a test defect.
- To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key.
- The slicing callable slices only the spatial axes, leaving the leading batch and channel axes whole, so the result is non-empty. Slicing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result against the same slice computed directly from the test image.
