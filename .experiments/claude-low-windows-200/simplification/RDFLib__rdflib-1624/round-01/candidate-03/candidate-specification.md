# Feature: prepared SPARQL Update (`prepareUpdate`)

## Goals
- Let callers parse and translate a SPARQL Update request once with `prepareUpdate`, then apply the prepared object through `Graph.update`, repeatedly and with per-call initial bindings. This mirrors `prepareQuery`.
- Represent a translated update with one container type, the Update counterpart of the Query container, which flows from translation to evaluation.
- Keep the string-based update path (`processUpdate` and the string branch of the update processor) behaviorally unchanged.

## Scope
- In scope: `prepareUpdate` and its export from the SPARQL plugin package; the Update container type; the return type of the update translation function; the input of the update evaluation function; the update processor's handling of the container; tests.
- Out of scope: store-level update APIs and defaults; the `Graph.update` signature; plugin registration; the SPARQL-endpoint update store (string-only); grammar changes; new SPARQL features.

## Assumptions
- Update parsing and translation already exist. Translation applies `base` and `initNs` through the existing prologue translation step.
- The parse result's prologue attribute is a list of declaration groups, one per prologue occurrence. A non-empty request has one group per operation. An empty request, including a declarations-only request, has exactly one group, which may be empty. The prologue translation step takes one group at a time, so the translation layer must apply it to a single group, never to the whole list.
- `Graph.update` first offers the request to the store's update method. The in-memory store raises the not-implemented signal, so the request falls through to the registered SPARQL update processor.
- Existing callers of the update translation function pass its result to the update evaluation function. Both sides change together, so they keep working.

## Terminology
- **Update container**: the object returned by the update translation function and by `prepareUpdate`. It holds a prologue and an ordered list of algebra operations.
- **Translated prologue**: the Prologue object produced by the prologue translation step from one declaration group plus `base` and `initNs`. It is not parser output.
- **Empty request**: an update string with no operations, either empty or containing only prologue declarations.
- **Declarations-only request**: an empty request with one or more PREFIX or BASE declarations.
- **Prepared update**: an Update container returned by `prepareUpdate`.

## Workflows
1. **Prepare**: the caller calls `prepareUpdate` with the update string, an initial namespace mapping (default empty), and an optional base IRI (default none). The function parses the string, translates the parse result with the update translation function, records the original arguments on the result as `prepareQuery` does, and returns the Update container. An empty request still yields an Update container.
2. **Apply through a graph**: `Graph.update` receives the prepared object and optional initial bindings. The store declines (memory stores), and the registered SPARQL update processor passes the container unchanged to the evaluation function. That function runs each algebra operation in order, with initial bindings converted to variables.
3. **Direct evaluation**: the caller passes a prepared update, a graph, and optional initial bindings directly to the evaluation function. It runs the same operations as step 2.
4. **String path (unchanged)**: the update processor given a string parses and translates it using only the namespace mapping (no base IRI), then evaluates the container. `processUpdate` translates using both the base IRI and the namespace mapping. Both behave as before.
5. **Reuse**: evaluation never mutates the container or its algebra list. One prepared update may be applied to several graphs, or repeatedly to one graph.
6. **Empty request**: evaluating its container performs no operations and raises nothing, so `Graph.update` and `processUpdate` on an empty or declarations-only string leave the graph unchanged.

## Data model
- The Update container has exactly two attributes:
  - `prologue`: a Prologue object (the same kind as `Query.prologue`) carrying the base IRI and namespace bindings. For a non-empty request it is the translated prologue. For an empty request it is the Prologue object produced by applying the prologue translation step, with `base` and `initNs`, to the single declaration group (which may be empty). A declarations-only request therefore keeps its PREFIX and BASE bindings even though it has no operations.
  - `algebra`: the ordered list of translated operations, in request order. It is empty for an empty request.
- Each operation keeps its own prologue attribute, as today.
- The container is read-only during evaluation.

## API contracts
- `prepareUpdate`: inputs are the update string, an initial namespace mapping (default empty), and a base IRI (default none). Output is an Update container carrying the original-arguments record, as `prepareQuery` does. Parse and translation errors propagate unchanged.
- Update translation function: always returns an Update container, on every path. For a request with operations, it holds the translated prologue and the algebra list. For an empty request, it holds the Prologue built from the single declaration group, `base`, and `initNs`, with an empty algebra list. It never returns a bare list, because evaluation reads the algebra attribute of its input.
- Update container constructor: takes the prologue first, then the algebra list, and stores both as attributes, mirroring the Query container.
- Update evaluation function: its input is an Update container, and it iterates the container's `algebra` list. It accepts the same initial-bindings mapping as today. Per-operation behavior (the silent flag and re-raising errors) is unchanged. An empty algebra list runs nothing and raises nothing.
- Update processor's update method: a string input is translated and then evaluated. An Update container input is passed unchanged to evaluation. The processor does not unwrap the container.
- Package export: `prepareUpdate` is exported from the SPARQL plugin package alongside `prepareQuery`.
- `processUpdate` keeps its parameters and behavior.

## Module architecture
- The Update container class is defined in the SPARQL types module, beside the Query container.
- `prepareUpdate` is defined in the processor module, beside `prepareQuery`. It calls the update translation function directly on the parse result, as `prepareQuery` calls the query translation function. It adds no list-wrapping and no extra branch for empty requests.
- The translation layer produces the container. The evaluation function is the single place that unwraps it. No other layer adds unwrapping or an iteration shim to the container.
- No parallel execution path is added: prepared updates reach evaluation through the existing processor-to-evaluation route.
- The store layer and `Graph.update` are unchanged.

## Implementation constraints
- Do not store the parser's prologue output on the container. Use the translated prologue.
- Apply `base` and `initNs` through the prologue translation step on both the empty-request and non-empty paths. On the empty path, pass the single declaration group, not the whole list: passing the list silently drops every PREFIX and BASE declaration. Do not write a separate prologue builder.
- Build the prologue before the empty-request early exit, so the exit returns the Update container with the built prologue and an empty algebra list. The early exit skips only per-operation translation.
- Each operation keeps its existing per-operation translation.
- Do not add a second accepted input type to the evaluation function, and do not add a fallback that silently accepts non-container values. Such input is unsupported.
- Do not add third-party or new standard-library imports.
- Change only the code this feature needs. Do not reformat or remove unrelated code. Keep the two blank lines between top-level definitions in the processor module, including between the update processor class and the SPARQL processor class.
- Format new and changed code to black, line length 88.

## Dependencies
- The translation module imports the Update name from the SPARQL types module, alongside its existing imports from there, because it constructs the container.
- The evaluation module does not import the Update name, because it reads attributes only.
- The processor module does not import the Update name, because `prepareUpdate` does not name the type. Its prepare function may omit a return annotation.
- The SPARQL types module gains no imports, so no import cycle is introduced.
- No plugin or entry-point registration is needed.

## Naming
- Use `prepareUpdate` and `Update`, mirroring `prepareQuery` and `Query`.
- Use the attribute names `prologue` and `algebra`, matching Query.

## Error handling
- Parse and translation failures raised by `prepareUpdate` propagate unchanged, as on the string path. No new error type is introduced.
- An empty request is not an error. Translating it and evaluating the result must not raise. An attribute error on an empty update is a defect in the early-return path.
- Evaluation keeps its error handling: a failing operation is re-raised unless it is marked silent.

## Documentation
- `prepareUpdate` and the Update container each get a short docstring in the style of `prepareQuery` and `Query`.
- The evaluation function's docstring states that it takes an Update container.
- The update translation function's docstring describes the Update container returned on every path, not a list.
- Do not add inline comments that merely restate the code.

## Compatibility
- The string path and `processUpdate` give the same results as before. An empty or declarations-only update string remains a silent no-op through `processUpdate` and `Graph.update`.
- Code that passes the translation result to the evaluation function keeps working, because both sides use the container.
- The SPARQL-endpoint update store accepts only strings. Prepared updates are unsupported there, which is not a regression.

## Behavioral acceptance criteria
- A prepared INSERT DATA update applied with `Graph.update` inserts its triples. Inserting two triples yields a graph of length two.
- The same prepared update applied to a second graph produces the same result. Applying it twice to one graph is idempotent for INSERT DATA.
- Prefixes given through `initNs` at prepare time resolve inside the update.
- Initial bindings passed to `Graph.update` are visible to the operations.
- Passing a prepared update directly to the evaluation function with a graph applies it without error, and without a "not iterable" error.
- A non-empty request translated by the translation function returns an Update container. Its `prologue` is a Prologue object, and its `algebra` has one entry per operation, in request order.
- An empty update string given to `Graph.update` or `processUpdate` completes without error and leaves the graph unchanged.
- Translating an empty request returns an Update container whose `prologue` is a Prologue object and whose `algebra` is empty. Evaluating it does not raise.
- A declarations-only request returns an Update container whose `algebra` is empty and whose `prologue` binds each declared prefix to its namespace. Evaluating it does not raise and leaves the graph unchanged.
- The string path gives the same results as before.

## Test requirements
- Add `test/test_sparql_prepare.py`, following the repository's sparql test naming. Name each test function for the behavior it checks, with the `test_` prefix.
- Cover: prepare then apply through `Graph.update`; reuse across two graphs and repeated application; `initNs` prefix resolution; direct evaluation; the container shape for a non-empty request (prologue type and algebra list); an empty request; a declarations-only request asserting that a declared prefix is bound in the prologue; and an empty update string through `Graph.update` or `processUpdate`.
- The no-mutation check compares a snapshot of the algebra taken before evaluation with one taken after. A suitable snapshot records, for each operation, its name and its textual form as a list of strings. Do not use a generic deep-copy on algebra nodes: the parse-tree node type cannot be deep-copied by the standard mechanism because its constructor requires a name, so the copy raises an error. Comparing object references cannot detect mutation.
- The existing `prepareQuery` test and the DAWG update tests must still pass.
- Follow repository test conventions. The module has no unused imports and is formatted to black with line length 88, including long lines and string literals.
