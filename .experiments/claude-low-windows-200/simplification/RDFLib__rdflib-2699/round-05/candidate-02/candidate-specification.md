# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path object for a complex path.
- Reject malformed path structures with a domain-specific exception. Reject Literal path nodes with TypeError. Report every other unusable input, including None and plain strings, with that exception.
- The result must work with Graph methods, and its n3 output must serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL utilities module in the rdflib extras package, with one public parsing function and one public exception class.
- Tests for that module in the existing extras test directory.

Out of scope:
- Changes to the core SPARQL path module, other rdflib modules, package `__init__` files, or their exports.
- Evaluating paths, validating whole shapes graphs, pyshacl integration, or writing to the shapes graph.
- Behavior changes to existing code. test/test_path.py must pass unmodified.

## Assumptions
- The caller owns a fully loaded Graph holding the shapes; the parser only reads it.
- The caller passes the object of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists. No SHACL term named sequencePath exists; do not invent one.

## Terminology
- Path node: the node passed to the parser as the value of `sh:path`.
- RDF list: a chain of rdf:first and rdf:rest links ending in rdf:nil. rdf:nil alone is an empty list.
- Modifier path: the result of sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, mapped to "*", "+", and "?" respectively.

## Workflows
Apply this recursive procedure to any path node. The first matching step decides the result, and nested errors propagate unchanged.
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI itself.
3. If the node has an rdf:first link, iterate it with the graph's existing list iteration. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return a sequence path of the results.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path of the result.
5. Otherwise, if the node has sh:alternativePath, iterate the RDF list named by its value with the same fewer-than-two check, and return an alternative path of the parsed items.
6. Otherwise, if the node has a modifier predicate, parse its value and return a modifier path with the matching text.
7. Otherwise, raise the SHACL path error naming the node.

List rules: a list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts. rdf:nil is invalid wherever a path is expected, including as a sequence item. A plain string or None has no triples, so it reaches step 7; never treat None as a wildcard.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, with two positional parameters in this order: shapes_graph and path_identifier.
- The input is a Graph and one node: an IRI, a blank node, or a Literal. The return annotation is the union of URIRef and Path.
- The parser keeps no state and never adds or removes triples, even when parsing fails.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior, not a subclass of ValueError.
- No new names are exported from the core path module or the top-level rdflib package.

## Module architecture
- Add one new file, rdflib/extras/shacl.py, holding the exception class and parsing function.
- The extras layer depends on the core layer only. Core modules, including rdflib/paths.py, never import from it or hold SHACL vocabulary or parsing logic.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings.
- No function-local imports.
- Use only read operations on the graph: value lookups, membership checks, and the graph's existing list iteration. Do not write a separate list-walking helper or second traversal loop.
- Use the postponed annotation evaluation style of sibling extras modules.
- Narrow every shapes-graph value lookup to a non-None result before passing it onward.
- Build each modifier path by calling the modifier path class directly with the parsed inner path and the literal text asterisk, plus, or question mark. Do not use the multiplication operator on a parsed result, because the type checker rejects it for IRI results.

## Dependencies and naming
- Allowed rdflib imports: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects; the Path class; and the Node type. Standard library typing names are allowed.
- No new third-party dependency; pyproject.toml and the lock file stay unchanged.

## Error handling
- A Literal path node raises TypeError with a message saying literals are not valid SHACL paths.
- Each SHACLPathError message names its problem: rdf:nil used as a path, a sequence or alternative with fewer than two items, a non-node input, or an unrecognized node.
- Do not wrap or re-raise errors from nested parses or list iteration. A cyclic rdf:rest chain raises ValueError, which must not be caught.
- The module emits no log output.

## Documentation
- Module docstring: one line describing it as utilities for SHACL shapes graphs.
- Function docstring: in the reST field style of sibling docstrings, state what a valid SHACL path is, what the parameters mean, and what is returned.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion. Each recognized path form has a short comment naming its SHACL predicate.

## Maintainability
- Keep lines within 88 columns; format both new modules as black 23 and sort imports per isort.
- Write the parse function's parameters one per line, with a trailing comma after the last one.
- Every type-ignore comment must sit on a line the type checker reports, including the unused type-ignore warning.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged. A three-item list of predicates returns a sequence path in order, with nested lists or alternatives parsed recursively.
- A blank node with sh:inversePath returns an inverse path. Modifier predicates return modifier paths, including combined forms such as a modifier wrapping an inverse.
- An RDF list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path, an empty or one-item sequence or alternative list, and a blank node with no recognized path predicate each raise SHACLPathError. A non-node input such as None or a plain string raises SHACLPathError, not TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module in the extras test directory, with postponed annotations as sibling test modules use, and only the imports it needs.
- Annotate with precise types: Graph, URIRef, the union of URIRef and Path, or the exception class type. Do not use Any where the type is known.
- Build the test graph from Turtle data in a module-scoped fixture, giving every shape a sh:path triple whose object is the path under test.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement: a modifier on a bare IRI needs a type-ignore for the operator error code, but one on an inverse-path expression needs none. Parser calls passing an optional lookup, a plain string, or None, including the expected-exception line, need a type-ignore for the argument-type error code. Add no others.
- One parametrized test covers valid and invalid shapes. Valid cases compare the result with the expected path; invalid cases assert the expected exception type.
- Invalid cases cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. An empty pair of parentheses in Turtle covers both rdf:nil-as-path and empty-sequence.
