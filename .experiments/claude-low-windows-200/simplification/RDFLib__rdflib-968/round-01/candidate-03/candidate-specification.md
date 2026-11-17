# Concise Bounded Description (CBD) for Graph

## Goals
- Add a public method named cbd to the Graph class. Given a resource term, it returns the Concise Bounded Description of that resource from the graph it is called on, as a new in-memory Graph.
- Implement the three CBD rules of the W3C Member Submission (https://www.w3.org/Submission/CBD/) under Workflows. Rule 3 (reification) is required and must not be narrowed.
- Keep the change additive: one method, its docstring, and its tests.

## Scope
In scope: the cbd method, its docstring, and its tests.

Out of scope:
- Implementing SPARQL DESCRIBE. The SPARQL evaluator raises "DESCRIBE not implemented" in this snapshot. This feature does not fix that and must not be described as its prerequisite.
- Adding formatters, linters, or other tools to requirements or setup files.
- Changing stores, parsers, serializers, plugins, or existing methods, including those on ConjunctiveGraph and Dataset.

## Assumptions
- The source graph supports triple-pattern queries where None is a wildcard for subject, predicate, or object.
- A node R is the reified subject of a statement S when S has an rdf:subject triple whose object is R. The rdf:Statement type, rdf:predicate, and rdf:object triples are not required for this.

## Terminology
- Starting node: the resource argument passed to cbd.
- Source graph: the Graph on which cbd is called. It is never modified.
- Result: the new Graph returned by cbd.
- Reifier: a node S that has an rdf:subject triple whose object is the node currently being processed.
- Blank node: an rdflib BNode term.

## Workflows
1. Create an empty result Graph.
2. Process the starting node with the node procedure below.

Node procedure (applied to the starting node and recursively to blank nodes, per step (a)):
(a) Query the source graph for all triples whose subject is the node and add each to the result. If a triple's object is a blank node and the result contains no triple whose subject is that blank node, run the node procedure on that blank node. Cycles terminate because expanded blank nodes are skipped.
(b) After step (a) finishes for this node, query the source graph for triples whose predicate is rdf:subject and whose object is the node. For each reifier S found, add every source triple whose subject is S. Include every reifier, whether or not S has an rdf:Statement type and whether or not its rdf:predicate or rdf:object values match any source triple.
(c) Do not run the node procedure on blank nodes that appear only as objects of triples added in step (b). Do not follow the rdf:object or rdf:predicate values of a reifier, or any other triple in which the node is an object, except through rdf:subject.
(d) Step (b) runs for every processed node, including blank nodes reached through step (a). A reifier of a blank node in the description therefore contributes its triples.

Invariants:
- The result contains only triples from the source graph, and the source graph is not modified.
- If the starting node has no subject triples and no reifiers, the result is an empty Graph, not an error or None.
- Insertion order does not matter.

## Data model
- The result is a new default Graph. Namespace bindings from the source graph are not copied.
- The terms used are rdf:subject and the BNode type. No new data structures are persisted or exposed.

## API contracts
- cbd is a public method on Graph with exactly one required positional parameter named resource, no default, and no other parameters.
- It returns a new Graph instance, never the source graph or a view of it.
- resource is used as given in triple-pattern queries. cbd does not convert, type-check, or reject it, and None is not special-cased; it passes through as a wildcard, as in the reference.
- ConjunctiveGraph and Dataset inherit cbd and get their context-aware triple queries through the instance they are called on. Do not override cbd in subclasses.

## Module architecture
- Place cbd in the graph module as the last method of Graph, after the existing Graph methods and before the ConjunctiveGraph class.
- Implement the traversal as a helper nested inside the method. The helper may call itself recursively for blank nodes.
- Build only on Graph's own triple-pattern query and add operations.

## Implementation constraints
- Read only through Graph's triple-pattern query and write only through the result's add. Do not touch store internals.
- Use the RDF namespace subject term and the BNode type already imported in the graph module. Add no imports.
- Detect blank nodes with an exact type check against BNode.
- The cycle guard matches the reference: expand a blank node only when the result has no triple with that blank node as subject.
- Run step (a) before step (b) for each node so the cycle guard sees triples already added.

## Dependencies
- No new packages, modules, or requirements. The reference changes only the graph module and adds one test file.
- Tests use only rdflib and the standard unittest module.

## Naming
- Method name: cbd. Parameter name: resource. Nested helper name should describe its role (the reference uses add_to_cbd).
- Test file: test/test_graph_cbd.py. Test class: CbdTestCase. Test methods use the camelCase testX form, such as testCbd and testCbdReified.

## Validation
- None. Invalid or None arguments are not rejected.

## Error handling
- cbd raises no exceptions of its own. Missing data yields an empty result Graph.

## Logging
- None.

## Documentation
- The docstring is the required documentation for cbd. Follow the repository's Graph docstring style: a summary line, a description of the three CBD rules, a note that the result is a subgraph of the source, and :param resource: and :return: fields.
- Describe reification as it behaves: every statement whose rdf:subject is the node is included, with no rdf:Statement type check and no predicate or object matching.
- Do not claim that cbd underlies SPARQL DESCRIBE, or W3C conformance for any unimplemented rule.
- A documentation page is optional. If added, each RST underline must be at least as long as its title. "Concise Bounded Description" has 27 characters.

## Compatibility
- The change is additive. Existing Graph, ConjunctiveGraph, and Dataset methods keep their behavior and output.
- ConjunctiveGraph and Dataset inherit cbd without registration.

## Behavioral acceptance criteria
- A resource with three direct triples, two pointing to URIs and one to a blank node with a nested blank node, yields all triples reachable by rules 1 and 2. Reference fixture counts: 8 for the blank-node resource, 3 for a resource with a type triple and two relation triples, 2 for a resource with two property triples, and 0 for a resource with no triples.
- Reified case A: resource R5 has three direct triples and one typed reifier with rdf:subject R5 and four other triples. cbd of R5 returns 8 triples.
- Reified case B: resource R6 has three direct triples, a typed reifier with five triples, and an untyped reifier with rdf:subject R6 and four other triples. cbd of R6 returns 13 triples. The untyped reifier must be included.
- Incoming reification: if statement (A p B) exists and a reifier has rdf:subject A and rdf:object B, cbd of B does not include the reifier's triples, and cbd of A does.
- A reifier with a blank-node object does not cause that blank node's triples to be added unless rules 1 or 2 reach it.
- A blank-node cycle terminates and returns each triple once.
- The source graph is unchanged after cbd, and the returned object is a different Graph instance.

## Test requirements
- test/test_graph_cbd.py has a unittest.TestCase class. setUp parses a Turtle fixture and binds the example prefix. tearDown closes the graph.
- Tests cover: the rule 1 and 2 counts; typed and untyped reifiers (untyped must be included); incoming-reification exclusion; blank-node non-expansion through reification; a blank-node cycle; and source-graph immutability.
- Tests must not assert a typed-only reifier rule or a predicate or object matching rule.
- Use the existing test runner and add no dependencies.
- Import only names the tests reference, such as unittest, Graph, and Namespace. Unused imports, such as BNode or URIRef when unused, violate the repository's flake8 check.
- End the module with a main guard that runs the unittest main entry point, matching the reference and repository convention.
