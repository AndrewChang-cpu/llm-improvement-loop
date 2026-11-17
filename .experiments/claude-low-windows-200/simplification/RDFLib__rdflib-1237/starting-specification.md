# Namespace membership with `in` (Namespace and closed namespaces)

## Goals
- Let callers test whether a URI reference belongs to a namespace object with the `in` operator and receive a boolean, for the namespace types in the namespace module: open prefix namespaces (Namespace) and closed term namespaces (ClosedNamespace and its subclass _RDFNamespace).
- Replace manual string-prefix checks with a membership test whose semantics match each namespace type.

## Scope
- In scope: the Namespace class, the ClosedNamespace class, the _RDFNamespace subclass, and the module-level instances of these classes (for example SH, RDF, RDFS, FOAF, SKOS, PROV, GEO).
- In scope as a secondary change: the closed-namespace IPython key-completion hook. The reference changes it so that it lists completions from the namespace's URI text (the directory listing of the URI string) rather than from the object itself. This change does not affect membership results. Implementers should make it so the result matches the reference.
- Not required: membership on NamespaceManager. The reference contains a misspelled, non-dispatched attempt at such a hook that Python's `in` operator never calls, so it has no effective behavior. Implementers need not replicate it. If an implementer adds NamespaceManager membership, the hook name must be spelled correctly and must actually be dispatched by `in`.
- Out of scope: term generation, graph, store, parser, and serializer code.

## Assumptions
- A URI reference is normally a URIRef.
- Prefix membership on Namespace compares text: the reference's text must begin with the namespace's text.
- Closed membership compares RDF node values with the term model's node-type-aware equality. A value is a member only when it is a URIRef whose text equals a stored term URI. A plain string or a Literal with identical text is not a member.
- A ClosedNamespace is constructed once from a base URI and a fixed list of term names, and each term maps to one full URI. ClosedNamespace objects do not support string concatenation; term URIs are obtained through the namespace's own term access.

## Terminology
- Prefix membership: a URI reference belongs to a Namespace when the reference's text begins with the namespace's text. The reference is the subject being tested. The namespace's text is the prefix. The roles are not interchangeable: asking whether the namespace's text begins with the reference's text (that is, whether the reference is a prefix of the namespace) is a different and incorrect test.
- Closed membership: a reference belongs to a ClosedNamespace only when it is a URIRef that equals (same node type and same text) one of the full URIs stored for that namespace's defined terms. Sharing the base URI is not enough. A plain string or Literal with the same text is not enough.
- Node-type-aware equality: rdflib's node equality, which returns False when the two operands have different node types, even if their text matches.
- Closed namespace: ClosedNamespace and any subclass, including _RDFNamespace.
- Container membership property: a URI of the form base URI, then an underscore, then a positive integer. _RDFNamespace resolves these during term resolution, but they are not stored as defined terms, so they are not members under closed membership. This result is the reference behavior.

## Workflows
- Evaluating `in` with a namespace on the right-hand side:
  1. If the right-hand side is a Namespace, return True when the reference's text begins with the namespace's text, otherwise False. Use the following pseudocode (not code; it describes the operand roles only):
     PSEUDOCODE, Namespace membership:
       input: ref (left operand), ns (the Namespace, whose value is the prefix)
       result = ref begins with prefix(ns)
       return result as a bool
     Apply the prefix test to the reference as given; do not convert the reference to text first. Do not reverse the roles of reference and prefix.
  2. If the right-hand side is a ClosedNamespace (including the RDF namespace), return True when the reference equals, under node-type-aware equality, one of the stored term URIs, otherwise False. Do not convert the reference or the stored values to text before comparing.
  3. Do not satisfy either case through sequence iteration over item access, or through term resolution. Those paths raise errors for names that are not defined terms.
- The result is always a boolean.

## Data model
- Namespace: no new state. Its text is the prefix.
- ClosedNamespace: the stored mapping from term name to full URI is the only source for membership. Membership is decided by comparing the reference against the stored URI values using node-type-aware equality.
- Container membership properties (for example the rdf container-property form) are not stored and are therefore not members. Membership for them is False.

## API contracts
- Namespace membership: the `in` operator invokes Python's membership hook named `__contains__` with a single argument named ref, and the hook returns a bool. The argument ref is the subject; the namespace's text is the prefix, as described in Terminology and Workflows. Results: a reference equal to the namespace's text is True (it begins with itself); a reference that is a proper prefix of the namespace's text (for example the namespace text without its trailing slash) is False.
- ClosedNamespace membership: the same hook name and argument name, returning a bool, with closed membership semantics. _RDFNamespace inherits this behavior without overriding it.
- For a ClosedNamespace, a plain string or a Literal whose text equals a term URI returns False.
- Namespace instances keep their existing type. The existing type check on SH must still pass.
- Attribute access and item access results, and the error types they raise for unknown term names, do not change.

## Module architecture
- Implement all membership logic in the namespace module, on the classes that already own term resolution.
- Place the Namespace prefix hook on Namespace and the closed-namespace hook on ClosedNamespace. Place the closed-namespace hook on ClosedNamespace so _RDFNamespace inherits it. Do not duplicate it on the subclass.
- Do not change the behavior of the NamespaceManager class for this feature.

## Implementation constraints
- Because Namespace is itself a text subclass, the prefix test must take the namespace's text as the prefix argument and the reference as the value being tested. Writing the test with the namespace as the receiver of a text-prefix check on the reference reverses the membership direction and is not allowed.
- Do not rely on Python's sequence-iteration fallback for `in`. Without a membership hook, `in` calls item access with index 0. On ClosedNamespace, term resolution raises KeyError for index 0, and KeyError is not IndexError, so the fallback fails. On _RDFNamespace, term resolution calls string methods on the integer and raises AttributeError. Implementing the hook on ClosedNamespace avoids both failures.
- The closed-namespace check must use the same node-type-aware equality as the rest of the term model. Converting either side to text before comparing is not allowed, because it makes plain strings and Literals match.
- Add no imports and no third-party dependencies.
- Keep term-resolution behavior unchanged. Any refactor must return the same results and raise the same errors.

## Error handling
- For any URI reference, `in` must return True or False on every namespace type. It must not raise KeyError or AttributeError.
- Unknown term names keep their existing errors: KeyError from closed-namespace term resolution, and AttributeError from attribute access.
- Behavior for non-string operands on Namespace is not part of the contract.

## Compatibility
- Namespace membership changes from a substring test to a prefix test. This is intended. Repository code does not depend on the old substring behavior.
- `in` on ClosedNamespace objects previously raised. It now returns a bool. This is intended.
- Public names exported from the namespace module do not change.

## Validation
- Membership tests must reach their assertions. ClosedNamespace objects do not support the `+` operator, so tests must not build term URIs by concatenating a namespace with a string. Use the namespace's attribute or item term access, or full URIRef values.
- Assert membership results with the unittest truth assertions (assertTrue and assertFalse), with a message, matching the existing style of the reference tests.
- Keep new lines within the 85-column max-line-length in the repository's .pep8 file where practical.

## Behavioral acceptance criteria
- Prefix, positive: a URIRef whose text begins with a Namespace's text (for example the reference http://example.org/thing against the namespace http://example.org/) is a member (True).
- Prefix, direction: a URIRef that is a proper prefix of the namespace's text (http://example.org against http://example.org/) is not a member (False). A URIRef that contains the namespace text but does not begin with it is not a member (False).
- Prefix, self: a reference equal to the namespace's text is a member (True).
- SH: a URI beginning with the SHACL namespace text (sh:example) returns True.
- RDFS: rdfs:label returns True. rdfs:example returns False, because it shares the RDF Schema base but is not a defined term. Both return a bool without raising.
- RDF: rdf:type returns True.
- Container membership property (for example rdf container form _1) returns False under closed membership.
- Non-URIRef operands on a closed namespace: a plain string whose text equals rdfs:label returns False in RDFS. A Literal whose text equals rdfs:label returns False in RDFS.
- Existing attribute and item term access produces the same results as before.

## Test requirements
- Add unit tests to the existing namespace test module. They must cover:
  - prefix membership for Namespace: a positive case with a full URI beginning with the namespace text, and a negative case with a URI that is a proper prefix of the namespace text (this negative case is required, because it detects a reversed direction);
  - closed membership for RDFS: a positive case for a defined term, and a negative case for a term that shares the RDF Schema base but is not defined;
  - closed membership for RDF: a positive case for a defined term.
- Recommended, not required: add non-URIRef negative cases (plain string and Literal with a defined term's text) for RDFS.
- Tests are not required to assert the container-property result. If they do, the result must be False.
- The new tests may live in the existing NamespacePrefixTest class or in a new test class in the same module.
- The Namespace class docstring doctests must still pass.
- All existing namespace tests must still pass.
