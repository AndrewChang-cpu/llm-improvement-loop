# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path for a complex path.
- Reject Literal path nodes with TypeError. Report every other unusable input, including None and plain strings, with the domain-specific exception.
- The result must work with Graph methods, and its n3 output must serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL module in the rdflib extras package, with one public parsing function and one public exception class, plus tests in the existing extras test directory.

Out of scope:
- Changes to the core SPARQL path module, other rdflib modules, package `__init__` files, or their exports.
- Evaluating paths, validating whole shapes graphs, pyshacl integration, or writing to the shapes graph.
- Behavior changes to existing code. test/test_path.py must pass unmodified.

## Assumptions
- The caller owns a fully loaded Graph; the parser only reads it and receives the object of a `sh:path` triple.
- Sequence paths are RDF lists. No SHACL term named sequencePath exists; do not invent one.
- Existing rdflib Path classes are used unchanged.

## Workflows
Apply this recursive procedure to any path node. The first matching step decides the result. Errors from nested parses propagate unchanged.
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI.
3. If the node has an rdf:first link, iterate it as an RDF list with the graph's existing list iteration. Fewer than two items raises the SHACL path error. Otherwise parse each item in order and return a sequence path.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path.
5. Otherwise, if the node has sh:alternativePath, iterate the RDF list named by its value with the same two-item check and return an alternative path of the parsed items.
6. Otherwise, if the node has sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, parse that value and return a modifier path with "*", "+", or "?" respectively.
7. Otherwise, raise the SHACL path error naming the node.

List rules: an RDF list is a chain of rdf:first and rdf:rest links ending in rdf:nil; rdf:nil alone is empty. A list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts. rdf:nil is invalid wherever a path is expected, including as a sequence item. A plain string or None has no triples and reaches step 7; None is never a wildcard.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, with positional parameters shapes_graph and path_identifier, in that order.
- Returns a URIRef or a Path; the return annotation is their union. The input is a Graph and one node: an IRI, a blank node, or a Literal.
- The parser keeps no state and never adds or removes triples, even when parsing fails.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior, not a ValueError subclass.
- A Literal path node raises TypeError. Every other failure, including a non-node input, raises SHACLPathError.
- No new names are exported from the core path module or the top-level rdflib package.

## Module architecture
- The extras layer depends on the core layer only. Core modules never import from it; rdflib/paths.py gets no SHACL vocabulary, error types, or parsing logic.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings.
- No function-local imports. Use only read operations on the graph: value lookups, membership checks, and the graph's existing list iteration. Do not write a separate list-walking helper or second traversal loop.
- Use the postponed annotation evaluation style of sibling extras modules.
- Use only the path predicates listed in Workflows, plus rdf:first and rdf:nil.
- Narrow every shapes-graph value lookup to a non-None result before passing it onward.
- Build modifier paths by calling the modifier path class directly with the parsed inner path and the modifier text. Do not apply the multiplication operator to a parsed result: an IRI result inherits string multiplication, which the type checker rejects.

## Dependencies and naming
- Allowed rdflib imports: top-level Graph, Literal, and URIRef; the paths module; the RDF and SH namespace objects; the Path class; and the Node type from the term module. Standard library typing names are allowed.
- No new third-party dependency; pyproject.toml and the lock file stay unchanged.
- Module shacl; function parse_shacl_path; exception SHACLPathError; test module test_shacl_extras.

## Error handling
- A Literal path node raises TypeError saying literals are not valid SHACL paths.
- Each SHACLPathError message names its problem: rdf:nil used as a path, a sequence or alternative with fewer than two items, a non-node input, or an unrecognized node.
- Do not wrap or re-raise errors from nested parses or list iteration. A cyclic rdf:rest chain raises ValueError, which must not be caught or converted.
- The module emits no log output.

## Documentation
- Module docstring: one line stating that it contains utilities for working with SHACL shapes graphs.
- Function docstring in the reST field style of sibling docstrings: what a valid SHACL path is, what the parameters mean, and what is returned, cross-referencing Graph, URIRef, and Path.
- A comment credits pyshacl's SHACL-to-SPARQL path conversion as the basis. Each recognized path form has a short comment naming its SHACL predicate.

## Maintainability
- Keep lines within 88 columns; format as black 23 would and order imports per the repository's isort rules.
- Write the parse function's parameters one per line, with a trailing comma after the last.
- Pass modifier text to the constructor as the literal text asterisk, plus, or question mark at the call site.
- New modules must pass the repository's type-check configuration, including the unused type-ignore warning.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged. A three-item list of predicates returns a sequence path in order; nested lists or alternatives inside it parse recursively.
- A blank node with sh:inversePath returns an inverse path. Modifiers wrapping other forms parse to the nested structure.
- An RDF list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path, an empty or one-item sequence list, an empty or one-item alternative list, and a blank node with no recognized path predicate each raise SHACLPathError. None or a plain string raises SHACLPathError, not TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module under the extras test directory, beginning with the postponed annotation import used by sibling test modules.
- Annotate with precise types: Graph, URIRef, the union of URIRef and Path, or the exception class type. Do not use Any where the type is known.
- Build the test graph from Turtle data in a module-scoped fixture, giving every shape a sh:path triple whose object is the path under test.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement: a modifier applied directly to a bare IRI carries a type-ignore naming the operator error code; one applied to an inverse-path expression carries none. Each parser call with an optional lookup result, a plain string, or None, including the line opening the expected-exception context, carries a type-ignore naming the argument-type error code. Add these comments only where the checker reports an error.
- One parametrized test covers valid and invalid shapes. Valid cases compare the result with the expected path; invalid cases assert the expected exception type.
- Invalid cases cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is an empty pair of parentheses, so one case covers both rdf:nil-as-path and empty-sequence.
