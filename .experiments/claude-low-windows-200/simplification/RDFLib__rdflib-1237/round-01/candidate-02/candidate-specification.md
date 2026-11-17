# Namespace membership with `in` (Namespace and closed namespaces)

## Goals
- Let callers test with `in` whether a URI reference belongs to a Namespace (open prefix namespace) or a ClosedNamespace (closed term namespace, including _RDFNamespace), receiving a boolean result.
- Replace manual string-prefix checks with membership tests whose semantics match each namespace type.

## Scope
- In scope: the Namespace class, the ClosedNamespace class, the _RDFNamespace subclass, and module-level instances of these classes (for example SH, RDF, RDFS, FOAF, SKOS, PROV, GEO).
- In scope as a secondary change: the closed-namespace IPython key-completion hook. The reference makes it list completions from the namespace's URI text (the directory listing of the URI string) rather than from the object itself. This does not affect membership results; match the reference.
- Not required: NamespaceManager membership. The reference contains a misspelled attempt at such a hook that `in` never calls, so it has no effective behavior. If an implementer adds NamespaceManager membership, the hook name must be spelled correctly and must actually be dispatched by `in`.
- Out of scope: term generation, graph, store, parser, and serializer code.

## Assumptions
- A URI reference is normally a URIRef and is the left operand of `in`.
- Prefix membership on Namespace compares text: the reference's text must begin with the namespace's text.
- Closed membership compares RDF nodes with rdflib's node-type-aware equality. A plain string or a Literal with identical text is not a member.
- A ClosedNamespace is constructed once from a base URI and a fixed list of term names, and each term maps to one full URI. ClosedNamespace objects do not support the `+` operator; term URIs are obtained through the namespace's own attribute or item access.

## Terminology
- Prefix membership: a reference belongs to a Namespace when the reference's text begins with the namespace's text. The reference is the subject being tested and the namespace's text is the prefix. Asking whether the namespace's text begins with the reference's text is a different and incorrect test.
- Closed membership: a reference belongs to a ClosedNamespace only when it is a URIRef that equals, with the same node type and same text, one of the full URIs stored for that namespace's defined terms. Sharing the base URI is not enough.
- Node-type-aware equality: rdflib's node equality, which returns False when the operands have different node types even if their text matches.
- Container membership property: a URI of the form base URI, underscore, positive integer (for example `_1`). _RDFNamespace resolves these during term resolution, but they are not stored as defined terms, so they are not closed members. This is the reference behavior.

## Workflows
- When a Namespace is on the right side of `in`: return True when the reference's text begins with the namespace's text, otherwise False. Apply the prefix test to the reference as given; do not convert the reference to text first and do not reverse the roles.
- When a ClosedNamespace (including the RDF namespace) is on the right side: return True when the reference equals, under node-type-aware equality, one of the stored term URIs, otherwise False. Do not convert the reference or the stored values to text before comparing.
- Do not satisfy either case through sequence iteration over item access, or through term resolution. Those paths raise errors for names that are not defined terms.
- The result is always a boolean.

## Data model
- Namespace: no new state. Its text is the prefix.
- ClosedNamespace: the stored mapping from term name to full URI is the only source for membership. Membership is decided by comparing the reference against the stored URI values with node-type-aware equality.
- Container membership properties are not stored and are therefore not members. Membership for them is False.

## API contracts
- Both classes implement Python's membership hook `__contains__`, which takes one argument named ref and returns a bool. The `in` operator invokes it.
- Namespace results: a reference equal to the namespace's text is True, since it begins with itself. A reference that is a proper prefix of the namespace's text (the namespace text without its trailing slash) is False.
- ClosedNamespace: closed membership semantics. _RDFNamespace inherits this behavior without overriding it. A plain string or a Literal whose text equals a term URI returns False.
- Namespace instances keep their existing type. The existing type check on SH must still pass.
- Attribute access and item access results, and the error types they raise for unknown term names, do not change.

## Module architecture
- Implement all membership logic in the namespace module, on the classes that already own term resolution.
- Place the prefix hook on Namespace and the closed hook on ClosedNamespace, so _RDFNamespace inherits the closed hook. Do not duplicate it on the subclass.
- Do not change the behavior of the NamespaceManager class for this feature.

## Implementation constraints
- Namespace is itself a text subclass, so the prefix test takes the namespace's text as the prefix and the reference as the value being tested. Writing the test with the namespace as the receiver of a text-prefix check on the reference reverses the membership direction and is not allowed.
- Do not rely on Python's sequence-iteration fallback for `in`. Without a membership hook, `in` calls item access with index 0. On ClosedNamespace, term resolution raises KeyError, which is not IndexError, so the fallback fails. On _RDFNamespace, term resolution calls string methods on the integer and raises AttributeError. Implementing the hook avoids both failures.
- The closed-namespace check must use the term model's node-type-aware equality. Converting either side to text is not allowed, because it makes plain strings and Literals match.
- Add no imports and no third-party dependencies.
- Keep term-resolution behavior unchanged. Any refactor must return the same results and raise the same errors.

## Error handling
- For any URI reference, `in` must return True or False on every namespace type. It must not raise KeyError or AttributeError.
- Unknown term names keep their existing errors: KeyError from closed-namespace term resolution, and AttributeError from attribute access.
- Behavior for non-string operands on Namespace is not part of the contract.

## Compatibility
- Namespace membership changes from a substring test to a prefix test. This is intended; repository code does not depend on the old substring behavior.
- `in` on ClosedNamespace objects previously raised and now returns a bool. This is intended.
- Public names exported from the namespace module do not change.

## Validation
- Tests must not build term URIs by concatenating a namespace with a string. Use attribute or item term access, or full URIRef values.
- Assert results with assertTrue and assertFalse, with a message, matching the existing style of the reference tests.
- Keep new lines within the 85-column max-line-length in the repository's .pep8 file where practical.

## Behavioral acceptance criteria
- Prefix, positive: URIRef http://example.org/thing against the Namespace http://example.org/ is True.
- Prefix, direction: http://example.org against http://example.org/ is False. A URI that contains the namespace text but does not begin with it is False.
- Prefix, self: a reference equal to the namespace's text is True.
- SH: a URI beginning with the SHACL namespace text (sh:example) returns True.
- RDFS: rdfs:label returns True. rdfs:example returns False, because it shares the RDF Schema base but is not a defined term.
- RDF: rdf:type returns True.
- Container membership property (for example the rdf `_1` form) returns False.
- Non-URIRef operands: a plain string or a Literal whose text equals rdfs:label returns False in RDFS.
- Existing attribute and item term access produces the same results as before.

## Test requirements
- Add unit tests to the existing namespace test module covering:
  - Namespace prefix: a positive case with a full URI beginning with the namespace text, and a negative case with a proper prefix of the namespace text. The negative case is required because it detects a reversed direction.
  - RDFS closed: a positive case for a defined term, and a negative case for a term that shares the base but is not defined.
  - RDF closed: a positive case for a defined term.
- Recommended, not required: non-URIRef negative cases (plain string, Literal) for RDFS. Container-property assertions, if present, must expect False.
- Tests may live in the existing NamespacePrefixTest class or in a new class in the same module.
- The Namespace docstring doctests and all existing namespace tests must still pass.
