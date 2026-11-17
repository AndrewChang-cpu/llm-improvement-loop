# Lambda transforms (vanilla and dictionary)

## Goals
- Provide a vanilla transform that applies one caller-supplied callable to its input value.
- Provide a dictionary transform that applies that same callable to each listed key of a mapping.
- Register both in the existing transform packages, with the repository's short-alias convention for the dictionary form, and document both in the transforms reference page.

## Scope
- Included: the Lambda class in the vanilla utility transforms module; the Lambdad class in the dictionary utility transforms module; the LambdaD and LambdaDict aliases; documentation entries; tests for both classes.
- Excluded: any change to existing transform classes or aliases; accepting a sequence of callables for func; per-key functions; output shape or type validation.

## Assumptions
- The caller supplies func and it accepts the value it is given (the whole input for Lambda, one item for Lambdad) and returns the transformed value.
- The framework does not inspect or constrain what func returns.
- A callable that is also iterable (for example, a container module) is still one callable and must be used as a whole.

## Terminology
- Vanilla transform: a transform that operates on a single input value rather than a mapping.
- Dictionary transform: a MapTransform that operates on a mapping and touches only its configured keys.
- Keys: a KeysCollection as accepted by the existing MapTransform base.
- Callable: a value for which the built-in callability check returns true.

## Workflows
- Lambda construction stores func after the callability check. Calling a Lambda returns func applied to the input. The input is passed through unchanged: no copy and no type conversion.
- Lambdad construction runs in this order: first the MapTransform base validates keys; then a single internal Lambda is built from func, which performs the callability check. If keys are empty or non-hashable, construction fails before func is checked.
- Calling a Lambdad makes a shallow copy of the input mapping. The copy is a new plain dictionary holding the same entries, built the way the existing dictionary transforms in the repository build their copies (the built-in dict type applied to the input mapping). The copy-module function is not used for this. For each configured key in order, the Lambdad replaces that key's value in the copy with the result of the internal Lambda applied to the value, and returns the copy. The caller's mapping is not modified. A configured key that is missing from the input raises the mapping's own lookup error and is not caught.

## Data model
- Lambda holds exactly one attribute: the callable.
- Lambdad holds the normalized key tuple produced by the MapTransform base and exactly one internal Lambda instance that wraps the callable. It holds no other state.

## API contracts
- Lambda is a transform class in the vanilla utility transforms module. Its constructor takes one required parameter named func, annotated with the Callable type. It has no default. Its call takes one positional argument named img and returns whatever func returns for it.
- Lambdad is a dictionary transform class in the dictionary utility transforms module. Its constructor takes keys (KeysCollection) and func (Callable, required, no default). Both must be usable with keyword arguments named keys and func.
- Both constructors are annotated as returning None.
- func on Lambdad is a single callable applied to every listed key. A list or tuple of callables is not a supported form.
- Lambdad's call takes one argument, the data mapping, and returns a mapping.
- The alias LambdaD and the alias LambdaDict both refer to the Lambdad class. Lambda has no alias.
- Both classes are reachable from the top-level transforms package through the existing star exports. The package initializer is not edited.

## Module architecture
- Lambda is appended at the end of the vanilla utility transforms module and subclasses the existing Transform base.
- Lambdad is placed in the dictionary utility transforms module as a new class definition inserted after the end of the ConcatItemsd class and before the alias block. Keep the module's usual two blank lines between the ConcatItemsd class and Lambdad, and between Lambdad and the first alias line. The alias block (from the IdentityD line through the ConcatItemsD line) must stay contiguous and in its original order; no alias line is moved, split, or interleaved with the new class. Lambdad subclasses MapTransform and delegates per-value work to Lambda.
- The dictionary module imports Lambda from the vanilla module, in the same direction as its existing imports. The vanilla module must not import from the dictionary module.
- The wrapper adds only key iteration and dictionary copying. All callable handling lives in Lambda.

## Implementation constraints
- Do not classify func by its iterability. Lambdad must not iterate func, must not split func per key, and must not accept per-key sequences. Any callable, including one that is also iterable, is passed whole to Lambda for every key.
- Lambda must not call the base initializer, because the Transform base defines none.
- Do not add parameters beyond those listed in the API contracts.
- Existing lines must not be changed. The only edits to existing lines in the dictionary module are adding Lambda to the existing array import list and adding Callable to the existing typing import; the only other change is appending one new alias line after the existing ConcatItemsD alias line. Every other existing line, including the existing IdentityD alias line, keeps its exact text, spacing, and position. Do not retype, re-space, or re-order any existing line.
- Whitespace-only edits count as changes to existing lines. In particular, the IdentityD alias line keeps the single space on each side of each equals sign it has in the original file. Removing or altering any of those spaces is a violation even though the code still runs, because it breaks the repository's flake8 whitespace-around-operator rule (E225). Do not reformat the alias block to make it look uniform.
- The Lambdad shallow copy must use the same plain-dictionary construction as the other dictionary transforms in the module. Do not use the copy module's copy function for this, even though the copy module is already imported in the dictionary module.
- Every new or changed line must satisfy the repository's style checks: flake8 under the repository's configuration (including whitespace-around-operator rules) and black at the repository's configured line length.

## Dependencies
- The only new import is the Callable name from the standard typing module, added to the existing typing import in the dictionary module. Callable is already available in the vanilla module.
- No new third-party packages.

## Naming
- Class names are Lambda and Lambdad.
- The aliases are LambdaD and LambdaDict, assigned to Lambdad in the same chained-assignment form as the other dictionary aliases, appended at the end of the existing alias block.
- The new alias line uses the same single-space-around-equals style as its neighboring alias lines. No existing alias line is reformatted.

## Validation
- Lambda validates func with a callability assertion whose message reads "func must be callable".
- Lambdad validates keys through the MapTransform base and validates func by constructing its internal Lambda. Keys are validated before func.
- Lambdad does not add its own validation for func.
- Before finishing, compare each modified file against its original version. For the dictionary module, the only original line that may disappear is the typing import line; the only added lines are the Lambda import entry, the Callable name in the typing import, the Lambdad class, and the new alias line. Every other original line must appear unchanged, including its spacing. Any other removed or re-spaced original line fails this check and must be restored before the work is complete.

## Error handling
- A non-callable func raises AssertionError at construction, for both Lambda and Lambdad. Do not raise TypeError or ValueError for this case, and do not wrap the assertion.
- Empty keys and non-hashable keys raise ValueError from the MapTransform base.
- A missing key in the input mapping raises the mapping's lookup error unchanged.
- Exceptions raised by func propagate unchanged.

## Documentation
- Each class has a docstring with a summary line, an example, and an Args section. Lambda documents func. Lambdad documents keys (with a reference to the MapTransform base) and func.
- Each example must be accurate for the behavior described. Use an array input and a slicing callable, and state only shapes or values the code actually produces. Do not show a list-repetition or per-key result.
- The reference documentation page gets a Lambda entry in the Vanilla Transforms section, placed immediately before the SplitChannel entry, and a Lambdad entry in the Dictionary-based Transforms section, placed after the ConcatItemsd entry and before the Transform Adaptors heading. Each entry uses the same heading-and-underline and autoclass-with-members-and-special-members pattern as its neighbors.

## Compatibility
- The change is purely additive. No existing class, function, signature, or alias changes behavior.

## Behavioral acceptance criteria
- Lambda with an identity callable returns the same value; Lambda with a slicing callable returns exactly the slice that the callable itself returns.
- Lambdad applies the callable to each listed key and returns a new mapping. Unlisted keys are unchanged, and the original mapping is not modified.
- Keys may be given as a dictionary keys view.
- A non-callable func raises AssertionError at construction for both classes.
- Empty keys raise ValueError.
- A callable that is also iterable is applied whole, once per listed key, and is not split into per-child calls.
- LambdaD and LambdaDict are the same object as Lambdad.

## Test requirements
- Tests live in the test modules for each class (tests/test_lambda.py and tests/test_lambdad.py) and subclass the shared NumpyImageTestCase2D base. Each file carries the repository license header and the standard main guard.
- Lambda tests cover an identity callable and a slicing callable. Lambdad tests cover the same two callables with the keys-view form.
- The slicing callable must slice only the spatial axes, leaving the leading batch and channel axes whole (for example, a leading range on the first spatial axis combined with a reversed-stride range on the last spatial axis), so that the expected result is non-empty. A slicing callable that indexes the leading size-1 batch axis is not acceptable, because it yields an empty array and does not exercise slicing. Compare each result against the same slice computed directly from the test image.
- Do not add tests that assert per-key list behavior or list-repetition behavior.
