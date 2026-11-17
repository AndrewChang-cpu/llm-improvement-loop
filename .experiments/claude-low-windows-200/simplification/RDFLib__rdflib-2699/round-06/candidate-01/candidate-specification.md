# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path object for a complex path.
- Reject malformed path structures with a domain-specific exception. Reject Literal path nodes with TypeError. Report every other unusable input, including None and plain strings, with the domain-specific exception.
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
- The caller owns a fully loaded Graph of shapes; the parser only reads it.
- The caller passes the object of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists. No SHACL term named sequencePath exists; do not invent one.
- Existing rdflib Path classes are used unchanged.

## Terminology
- RDF list: rdf:first and rdf:rest links ending in rdf:nil. rdf:nil alone is an empty list.
- Modifier path: the result of sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, mapped to "*", "+", and "?".

## Workflows
Apply this recursive procedure to any path node. The first matching step decides the result. Errors from nested parses propagate unchanged.
1. Literal: raise the literal type error.
2. IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI.
3. Node with rdf:first: iterate it as an RDF list using the graph's existing list iteration. Fewer than two items raises the SHACL path error. Otherwise parse each item in order and return a sequence path.
4. Node with sh:inversePath: parse its value and return an inverse path.
5. Node with sh:alternativePath: iterate the RDF list named by its value with the same fewer-than-two check, and return an alternative path of the parsed items.
6. Node with sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath: parse that value and return a modifier path with "*", "+", or "?".
7. Anything else, including None and plain strings (which have no triples): raise the SHACL path error naming the node.

List rules: a list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts. rdf:nil is invalid wherever a path is expected, including as a sequence item or as the value of sh:alternativePath. Do not treat None as a wildcard.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, taking two positional parameters in order: shapes_graph and path_identifier.
- Returns a URIRef or a Path; the return annotation is the union of those types. Input: a Graph and one node.
- Keeps no state and never adds or removes triples, even when parsing fails.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior, not a subclass of ValueError.
- A Literal path node raises TypeError. Every other failure, including a non-node input, raises SHACLPathError.
- Each SHACLPathError message names its problem: rdf:nil as a path, a sequence or alternative with fewer than two items, a non-node input, or an unrecognized node.
- Errors from nested parses or list iteration are not wrapped or re-raised. A cyclic rdf:rest chain raises ValueError, which must pass through uncaught.
- No new names are exported from the core path module or the top-level rdflib package. The module emits no log output.

## Module architecture
- Add exactly one new file, rdflib/extras/shacl.py, containing the exception class and the parsing function.
- The extras layer depends on the core layer only. Core modules never import from it; rdflib/paths.py stays free of SHACL vocabulary, error types, and parsing logic.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects; never hard-code IRIs as strings.
- No function-local imports. If an import is hard to place, the design is wrong.
- Use only read operations on the graph: value lookups, membership checks, and the existing list iteration. Write no separate list-walking helper or second traversal loop.
- Use the postponed annotation evaluation style of sibling extras modules.
- Use only the SHACL path predicates in Workflows, plus rdf:first and rdf:nil.
- Narrow every shapes-graph value lookup to a non-None result before passing it onward.
- Build modifier paths by calling the modifier path class directly with the parsed inner path and the modifier text. Do not multiply a parsed result: an IRI inherits string multiplication, which the type checker rejects.
- Allowed rdflib imports: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects; the Path class; and the Node type from the term module.
- No new third-party dependency; pyproject.toml and the lock file stay unchanged.

## Documentation and style
- Module docstring: one line saying it contains utilities for working with SHACL shapes graphs.
- Function docstring: reST field style of sibling docstrings; state what a valid SHACL path is, the parameters, and the return value, cross-referencing Graph, URIRef, and Path.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion as the basis. Each recognized path form has a short comment naming its SHACL predicate.
- Keep lines within 88 columns; format both new modules as black 23 would, and order imports per the repository's isort rules.
- Put the parse function's parameters one per line, with a trailing comma after the last.
- At the call site, pass modifier values to the constructor as the strings "*", "+", or "?".
- Both new modules must pass the repository's type-check configuration, including the unused type-ignore warning.

## Behavioral acceptance criteria
- An IRI returns unchanged. A three-item predicate list returns a sequence path in order; nested lists or alternatives parse recursively.
- A blank node with sh:inversePath returns an inverse path. Modifiers return modifier paths; combined forms such as a modifier wrapping an inverse parse to the nested structure.
- A list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- rdf:nil as a path, an empty or one-item sequence, an empty or one-item alternative, and a blank node with no recognized path predicate each raise SHACLPathError. None or a plain string raises SHACLPathError, not TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module under the extras test directory, beginning with the postponed annotation import used by sibling test modules, importing only the names it uses.
- Annotate with precise types: Graph, URIRef, the union of URIRef and Path, or the exception class type. Do not use Any where the type is known.
- Build the graph from Turtle data in a module-scoped fixture, giving every shape a sh:path triple whose object is the path under test.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement: a modifier applied directly to a bare IRI carries a type-ignore naming the operator error code; one applied to an inverse-path expression carries none. Each parser call passing an optional lookup result, a plain string, or None, including the line opening the expected-exception context, carries a type-ignore naming the argument-type error code.
- One parametrized test covers valid and invalid shapes. Valid cases compare results with expected paths; invalid cases assert the expected exception type.
- Invalid cases cover each error branch: rdf:nil as a path, an empty sequence, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is an empty pair of parentheses, so one case covers both rdf:nil-as-path and empty sequence.
