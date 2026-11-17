# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input.
- Provide a dictionary transform that applies the same callable to each listed key of a mapping.
- Register both in the existing transform packages, add the dictionary short alias, and document both on the transforms reference page.

## Scope
- Included: Lambda in the vanilla utility module; Lambdad in the dictionary utility module; the LambdaD and LambdaDict aliases; documentation; tests.
- Excluded: sequences of callables, per-key functions, output validation, and changes to existing classes or aliases.
- The change is purely additive.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect the return value.
- A callable that is also iterable is still one callable and is used whole.

## Workflows
- Lambda construction stores func after the callability check. Calling Lambda returns func applied to the input, unchanged: no copy and no type conversion. Lambda holds only the callable.
- Lambdad construction validates keys through the MapTransform base, then builds one internal Lambda from func, whose callability check runs next. Empty or non-hashable keys therefore fail first. Lambdad holds the normalized key tuple and that internal Lambda, nothing else.
- Calling Lambdad shallow-copies the input mapping with the built-in dict type, as other dictionary transforms do; copy.copy is not used. For each configured key in order, it replaces that value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is not modified. A missing configured key raises the mapping's lookup error, uncaught.

## API contracts
- Lambda is in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated Callable, with no default. Its call takes one positional argument named img and returns what func returns for it.
- Lambdad is in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments. Its call takes the data mapping and returns a mapping. Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla module and subclasses the Transform base.
- Lambdad sits after the ConcatItemsd class and before the alias block, separated by two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in its original order.
- The dictionary module imports Lambda from the vanilla module, never the reverse.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, including an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Add no parameters beyond those in the API contracts.
- Existing lines must not change. The only edits to existing dictionary-module lines are adding Lambda to the array import list and Callable to the typing import. The only other change is appending one alias line after the ConcatItemsD alias line.
- Whitespace-only edits count as changes. The IdentityD alias line keeps single spaces around each equals sign, as flake8's E225 rule requires.
- New or changed lines must pass flake8 under the repository configuration and black at the configured line length.

## Naming
- LambdaD and LambdaDict use the same chained-assignment form as the other dictionary aliases, appended at the end of the alias block.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable". Lambdad validates func only by constructing its internal Lambda.
- Before finishing, compare each modified file with its original. In the dictionary module, only the typing import line may disappear. Added lines are limited to the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. All other original lines must appear unchanged.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- Missing input keys and exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in the Vanilla Transforms section, before SplitChannel, and a Lambdad entry after ConcatItemsd and before the Transform Adaptors heading, each following its neighbors' pattern.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- A non-callable func raises AssertionError at construction for both classes. Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass the shared NumpyImageTestCase2D base, and carry the repository license header and standard main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable.
- Pass a keys view only when the mapping's sole entry is the image. Otherwise a view includes non-array entries, and slicing a string raises TypeError, a test defect.
- To check that an unlisted entry is preserved, build Lambdad with an explicit keys collection naming only the image key.
- The slicing callable slices only spatial axes, leaving leading batch and channel axes whole. Slicing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result with the same slice computed directly from the test image.
