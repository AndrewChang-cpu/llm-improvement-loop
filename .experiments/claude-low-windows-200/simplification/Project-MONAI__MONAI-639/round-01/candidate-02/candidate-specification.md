# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies the same callable to each listed key of a mapping.
- Register both in the existing transform packages, using the repository's short-alias convention for the dictionary form, and document both on the transforms reference page.

## Scope
- Included: the Lambda class in the vanilla utility transforms module; the Lambdad class in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation entries; tests for both classes.
- Excluded: changes to existing transform classes or aliases; sequences of callables for func; per-key functions; output shape or type validation.

## Assumptions
- func accepts the value it receives (the whole input for Lambda, one item for Lambdad) and returns the transformed value.
- The framework does not inspect or constrain what func returns.
- A callable that is also iterable (for example, a container module) is still one callable and is used whole.

## Terminology
- Vanilla transform: a transform operating on a single input value rather than a mapping.
- Dictionary transform: a MapTransform operating on a mapping and touching only its configured keys.
- Keys: a KeysCollection as accepted by the existing MapTransform base.
- Callable: a value for which the built-in callability check returns true.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, passed through unchanged: no copy, no type conversion.
- Lambdad construction runs in this order: the MapTransform base validates keys first; then one internal Lambda is built from func, which performs the callability check. Empty or non-hashable keys fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input mapping, built with the built-in dict type applied to the input, as the existing dictionary transforms do. The copy-module function is not used. For each configured key in order, the Lambdad replaces that key's value in the copy with the internal Lambda's result for that value, then returns the copy. The caller's mapping is not modified. A configured key missing from the input raises the mapping's own lookup error, uncaught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the normalized key tuple produced by the MapTransform base and exactly one internal Lambda wrapping the callable. It holds no other state.

## API contracts
- Lambda is a transform class in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated with the Callable type, with no default. Its call takes one positional argument named img and returns whatever func returns for it.
- Lambdad is a dictionary transform class in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default). Both parameters must be usable as keyword arguments named keys and func.
- Both constructors are annotated as returning None.
- func on Lambdad is one callable applied to every listed key. A list or tuple of callables is not supported.
- Lambdad's call takes one argument, the data mapping, and returns a mapping.
- The aliases LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla utility transforms module and subclasses the existing Transform base.
- Lambdad is inserted in the dictionary utility transforms module after the ConcatItemsd class and before the alias block, with the module's usual two blank lines on each side. It subclasses MapTransform and delegates per-value work to Lambda.
- The alias block, from the IdentityD line through the ConcatItemsD line, stays contiguous and in its original order. No alias line is moved, split, or interleaved with the new class.
- The dictionary module imports Lambda from the vanilla module, matching the direction of its existing imports. The vanilla module must not import from the dictionary module.
- The wrapper adds only key iteration and dictionary copying. All callable handling lives in Lambda.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Every callable, including an iterable one, is passed whole to Lambda for each key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Add no parameters beyond those listed in the API contracts.
- Existing lines must not change. In the dictionary module, the only permitted edits to existing lines are adding Lambda to the existing array import list and adding Callable to the existing typing import. The only other change is appending one alias line after the existing ConcatItemsD alias line. Every other existing line keeps its exact text, spacing, and position, including the IdentityD alias line.
- Whitespace-only edits count as changes. The IdentityD alias line keeps the single space on each side of each equals sign. Removing those spaces breaks flake8's whitespace-around-operator rule (E225). Do not reformat the alias block to look uniform.
- The Lambdad shallow copy uses the same plain-dictionary construction as the other dictionary transforms, not the copy module, even though that module is already imported.
- Every new or changed line must pass the repository's flake8 configuration and black at the configured line length.

## Dependencies
- The only new import is the Callable name from the standard typing module, added to the existing typing import in the dictionary module. Callable is already available in the vanilla module.
- No new third-party packages.

## Naming
- Classes: Lambda and Lambdad.
- Aliases: LambdaD and LambdaDict, assigned to Lambdad in the same chained-assignment form as the other dictionary aliases and appended at the end of the existing alias block.
- The new alias line uses the same single-space-around-equals style as its neighbors. No existing alias line is reformatted.

## Validation
- Lambda validates func with a callability assertion whose message reads "func must be callable".
- Lambdad validates keys through the MapTransform base, then validates func by constructing its internal Lambda. Keys are validated before func.
- Lambdad adds no validation of its own for func.
- Before finishing, compare each modified file with its original. In the dictionary module, the only original line that may disappear is the typing import line. The only added lines are the Lambda import entry, the Callable name in the typing import, the Lambdad class, and the new alias line. Every other original line must appear unchanged, including spacing. Any other removed or re-spaced original line must be restored.

## Error handling
- A non-callable func raises AssertionError at construction for both Lambda and Lambdad. Do not raise TypeError or ValueError for this case, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- A key missing from the input mapping raises the mapping's lookup error unchanged.
- Exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (with a reference to the MapTransform base) and func.
- Examples must be accurate for the described behavior. Use an array input and a slicing callable, and state only shapes or values the code actually produces. Do not show list-repetition or per-key results.
- The reference documentation page gets a Lambda entry in the Vanilla Transforms section, immediately before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section, after the ConcatItemsd entry and before the Transform Adaptors heading. Each entry follows the heading-and-underline and autoclass-with-members-and-special-members pattern of its neighbors.

## Compatibility
- The change is purely additive. No existing class, function, signature, or alias changes behavior.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value. Lambda with a slicing callable returns exactly the slice that the callable returns.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- Keys may be given as a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes.
- Empty keys raise ValueError.
- An iterable callable is applied whole, once per listed key, not split into per-child calls.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py and subclass the shared NumpyImageTestCase2D base. Each file carries the repository license header and the standard main guard.
- Lambda tests cover an identity callable and a slicing callable.
- Lambdad tests cover the same two callables, passing keys as a keys view of a mapping whose only entry is the image. Since a keys view includes every entry, no non-array entry (such as a string or metadata value) may be in that mapping; otherwise the slicing callable fails with a TypeError, a test defect rather than an implementation defect.
- To check that an unlisted entry is preserved, build Lambdad with an explicit keys collection naming only the image key, and keep the extra entry outside that collection. Never apply a slicing callable to a non-array entry.
- The slicing callable slices only spatial axes, leaving leading batch and channel axes whole (for example, a leading range on the first spatial axis and a reversed-stride range on the last), so the expected result is non-empty. Slicing the leading size-1 batch axis is unacceptable because it yields an empty array. Compare each result against the same slice computed directly from the test image.
- Do not add tests asserting per-key list or list-repetition behavior.
