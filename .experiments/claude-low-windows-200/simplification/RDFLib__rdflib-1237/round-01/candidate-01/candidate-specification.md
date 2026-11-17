# Namespace membership with `in` (Namespace and closed namespaces)

## Goals
- Let callers test with `in` whether a URI reference belongs to a namespace object, returning a boolean, for open prefix namespaces (Namespace) and closed term namespaces (ClosedNamespace and its subclass _RDFNamespace).
- Replace manual string-prefix checks with a membership test whose semantics match each namespace type.

## Scope
- In scope: the Namespace class, the ClosedNamespace class, _RDFNamespace, and module-level instances of these classes (for example SH, RDF, RDFS, FOAF, SKOS, PROV, GEO).
- In scope as a secondary change: the closed-namespace IPython key-completion hook should list completions from the namespace's URI text rather than from the object itself, matching the reference. This does not affect membership.
- Not required: membership on NamespaceManager. The reference has a misspelled hook that `in` never calls. Implementers need not add it. If they do, the hook name must be spelled correctly and must actually be dispatched by `in`.
- Out of scope: term generation, graph, store, parser, and serializer code.

## Assumptions
- A URI reference is normally a URIRef.
- Prefix membership compares text: the reference's text must begin with the namespace's text.
- Closed membership compares RDF nodes with the term model's node-type-aware equality. A value is a member only when it is a URIRef equal to a stored term URI.
- A ClosedNamespace is built once from a base URI and a fixed list of term names, and each term maps to one full URI. ClosedNamespace objects do not support `+`; term URIs come from the namespace's own term access.

## Terminology
- Prefix membership: a reference belongs to a Namespace when the reference's text begins with the namespace's text. The reference is the subject; the namespace's text is the prefix. Testing whether the namespace's text begins with the reference's text is a different, incorrect test.
- Closed membership: a reference belongs to a ClosedNamespace only when it is a URIRef whose text equals one of the full URIs stored for that namespace's defined terms. Sharing the base URI is not enough, and a plain string or Literal with the same text is not enough.
- Node-type-aware equality: rdflib's node equality, which returns False when the operands have different node types even if their text matches.
- Closed namespace: ClosedNamespace and any subclass, including _RDFNamespace.
- Container membership property: a URI of the form base URI, underscore, positive integer (for example rdf _1). _RDFNamespace resolves these during term resolution, but they are not stored as defined terms, so they are not members.

## Workflows
- When a Namespace is the right-hand operand of `in`, return True if the reference's text begins with the namespace's text, otherwise False. Apply the prefix test to the reference as given; do not convert it to text first, and do not reverse the roles.
- When a ClosedNamespace (including the RDF namespace) is the right-hand operand, return True if the reference equals, under node-type-aware equality, one of the stored term URIs, otherwise False. Do not convert the reference or stored values to text.
- Do not satisfy either case through sequence iteration over item access, or through term resolution. Those paths raise errors for names that are not defined terms.
- The result is always a boolean.

## Data model
- Namespace: no new state. Its text is the prefix.
- ClosedNamespace: the stored mapping from term name to full URI is the only source for membership.
- Container membership properties are not stored, so membership for them is False.

## API contracts
- Both classes implement the membership hook named `__contains__`, taking one argument named ref and returning a bool. The `in` operator invokes it.
- Namespace: a reference equal to the namespace's text is True. A reference that is a proper prefix of the namespace's text (the text without its trailing slash, for example) is False.
- ClosedNamespace: closed membership semantics. _RDFNamespace inherits this without overriding it.
- A plain string or Literal whose text equals a term URI returns False on a ClosedNamespace.
- Namespace instances keep their existing type. The existing type check on SH must still pass.
- Attribute and item access results, and the error types for unknown term names, do not change.

## Module architecture
- Implement all membership logic in the namespace module, on the classes that already own term resolution.
- Put the prefix hook on Namespace and the closed-namespace hook on ClosedNamespace, so _RDFNamespace inherits it without a duplicate.
- Do not change NamespaceManager behavior for this feature.

## Implementation constraints
- Because Namespace is a text subclass, the prefix test must use the namespace's text as the prefix and the reference as the tested value. Making the namespace the receiver of a text-prefix check on the reference reverses the direction and is not allowed.
- Do not rely on Python's sequence-iteration fallback for `in`. Without the hook, `in` calls item access with index 0: on ClosedNamespace this raises KeyError, which the fallback does not catch, and on _RDFNamespace it raises AttributeError. The hook avoids both.
- Closed membership must use the term model's node-type-aware equality. Converting either side to text is not allowed.
- Add no imports and no third-party dependencies.
- Term-resolution behavior is unchanged. Any refactor must return the same results and raise the same errors.

## Error handling
- For any URI reference, `in` returns True or False on every namespace type and never raises KeyError or AttributeError.
- Unknown term names keep their existing errors: KeyError from closed-namespace term resolution, AttributeError from attribute access.
- Non-string operands on Namespace are not part of the contract.

## Compatibility
- Namespace membership changes from a substring test to a prefix test. This is intended; repository code does not depend on the substring behavior.
- `in` on ClosedNamespace previously raised and now returns a bool. This is intended.
- Public names exported from the namespace module do not change.

## Validation
- Tests must not build term URIs by concatenating a namespace with a string. Use attribute or item term access, or full URIRef values.
- Assert results with assertTrue and assertFalse, with a message, matching the reference test style.
- Keep new lines within the 85-column limit in the repository's .pep8 file where practical.

## Behavioral acceptance criteria
- Prefix, positive: the URIRef http://example.org/thing is a member of the Namespace http://example.org/ (True).
- Prefix, direction: http://example.org is not a member of http://example.org/ (False). A URI that contains the namespace text without beginning with it is not a member (False).
- Prefix, self: a reference equal to the namespace's text is True.
- SH: a URI beginning with the SHACL namespace text returns True.
- RDFS: rdfs:label returns True. rdfs:example returns False, because it shares the RDF Schema base but is not a defined term.
- RDF: rdf:type returns True.
- Container membership property (for example rdf _1) returns False under closed membership.
- On RDFS, a plain string or Literal whose text equals rdfs:label returns False.
- Existing attribute and item term access produces the same results as before.

## Test requirements
- Add unit tests to the existing namespace test module, covering:
  - Namespace prefix membership: a positive case with a full URI beginning with the namespace text, and a negative case with a URI that is a proper prefix of the namespace text. The negative case is required because it detects a reversed direction.
  - RDFS closed membership: a positive case for a defined term and a negative case for an undefined term sharing the RDF Schema base.
  - RDF closed membership: a positive case for a defined term.
- Recommended, not required: non-URIRef negative cases (plain string and Literal) for RDFS.
- If the container-property result is asserted, it must be False.
- New tests may live in the existing NamespacePrefixTest class or a new class in the same module.
- The Namespace class docstring doctests and all existing namespace tests must still pass.
