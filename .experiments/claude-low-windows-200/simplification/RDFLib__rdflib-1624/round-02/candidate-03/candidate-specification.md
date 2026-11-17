# Feature: prepared SPARQL Update (`prepareUpdate`)
## Goals
- Let callers translate a SPARQL Update request once with `prepareUpdate`, then apply the prepared object through `Graph.update` repeatedly, with per-call initial bindings. This mirrors `prepareQuery`.
- Represent a translated update with one Update container, the counterpart of the Query container, flowing from translation to evaluation.
- Leave the string update path (`processUpdate` and the string branch of the update processor) behaviorally unchanged.
## Scope
- In scope: `prepareUpdate` and its export from the SPARQL plugin package; the Update container; the update translation function's return type; the update evaluation function's input; the update processor's handling of the container; tests.
- Out of scope: store-level update APIs and defaults; the `Graph.update` signature; plugin registration; the SPARQL-endpoint update store (string-only); grammar changes; new SPARQL features.
## Assumptions
- Update parsing and translation exist. Translation applies `base` and `initNs` through the existing prologue translation step.
- The parse result's prologue attribute is a list of declaration groups, one per prologue occurrence. A non-empty request has one group per operation. An empty request (no operations, possibly only declarations) has exactly one group, which may be empty. The prologue translation step handles one group at a time, so translation must apply it to a single group, never the whole list.
- `Graph.update` offers the request to the store's update method first. The in-memory store raises the not-implemented signal, so the request falls through to the registered SPARQL update processor.
- Existing callers pass the translation result straight to the evaluation function. Both sides change together, so they keep working.
## Terminology
- **Update container**: the object returned by the update translation function and by `prepareUpdate`. It holds a prologue and an ordered algebra list.
- **Translated prologue**: the Prologue object from the prologue translation step applied to one declaration group plus `base` and `initNs`. Not raw parser output.
- **Empty request**: an update string with no operations, either empty or containing only PREFIX or BASE declarations.
- **Prepared update**: an Update container returned by `prepareUpdate`.
## Workflows
1. **Prepare**: the caller calls `prepareUpdate` with the update string, an initial namespace mapping (default empty), and an optional base IRI (default none). It parses the string, translates the parse result with the update translation function, records the original arguments on the result as `prepareQuery` does, and returns the Update container. An empty request still yields a container with an empty algebra list.
2. **Apply through a graph**: `Graph.update` receives the prepared object and optional initial bindings. The graph offers it to the store (which declines for memory stores), then to the registered SPARQL update processor. The processor passes the container unchanged to the evaluation function, which runs each algebra operation in order, with initial bindings converted to variables.
3. **Direct evaluation**: the caller passes a prepared update, a graph, and optional initial bindings to the evaluation function. It runs the same operations as step 2.
4. **String path (unchanged)**: the processor parses and translates a string using only the namespace mapping (no base IRI), then evaluates the container. `processUpdate` translates using both base IRI and namespace mapping. Both behave as before.
5. **Reuse**: evaluation never mutates the container or its algebra list. One prepared update may be applied to several graphs, or several times to one graph.
6. **Empty request**: translation yields a container with an empty algebra list and a prologue built from the declaration group. Evaluating it performs no operations and raises nothing. `Graph.update` and `processUpdate` on an empty or declarations-only string leave the graph unchanged.
## Data model
- The Update container has exactly two attributes:
  - `prologue`: a Prologue object (same kind as `Query.prologue`) carrying the base IRI and namespace bindings from `initNs`. For a non-empty request it is the translated prologue. For an empty request it is the Prologue produced by applying the prologue translation step, with `base` and `initNs`, to the single declaration group (which may be empty). A declarations-only request keeps its PREFIX and BASE bindings here, though it has no operations.
  - `algebra`: the ordered list of translated operations in request order. Empty for an empty request.
- The prologue is never the raw parser output or the list of declaration groups.
- Each operation keeps its own prologue attribute, as today.
- The container is read-only during evaluation.
## API contracts
- `prepareUpdate`: inputs are the update string, an initial namespace mapping (default empty), and a base IRI (default none). Output is an Update container carrying the original-arguments record. Parse and translation errors propagate unchanged.
- Update translation function: always returns an Update container, on every path. For requests with operations it holds the translated prologue and the algebra list. For an empty request it holds the Prologue built from the single declaration group, `base`, and `initNs`, with an empty algebra list. It must never return a bare list.
- Update container constructor: takes the prologue first, then the algebra list, storing both as attributes, mirroring the Query container.
- Update evaluation function: input is an Update container; it iterates the container's `algebra` attribute. It accepts the same initial-bindings mapping as today. Per-operation behavior, including the silent flag and re-raising errors, is unchanged. An empty algebra list runs nothing and raises nothing.
- Update processor's update method: a string is translated then evaluated. An Update container is passed unchanged to the evaluation function. The processor does not unwrap it.
- Package export: `prepareUpdate` is exported from the SPARQL plugin package alongside `prepareQuery`.
- `processUpdate` keeps its existing parameters and behavior.
## Module architecture
- The Update container class lives in the SPARQL types module, beside the Query container.
- `prepareUpdate` lives in the processor module, beside `prepareQuery`. It calls the update translation function directly on the parse result, as `prepareQuery` does. It must not wrap or re-package a translated list, and must not add an empty-request branch.
- The translation layer produces the container, using the prologue from the translation step.
- The evaluation function is the single place that unwraps the container. No other layer adds unwrapping or an iteration shim for list-style loops.
- No parallel execution path: prepared updates reach evaluation through the existing processor-to-evaluation route.
- The store layer and `Graph.update` are unchanged.
## Implementation constraints
- Do not store the parser's prologue output on the container. Use the translated prologue.
- Apply `base` and `initNs` through the prologue translation step on the empty-request path as well as the non-empty path, passing it the single declaration group. Passing the whole list silently drops every PREFIX and BASE declaration. Do not write a separate prologue builder.
- Build the prologue before the empty-request early exit, so the exit returns the Update container with the built prologue and an empty algebra list. The exit skips only per-operation translation.
- Each operation keeps its existing per-operation translation.
- The evaluation function accepts one input type only: the Update container. Do not add a fallback that silently accepts other values.
- Add no third-party or new standard-library imports.
- Change only code this feature needs. Do not reformat or remove unrelated code. Keep the existing two blank lines between top-level definitions in the processor module.
- Format new and changed code to black, line length 88.
## Dependencies
- The translation module imports the Update name from the SPARQL types module, alongside its existing imports from there.
- The evaluation module does not import the Update name; it reads attributes only.
- The processor module does not import the Update name, since `prepareUpdate` does not name the type. Its prepare function may omit a return annotation.
- The SPARQL types module gains no new imports, so no import cycle is introduced.
- No new plugin or entry-point registration.
## Naming
- Use `prepareUpdate` and `Update`, mirroring `prepareQuery` and `Query`. Use attribute names `prologue` and `algebra`, matching the Query container.
## Error handling
- Parse and translation failures from `prepareUpdate` propagate unchanged, as on the string path. No new error type.
- An empty request is not an error: translating and evaluating it must not raise. An attribute error on an empty update is a defect in the early-return path.
- The evaluation function keeps its handling: an operation's failure is re-raised unless the operation is silent.
## Documentation
- `prepareUpdate` and the Update container each get a short docstring in the style of `prepareQuery` and `Query`.
- The evaluation function's docstring states that it takes an Update container. The translation function's docstring describes the container returned on every path, not a list.
- Do not add inline comments that restate the code.
## Compatibility
- The string path and `processUpdate` produce the same results as before. An empty or declarations-only string remains a silent no-op through `processUpdate` and `Graph.update`.
- Code passing the translation result to the evaluation function keeps working, since both sides use the container.
- The SPARQL-endpoint update store accepts only strings. Prepared updates are unsupported there; this is not a regression.
## Behavioral acceptance criteria
- A prepared INSERT DATA update applied with `Graph.update` inserts its triples. Inserting two triples yields a graph of length two.
- The same prepared update applied to a second graph gives the same result. Applying it twice to one graph is idempotent for INSERT DATA.
- Prefixes given through `initNs` at prepare time resolve inside the update.
- Initial bindings passed to `Graph.update` are visible to the operations.
- Passing a prepared update directly to the evaluation function with a graph applies it without error and never raises a "not iterable" error.
- A non-empty request translated by the translation function returns an Update container whose `prologue` is a Prologue object and whose `algebra` has one entry per operation, in request order.
- An empty update string given to `Graph.update` or `processUpdate` completes without error and leaves the graph unchanged.
- Translating an empty request returns an Update container whose `prologue` is a Prologue object and whose `algebra` is empty. Evaluating it does not raise.
- A declarations-only request returns an Update container with empty `algebra` whose `prologue` binds the declared prefixes. Evaluating it does not raise and leaves the graph unchanged.
- The string path gives the same results as before.
## Test requirements
- Add `test/test_sparql_prepare.py` following the repository's sparql test naming. Name each test for the behavior it checks, with the `test_` prefix.
- Cover: prepare then apply through `Graph.update`; reuse across two graphs and repeated application; `initNs` prefix resolution; direct evaluation through the evaluation function; container shape (prologue type and algebra list) for a non-empty request; an empty request; a declarations-only request asserting a declared prefix is bound in the prologue; an empty update string through `Graph.update` or `processUpdate`.
- The no-mutation check compares, before and after evaluation, a representation of the algebra that records each operation's name and textual form as a list of strings. Do not use a generic deep copy of algebra nodes, since the parse-tree node type cannot be deep-copied (its constructor requires a name). Comparing object references cannot detect mutation.
- The existing `prepareQuery` test and the DAWG update tests must still pass.
- No unused imports; format to black, line length 88.
