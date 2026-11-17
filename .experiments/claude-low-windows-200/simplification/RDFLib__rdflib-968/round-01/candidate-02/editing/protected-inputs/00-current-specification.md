# Concise Bounded Description (CBD) for Graph

## Goals
- Add a public method named cbd to the Graph class. Given a resource term, it returns the Concise Bounded Description of that resource from the graph it is called on, as a new in-memory Graph.
- Implement the three CBD rules of the W3C Member Submission (https://www.w3.org/Submission/CBD/) exactly as specified under Workflows. Rule 3 (reification) is part of the required behavior and must not be narrowed.
- Keep the change additive: one method, its docstring, and its tests.

## Scope
In scope: the cbd method on Graph, its docstring, and its tests.

Out of scope:
- Implementing SPARQL DESCRIBE. In this snapshot the SPARQL evaluator raises a "DESCRIBE not implemented" error. This feature does not make DESCRIBE work and must not be described as its prerequisite or building block.
- Adding a formatter, linter, or any other tool to requirements or setup files.
- Changing stores, parsers, serializers, plugins, or the behavior of any existing method, including those on ConjunctiveGraph and Dataset.
- Adding argument validation, argument conversion, or special handling of None.

## Assumptions
- The source graph supports triple-pattern queries in which None is a wildcard for subject, predicate, or object.
- Reification is expressed with rdf:subject triples: a node R is the reified subject of a statement S when S has an rdf:subject triple whose object is R. The rdf:Statement type, rdf:predicate, and rdf:object triples are not needed for a node to count as a reification.

## Terminology
- Starting node: the resource argument passed to cbd.
- Source graph: the Graph on which cbd is called. It is never modified.
- Result: the new Graph returned by cbd.
- Reifier: a node S that has an rdf:subject triple whose object is the node currently being processed.
- Blank node: an rdflib blank node term (the BNode type).

## Workflows
1. Create an empty result Graph.
2. Process the starting node with the node procedure below.

Node procedure (applied to the starting node, and recursively to blank nodes as described in step (a)):
(a) Query the source graph for all triples whose subject is the node. Add each such triple to the result. If a triple's object is a blank node and the result does not already contain any triple whose subject is that blank node, run the node procedure on that blank node. Recursion continues through blank nodes that were not already expanded, so cycles terminate.
(b) After step (a) has finished for this node, query the source graph for all triples whose predicate is rdf:subject and whose object is the node. For each reifier S found, add every triple of the source graph whose subject is S to the result. Include every reifier found, regardless of whether S has an rdf:Statement type, and regardless of whether S's rdf:predicate or rdf:object values match any triple in the source graph.
(c) Do not run the node procedure on blank nodes that are objects of the triples added in step (b). Do not follow the rdf:object or rdf:predicate values of a reifier, and do not follow any triple in which the node appears as an object other than through rdf:subject.
(d) Step (b) runs for every node the procedure processes, including blank nodes reached through step (a). A reifier of a blank node that is part of the description therefore contributes its triples.

Invariants:
- The result contains only triples that exist in the source graph; the source graph is not modified.
- If the starting node has no subject triples and no reifiers, the result is an empty Graph (not an error, not None).
- The result is the set of triples produced by the procedure; the order in which they are added does not matter.

## Data model
- The result is a new default Graph. Namespace bindings from the source graph are not copied.
- The vocabulary terms used are the rdflib RDF namespace's subject term (rdf:subject) and the BNode term type. No new data structures are persisted or exposed.

## API contracts
- cbd is a public method on Graph taking exactly one required positional parameter named resource, with no default and no additional parameters.
- The method returns a new Graph instance. It never returns the source graph itself or a view of it.
- resource is used as given in the triple-pattern queries. The method does not convert it to another term type, does not type-check it, and does not raise for None. Passing None is not special-cased; it passes through as a wildcard, as the reference does.
- Subclasses that inherit cbd (ConjunctiveGraph and Dataset) get the behavior through the triple-pattern query of the instance they are called on, so their context-aware triple queries apply. Do not override cbd in subclasses.

## Module architecture
- The method belongs to the Graph class in the graph module. Place it as the last method of Graph, after the existing Graph methods and before the ConjunctiveGraph class definition.
- Implement the traversal as a helper function nested inside the method. The helper may call itself recursively for blank nodes.
- Responsibility stays in Graph: the method builds on Graph's own triple-pattern query and add operations.

## Implementation constraints
- Read only through Graph's triple-pattern query and write only to the result Graph's add. Do not touch store internals.
- Use the RDF namespace subject term and the BNode type, which are already imported in the graph module. Add no imports.
- Detect blank nodes with an exact type check against the BNode type.
- The cycle guard must match the reference: a blank node is expanded only when the result does not yet contain any triple with that blank node as subject.
- Run step (a) before step (b) for each node, so that the cycle guard sees the triples already added for that node.

## Dependencies
- No new packages, modules, or requirements. The reference changes only the graph module and adds one test file.
- Tests use only rdflib and the standard unittest module.

## Naming
- Method name: cbd. Parameter name: resource. Nested helper name should describe its role (the reference uses a name like add_to_cbd).
- Test file: test/test_graph_cbd.py. Test class: CbdTestCase.
- Test method names use the camelCase testX form used by the repository's Graph tests and by the reference (for example testCbd and testCbdReified).

## Validation
- No input validation is added. Invalid or None arguments are not rejected by cbd.

## Error handling
- cbd raises no exceptions of its own. Missing data yields an empty result Graph.

## Logging
- No logging is added.

## Documentation
- The docstring is the required documentation for cbd. It must follow the repository's Graph docstring style: a summary line, a description of the three CBD rules, a note that the result is a subgraph of the source, and :param resource: and :return: fields.
- The docstring must describe the reification rule as it behaves: every statement whose rdf:subject is the node is included, with no rdf:Statement type check and no predicate or object matching.
- The docstring must not claim that cbd is the basis of SPARQL DESCRIBE, and must not claim W3C conformance for any rule that is not implemented.
- The reference adds no documentation page. Adding one is optional. If a documentation page is added, every RST section underline must be at least as long as its title; "Concise Bounded Description" is 27 characters, so its underline needs at least 27 characters.

## Compatibility
- The change is additive. Existing Graph, ConjunctiveGraph, and Dataset methods keep their current behavior and output.
- cbd is inherited by ConjunctiveGraph and Dataset without any registration.

## Behavioral acceptance criteria
- For a resource with three direct triples, two of which point to URI objects and one of which points to a blank node with a nested blank node, the result contains all triples reachable by rules 1 and 2 (the reference fixture gives 8 for its blank-node resource, 3 for a resource with a type triple and two relation triples, 2 for a resource with two property triples, and 0 for a resource with no triples).
- Reified case A: a resource R5 with three direct triples, plus one typed reifier whose rdf:subject is R5 and which has four other triples (rdf:predicate, rdf:object, and one more property). cbd of R5 returns 8 triples.
- Reified case B: a resource R6 with three direct triples, plus a typed reifier with five triples and an untyped reifier with rdf:subject R6 and four other triples (rdf:predicate, rdf:object, and two more properties). cbd of R6 returns 13 triples. The untyped reifier must be included.
- Incoming reification: when a statement (A p B) exists and a reifier has rdf:subject A and rdf:object B, cbd of B does not include the reifier's triples; cbd of A does.
- A reifier whose triples contain a blank-node object does not cause that blank node's triples to be added, unless the blank node is reached by rules 1 or 2.
- A blank-node cycle terminates and returns each triple once.
- The source graph is unchanged after cbd is called, and the returned object is a different Graph instance.

## Test requirements
- test/test_graph_cbd.py contains a unittest.TestCase class. setUp parses a Turtle fixture and binds the example prefix. tearDown closes the graph.
- Tests must cover: the rules 1 and 2 counts; typed and untyped reifiers (the untyped case must be included); the incoming-reification exclusion; the blank-node-in-reification non-expansion; a blank-node cycle; source-graph immutability.
- Tests must not assert a typed-only reifier rule or a predicate/object matching rule.
- Tests use the repository's existing test runner and add no dependencies.
- The test module imports only the names its tests actually reference: the unittest module and the rdflib Graph and Namespace names. Do not import term classes such as BNode or URIRef unless the module uses them; an unused import is a lint violation under the repository's flake8 dependency and fails the test-module conventions.
- The test module ends with a main-guard block that runs the unittest main entry point when the file is executed directly, matching the reference test module and the common repository convention for test modules.
