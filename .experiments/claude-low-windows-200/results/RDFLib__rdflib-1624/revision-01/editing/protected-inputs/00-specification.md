# Feature: prepared SPARQL Update (`prepareUpdate`)

## Goals
- Let callers parse and translate a SPARQL Update request once with `prepareUpdate`, then apply the prepared object to a graph through `Graph.update`, repeatedly and with per-call initial bindings. This mirrors how `prepareQuery` already works for SPARQL queries.
- Represent a parsed-and-translated update with a single container type that is the Update counterpart of the existing Query container. The container is the one value that flows from translation to evaluation.
- Leave the existing string-based update path (`processUpdate` and the string branch of the update processor) behaviorally unchanged.

## Scope
- In scope: the `prepareUpdate` function and its export from the SPARQL plugin package; the Update container type; the return type of the update translation function; the input accepted by the update evaluation function; the update processor's handling of the container; tests for the feature.
- Out of scope: store-level update APIs and their defaults; the signature of `Graph.update`; plugin registration; the SPARQL-endpoint update store (it accepts only strings); grammar changes; new SPARQL features.

## Assumptions
- Update parsing and translation already exist. Translation applies `base` and `initNs` through the existing prologue translation step.
- `Graph.update` first offers the request to the store's own update method. The in-memory store raises the not-implemented signal, so the request falls through to the registered SPARQL update processor.
- Existing callers of the update translation function (for example the DAWG test runner) pass its result straight to the update evaluation function. Both sides change together, so those callers keep working.

## Terminology
- **Update container**: the object returned by the update translation function and by `prepareUpdate`. It holds a prologue and an ordered list of algebra operations.
- **Translated prologue**: the Prologue object produced by the prologue translation step from the request's prologue data plus `base` and `initNs`. It is not the raw output of the parser.
- **Algebra list**: the ordered list of translated update operations held by the container. Each operation keeps its own prologue reference, as it does today.
- **Prepared update**: an Update container returned by `prepareUpdate`.

## Workflows
1. **Prepare**: the caller calls `prepareUpdate` with the update string, an initial namespace mapping (default empty), and an optional base IRI (default none). The function parses the string, translates the parse result with the update translation function using the base and namespaces, records the original arguments on the result the same way `prepareQuery` does, and returns the Update container.
2. **Apply through a graph**: the caller calls `Graph.update` with the prepared object and optional initial bindings. The graph offers it to the store (which declines for memory stores), then to the registered SPARQL update processor. That processor passes the container unchanged to the update evaluation function, which iterates the container's algebra list and executes each operation in order, with initial bindings converted to variables.
3. **Direct evaluation**: the caller passes a prepared update directly to the update evaluation function together with a graph and optional initial bindings. It runs the same operations as step 2.
4. **String path (unchanged)**: when the processor receives a string, it parses and translates it into an Update container and then evaluates it. Behavior is identical to the current string path, which does not forward the base IRI on this path.
5. **Reuse**: evaluating a prepared update never mutates the container or its algebra list. The same prepared update may be applied to several graphs, or several times to one graph.

## Data model
- The Update container has exactly two attributes:
  - `prologue`: the translated Prologue object (same kind of object as `Query.prologue`), which carries the base IRI and the namespace bindings from `initNs`. It is the prologue the translation step ends with.
  - `algebra`: the ordered list of translated operations, in request order.
- The container's prologue must never be the raw parser output for the prologue.
- Each operation in the algebra list keeps its own prologue attribute, as today.
- The container is read-only during evaluation.

## API contracts
- `prepareUpdate`: inputs are the update string, an initial namespace mapping (default empty), and a base IRI (default none). Output is an Update container. The result carries the original-arguments record exactly as `prepareQuery` does. Parse and translation errors propagate unchanged.
- Update translation function: for a request that contains operations, it returns an Update container (prologue plus algebra list) instead of a bare list. For an empty request it keeps its existing early return of an empty list. Evaluating an empty result must not raise.
- Update container constructor: takes the prologue first, then the algebra list, and stores both as attributes. The shape mirrors `Query(prologue, algebra)`.
- Update evaluation function: its input is an Update container. It iterates the container's `algebra` list, not the container object itself. It accepts the same initial-bindings mapping as today. Per-operation behavior (including the silent flag and re-raising errors) is unchanged.
- Update processor's update method: a string input is translated and then evaluated. An Update container input is passed unchanged to the evaluation function. The processor does not unwrap the container itself.
- Package export: `prepareUpdate` is exported from the SPARQL plugin package alongside `prepareQuery`.
- The processing function for update strings (`processUpdate`) keeps its signature and behavior.

## Module architecture
- The Update container class is defined in the SPARQL types module, beside the Query container.
- `prepareUpdate` is defined in the processor module, beside `prepareQuery`. It calls the update translation function directly on the parse result, mirroring the way `prepareQuery` calls the query translation function. It must not wrap or re-package a list returned by translation.
- The translation layer produces the container. The prologue comes from the translation step.
- The evaluation function is the single place that unwraps the container. The processor passes the container through. No other layer adds unwrapping, and the container must not gain an iteration shim to make a list-style loop work.
- No parallel execution path is added. Prepared updates reach evaluation through the existing processor-to-evaluation route.
- The store layer and the `Graph.update` method are unchanged.

## Implementation constraints
- Do not store the parser's prologue output on the container. Use the translated prologue from the translation step.
- Translation must still apply `base` and `initNs` through the prologue translation step, and each operation keeps its existing per-operation translation.
- Keep the existing empty-request early return in the translation function.
- Do not add a second accepted input type to the evaluation function.
- Do not add third-party or new standard-library imports.

## Dependencies
- The translation module, the evaluation module, and the processor module each import the Update name from the SPARQL types module, alongside the names they already import from it. This keeps the existing dependency direction.
- The SPARQL types module gains no new imports, so no import cycle is introduced.
- No new plugin or entry-point registration is needed.

## Naming
- Use `prepareUpdate` and `Update`, mirroring `prepareQuery` and `Query`.
- Use the attribute names `prologue` and `algebra`, matching the Query container.

## Error handling
- Parse and translation failures raised by `prepareUpdate` propagate unchanged, the same as on the string path. No new error type is introduced.
- The evaluation function keeps its current error handling: an operation's failure is re-raised unless the operation is marked silent.
- Passing a value that is not an Update container to the evaluation function is not a supported input. Do not add a fallback that silently accepts it.

## Documentation
- `prepareUpdate` and the Update container each get a short docstring in the style of `prepareQuery` and `Query`.
- The evaluation function's docstring states that it takes an Update container.

## Compatibility
- The string update path and `processUpdate` produce the same results as before.
- Code that calls the update translation function and passes the result to the evaluation function keeps working, because both sides now use the container.
- The SPARQL-endpoint update store accepts only strings. Prepared updates are not supported there, which is not a regression.

## Behavioral acceptance criteria
- A prepared INSERT DATA update applied with `Graph.update` inserts its triples. Inserting two triples yields a graph of length two.
- The same prepared update applied to a second graph produces the same result. Applying it twice to one graph is idempotent for INSERT DATA.
- Prefixes given through `initNs` at prepare time resolve inside the update.
- Initial bindings passed to `Graph.update` are visible to the operations.
- Passing a prepared update directly to the evaluation function with a graph applies it without error. It must not raise a "not iterable" error.
- A non-empty request translated by the translation function returns an Update container. Its `prologue` is a Prologue object. Its `algebra` has one entry per operation, in request order.
- The string path gives the same results as before.

## Test requirements
- Add a new test module under `test/` for prepared updates. It must cover: prepare then apply through `Graph.update`; reuse across two graphs and repeated application; `initNs` prefix resolution; direct evaluation through the evaluation function; and the container's shape (prologue type and algebra list).
- The existing `prepareQuery` test and the DAWG update tests must still pass.
- Use the repository's test conventions for the new module.
