# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies that same callable to each listed key of a mapping.
- Register both in the existing transform packages, add the LambdaD and LambdaDict aliases, and document both in the transforms reference page.

## Scope
- Included: Lambda in the vanilla utility transforms module; Lambdad in the dictionary utility transforms module; the two aliases; documentation entries; tests for both classes.
- Excluded: changes to existing transform classes or aliases; sequences of callables for func; per-key functions; output shape or type validation.

## Assumptions
- func accepts the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value.
- The framework does not inspect or constrain what func returns.
- A callable that is also iterable (for example, a container module) is still one callable and is used whole.

## Terminology
- Vanilla transform: operates on a single input value rather than a mapping.
- Dictionary transform: a MapTransform that operates on a mapping and touches only its configured keys.
- Keys: a KeysCollection as accepted by the existing MapTransform base.
- Callable: a value for which the built-in callability check returns true.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input, passed through unchanged: no copy and no type conversion.
- Lambdad construction validates keys first through the MapTransform base, then builds one internal Lambda from func, which performs the callability check. Empty or non-hashable keys fail before func is checked.
- Calling a Lambdad makes a shallow copy of the input mapping using the built-in dict type, as the existing dictionary transforms do. The copy-module function is not used. For each configured key in order, it replaces that key's value in the copy with the internal Lambda's result for that value, then returns the copy. The caller's mapping is not modified. A configured key missing from the input raises the mapping's own lookup error, uncaught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the normalized key tuple from the MapTransform base and exactly one internal Lambda wrapping the callable. It holds no other state.

## API contracts
- Lambda is in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated Callable, with no default. Its call takes one positional argument named img and returns whatever func returns for it.
- Lambdad is in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default), usable as keyword arguments named keys and func. Its call takes one argument, the data mapping, and returns a mapping.
- Both constructors are annotated as returning None.
- Lambdad's func is a single callable applied to every listed key. A list or tuple of callables is not supported.
- LambdaD and LambdaDict both refer to Lambdad. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla utility transforms module and subclasses the existing Transform base.
- Lambdad is a new class in the dictionary utility transforms module, placed after the ConcatItemsd class and before the alias block, with two blank lines before and after it. It subclasses MapTransform and delegates per-value work to Lambda.
- The dictionary module imports Lambda from the vanilla module, matching its existing import direction. The vanilla module must not import from the dictionary module.
- The wrapper adds only key iteration and dictionary copying. All callable handling lives in Lambda.

## Implementation constraints
- Do not classify func by iterability. Lambdad must not iterate func, split it per key, or accept per-key sequences. Every key receives the whole callable.
- Lambda must not call the base initializer, because the Transform base defines none.
- Add no parameters beyond those listed in the API contracts.
- Existing lines in the dictionary module keep their exact text, spacing, and position. The only permitted edits to existing lines are adding Lambda to the existing array import list and replacing the typing import line with one that also names Callable. The only other addition is one new alias line appended after the ConcatItemsD alias line. The IdentityD alias line and the rest of the alias block stay unchanged, including the single space on each side of each equals sign. Whitespace-only edits count as changes; altering spacing breaks flake8 rule E225. Do not reformat the alias block.
- Build the shallow copy with plain dictionary construction, not the copy module, even though copy is already imported.
- Every new or changed line must pass flake8 under the repository configuration and black at the configured line length.

## Dependencies
- The only new import is the Callable name from the standard typing module, added to the existing typing import in the dictionary module. Callable is already available in the vanilla module.
- No new third-party packages.

## Naming
- Classes: Lambda and Lambdad.
- Aliases: LambdaD and LambdaDict, in the same chained-assignment form as the other dictionary aliases, appended at the end of the alias block with single spaces around the equals sign.

## Validation
- Lambda asserts callability with the message "func must be callable".
- Lambdad validates keys through the MapTransform base, then validates func through its internal Lambda. Keys are validated first. Lambdad adds no validation of its own.
- Before finishing, compare each modified file against its original. For the dictionary module, the only original line that may disappear is the typing import line. Added lines are limited to the Lambda import entry, the Callable name, the Lambdad class, and the new alias line. Every other original line must appear unchanged; restore any that are removed or re-spaced.

## Error handling
- A non-callable func raises AssertionError at construction, for both classes. Do not raise TypeError or ValueError for this case, and do not wrap the assertion.
- Empty or non-hashable keys raise ValueError from the MapTransform base.
- A missing key raises the mapping's lookup error unchanged.
- Exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (referencing the MapTransform base) and func.
- Examples must match the described behavior: use an array input and a slicing callable, and show only shapes or values the code produces. Do not show list-repetition or per-key results.
- The reference page gets a Lambda entry in the Vanilla Transforms section immediately before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section after the ConcatItemsd entry and before the Transform Adaptors heading. Each uses the same heading-underline and autoclass-with-members-and-special-members pattern as its neighbors.

## Compatibility
- Purely additive. No existing class, function, signature, or alias changes behavior.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; with a slicing callable it returns exactly the slice the callable returns.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged and the original mapping is not modified.
- Keys may be given as a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes.
- Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in tests/test_lambda.py and tests/test_lambdad.py, subclass NumpyImageTestCase2D, and carry the repository license header and standard main guard.
- Lambda tests cover an identity callable and a slicing callable.
- Lambdad tests cover the same two callables, passing keys as a keys view of a mapping whose only entry is the image. A keys view includes every entry, so no non-array entry (string or metadata) may be in that mapping; a slicing callable would raise TypeError there, which is a test defect.
- To check that an unlisted entry is preserved, build Lambdad with an explicit keys collection naming only the image key, keeping the extra entry outside it. Never apply a slicing callable to a non-array entry.
- The slicing callable slices only spatial axes, leaving leading batch and channel axes whole (for example, a leading range on the first spatial axis and a reversed-stride range on the last). Indexing the leading size-1 batch axis yields an empty array and is not acceptable. Compare each result against the same slice computed from the test image.
- Do not add tests asserting per-key list or list-repetition behavior.
