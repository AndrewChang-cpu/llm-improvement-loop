# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple in a shapes graph into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path object for a complex path.
- Reject malformed paths with a domain-specific exception, so callers can tell SHACL path failures from other errors. Literal path nodes raise TypeError instead.
- The result must work with Graph methods (for example as a predicate to triples or value), and its n3 output must serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL utilities module in the existing rdflib extras package, with one public parsing function and one public exception class.
- Tests for that module in the existing extras test directory.

Out of scope:
- Any change to the core SPARQL path module or any other existing rdflib module, including package `__init__` files. No exports from those.
- Evaluating paths against data, validating shapes graphs, pyshacl integration, or writing to the shapes graph.

## Assumptions
- The caller owns a fully loaded Graph holding the shapes, and passes the object node of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists (rdf:first and rdf:rest chains ending in rdf:nil). No SHACL term named sequencePath exists; do not invent one.
- The existing rdflib Path classes (sequence, inverse, alternative, modifier) are used unchanged.

## Terminology
- Path node: the node passed to the parser as the value of `sh:path`.
- Simple path: an IRI path node that is not rdf:nil.
- Complex path: a blank node that is an RDF list or carries one of the SHACL path predicates.
- RDF list: a chain of rdf:first and rdf:rest links ending in rdf:nil. rdf:nil alone is an empty list.
- Modifier path: the result of sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, mapped to "*", "+", and "?" respectively.

## Workflows
The parser applies this recursive procedure to any path node, sending items and nested values through it again. In order:
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI itself.
3. If the node has an rdf:first link, iterate it as an RDF list using the graph's existing list-iteration method. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return a sequence path of the results.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path of the result.
5. Otherwise, if the node has sh:alternativePath, iterate the RDF list named by its value the same way. Fewer than two items raises the SHACL path error. Otherwise parse each item in order and return an alternative path of the results.
6. Otherwise, if the node has sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, parse that predicate's value and return a modifier path with "*", "+", or "?" respectively.
7. Otherwise, raise the SHACL path error naming the node.

The first matching step decides the result. Errors from nested parses propagate unchanged.

Non-node inputs need no separate type check. A plain string or None has no triples in the graph, and a value lookup with a None subject returns nothing, so both fail every lookup and reach step 7. Do not treat None as a wildcard or add special handling.

## Data model
- Input: a Graph and one path node, which is an IRI, a blank node, or a Literal.
- Output: either the IRI itself (a URIRef) or a Path instance from the core path module.
- The parser keeps no state and creates no persistent data. The graph gains or loses no triples, even when parsing fails.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, taking two positional parameters in this order: the shapes graph (shapes_graph) and the path node (path_identifier).
- Returns a URIRef or a Path; the return annotation is the union of those types.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior. It must not subclass ValueError.
- A Literal path node raises TypeError. No other input raises TypeError.
- Every other failure, including a non-node input that is not a Literal, raises SHACLPathError.
- No new names are exported from the core path module or the top-level rdflib package.

## Module architecture
- Add exactly one new file, rdflib/extras/shacl.py, holding the exception class and the parsing function.
- The extras layer depends on the core layer only. Core modules never import from it. rdflib/paths.py stays free of SHACL vocabulary, error types, and parsing logic.
- No registry, plugin, or package `__init__` change is needed.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings. Use only the SHACL path predicates listed in Workflows, plus rdf:first and rdf:nil.
- No function-local imports. Keep the dependency one-way (extras to core).
- Use only read operations on the graph: value lookups, membership checks, and list iteration. Use the graph's existing list-iteration method; do not write a separate list-walking helper or second traversal loop.
- Use the postponed annotation evaluation style of sibling extras modules.
- Narrow every shapes-graph value lookup to a non-None result before passing it on. Bind the result, check for absence, and pass only the narrowed value to the parser or to list iteration.
- Build each modifier path by calling the modifier path class directly with the parsed inner path and the modifier text. Do not apply the multiplication operator to a parsed result: an IRI result inherits string multiplication, which the type checker rejects.
- Pass modifier text at the call site as the literal text asterisk, plus, or question mark, not through variables or constants.

## Dependencies and naming
- Allowed rdflib imports for the new module: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects; the Path class from the paths module; and the Node type from the term module. Standard library typing names are allowed.
- No new third-party dependency. pyproject.toml and the lock file stay unchanged.
- Module: shacl, inside the extras package. Test module: test_shacl_extras, under the extras test directory.

## Validation and errors
- Check for a Literal before any other check.
- For an RDF list used as a sequence or as alternatives, walk the whole list and count its items before parsing any item. Reject lists with fewer than two items, including empty and single-item lists.
- A list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts.
- rdf:nil is invalid wherever a path is expected: as the whole path, as a sequence item, and as the value of sh:alternativePath (an empty list). Reject any blank node matching none of the recognized forms.
- A Literal path node raises TypeError with a message saying literals are not valid SHACL paths.
- These raise SHACLPathError with a message naming the problem: rdf:nil used as a path, a sequence or alternative with fewer than two items, a non-node input matching no recognized form, and an unrecognized node.
- Do not wrap or re-raise errors from nested parses. Errors from the graph's list iteration propagate unchanged: a cyclic rdf:rest chain makes list iteration raise ValueError, and that must not be caught or converted. Do not use ValueError for the SHACL-specific cases.

## Logging and documentation
- The module emits no log output. Errors are reported only by exceptions.
- Module docstring: one line stating that it contains utilities for working with SHACL shapes graphs.
- Function docstring: what a valid SHACL path is, what the parameters mean, and what is returned (a URIRef or a Path). Use the same reST field style as sibling docstrings and cross-reference the Graph, URIRef, and Path types.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion as the basis of the implementation. Each recognized path form has a short comment naming its SHACL predicate.

## Maintainability
- Keep lines within 88 columns, the configured black and ruff length; exactly 88 is allowed. Format as black 23 would: wrap only when the joined form exceeds 88 columns, and join any wrapped expression that fits.
- Write the parse function's parameters one per line with a trailing comma after the last.
- Order imports per the repository's isort rules (black profile, 88 columns).
- New modules must pass the repository's type-check configuration, which covers the rdflib and test directories and warns on unused type-ignore comments. Every type-ignore comment must sit on a line the checker reports. If the checker is not installed, apply these rules by reading the code.

## Compatibility
- No behavior of any existing rdflib module changes. Existing tests in test/test_path.py must pass unmodified. Add no SHACL tests there.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged.
- A three-item RDF list of predicates returns a sequence path with those predicates in order. A nested list inside a sequence parses recursively into a nested sequence.
- A blank node with sh:inversePath returns an inverse path of the parsed value.
- A blank node with sh:alternativePath whose list has three or more items returns an alternative path; nested alternatives and sequences inside it parse correctly.
- Blank nodes with sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath return modifier paths with "*", "+", or "?" respectively.
- Combined forms (for example a modifier wrapping an inverse, or a sequence containing alternatives and modifiers) parse to the structure the nested forms describe.
- An RDF list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path raises SHACLPathError. A one-item list and the empty list each raise SHACLPathError as a sequence. An alternative with an empty or one-item list raises SHACLPathError.
- A blank node with no recognized path predicate raises SHACLPathError.
- None or a plain string raises SHACLPathError, not TypeError. A Literal path node raises TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module under the extras test directory, importing the function and exception from rdflib.extras.shacl.
- Begin with the postponed annotation import used by the repository's other test modules. Order imports per isort: standard library, then the third-party pytest import, then first-party rdflib imports sorted by module path (rdflib, rdflib.extras.shacl, rdflib.namespace, rdflib.paths). Import only names the module uses.
- Annotate with precise types: Graph for the graph, URIRef for the resource, the union of URIRef and Path for expected values, and the exception class type for invalid cases. Do not use Any where the type is known.
- Build the test graph from Turtle data in a module-scoped fixture. Use an example namespace object for shape IRIs, and give every shape a sh:path triple whose object is the path under test. Do not hand-build IRI strings or invent predicates for the path link. Look up each shape's path with the SH path predicate.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement for the multiplication operator: where a modifier literal applies directly to a bare IRI, the line carries a type-ignore naming the operator error code. Where it applies to an inverse-path expression, the checker reports nothing, so add no comment. A line with both kinds carries one comment for the reported term.
- Type-ignore placement for non-Node arguments: each line calling the parser with an optional lookup result, the line opening the expected-exception context, and any line passing a deliberately non-node argument (a plain string or None) carries a type-ignore naming the argument-type error code on that line. Do not add it to lines the checker accepts, because warn_unused_ignores fails them.
- One parametrized test covers valid and invalid shapes. Valid cases compare the result with the expected path; invalid cases assert the expected exception type.
- Invalid cases cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is an empty pair of parentheses, which is rdf:nil, so one case covers both the rdf:nil-as-path and empty-sequence branches.
