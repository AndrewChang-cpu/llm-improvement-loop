# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies the same callable to each listed key of a mapping.
- Register both in the existing transform packages, with the repository's short-alias convention for the dictionary form, and document both on the transforms reference page.

## Scope
- Included: the Lambda class in the vanilla utility transforms module; the Lambdad class and its aliases in the dictionary utility transforms module; documentation entries; tests for both classes.
- Excluded: changes to existing transform classes or aliases; sequences of callables; per-key functions; output shape or type validation.

## Assumptions
- func receives the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect or constrain the return value.
- A callable that is also iterable is still one callable and is used whole.

## Terminology
- Vanilla transform: a transform operating on a single input value rather than a mapping.
- Dictionary transform: a MapTransform operating on a mapping and touching only its configured keys.
- Keys: a KeysCollection as accepted by the existing MapTransform base.
- Callable: a value for which the built-in callability check returns true.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, unchanged: no copy and no type conversion.
- Lambdad construction validates keys first through the MapTransform base, then builds one internal Lambda from func, which performs the callability check.
- Calling a Lambdad makes a shallow copy of the input using the built-in dict type, the same plain-dictionary construction the other dictionary transforms use. The copy module is not used. For each configured key in order, it replaces that key's value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is not modified. A configured key missing from the input raises the mapping's lookup error, uncaught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the normalized key tuple from the MapTransform base and one internal Lambda wrapping the callable. No other state.

## API contracts
- Lambda is in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated Callable, with no default. Its call takes one positional argument named img and returns what func returns for it.
- Lambdad is in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- func on Lambdad is one callable applied to every listed key. A list or tuple of callables is not supported.
- The aliases LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla utility transforms module and subclasses the existing Transform base.
- Lambdad is inserted in the dictionary utility transforms module after the ConcatItemsd class and before the alias block, with two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda.
- The alias block (IdentityD through ConcatItemsD) stays contiguous and in original order. No alias line is moved, split, or interleaved with the new class.
- The dictionary module imports Lambda from the vanilla module, matching the existing import direction. The vanilla module must not import from the dictionary module.
- The wrapper adds only key iteration and copying. All callable handling lives in Lambda.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Any callable, including an iterable one, is passed whole to Lambda for every key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Add no parameters beyond those in the API contracts.
- Existing lines must not change. In the dictionary module, the only edits are adding Lambda to the existing array import list, adding Callable to the existing typing import, and appending one alias line after the ConcatItemsD alias line.
- Whitespace-only edits count as changes. The IdentityD alias line keeps the single space on each side of each equals sign; removing them breaks flake8 rule E225. Do not reformat the alias block to look uniform.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length.

## Dependencies
- The only new import is the Callable name from the standard typing module, added to the existing typing import in the dictionary module. The vanilla module already has Callable.

## Naming
- Classes: Lambda and Lambdad.
- Aliases: LambdaD and LambdaDict, assigned to Lambdad in the same chained-assignment form as the other dictionary aliases, appended at the end of the alias block with single spaces around the equals sign like their neighbors.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Lambdad adds no validation of its own. It validates keys through the MapTransform base, then validates func by constructing its internal Lambda.
- Before finishing, compare each modified file with its original. In the dictionary module, the only original line that may disappear is the typing import line. The only added lines are the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must appear unchanged, including spacing.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- A missing key in the input raises the mapping's lookup error unchanged.
- Exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples must be accurate. Use an array input and a slicing callable, and state only shapes or values the code produces. Do not show list-repetition or per-key results.
- The reference page gets a Lambda entry in the Vanilla Transforms section immediately before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section after the ConcatItemsd entry and before the Transform Adaptors heading. Each follows the heading-and-underline and autoclass-with-members-and-special-members pattern of its neighbors.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly the slice that callable returns.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified. Keys may be a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes. Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass the shared NumpyImageTestCase2D base, and carry the repository license header and standard main guard.
- Lambda and Lambdad tests each cover an identity callable and a slicing callable.
- Lambdad tests pass keys as a keys view of a mapping whose only entry is the image. A keys view includes every entry, so the mapping must hold no non-array entry; a slicing callable would raise TypeError on it, which is a test defect.
- To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key, keeping the extra entry outside it.
- The slicing callable slices only spatial axes, leaving leading batch and channel axes whole (for example, a leading range on the first spatial axis and a reversed-stride range on the last), so the result is non-empty. Slicing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result against the same slice computed directly from the test image.
- Do not add tests asserting per-key list or list-repetition behavior.
