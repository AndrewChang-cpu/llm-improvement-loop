# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform applying one caller-supplied callable to its input, and a dictionary transform applying it to each listed key.

## Scope
- Included: Lambda, Lambdad, the LambdaD and LambdaDict aliases, documentation, tests.
- Excluded: changes to existing classes or aliases, sequences of callables, per-key functions, output validation.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value.

## Workflows
- Constructing Lambda checks callability, then stores func. Calling Lambda returns func applied to the input.
- Constructing Lambdad validates keys through the MapTransform base, then builds one internal Lambda from func, which checks callability. Empty or non-hashable keys fail before func is checked.
- Calling Lambdad makes a shallow copy with the built-in dict type, not copy.copy. For each key in order, it replaces that value with the internal Lambda's result and returns the copy. The caller's mapping is unchanged.

## API contracts
- Lambda takes one required parameter, func (annotated Callable, no default). Its call takes one positional argument, img, and returns func's result.
- Lambdad takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad applies one callable to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through existing star exports; the package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla module, subclasses Transform, and holds only the callable.
- Lambdad sits after ConcatItemsd and before the alias block, with two blank lines on each side. It subclasses MapTransform, holds the normalized key tuple and one internal Lambda, and delegates to Lambda.
- The alias block stays contiguous and in original order. LambdaD and LambdaDict are appended at its end in the same chained-assignment form.
- The dictionary module imports Lambda from the vanilla module. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Pass any callable, even an iterable one, whole to Lambda for every key.
- Lambda must not call the base initializer, because Transform defines none.
- Add no parameters beyond the API contracts and no third-party packages.
- Existing lines must not change, except the two import edits and the appended alias line. Whitespace-only edits count as changes.
- New or changed lines must pass flake8 and black at the repository configuration.

## Validation
- Diff each modified file against its original. In the dictionary module, only the typing import line may disappear, and only the Lambda import entry, the Callable name, the Lambdad class, and the new alias line may be added. All other original lines must be unchanged.

## Error handling
- A non-callable func raises AssertionError with the message "func must be callable" at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base. Missing input keys and exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func; Lambdad documents keys (referring to the MapTransform base) and func.
- Examples use an array input and a slicing callable, and state only values the code produces.
- The reference page gets a Lambda entry in the Vanilla Transforms section before SplitChannel, and a Lambdad entry after ConcatItemsd and before Transform Adaptors, matching neighboring entries.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly that slice.
- Lambdad returns a new mapping with listed keys transformed, unlisted keys unchanged, and the original untouched. Keys may be a dictionary keys view. An iterable callable is applied whole, once per listed key.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the repository license header and main guard.
- Each test file covers an identity callable and a slicing callable.
- Use a keys view only when the image is the sole entry; otherwise slicing a string entry raises TypeError. To test preservation of unlisted entries, pass explicit keys naming only the image.
- The slicing callable slices only spatial axes, keeping batch and channel axes whole, so results are non-empty. Compare each result against the same slice computed from the test image.
