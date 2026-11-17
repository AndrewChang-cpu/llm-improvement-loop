# Lambda transforms (vanilla and dictionary)

## Scope
- Provide a vanilla transform, Lambda, that applies one caller-supplied callable to its input value.
- Provide a dictionary transform, Lambdad, that applies the same callable to each listed key of a mapping.
- Included: both classes; the LambdaD and LambdaDict aliases; documentation entries; tests for both classes.
- Excluded: changes to existing classes or aliases; sequences of callables; per-key functions; output validation. All changes are additive.

## Assumptions
- func accepts the value it receives (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect the return value.
- A callable that is also iterable is still one callable and is used whole.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, unchanged: no copy and no type conversion.
- Lambdad construction first validates keys through the MapTransform base, then builds one internal Lambda from func, which performs the callability check. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input mapping with the built-in dict type, as the other dictionary transforms in the module do; copy.copy is not used. For each configured key in order, it replaces that key's value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is not modified. A missing configured key raises the mapping's lookup error, uncaught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the normalized key tuple from the MapTransform base and one internal Lambda, and no other state.

## API contracts
- Lambda is in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated Callable, with no default. Its call takes one positional argument named img and returns what func returns for it.
- Lambdad is in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- func on Lambdad is one callable applied to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. Do not edit the package initializer.

## Module architecture
- Lambda is appended at the end of the vanilla utility transforms module and subclasses the existing Transform base.
- Lambdad is inserted after the ConcatItemsd class and before the alias block, with two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in its original order. No alias line is moved, split, or interleaved with the new class.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.
- The wrapper adds only key iteration and dictionary copying. All callable handling lives in Lambda.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Any callable, including an iterable one, is passed whole to Lambda for every key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Add no parameters beyond those in the API contracts.
- Existing lines must not change. In the dictionary module, the only edits are adding Lambda to the existing array import list, adding Callable to the existing typing import, and appending one alias line after the ConcatItemsD alias line.
- Whitespace-only edits count as changes. The IdentityD alias line keeps the single space on each side of each equals sign, because removing them breaks flake8's E225 rule.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length.
- The only new import is Callable from the standard typing module. No third-party packages are added.
- LambdaD and LambdaDict are assigned to Lambdad in the same chained-assignment form as the other dictionary aliases, appended at the end of the existing alias block, with single spaces around the equals sign.

## Validation and error handling
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only by constructing its internal Lambda.
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError for this, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base. Missing input keys and exceptions raised by func propagate unchanged.
- Before finishing, compare each modified file with its original. In the dictionary module, the only original line that may disappear is the typing import line. The only added lines are the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must appear unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples use an array input and a slicing callable, and state only shapes or values the code produces. Do not show list-repetition or per-key results.
- The reference page gets a Lambda entry in the Vanilla Transforms section, immediately before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section, after ConcatItemsd and before the Transform Adaptors heading. Each follows the heading-and-underline and autoclass pattern of its neighbors.

## Acceptance criteria
- Lambda with an identity callable returns the same value. Lambda with a slicing callable returns exactly the slice that callable returns.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- Keys may be given as a dictionary keys view. A callable that is also iterable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass the shared NumpyImageTestCase2D base, and carry the repository license header and the standard main guard.
- Each test file covers an identity callable and a slicing callable.
- Pass a keys view only when the mapping's sole entry is the image, because a keys view includes every entry and a slicing callable on a non-array entry such as a string raises TypeError. To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key.
- The slicing callable slices only spatial axes, leaving the leading batch and channel axes whole, so the result is non-empty. Slicing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result against the same slice computed directly from the test image.
- Do not add tests that assert per-key list or list-repetition behavior.
