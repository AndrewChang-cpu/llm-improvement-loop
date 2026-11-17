# Feature: prepared SPARQL Update (`prepareUpdate`)

## Goals
- Let callers translate a SPARQL Update request once with `prepareUpdate`, then apply the result to graphs through `Graph.update`, repeatedly and with per-call initial bindings. This mirrors `prepareQuery`.
- Represent a translated update with one container type, the Update counterpart of the Query container, passed from translation to evaluation.
- Leave the string-based update path (`processUpdate` and the string branch of the update processor) unchanged.

## Scope
- In scope: `prepareUpdate` and its export from the SPARQL plugin package; the Update container; the return type of the update translation function; the input of the update evaluation function; the update processor's handling of the container; tests.
- Out of scope: store-level update APIs; the `Graph.update` signature; plugin registration; the SPARQL-endpoint update store (it accepts only strings); grammar; new SPARQL features.

## Assumptions
- Update parsing and translation exist. Translation applies `base` and `initNs` through the existing prologue translation step.
- The parse result's prologue attribute is a list of declaration groups, one per prologue occurrence. A non-empty request has one group per operation. An empty request, including a declarations-only request, has exactly one group, which may be empty. The prologue translation step handles one group at a time, so it must receive a single group, never the whole list.
- `Graph.update` first offers the request to the store's update method. The in-memory store raises the not-implemented signal, so the request falls through to the registered SPARQL update processor.
- Existing callers pass the translation result straight to the evaluation function. Both sides change together, so those callers keep working.

## Terminology
- **Update container**: the object returned by the update translation function and by `prepareUpdate`. It holds a prologue and an ordered list of algebra operations.
- **Translated prologue**: the Prologue object produced by the prologue translation step from one declaration group plus `base` and `initNs`, never raw parser output.
- **Empty request**: an update string with no operations, either empty or containing only prologue declarations.
- **Declarations-only request**: an empty request with one or more PREFIX or BASE declarations.

## Workflows
1. **Prepare**: the caller calls `prepareUpdate` with the update string, an initial namespace mapping (default empty), and an optional base IRI (default none). The function parses the string, translates the parse result with the update translation function, records the original arguments on the result as `prepareQuery` does, and returns the Update container. An empty request still yields a container with an empty algebra list.
2. **Apply through a graph**: the caller calls `Graph.update` with the prepared object and optional initial bindings. The graph offers it to the store (which declines for memory stores), then to the registered SPARQL update processor. The processor passes the container unchanged to the evaluation function, which runs each operation in order, with initial bindings converted to variables.
3. **Direct evaluation**: the caller passes a prepared update, a graph, and optional initial bindings directly to the evaluation function. It runs the same operations as step 2.
4. **String path (unchanged)**: for a string, the processor parses and translates using only the namespace mapping (no base IRI), then evaluates the container. `processUpdate` translates with both the base IRI and the namespace mapping. Both behave as before.
5. **Reuse**: evaluation never mutates the container or its algebra list. One prepared update may be applied to several graphs, or several times to one graph.
6. **Empty request**: translation yields a container with an empty algebra list and a prologue built from the declaration group. Evaluating it performs no operations and raises nothing. `Graph.update` and `processUpdate` on an empty or declarations-only string leave the graph unchanged.

## Data model
- The Update container has exactly two attributes:
  - `prologue`: a Prologue object (the same kind as `Query.prologue`) carrying the base IRI and namespace bindings from `initNs`. For an empty request, it is the Prologue produced by applying the prologue translation step, with `base` and `initNs`, to the single declaration group (which may be empty). A declarations-only request therefore keeps its PREFIX and BASE bindings here, though it has no operations.
  - `algebra`: the ordered translated operations in request order. Empty for an empty request.
- Each operation keeps its own prologue attribute, as today.
- The container is read-only during evaluation.

## API contracts
- `prepareUpdate`: inputs are the update string, an initial namespace mapping (default empty), and a base IRI (default none). Output is an Update container carrying the original-arguments record. Parse and translation errors propagate unchanged.
- Update translation function: always returns an Update container, on every path. For an empty request it holds the Prologue built from the single declaration group, `base`, and `initNs`, with an empty algebra list. It must never return a bare list, because evaluation reads the algebra attribute of its input.
- Update container constructor: takes the prologue first, then the algebra list, storing both as attributes, mirroring the Query container.
- Update evaluation function: input is an Update container; it iterates the container's `algebra` list. It accepts the same initial-bindings mapping as today. Per-operation behavior, including the silent flag and re-raising errors, is unchanged. An empty algebra list runs no operations and raises nothing.
- Update processor's update method: a string is translated then evaluated. An Update container is passed unchanged to the evaluation function. The processor does not unwrap it.
- `prepareUpdate` is exported from the SPARQL plugin package alongside `prepareQuery`. `processUpdate` keeps its existing parameters and behavior.

## Module architecture
- The Update container class is defined in the SPARQL types module, beside the Query container.
- `prepareUpdate` is defined in the processor module, beside `prepareQuery`. It calls the update translation function directly on the parse result. It must not wrap or re-package the result, and must not add an empty-request branch.
- The evaluation function is the single place that unwraps the container. No other layer adds unwrapping, and the container must not gain an iteration shim for list-style loops.
- No parallel execution path. Prepared updates reach evaluation through the existing processor-to-evaluation route. The store layer and `Graph.update` are unchanged.

## Implementation constraints
- Do not store the parser's prologue output on the container. Use the translated prologue.
- Translation applies `base` and `initNs` through the prologue translation step on the empty-request path too. Pass it the single declaration group. Passing the whole list silently drops every PREFIX and BASE declaration. Do not write a separate prologue builder.
- Build the prologue before the empty-request early exit, so the exit returns the container with the built prologue and an empty algebra list. The exit skips only per-operation translation.
- Each operation keeps its existing per-operation translation.
- The evaluation function accepts one input type only: the Update container.
- Add no new imports. Change only code this feature needs; do not reformat or remove unrelated code. Keep the existing two blank lines between top-level definitions in the processor module.
- Format new and changed code to black with line length 88.

## Dependencies
- The translation module imports the Update name from the SPARQL types module, alongside its existing imports, because it constructs the container.
- The evaluation and processor modules do not import the Update name. The processor's prepare function may omit a return annotation.
- The SPARQL types module gains no new imports, so no import cycle arises.

## Naming
- Use `prepareUpdate` and `Update`, mirroring `prepareQuery` and `Query`. Use the attribute names `prologue` and `algebra`.

## Error handling
- Parse and translation failures from `prepareUpdate` propagate unchanged. No new error type.
- An empty request is not an error. Translating and evaluating it must not raise. An attribute error on an empty update is a defect in the early-return path.
- The evaluation function keeps its current handling: an operation's failure is re-raised unless the operation is silent.
- A non-Update value passed to the evaluation function is unsupported. Do not add a fallback that silently accepts it.

## Documentation
- `prepareUpdate` and the Update container each get a short docstring in the style of `prepareQuery` and `Query`.
- The evaluation function's docstring states that it takes an Update container. The translation function's docstring describes the container it returns on every path, not a list.
- Do not add inline comments that restate the code.

## Compatibility
- The string path and `processUpdate` produce the same results as before. An empty or declarations-only string remains a silent no-op through `processUpdate` and `Graph.update`.
- The SPARQL-endpoint update store accepts only strings. Prepared updates are unsupported there, which is not a regression.

## Behavioral acceptance criteria
- A prepared INSERT DATA update applied with `Graph.update` inserts its triples. Inserting two triples yields a graph of length two.
- The same prepared update applied to a second graph gives the same result. Applying it twice to one graph is idempotent for INSERT DATA.
- Prefixes given through `initNs` at prepare time resolve inside the update. Initial bindings passed to `Graph.update` are visible to the operations.
- Passing a prepared update directly to the evaluation function with a graph applies it without error and never raises a "not iterable" error.
- A non-empty request translated by the translation function returns an Update container whose `prologue` is a Prologue object and whose `algebra` has one entry per operation, in request order.
- An empty update string given to `Graph.update` or `processUpdate` completes without error and leaves the graph unchanged.
- Translating an empty request returns an Update container whose `prologue` is a Prologue object and whose `algebra` is empty. Evaluating it does not raise.
- A declarations-only request returns an Update container with an empty `algebra` whose `prologue` binds the declared prefixes to their namespaces. Evaluating it does not raise and leaves the graph unchanged.
- The string path gives the same results as before.

## Test requirements
- Add `test/test_sparql_prepare.py` following the repository's sparql test naming. Name each test function for the behavior it checks, with the `test_` prefix.
- Cover: prepare then apply through `Graph.update`; reuse across two graphs and repeated application; `initNs` prefix resolution; direct evaluation; the container shape for a non-empty request; an empty request; a declarations-only request, asserting a declared prefix is bound in the prologue; an empty update string through `Graph.update` or `processUpdate`.
- The no-mutation check compares a representation of the algebra taken before evaluation with one taken after. A suitable representation records, for each operation, its name and textual form as a list of strings. Do not use a generic deep copy on algebra nodes, because the parse-tree node type cannot be deep-copied by the standard mechanism (its constructor requires a name). Comparing object references cannot detect mutation.
- The existing `prepareQuery` test and the DAWG update tests must still pass.
- Keep the module free of unused imports, and format it to black with line length 88.
