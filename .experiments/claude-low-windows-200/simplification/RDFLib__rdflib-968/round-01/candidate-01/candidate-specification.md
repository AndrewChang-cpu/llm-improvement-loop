# Concise Bounded Description (CBD) for Graph

## Goals
- Add a public method named cbd to Graph. Given a resource term, it returns the Concise Bounded Description of that resource from the graph it is called on, as a new in-memory Graph.
- Implement the three CBD rules of the W3C Member Submission (https://www.w3.org/Submission/CBD/) as specified under Workflows. Rule 3 (reification) is required and must not be narrowed.
- Keep the change additive: one method, its docstring, and its tests.

## Scope
In scope: the cbd method, its docstring, and its tests.

Out of scope:
- Implementing SPARQL DESCRIBE. The SPARQL evaluator currently raises "DESCRIBE not implemented". Do not describe this feature as a prerequisite or building block for DESCRIBE.
- Changing stores, parsers, serializers, plugins, or existing methods, including those on ConjunctiveGraph and Dataset.
- Adding formatters, linters, or other tools to requirements or setup files.
- Argument validation, argument conversion, or special handling of None.

## Assumptions
- The source graph supports triple-pattern queries where None is a wildcard for subject, predicate, or object.
- Reification uses rdf:subject triples: node R is reified by statement S when S has an rdf:subject triple whose object is R. The rdf:Statement type, rdf:predicate, and rdf:object triples are not needed.

## Terminology
- Starting node: the resource argument.
- Source graph: the Graph cbd is called on. It is never modified.
- Result: the new Graph returned.
- Reifier: a node S with an rdf:subject triple whose object is the node being processed.
- Blank node: an rdflib BNode term.

## Workflows
1. Create an empty result Graph.
2. Run the node procedure on the starting node.

Node procedure, for a node N:
(a) Query the source graph for all triples whose subject is N and add each to the result. For each object that is a blank node, run the node procedure on it only if the result does not already contain any triple whose subject is that blank node. Cycles therefore terminate.
(b) After step (a) finishes for N, query the source graph for triples whose predicate is rdf:subject and whose object is N. For each reifier S found, add every source triple whose subject is S. Include every reifier, whether or not S has an rdf:Statement type and whether or not its rdf:predicate or rdf:object values match any triple.
(c) Do not follow the rdf:object or rdf:predicate values of a reifier. Do not run the node procedure on blank nodes that appear only as objects of triples added in step (b). Do not follow any other triple in which N appears as an object.
(d) Step (b) runs for every processed node, including blank nodes reached through step (a). A reifier of a blank node in the description therefore contributes its triples.

Invariants:
- The result contains only source triples; the source graph is unchanged.
- A starting node with no subject triples and no reifiers yields an empty Graph, not an error or None.
- Insertion order does not matter.

## Data model
- The result is a new default Graph. Source namespace bindings are not copied.
- Only the rdflib RDF namespace subject term and the BNode type are used. No new data structures are persisted or exposed.

## API contracts
- cbd is a public Graph method with exactly one required positional parameter named resource, no default, and no other parameters.
- It returns a new Graph instance, never the source graph or a view of it.
- resource is used as given in triple-pattern queries: no conversion, no type check, no exception for None. None passes through as a wildcard, as in the reference.
- ConjunctiveGraph and Dataset inherit cbd unchanged; their context-aware triple queries apply through the instance called. Do not override cbd in subclasses.

## Module architecture
- Place cbd in the Graph class in the graph module as its last method, after the existing Graph methods and before the ConjunctiveGraph class definition.
- Implement traversal as a helper nested inside cbd. The helper may recurse for blank nodes.
- Build only on Graph's own triple-pattern query and add operations.

## Implementation constraints
- Read only through triple-pattern queries; write only through the result's add. Do not touch store internals.
- Use the RDF namespace subject term and BNode type already imported in the graph module. Add no imports.
- Detect blank nodes with an exact type check against BNode.
- Cycle guard: expand a blank node only when the result has no triple with that blank node as subject.
- Run step (a) before step (b) for each node so the guard sees triples already added.

## Dependencies
- No new packages, modules, or requirements. The reference changes only the graph module and adds one test file.
- Tests use only rdflib and the standard unittest module.

## Naming
- Method cbd; parameter resource. The nested helper's name describes its role (the reference uses a name like add_to_cbd).
- Test file test/test_graph_cbd.py; class CbdTestCase; methods in the camelCase testX form used by the repository's Graph tests, such as testCbd and testCbdReified.

## Validation
- No input validation. cbd does not reject invalid or None arguments.

## Error handling
- cbd raises no exceptions of its own. Missing data yields an empty result Graph.

## Logging
- No logging is added.

## Documentation
- The docstring is the required documentation. Follow the repository's Graph docstring style: a summary line, a description of the three CBD rules, a note that the result is a subgraph of the source, and :param resource: and :return: fields.
- Describe reification as it behaves: every statement whose rdf:subject is the node is included, with no rdf:Statement check and no predicate or object matching.
- Do not claim cbd underlies SPARQL DESCRIBE, or claim W3C conformance for any unimplemented rule.
- A documentation page is optional and not in the reference. If added, each RST underline must be at least as long as its title; "Concise Bounded Description" needs at least 27 characters.

## Compatibility
- The change is additive. Existing Graph, ConjunctiveGraph, and Dataset methods keep their behavior and output. Inheritance requires no registration.

## Behavioral acceptance criteria
- Rules 1 and 2 counts from the reference fixture: 8 triples for the blank-node resource (three direct triples, two to URI objects, one to a blank node with a nested blank node), 3 for a resource with a type triple and two relation triples, 2 for a resource with two property triples, and 0 for a resource with no triples.
- Reified case A: R5 has three direct triples plus one typed reifier whose rdf:subject is R5 and which has four other triples. cbd of R5 returns 8 triples.
- Reified case B: R6 has three direct triples plus a typed reifier with five triples and an untyped reifier with rdf:subject R6 and four other triples (rdf:predicate, rdf:object, and two more properties). cbd of R6 returns 13 triples; the untyped reifier must be included.
- Incoming reification: when statement (A p B) exists and a reifier has rdf:subject A and rdf:object B, cbd of B excludes the reifier's triples and cbd of A includes them.
- A reifier's blank-node object does not get its triples added unless the blank node is reached by rules 1 or 2.
- A blank-node cycle terminates and returns each triple once.
- The source graph is unchanged after cbd is called, and the returned object is a different Graph instance.

## Test requirements
- test/test_graph_cbd.py contains a unittest.TestCase class. setUp parses a Turtle fixture and binds the example prefix; tearDown closes the graph.
- Tests cover: the rules 1 and 2 counts; typed and untyped reifiers (the untyped case must be included); the incoming-reification exclusion; blank-node non-expansion in reification; a blank-node cycle; source-graph immutability.
- Do not assert a typed-only reifier rule or a predicate or object matching rule.
- Use the repository's existing test runner and add no dependencies.
- Import only names the tests reference. Do not import BNode or URIRef unless used, because unused imports violate the repository's flake8 check.
- End the module with a main guard that runs the unittest main entry point when the file is executed directly.
