# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path object for a complex path.
- Reject malformed path structures with a domain-specific exception, so callers can tell SHACL path failures apart. Reject Literal path nodes with TypeError.
- The result must work with Graph methods, and its n3 output must serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL utilities module in the existing rdflib extras package, with one public parsing function and one public exception class.
- Tests for that module in the existing extras test directory.

Out of scope:
- Changes to the core SPARQL path module or any other existing rdflib module, including package `__init__` files and their exports.
- Evaluating paths, validating whole shapes graphs, pyshacl integration, or writing to the shapes graph.

## Assumptions
- The caller owns a fully loaded rdflib Graph holding the shapes; the parser only reads it.
- The caller passes the object node of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists. No SHACL term named sequencePath exists; do not invent one.

## Terminology
- RDF list: a chain of rdf:first and rdf:rest links ending in rdf:nil, which alone denotes an empty list.

## Workflows
Apply this procedure recursively to any path node. The first matching step decides the result. Errors from nested parses propagate unchanged.
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI itself.
3. If the node has an rdf:first link, iterate it as an RDF list with the graph's existing list-iteration method. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return a sequence path.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path.
5. Otherwise, if the node has sh:alternativePath, iterate the RDF list named by its value as in step 3, parse each item in order, and return an alternative path.
6. Otherwise, if the node has sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, parse that predicate's value and return a modifier path with "*", "+", or "?" respectively.
7. Otherwise, raise the SHACL path error naming the node.

List rules: a list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts. rdf:nil is invalid wherever a path is expected, including as a sequence item and as the value of sh:alternativePath. Non-node inputs need no separate type check: a plain string or None has no triples, so it reaches step 7. Do not treat None as a wildcard.

## Data model
- Input: a Graph and one path node, an IRI, a blank node, or a Literal. Output: a URIRef or a Path instance from the core path module.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, with two positional parameters in this order: shapes_graph and path_identifier.
- Returns a URIRef or a Path; the return annotation is the union of those two types.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior, and not a ValueError subclass.
- A Literal path node raises TypeError. Every other failure, including a non-node input, raises SHACLPathError.

## Module architecture
- Add exactly one new file, rdflib/extras/shacl.py, containing the exception class and the parsing function. Export no new names from the core path module or the top-level rdflib package.
- The extras layer depends on the core layer only. Core modules never import from it.
- rdflib/paths.py stays free of SHACL vocabulary, error types, and parsing logic.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings. Place all imports at module level.
- The parser is read-only and keeps no state. Use only value lookups, membership checks, and the graph's existing list-iteration method. Do not write a separate list walker or second traversal loop.
- Use only the SHACL path predicates listed in Workflows, plus rdf:first and rdf:nil.
- Narrow every shapes-graph value lookup to a non-None result before passing it onward. Never pass an optional lookup result into a parameter that requires a node.
- Build each modifier path by calling the modifier path class directly. Do not apply the multiplication operator to a parsed result, because an IRI result inherits string multiplication, which the type checker rejects.
- Use the postponed annotation evaluation style of sibling extras modules.

## Dependencies
- Allowed rdflib imports for the new module: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects; the Path class; and the Node type from the term module. Standard library typing names are allowed.
- No new third-party dependency; pyproject.toml and the lock file stay unchanged.

## Error handling
- A Literal path node raises TypeError with a message saying literals are not valid SHACL paths.
- Each SHACLPathError message names its problem: rdf:nil used as a path, a sequence or alternative with fewer than two items, a non-node input, or an unrecognized node.
- Do not wrap or re-raise errors from nested parses or from list iteration. A cyclic rdf:rest chain raises ValueError, which must not be caught or converted.
- The module emits no log output.

## Documentation
- Module docstring: one line stating that it contains utilities for working with SHACL shapes graphs.
- Function docstring: what a valid SHACL path is, what the parameters mean, and what is returned, in the reST field style of sibling docstrings.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion as the basis of the implementation. Each recognized path form has a short comment naming its SHACL predicate.

## Maintainability
- Keep lines within 88 columns; format both new modules as black 23 would; order imports per the repository's isort rules.
- Write the parse function's parameter list one parameter per line, with a trailing comma after the last one.
- The new modules must pass the repository's type-check configuration, including the unused type-ignore warning. Every type-ignore comment must sit on a line the checker reports. If the checker is not installed, check these rules by reading the code.

## Compatibility
- No behavior of any existing rdflib module changes. Existing tests in test/test_path.py must pass unmodified, and no SHACL tests go there.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged. A three-item list of predicates returns a sequence path in order, with nested lists or alternatives parsed recursively.
- A blank node with sh:inversePath returns an inverse path of the parsed value. Modifier predicates return modifier paths, and combined forms such as a modifier wrapping an inverse parse to the nested structure.
- An RDF list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path, an empty or one-item sequence or alternative list, and a blank node with no recognized path predicate each raise SHACLPathError.
- A non-node input such as None or a plain string raises SHACLPathError, not TypeError. A Literal path node raises TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module under the extras test directory, importing the function and exception from rdflib.extras.shacl, beginning with the postponed annotation import used by the repository's other test modules. Order imports per isort, import only names the module uses, and annotate with precise types.
- Build the test graph from Turtle data in a module-scoped fixture, using an example namespace object for shape IRIs. Give every shape a sh:path triple whose object is the path under test, and look it up with the SH path predicate.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement: where a modifier literal applies directly to a bare IRI, the line carries a type-ignore naming the operator error code. Where a modifier applies to an inverse-path expression, add no comment. A line with both kinds carries one comment for the reported term.
- Each line calling the parser with an optional lookup result, the line opening the expected-exception context, and any line calling the parser with a plain string or None carries a type-ignore naming the argument-type error code. Do not add it to lines the checker accepts, because warn_unused_ignores fails them.
- One parametrized test covers valid and invalid shapes. Valid cases compare the result with the expected path; invalid cases assert the expected exception type.
- Invalid cases must cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is an empty pair of parentheses, so one case covers both rdf:nil-as-path and empty-sequence.
