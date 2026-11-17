# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path object for a complex path.
- Reject malformed path structures with a domain-specific exception, so callers can tell SHACL path failures apart. Literal path nodes raise TypeError instead.
- The result must work with Graph methods (for example as a predicate to triples or value), and its n3 output must serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL utilities module in the existing rdflib extras package, with one public parsing function and one public exception class.
- Tests for that module in the existing extras test directory.

Out of scope:
- Changes to any existing rdflib module, including the core SPARQL path module, package `__init__` files, and their exports.
- Evaluating paths, validating whole shapes graphs, pyshacl integration, or writing to the shapes graph.

## Assumptions
- The caller owns a fully loaded rdflib Graph holding the shapes; the parser only reads it.
- The caller passes the object node of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists. No SHACL term named sequencePath exists; do not invent one.
- The existing rdflib Path classes are used unchanged.

## Terminology
- Path node: the node passed to the parser as the value of `sh:path`.
- RDF list: a chain of rdf:first and rdf:rest links ending in rdf:nil. rdf:nil alone denotes an empty list.
- Modifier path: the result of sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, mapped to "*", "+", and "?".

## Workflows
Apply this recursive procedure to any path node. The first matching step decides the result. Errors from nested parses propagate unchanged.
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI itself.
3. If the node has an rdf:first link, iterate it as an RDF list with the graph's existing list-iteration method. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return a sequence path of the results.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path of the result.
5. Otherwise, if the node has sh:alternativePath, iterate the RDF list named by its value as in step 3, and return an alternative path of the parsed items.
6. Otherwise, if the node has sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, parse that predicate's value and return a modifier path with "*", "+", or "?" respectively.
7. Otherwise, raise the SHACL path error naming the node.

List rules: a list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts. rdf:nil is invalid wherever a path is expected, including as a sequence item. A plain string or None has no triples, so it reaches step 7 without a separate type check. Do not treat None as a wildcard.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, with two positional parameters in this order: shapes_graph (a Graph) and path_identifier (the path node).
- Returns a URIRef or a Path; the return annotation is the union of those two types.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior. It must not subclass ValueError.
- A Literal path node raises TypeError. Every other failure, including a non-node input, raises SHACLPathError.
- The parser keeps no state and never adds or removes triples, even when parsing fails.
- No new names are exported from the core path module or the top-level rdflib package.

## Module architecture
- Add exactly one new file, rdflib/extras/shacl.py, containing the exception class and the parsing function.
- The extras layer depends on the core layer only. Core modules, including rdflib/paths.py, never import from it and contain no SHACL vocabulary, error types, or parsing logic.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings.
- No function-local imports. Use only read operations on the graph: value lookups, membership checks, and the graph's existing list iteration. Do not write a separate list-walking helper.
- Use the postponed annotation evaluation style of sibling extras modules.
- Use only the SHACL path predicates listed in Workflows, plus rdf:first and rdf:nil.
- Narrow every shapes-graph value lookup to a non-None result before passing it onward.
- Build each modifier path by calling the modifier path class directly with the parsed inner path and the modifier text. Do not apply the multiplication operator to a parsed result: an IRI result inherits string multiplication, which the type checker rejects.

## Dependencies
- Allowed rdflib imports for the new module: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects; the Path class; and the Node type from the term module.
- Standard library typing names are allowed. No new third-party dependency; pyproject.toml and the lock file stay unchanged.

## Naming
- Module: shacl, inside the extras package. Function: parse_shacl_path. Exception: SHACLPathError. Test module: test_shacl_extras, under the extras test directory.

## Error handling
- A Literal path node raises TypeError with a message saying literals are not valid SHACL paths.
- Each SHACLPathError message names its problem: rdf:nil used as a path, a sequence or alternative with fewer than two items, a non-node input, or an unrecognized node.
- Do not wrap or re-raise errors from nested parses or list iteration. A cyclic rdf:rest chain raises ValueError, which must not be caught.
- The module emits no log output.

## Documentation
- Module docstring: one line stating that it contains utilities for working with SHACL shapes graphs.
- Function docstring: what a valid SHACL path is, the parameters, and the return value, in the reST field style of sibling docstrings.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion as the basis. Each recognized path form has a short comment naming its SHACL predicate.

## Maintainability
- Keep lines within 88 columns and format both new modules as black 23 would; order imports per the repository's isort rules.
- Write the parameter list one parameter per line with a trailing comma after the last one.
- Pass modifier values to the constructor as the literal text asterisk, plus, or question mark.
- The new modules must pass the repository's type-check configuration, including the unused type-ignore warning. Every type-ignore comment must sit on a line the checker reports.

## Compatibility
- No behavior of any existing rdflib module changes. Existing tests in test/test_path.py must pass unmodified, and no SHACL tests go there.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged. A three-item list of predicates returns a sequence path in order, and nested lists or alternatives inside it parse recursively.
- A blank node with sh:inversePath returns an inverse path of the parsed value. Modifier predicates return modifier paths, including when wrapping an inverse.
- An RDF list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path, an empty or one-item sequence or alternative list, and a blank node with no recognized path predicate each raise SHACLPathError.
- A non-node input such as None or a plain string raises SHACLPathError, not TypeError. A Literal path node raises TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module under the extras test directory, beginning with the postponed annotation import used by the repository's other test modules. Import only the names it uses, in isort order.
- Annotate with precise types (Graph, URIRef, the union of URIRef and Path, or the exception class).
- Build the test graph from Turtle data in a module-scoped fixture, using an example namespace object for shape IRIs. Give every shape a sh:path triple whose object is the path under test, and look it up with the SH path predicate.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement for the multiplication operator: where a modifier literal applies directly to a bare IRI, the line carries a type-ignore naming the operator error code. Where a modifier applies to an inverse-path expression, add no comment. A line with both kinds carries one comment for the reported term.
- Type-ignore placement for non-Node arguments: each line calling the parser with an optional lookup result, the line opening the expected-exception context, and any line calling the parser with a plain string or None carries a type-ignore naming the argument-type error code. Lines the checker accepts get none, because warn_unused_ignores fails them.
- One parametrized test covers valid and invalid shapes. Valid cases compare the result with the expected path; invalid cases assert the expected exception type.
- Invalid cases cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is an empty pair of parentheses, so one case covers both rdf:nil-as-path and empty-sequence.
