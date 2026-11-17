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
- The parse result's prologue attribute is a list of declaration groups, one group per prologue occurrence, as the grammar's list-valued parameter produces it. A non-empty request has one group per operation, aligned with its operation list. An empty request, including a declarations-only request, has exactly one group, which may itself be empty. The prologue translation step handles one declaration group at a time, so the translation layer must apply it to a single group, never to the whole list.
- `Graph.update` first offers the request to the store's own update method. The in-memory store raises the not-implemented signal, so the request falls through to the registered SPARQL update processor.
- Existing callers of the update translation function (for example the DAWG test runner) pass its result straight to the update evaluation function. Both sides change together, so those callers keep working.

## Terminology
- **Update container**: the object returned by the update translation function and by `prepareUpdate`. It holds a prologue and an ordered list of algebra operations.
- **Translated prologue**: the Prologue object produced by the prologue translation step from one declaration group plus `base` and `initNs`. It is not the raw output of the parser.
- **Algebra list**: the ordered list of translated update operations held by the container. Each operation keeps its own prologue reference, as it does today.
- **Empty request**: an update string that contains no operations, either empty or consisting only of prologue declarations.
- **Declarations-only request**: an empty request that contains one or more PREFIX or BASE declarations and no operations.
- **Prepared update**: an Update container returned by `prepareUpdate`.

## Workflows
1. **Prepare**: the caller calls `prepareUpdate` with the update string, an initial namespace mapping (default empty), and an optional base IRI (default none). The function parses the string, translates the parse result with the update translation function using the base and namespaces, records the original arguments on the result the same way `prepareQuery` does, and returns the Update container. An empty request still produces an Update container, whose algebra list is empty.
2. **Apply through a graph**: the caller calls `Graph.update` with the prepared object and optional initial bindings. The graph offers it to the store (which declines for memory stores), then to the registered SPARQL update processor. That processor passes the container unchanged to the update evaluation function, which iterates the container's algebra list and executes each operation in order, with initial bindings converted to variables.
3. **Direct evaluation**: the caller passes a prepared update directly to the update evaluation function together with a graph and optional initial bindings. It runs the same operations as step 2.
4. **String path (unchanged)**: when the update processor receives a string, it parses and translates it using only the namespace mapping (no base IRI), then evaluates the resulting container. `processUpdate` instead translates using both the base IRI and the namespace mapping. Both behave exactly as they did before this feature.
5. **Reuse**: evaluating a prepared update never mutates the container or its algebra list. The same prepared update may be applied to several graphs, or several times to one graph.
6. **Empty request**: translating an empty request yields a container whose algebra list is empty and whose prologue is built from the request's declaration group (see Data model). Evaluating that container performs no operations and completes without error, so `Graph.update` and `processUpdate` on an empty or declarations-only update string leave the graph unchanged, as they did before this feature.

## Data model
- The Update container has exactly two attributes:
  - `prologue`: a Prologue object (same kind of object as `Query.prologue`), which carries the base IRI and the namespace bindings from `initNs`. For a non-empty request it is the translated prologue the translation step ends with. For an empty request it is the Prologue object produced by applying the same prologue translation step, with `base` and `initNs`, to the single declaration group the parse result holds (which may be empty). A declarations-only request therefore keeps its PREFIX and BASE bindings in `prologue`, even though it has no operations.
  - `algebra`: the ordered list of translated operations, in request order. It is an empty list for an empty request.
- The container's prologue must never be the raw parser output or the parser's list of declaration groups.
- Each operation in the algebra list keeps its own prologue attribute, as today.
- The container is read-only during evaluation.

## API contracts
- `prepareUpdate`: inputs are the update string, an initial namespace mapping (default empty), and a base IRI (default none). Output is an Update container. The result carries the original-arguments record exactly as `prepareQuery` does. Parse and translation errors propagate unchanged.
- Update translation function: it always returns an Update container, on every path. For a request that contains operations, the container holds the translated prologue and the algebra list. For an empty request (including a declarations-only request), the container holds the Prologue object built from the single declaration group, `base`, and `initNs`, together with an empty algebra list. The function must not return a bare list on any path, because the evaluation function reads the algebra attribute of its input.
- Update container constructor: takes the prologue first, then the algebra list, and stores both as attributes. The shape mirrors the Query container.
- Update evaluation function: its input is an Update container. It iterates the container's `algebra` list, not the container object itself. It accepts the same initial-bindings mapping as today. Per-operation behavior (including the silent flag and re-raising errors) is unchanged. An empty algebra list means no operations are run and no error is raised.
- Update processor's update method: a string input is translated and then evaluated. An Update container input is passed unchanged to the evaluation function. The processor does not unwrap the container itself.
- Package export: `prepareUpdate` is exported from the SPARQL plugin package alongside `prepareQuery`.
- The processing function for update strings (`processUpdate`) keeps its existing parameters and behavior.

## Module architecture
- The Update container class is defined in the SPARQL types module, beside the Query container.
- `prepareUpdate` is defined in the processor module, beside `prepareQuery`. It calls the update translation function directly on the parse result, mirroring the way `prepareQuery` calls the query translation function. It must not wrap or re-package a list returned by translation, and it must not add any extra branch for empty requests.
- The translation layer produces the container. The prologue comes from the translation step.
- The evaluation function is the single place that unwraps the container. The processor passes the container through. No other layer adds unwrapping, and the container must not gain an iteration shim to make a list-style loop work.
- No parallel execution path is added. Prepared updates reach evaluation through the existing processor-to-evaluation route.
- The store layer and the `Graph.update` method are unchanged.

## Implementation constraints
- Do not store the parser's prologue output on the container. Use the translated prologue from the translation step.
- Translation must still apply `base` and `initNs` through the prologue translation step on the empty-request path as well as the non-empty path. On the empty-request path, the translation layer takes the parse result's single declaration group and applies the translation step to that one group. Do not pass the parse result's whole list of groups to the step: the step expects one group, so a list silently drops every PREFIX and BASE declaration. Do not write a separate prologue builder for this path.
- Build the prologue before the empty-request early exit, so that the early exit can return the Update container with the built prologue and an empty algebra list. The early exit skips only per-operation translation, and it must not return a bare list.
- Each operation keeps its existing per-operation translation.
- Do not add a second accepted input type to the evaluation function.
- Do not add third-party or new standard-library imports.
- Change only the code this feature needs. Do not reformat or remove unrelated code. Keep the existing two blank lines between top-level definitions in the processor module, including between the update processor class and the SPARQL processor class.
- Format new and changed code to the repository's black configuration (line length 88).

## Dependencies
- The translation module imports the Update name from the SPARQL types module, alongside the names it already imports from there, because it constructs the container.
- The evaluation module does not import the Update name. It reads attributes only, so an import there would be unused.
- The processor module must not import the Update name. `prepareUpdate` does not name the type, so an import there would be unused. Its prepare function may omit a return annotation.
- The SPARQL types module gains no new imports, so no import cycle is introduced.
- No new plugin or entry-point registration is needed.

## Naming
- Use `prepareUpdate` and `Update`, mirroring `prepareQuery` and `Query`.
- Use the attribute names `prologue` and `algebra`, matching the Query container.

## Error handling
- Parse and translation failures raised by `prepareUpdate` propagate unchanged, the same as on the string path. No new error type is introduced.
- An empty request is not an error. Translating it and evaluating the result must not raise. An attribute error or similar failure on an empty update is a defect in the early-return path, not an accepted behavior.
- The evaluation function keeps its current error handling: an operation's failure is re-raised unless the operation is marked silent.
- Passing a value that is not an Update container to the evaluation function is not a supported input. Do not add a fallback that silently accepts it.

## Documentation
- `prepareUpdate` and the Update container each get a short docstring in the style of `prepareQuery` and `Query`.
- The evaluation function's docstring states that it takes an Update container.
- The update translation function's docstring must describe the Update container it returns on every path. It must not describe a list return.
- Do not add inline comments that merely restate the code.

## Compatibility
- The string update path and `processUpdate` produce the same results as before. An empty or declarations-only update string remains a silent no-op through `processUpdate` and `Graph.update`.
- Code that calls the update translation function and passes the result to the evaluation function keeps working, because both sides now use the container.
- The SPARQL-endpoint update store accepts only strings. Prepared updates are not supported there, which is not a regression.

## Behavioral acceptance criteria
- A prepared INSERT DATA update applied with `Graph.update` inserts its triples. Inserting two triples yields a graph of length two.
- The same prepared update applied to a second graph produces the same result. Applying it twice to one graph is idempotent for INSERT DATA.
- Prefixes given through `initNs` at prepare time resolve inside the update.
- Initial bindings passed to `Graph.update` are visible to the operations.
- Passing a prepared update directly to the evaluation function with a graph applies it without error. It must not raise a "not iterable" error.
- A non-empty request translated by the translation function returns an Update container. Its `prologue` is a Prologue object. Its `algebra` has one entry per operation, in request order.
- An empty update string, given to `Graph.update` or `processUpdate`, completes without error and leaves the graph unchanged.
- Translating an empty request returns an Update container whose `prologue` is a Prologue object and whose `algebra` is empty. Evaluating that container does not raise.
- A declarations-only request (one or more PREFIX or BASE declarations and no operations) translated by the translation function returns an Update container whose `algebra` is empty and whose `prologue` binds the declared prefixes to their namespaces. Evaluating that container does not raise and leaves the graph unchanged.
- The string path gives the same results as before.

## Test requirements
- Add a new test module under `test/` named for the feature, `test_sparql_prepare.py`, following the repository's sparql test naming. Name each test function for the behavior it checks, and give each test function the `test_` prefix that the repository uses.
- The module must cover: prepare then apply through `Graph.update`; reuse across two graphs and repeated application; `initNs` prefix resolution; direct evaluation through the evaluation function; the container's shape (prologue type and algebra list) for a non-empty request; an empty request; a declarations-only request, asserting that a declared prefix is bound in the container's prologue; and an empty update string through `Graph.update` or `processUpdate`.
- The no-mutation check must compare a representation of the algebra taken before evaluation against the same representation taken after evaluation. A suitable representation records, for each operation, its name and its textual form as a list of strings. Do not use a generic deep-copy utility on the algebra nodes: the parse-tree node type cannot be deep-copied by the standard copy mechanism, because its constructor requires a name, so the copy raises an error. Comparing the same object references cannot detect mutation.
- The existing `prepareQuery` test and the DAWG update tests must still pass.
- Use the repository's test conventions for the new module. Keep the test module free of unused imports, and format the whole module to black with line length 88, checking long lines and string literals as well as code.

