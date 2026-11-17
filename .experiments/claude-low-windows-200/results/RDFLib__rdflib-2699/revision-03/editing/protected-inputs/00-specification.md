# SHACL path parsing utility

## Goals
- Provide a utility that converts the object of a SHACL `sh:path` triple in a shapes graph into an RDFLib object that callers can use as a predicate: a URIRef when the path is a plain predicate, or a Path object when the path is complex.
- Reject malformed SHACL path structures with a domain-specific exception. Reject Literal path nodes with a TypeError. Report every other unusable input, including non-node values such as None or a plain string, with the same domain-specific exception, so callers can tell SHACL path failures apart from other errors.
- Let the result be passed to Graph methods (for example as a predicate to triples or value) and let its n3 output serve as a SPARQL property path.

## Scope
In scope:
- One new SHACL utilities module in the existing rdflib extras package.
- One public parsing function and one public exception class, both in that module.
- Tests for that module in the existing extras test directory.

Out of scope:
- Any change to the core SPARQL path module or to any other existing rdflib module, including package `__init__` files and the top-level package.
- Exporting the function or exception from the core path module or from the top-level package.
- Evaluating paths against data graphs, validating a whole shapes graph, or integrating with pyshacl.
- Writing to the shapes graph in any way.

## Assumptions
- The caller owns a fully loaded rdflib Graph that holds the shapes; the parser only reads it.
- The caller passes the object node of a `sh:path` triple, not the shape subject.
- Sequence paths are RDF lists (rdf:first and rdf:rest chains ending in rdf:nil). No SHACL term named sequencePath exists; do not invent one.
- The existing rdflib Path classes (sequence, inverse, alternative, and modifier paths) are used as they are.

## Terminology
- Path node: the node passed to the parser as the value of `sh:path`.
- Simple path: a path node that is an IRI and is not rdf:nil.
- Complex path: a blank node that is an RDF list or carries one of the SHACL path predicates.
- RDF list: a chain of rdf:first and rdf:rest links. The IRI rdf:nil terminates a list, and rdf:nil on its own denotes an empty list.
- Modifier path: the result of sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, mapped to the modifiers "*", "+", and "?" respectively.

## Workflows
The parser applies the following procedure to any path node. It is recursive: items and nested values are parsed by the same procedure. Procedure (pseudocode, not code):
1. If the node is a Literal, raise the literal type error.
2. If the node is an IRI, then if it is rdf:nil, raise the SHACL path error; otherwise return the IRI itself.
3. If the node has an rdf:first link, collect its items by iterating the RDF list through the graph's existing list-iteration method. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in list order and return a sequence path built from the results in that order.
4. Otherwise, if the node has sh:inversePath, parse its value and return an inverse path of the result.
5. Otherwise, if the node has sh:alternativePath, collect the items of the RDF list named by its value using the same list-iteration method. If it has fewer than two items, raise the SHACL path error. Otherwise parse each item in order and return an alternative path of the results.
6. Otherwise, if the node has sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath, parse the value of that predicate and return a modifier path with "*", "+", or "?" respectively.
7. Otherwise, raise the SHACL path error naming the node.

The checks run in the order above, and the first match decides the result. Errors raised while parsing nested values propagate unchanged. Inputs that are not nodes get no separate type check. A plain string such as "x" has no triples in the graph, so it fails every lookup in steps 2 through 6 and reaches step 7. A None input is different: the graph's value lookup treats a None subject as a wildcard that matches any subject carrying that predicate, so a None input can follow an earlier step and its outcome depends on the contents of the graph. Do not add special handling that changes how other inputs are processed.

## Data model
- Input: a Graph and one path node. A path node is an IRI, a blank node, or a Literal.
- Output: either an IRI (returned as the URIRef node itself) or a Path instance from the core path module.
- The parser stores no state between calls and creates no persistent data.
- The shapes graph must not gain or lose any triples as a side effect of parsing, including when the parse fails.

## API contracts
- A public function named parse_shacl_path, in the module rdflib.extras.shacl, takes two positional parameters in this order: the shapes graph (named shapes_graph) and the path node (named path_identifier).
- It returns a URIRef or a Path. The return annotation is the union of those two types.
- A public exception named SHACLPathError is defined in the same module. It is a direct subclass of the built-in Exception with no added behavior. It must not be a subclass of ValueError.
- A Literal path node raises the built-in TypeError. No other input raises TypeError.
- Every other structural failure, including a non-node input that is not a Literal, raises SHACLPathError.
- No new names are exported from the core path module or the top-level rdflib package.

## Module architecture
- Add exactly one new file, rdflib/extras/shacl.py. It contains the exception class and the parsing function.
- The extras layer depends on the core layer. The new module imports from core modules; core modules do not import from it.
- The core SPARQL path module (rdflib/paths.py) stays free of SHACL vocabulary, SHACL error types, and SHACL parsing logic.
- No registry, plugin, or package `__init__` change is needed.

## Implementation constraints
- Read SH and RDF vocabulary from the rdflib.namespace objects. Do not hard-code SHACL or RDF IRIs as strings.
- Do not use function-local imports to get around import-order problems. If an import is hard to place, the design is wrong; keep the dependency one-way (extras to core).
- Use only read operations on the graph: value lookups, membership checks, and list iteration. Never add or remove triples.
- Do not write a separate list-walking helper or a second list-traversal loop. List traversal goes through the graph's existing list-iteration method, so that list semantics stay identical to the rest of rdflib.
- Use the postponed annotation evaluation style used by sibling extras modules.
- Use only the standard SHACL path predicates listed in Workflows, plus rdf:first and rdf:nil. Do not treat any other predicate as a path form.

## Dependencies
- Allowed rdflib imports for the new module: the top-level Graph, Literal, and URIRef names; the paths module; the RDF and SH namespace objects from rdflib.namespace; the Path class from the paths module; and the Node type from the term module.
- Standard library typing names for annotations are allowed.
- No new third-party dependency. pyproject.toml and the lock file stay unchanged.

## Naming
- Module: shacl, inside the extras package.
- Function: parse_shacl_path. Parameters: shapes_graph, then path_identifier.
- Exception: SHACLPathError.
- Test module: test_shacl_extras, under the extras test directory.

## Validation
- Check for a Literal before any other check.
- For an RDF list used as a sequence or as alternatives, count the items after walking the whole list, and reject any list with fewer than two items. Reject the empty list and the single-item list alike. Do this check before parsing any item.
- A list whose final cell has an rdf:first link but no rdf:rest link ends at that cell; its item is counted as part of the list.
- Treat the IRI rdf:nil as invalid wherever a path is expected: as the whole path, as an item in a sequence, and as the value of sh:alternativePath. In the alternative case it appears as an empty list.
- Reject any blank node that matches none of the recognized forms.

## Error handling
- A Literal path node raises TypeError with a message stating that literals are not valid SHACL paths.
- The following raise SHACLPathError with a message that names the problem: rdf:nil used as a path, a sequence with fewer than two items, an alternative with fewer than two items, a non-node input that matches no recognized form, and an unrecognized node.
- Do not wrap or re-raise errors from nested parses; let them propagate.
- Errors raised by the graph's list iteration itself, such as a cyclic rdf:rest chain, propagate unchanged. Do not catch them and do not convert them to SHACLPathError.
- Do not use ValueError for the SHACL-specific cases listed above.

## Logging
- The module emits no log output. Errors are reported only by exceptions.

## Documentation
- The module docstring is one line stating that it contains utilities for working with SHACL shapes graphs.
- The function docstring describes what a valid SHACL path is, what the parameters mean, and what the return value is (a URIRef or a Path). It uses the same reST field style as sibling docstrings and cross-references the Graph, URIRef, and Path types.
- A comment near the function credits pyshacl's SHACL-to-SPARQL path conversion as the basis of the implementation.
- Each recognized path form has a short comment naming the SHACL predicate it handles.

## Maintainability
- Keep all lines within 88 columns, the repository's configured black and ruff line length. A line of exactly 88 characters is within the limit.
- Format the new module and the test module the way the repository's configured black formatter (version 23) would. Wrap a call or expression only when its joined form would exceed 88 columns, and join any wrapped expression whose joined form fits.
- The parse function's parameter list is written with one parameter per line and a trailing comma after the last parameter. That trailing comma is what keeps the wrapped form stable under black. Do not wrap the parameter list without the trailing comma.
- Order imports the way the repository's configured isort rules require (black profile, 88 columns), in each new module.
- Keep the SHACL logic in its single module so it can be changed without touching core path behavior.
- Pass each modifier value to the modifier path constructor as the literal text asterisk, plus, or question mark, written at the call site. Do not route these values through variables or module constants whose type is plain text, because the repository's type-check gate rejects them.

## Compatibility
- No behavior of any existing rdflib module changes.
- The existing tests in test/test_path.py must pass without modification.

## Behavioral acceptance criteria
- An IRI path node returns that IRI unchanged.
- A three-item RDF list of predicates returns a sequence path with those predicates in order.
- A nested RDF list inside a sequence is parsed recursively into a nested sequence.
- A blank node with sh:inversePath returns an inverse path of the parsed value.
- A blank node with sh:alternativePath whose list has three or more items returns an alternative path, and nested alternatives and sequences inside it parse correctly.
- Blank nodes with sh:zeroOrMorePath, sh:oneOrMorePath, or sh:zeroOrOnePath return modifier paths with "*", "+", or "?" respectively.
- Combined forms (for example a modifier wrapping an inverse, or a sequence containing alternatives and modifiers) parse to the structure the nested forms describe.
- An RDF list whose final cell has an rdf:first link but no rdf:rest link is read as ending at that cell, and its items are parsed.
- The IRI rdf:nil as a path raises SHACLPathError.
- An RDF list with one item, and the empty RDF list, each raise SHACLPathError when used as a sequence.
- An alternative whose list is empty or has one item raises SHACLPathError.
- A blank node with no recognized path predicate raises SHACLPathError.
- A non-node input such as None or a plain string raises SHACLPathError, not TypeError.
- A Literal path node raises TypeError.
- After any call, including a failing call, the shapes graph has the same triples it had before.

## Test requirements
- Add one new test module under the extras test directory. It imports the function and the exception from rdflib.extras.shacl.
- The test module begins with the postponed annotation import used by the repository's other test modules, so that annotations written with built-in generic types are safe on every supported Python version.
- Keep the test module's imports ordered as the repository's isort rules require.
- Import only the names the test module actually uses. The repository's ruff configuration enables the unused-import check, so an imported name with no use in the module is a lint failure. Do not import the RDF vocabulary object unless the test module references it.
- Annotate fixture and test parameters with the precise types: the graph as Graph, the resource as URIRef, and the expected value as the union of URIRef and Path, or as the exception class type for invalid cases. Do not use a catch-all type such as Any where a precise type is known.
- Build the test graph from Turtle data in a module-scoped fixture. Use an example namespace object for the shape IRIs, and give every shape a sh:path triple whose object is the path under test. Do not hand-build IRI strings or invent predicates for the path link.
- Look up each shape's path with the SH vocabulary's path predicate. Build expected values with rdflib's path operators: the slash operator for sequences, the pipe operator for alternatives, the tilde operator for inverse paths, and the multiplication operator with the literal text for modifiers. Add a type-ignore comment only on an operator line that the repository's type checker reports.
- Use one parametrized test over both valid and invalid shapes. Valid cases compare the result with the expected path. Invalid cases assert the expected exception type.
- The invalid cases must cover each error branch: rdf:nil as a path, an empty sequence list, a one-item sequence, an empty alternative, a one-item alternative, an unrecognized blank node, and a Literal. In Turtle the empty list is written as an empty pair of parentheses, which is rdf:nil, so one case built from it covers both the rdf:nil-as-path branch and the empty-sequence branch.
- Do not add SHACL tests to test/test_path.py.

