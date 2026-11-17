# SHACL path parsing utility

## Goals
- Convert the object of a SHACL `sh:path` triple into an RDFLib object usable as a predicate: a URIRef for a plain predicate, or a Path object for a complex path.
- Reject malformed path structures with a domain-specific exception. Reject Literal path nodes with TypeError. Report every other unusable input, including None and plain strings, with the same domain-specific exception, so callers can tell SHACL path failures from other errors.
- The result must work with Graph methods (for example as a predicate to triples or value), and its n3 output must serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL utilities module in the existing rdflib extras package, with one public parsing function and one public exception class.
- Tests for that module in the existing extras test directory.

Out of scope:
- Changes to the core SPARQL path module or any other existing rdflib module, including package `__init__` files. No exports from those.
- Evaluating paths, validating whole shapes graphs, pyshacl integration, or writing to the shapes graph.

## Assumptions
- The caller owns a fully loaded rdflib Graph holding the shapes; the parser only reads it.
- The caller passes the object node of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists. No SHACL term named sequencePath exists; do not invent one.
- The existing rdflib Path classes are used unchanged.

## Terminology
- Path node: the node passed to the parser as the value of `sh:path`.
- Complex path: a blank node that is an RDF list or carries one of the SHACL path predicates.
- RDF list: a chain of rdf:first and rdf:rest links ending in rdf:nil. rdf:nil on its own denotes an empty list.
- Modifier path: the result of sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, mapped to the modifiers "*", "+", and "?" respectively.

## Workflows
The parser applies this recursive procedure to any path node, in order. The first matching step decides the result. Errors from nested parses propagate unchanged.
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI: if it is rdf:nil, raise the SHACL path error; otherwise return the IRI itself.
3. If the node has an rdf:first link, iterate it as an RDF list using the graph's existing list-iteration method. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return a sequence path of the results.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path of the result.
5. Otherwise, if the node has sh:alternativePath, iterate the RDF list named by its value the same way. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return an alternative path of the results.
6. Otherwise, if the node has sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, parse that predicate's value and return a modifier path with "*", "+", or "?" respectively.
7. Otherwise, raise the SHACL path error naming the node.

Non-node inputs need no separate type check. A plain string or None has no triples in the graph, so it fails every lookup in steps 2 through 6 and reaches step 7. Do not treat None as a wildcard.

## Data model
- Input: a Graph and one path node, which is an IRI, a blank node, or a Literal.
- Output: either the IRI node itself (a URIRef) or a Path instance from the core path module.
- The parser keeps no state between calls.
- The shapes graph gains or loses no triples as a side effect of parsing, including when parsing fails.

## API contracts
- Public function parse_shacl_path in module rdflib.extras.shacl, with two positional parameters in this order: shapes_graph and path_identifier.
- Returns a URIRef or a Path; the return annotation is the union of those two types.
- Public exception SHACLPathError in the same module: a direct subclass of Exception with no added behavior. It must not subclass ValueError.
- A Literal path node raises TypeError. Every other failure, including a non-node input that is not a Literal, raises SHACLPathError.
- No new names are exported from the core path module or the top-level rdflib package.

## Module architecture
- Add exactly one new file, rdflib/extras/shacl.py, containing the exception class and the parsing function.
- The extras layer depends on the core layer only. Core modules never import from it.
- rdflib/paths.py stays free of SHACL vocabulary, SHACL error types, and SHACL parsing logic.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings.
- No function-local imports. If an import is hard to place, the design is wrong; keep the dependency one-way (extras to core).
- Use only read operations on the graph: value lookups, membership checks, and list iteration. Never add or remove triples.
- Do not write a separate list-walking helper or second traversal loop. Use the graph's existing list-iteration method so list semantics match the rest of rdflib.
- Use the postponed annotation evaluation style of sibling extras modules.
- Use only the SHACL path predicates listed in Workflows, plus rdf:first and rdf:nil. Treat no other predicate as a path form.
- Narrow every shapes-graph value lookup to a non-None result before passing it onward: bind the result, check for absence, and pass only the narrowed value. Never pass an optional lookup result into a parameter that requires a node.
- Build each modifier path by calling the modifier path class from the paths module directly, with the parsed inner path and the modifier text. Do not apply the multiplication operator to a parsed result: an IRI result inherits string multiplication, which the type checker rejects.

## Dependencies
- Allowed rdflib imports for the new module: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects; the Path class from the paths module; and the Node type from the term module.
- Standard library typing names are allowed. No new third-party dependency; pyproject.toml and the lock file stay unchanged.

## Naming
- Module: shacl, inside the extras package. Function: parse_shacl_path. Exception: SHACLPathError.
- Test module: test_shacl_extras, under the extras test directory.

## Validation
- Check for a Literal before any other check.
- For an RDF list used as a sequence or as alternatives, walk the whole list, count its items, and reject lists with fewer than two items (including empty and single-item lists) before parsing any item.
- A list whose final cell has rdf:first but no rdf:rest ends at that cell, and that cell's item counts.
- rdf:nil is invalid wherever a path is expected: as the whole path, as a sequence item, and as the value of sh:alternativePath (where it appears as an empty list).
- Reject any blank node matching none of the recognized forms.

## Error handling
- A Literal path node raises TypeError with a message saying literals are not valid SHACL paths.
- The SHACLPathError cases each carry a message naming the problem: rdf:nil used as a path, a sequence or alternative with fewer than two items, a non-node input matching no recognized form, and an unrecognized node.
- Do not wrap or re-raise errors from nested parses.
- Errors from the graph's list iteration propagate unchanged. A cyclic rdf:rest chain makes list iteration raise ValueError; do not catch it or convert it to SHACLPathError.

## Logging
- The module emits no log output. Errors are reported only by exceptions.

## Documentation
- Module docstring: one line stating that it contains utilities for working with SHACL shapes graphs.
- Function docstring: what a valid SHACL path is, what the parameters mean, and what is returned. Use the same reST field style as sibling docstrings and cross-reference the Graph, URIRef, and Path types.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion as the basis of the implementation. Each recognized path form has a short comment naming the SHACL predicate it handles.

## Maintainability
- Keep lines within 88 columns, the configured black and ruff length; exactly 88 is allowed.
- Format both new modules as black 23 would, and order imports per the repository's isort rules (black profile, 88 columns).
- Write the parse function's parameter list one parameter per line with a trailing comma after the last one.
- Pass modifier values to the constructor as the literal text asterisk, plus, or question mark at the call site, not through variables or constants of plain text type.
- The new modules must pass the repository's type-check configuration, including the unused type-ignore warning. Every type-ignore comment must sit on a line the checker reports. If the checker is not installed, apply these rules by reading the code.

## Compatibility
- No behavior of any existing rdflib module changes.
- Existing tests in test/test_path.py must pass without modification. Add no SHACL tests there.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged.
- A three-item RDF list of predicates returns a sequence path with those predicates in order; a nested RDF list inside a sequence parses recursively into a nested sequence.
- A blank node with sh:inversePath returns an inverse path of the parsed value.
- A blank node with sh:alternativePath whose list has three or more items returns an alternative path; nested alternatives and sequences inside it parse correctly.
- Blank nodes with sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath return modifier paths with "*", "+", or "?" respectively.
- Combined forms (for example a modifier wrapping an inverse) parse to the structure the nested forms describe.
- An RDF list whose final cell has rdf:first but no rdf:rest is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path raises SHACLPathError. An RDF list with one item, and the empty list, each raise SHACLPathError when used as a sequence. An alternative whose list is empty or has one item raises SHACLPathError.
- A blank node with no recognized path predicate raises SHACLPathError.
- A non-node input such as None or a plain string raises SHACLPathError, not TypeError. A Literal path node raises TypeError.
- After any call, including a failing one, the shapes graph has the same triples as before.

## Test requirements
- One new test module under the extras test directory, importing the function and exception from rdflib.extras.shacl.
- Begin it with the postponed annotation import used by the repository's other test modules.
- Order imports per isort: standard library, then the third-party pytest import, then first-party rdflib imports sorted by module path. Import only names the module uses.
- Annotate with precise types: Graph for the graph, URIRef for the resource, the union of URIRef and Path for expected values, or the exception class type for invalid cases. Do not use Any where the type is known.
- Build the test graph from Turtle data in a module-scoped fixture. Use an example namespace object for shape IRIs, and give every shape a sh:path triple whose object is the path under test. Look up each shape's path with the SH path predicate.
- Build expected values with rdflib's operators: slash for sequences, pipe for alternatives, tilde for inverses, and multiplication with the literal text for modifiers.
- Type-ignore placement for the multiplication operator: where a modifier literal applies directly to a bare IRI, the line carries a type-ignore naming the operator error code. Where a modifier applies to an inverse-path expression, add no comment. A line with both kinds carries one comment for the reported term.
- Type-ignore placement for non-Node arguments: each line calling the parser with an optional lookup result, the line opening the expected-exception context, and any line calling the parser with a plain string or None carries a type-ignore naming the argument-type error code on that same line. Do not add it to lines the checker accepts, because warn_unused_ignores fails them.
- One parametrized test covers valid and invalid shapes. Valid cases compare the result with the expected path; invalid cases assert the expected exception type.
- Invalid cases must cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is an empty pair of parentheses, which is rdf:nil, so one case covers both the rdf:nil-as-path and empty-sequence branches.
