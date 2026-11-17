# Feature: prepared SPARQL Update (`prepareUpdate`)

## Goals
- Let callers translate a SPARQL Update request once with `prepareUpdate`, then apply the result to graphs through `Graph.update`, repeatedly and with per-call initial bindings. This mirrors `prepareQuery`.
- Represent a translated update with one container type, the Update counterpart of the Query container, which flows from translation to evaluation.
- Leave the string-based update path (`processUpdate` and the string branch of the update processor) behaviorally unchanged.

## Scope
- In scope: `prepareUpdate` and its export from the SPARQL plugin package; the Update container; the return type of the update translation function; the input of the update evaluation function; the update processor's handling of the container; tests.
- Out of scope: store-level update APIs; the signature of `Graph.update`; plugin registration; the SPARQL-endpoint update store (it accepts only strings); grammar changes; new SPARQL features.

## Assumptions
- Update parsing and translation already exist. Translation applies `base` and `initNs` through the existing prologue translation step.
- The parse result's prologue attribute is a list of declaration groups: one per operation for a non-empty request, and exactly one (possibly empty) for an empty request, including a declarations-only request. The prologue translation step handles one group at a time, so translation must apply it to a single group, never the whole list.
- `Graph.update` first offers the request to the store's update method. The in-memory store raises the not-implemented signal, so the request falls through to the registered SPARQL update processor.
- Existing callers pass the translation result straight to the evaluation function. Both sides change together, so they keep working.

## Terminology
- **Update container**: the object returned by the update translation function and by `prepareUpdate`. It holds a prologue and an ordered algebra list.
- **Translated prologue**: the Prologue produced by the prologue translation step from one declaration group plus `base` and `initNs`, not raw parser output.
- **Empty request**: an update string with no operations, either empty or containing only PREFIX or BASE declarations (a declarations-only request).
- **Prepared update**: an Update container returned by `prepareUpdate`.

## Workflows
1. **Prepare**: the caller calls `prepareUpdate` with the update string, an initial namespace mapping (default empty), and an optional base IRI (default none). The function parses the string, translates the parse result with the update translation function, records the original arguments on the result as `prepareQuery` does, and returns the Update container.
2. **Apply through a graph**: the caller calls `Graph.update` with the prepared object and optional initial bindings. The graph offers it to the store (which declines for memory stores), then to the registered SPARQL update processor. The processor passes the container unchanged to the evaluation function, which runs each operation in order, with initial bindings converted to variables.
3. **Direct evaluation**: the caller passes a prepared update to the evaluation function with a graph and optional initial bindings, and it runs the same operations as step 2.
4. **String path (unchanged)**: the update processor parses and translates a string using only the namespace mapping, then evaluates the container. `processUpdate` translates using both the base IRI and the namespace mapping.
5. **Reuse**: evaluation never mutates the container or its algebra list. One prepared update may be applied to several graphs, or several times to one graph.
6. **Empty request**: translation yields a container with an empty algebra list. Evaluating it performs no operations and raises nothing. `Graph.update` and `processUpdate` on an empty or declarations-only string leave the graph unchanged.

## Data model
- The Update container has exactly two attributes:
  - `prologue`: a Prologue object (the same kind as `Query.prologue`) carrying the base IRI and namespace bindings from `initNs`. For an empty request it is built from the single declaration group, so a declarations-only request keeps its PREFIX and BASE bindings even with no operations.
  - `algebra`: the ordered list of translated operations in request order. Empty for an empty request.
- The prologue is never the raw parser output or the list of declaration groups.
- Each operation keeps its own prologue attribute, as today.
- The container is read-only during evaluation.

## API contracts
- `prepareUpdate`: inputs are the update string, an initial namespace mapping (default empty), and a base IRI (default none). Output is an Update container carrying the original-arguments record, as `prepareQuery` does. Parse and translation errors propagate unchanged.
- Update translation function: it always returns an Update container, on every path. For an empty request it returns the Prologue built from the single declaration group, `base`, and `initNs`, with an empty algebra list. It must never return a bare list.
- Update container constructor: takes the prologue first, then the algebra list, and stores both as attributes, mirroring the Query container.
- Update evaluation function: its input is an Update container, and it iterates the container's `algebra` list. It accepts the same initial-bindings mapping as today. Per-operation behavior, including the silent flag and re-raising errors, is unchanged. An empty algebra list runs no operations and raises no error.
- Update processor's update method: a string is translated and then evaluated. An Update container is passed unchanged to the evaluation function. The processor does not unwrap it.
- Package export: `prepareUpdate` is exported from the SPARQL plugin package alongside `prepareQuery`.
- `processUpdate` keeps its existing parameters and behavior.

## Module architecture
- The Update container class is defined in the SPARQL types module, beside the Query container.
- `prepareUpdate` is defined in the processor module, beside `prepareQuery`. It calls the update translation function directly on the parse result. It must not wrap or re-package the result and must not add a branch for empty requests.
- The translation layer produces the container. The evaluation function is the single place that unwraps it; no other layer adds unwrapping or an iteration shim.
- No parallel execution path is added. The store layer and `Graph.update` are unchanged.

## Implementation constraints
- Do not store the parser's prologue output on the container. Use the translated prologue.
- On the empty-request path, apply the prologue translation step to the parse result's single declaration group. Passing the whole list silently drops every PREFIX and BASE declaration. Do not write a separate prologue builder.
- Build the prologue before the empty-request early exit, so the exit returns the Update container with the built prologue and an empty algebra list. The early exit skips only per-operation translation.
- Each operation keeps its existing per-operation translation.
- The evaluation function accepts one input type only: the Update container.
- Add no third-party or new standard-library imports, and no import cycle.
- Change only the code this feature needs. Do not reformat or remove unrelated code. Keep the existing two blank lines between top-level definitions in the processor module.
- Format new and changed code to black with line length 88.

## Dependencies
- The translation module imports the Update name from the SPARQL types module, alongside its existing imports, because it constructs the container.
- The evaluation module and the processor module do not import the Update name. The processor's prepare function may omit a return annotation.
- The SPARQL types module gains no new imports. No new plugin or entry-point registration is needed.

## Naming
- Use `prepareUpdate` and `Update`, mirroring `prepareQuery` and `Query`.
- Use the attribute names `prologue` and `algebra`, matching the Query container.

## Error handling
- Parse and translation failures raised by `prepareUpdate` propagate unchanged. No new error type is introduced.
- An empty request is not an error. Translating and evaluating it must not raise. An attribute error on an empty update is a defect in the early-return path.
- The evaluation function keeps its current handling: an operation's failure is re-raised unless the operation is silent.
- Passing a non-Update value to the evaluation function is unsupported. Do not add a fallback that accepts it silently.

## Documentation
- `prepareUpdate` and the Update container each get a short docstring in the style of `prepareQuery` and `Query`.
- The evaluation function's docstring states that it takes an Update container. The update translation function's docstring describes the container it returns on every path, not a list.
- Do not add inline comments that restate the code.

## Compatibility
- The string update path and `processUpdate` produce the same results as before. An empty or declarations-only string remains a silent no-op through `processUpdate` and `Graph.update`.
- Code that passes the translation result to the evaluation function keeps working, because both sides use the container.
- The SPARQL-endpoint update store accepts only strings. Prepared updates are unsupported there, which is not a regression.

## Behavioral acceptance criteria
- A prepared INSERT DATA update applied with `Graph.update` inserts its triples. Inserting two triples yields a graph of length two.
- Applying the same prepared update to a second graph gives the same result. Applying it twice to one graph is idempotent for INSERT DATA.
- Prefixes given through `initNs` at prepare time resolve inside the update.
- Initial bindings passed to `Graph.update` are visible to the operations.
- Passing a prepared update directly to the evaluation function with a graph applies it without error and never raises a "not iterable" error.
- A non-empty request returns an Update container whose `prologue` is a Prologue object and whose `algebra` has one entry per operation, in request order.
- An empty update string given to `Graph.update` or `processUpdate` completes without error and leaves the graph unchanged.
- Translating an empty request returns an Update container with a Prologue and an empty `algebra`. Evaluating it does not raise.
- A declarations-only request returns an Update container whose `algebra` is empty and whose `prologue` binds the declared prefixes. Evaluating it does not raise and leaves the graph unchanged.
- The string path gives the same results as before.

## Test requirements
- Add a test module `test/test_sparql_prepare.py` following the repository's sparql test naming. Name each test function for the behavior it checks, with the `test_` prefix.
- The module must cover: prepare then apply through `Graph.update`; reuse across two graphs and repeated application; `initNs` prefix resolution; direct evaluation; the container shape for a non-empty request; an empty request; a declarations-only request, asserting a declared prefix is bound in the prologue; and an empty update string through `Graph.update` or `processUpdate`.
- The no-mutation check compares, before and after evaluation, a representation of the algebra that records for each operation its name and its textual form as a list of strings. Do not use a generic deep-copy on algebra nodes: the parse-tree node type cannot be deep-copied by the standard mechanism, because its constructor requires a name. Comparing object references cannot detect mutation.
- The existing `prepareQuery` test and the DAWG update tests must still pass.
- Keep the module free of unused imports, and format it to black with line length 88.
