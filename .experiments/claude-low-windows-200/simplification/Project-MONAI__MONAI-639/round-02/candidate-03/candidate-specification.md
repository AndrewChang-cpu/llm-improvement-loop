# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies the same callable to each listed key of a mapping.
- Register both in the existing transform packages, using the short-alias convention for the dictionary form, and document both on the transforms reference page.

## Scope
- Included: the Lambda class in the vanilla utility transforms module; the Lambdad class in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation entries; tests for both classes.
- Excluded: changes to existing transforms or aliases; sequences of callables; per-key functions; output shape or type validation.

## Assumptions
- func accepts the value it receives (the whole input for Lambda, one item for Lambdad) and returns the transformed value. The framework does not inspect or constrain the return value.
- A callable that is also iterable is still one callable and is used whole.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, unchanged: no copy and no type conversion.
- Lambdad construction validates keys first through the MapTransform base, then builds one internal Lambda from func, which performs the callability check. Empty or non-hashable keys therefore fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input using the built-in dict type, as the module's other dictionary transforms do. The copy module is not used. For each configured key in order, it replaces that key's value in the copy with the internal Lambda's result, then returns the copy. The caller's mapping is not modified. A configured key missing from the input raises the mapping's lookup error, uncaught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the key tuple normalized by the MapTransform base and one internal Lambda wrapping the callable, and no other state.

## API contracts
- Lambda is a transform class in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated Callable, with no default. Its call takes one positional argument named img and returns what func returns for it.
- Lambdad is a dictionary transform class in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Its call takes the data mapping and returns a mapping.
- Both constructors are annotated as returning None.
- func on Lambdad is one callable applied to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla utility transforms module and subclasses the existing Transform base.
- Lambdad is inserted in the dictionary utility transforms module after the ConcatItemsd class and before the alias block, with two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda. The wrapper adds only key iteration and dictionary copying.
- The alias block, from the IdentityD line through the ConcatItemsD line, stays contiguous and in original order. No alias line is moved, split, or interleaved with the new class.
- The dictionary module imports Lambda from the vanilla module, matching the existing import direction. The vanilla module must not import from the dictionary module.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Any callable, including an iterable one, is passed whole to Lambda for every key.
- Lambda must not call the base initializer, because Transform defines none.
- Existing lines must not change. In the dictionary module, the only edits are adding Lambda to the existing array import list, adding Callable to the existing typing import, and appending one alias line after the ConcatItemsD alias line.
- Whitespace-only edits count as changes. The IdentityD alias line keeps the single space on each side of each equals sign it has in the original; removing them breaks flake8 rule E225. Do not reformat the alias block to look uniform.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length.

## Dependencies
- The only new import is the Callable name from the standard typing module, added to the existing typing import in the dictionary module. The vanilla module already imports Callable.
- No new third-party packages.

## Naming
- Class names are Lambda and Lambdad.
- The aliases LambdaD and LambdaDict are assigned to Lambdad in the same chained-assignment form as the other dictionary aliases, appended at the end of the alias block, with single spaces around the equals sign.

## Validation
- Lambda asserts that func is callable, with the message "func must be callable".
- Lambdad validates keys through the MapTransform base, then validates func by constructing its internal Lambda.
- Before finishing, diff each modified file against its original. In the dictionary module, the only removed original line may be the typing import; the only added lines are the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must match exactly, including spacing.

## Error handling
- A non-callable func raises AssertionError at construction for both classes. Do not raise TypeError or ValueError, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- A missing key in the input raises the mapping's lookup error unchanged.
- Exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referring to the MapTransform base) and func.
- Examples must be accurate: use an array input and a slicing callable, and state only shapes or values the code produces. Do not show list-repetition or per-key results.
- The reference documentation page gets a Lambda entry in the Vanilla Transforms section, immediately before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section, after the ConcatItemsd entry and before the Transform Adaptors heading. Each follows the heading-and-underline and autoclass pattern of its neighbors.

## Compatibility
- The change is purely additive. No existing class, function, signature, or alias changes behavior.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value. Lambda with a slicing callable returns exactly the slice that callable returns.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- Keys may be given as a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes. Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass the shared NumpyImageTestCase2D base, and carry the repository license header and standard main guard.
- Each file covers an identity callable and a slicing callable.
- Lambdad tests pass the keys as a keys view of a mapping whose only entry is the image. A keys view includes every entry, so a non-array entry would make a slicing callable fail with a TypeError, a test defect.
- To check that an unlisted entry is preserved, build the Lambdad with an explicit keys collection naming only the image key, keeping the extra entry outside it. Never apply a slicing callable to a non-array entry.
- The slicing callable slices only spatial axes, leaving leading batch and channel axes whole (for example, a leading range on the first spatial axis and a reversed-stride range on the last), so the expected result is non-empty. Slicing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result against the same slice computed directly from the test image.
- Do not add tests asserting per-key list or list-repetition behavior.
