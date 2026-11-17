# Namespace membership with `in` (Namespace and closed namespaces)

## Goals
- Let callers test with `in` whether a URI reference belongs to a namespace, returning a boolean, for Namespace (open prefix) and ClosedNamespace (closed term) types, including _RDFNamespace.
- Replace manual string-prefix checks with this membership test.

## Scope
- In scope: Namespace, ClosedNamespace, _RDFNamespace, and module-level instances (SH, RDF, RDFS, FOAF, SKOS, PROV, GEO).
- In scope as a secondary change: the closed-namespace IPython key-completion hook should list completions from the namespace's URI text (the directory listing of the URI string) rather than the object itself. This does not affect membership.
- Not required: membership on NamespaceManager. The reference has a misspelled hook that `in` never calls. Implementers may skip it; if added, the hook name must be spelled correctly and dispatched by `in`.
- Out of scope: term generation, graph, store, parser, and serializer code.

## Assumptions
- A URI reference is normally a URIRef.
- Namespace membership compares text: the reference's text must begin with the namespace's text.
- Closed membership uses node-type-aware equality. A value is a member only if it is a URIRef equal to a stored term URI. Plain strings and Literals with identical text are not members.
- A ClosedNamespace is built once from a base URI and a fixed term list; each term maps to one full URI. ClosedNamespace does not support `+`; term URIs come from the namespace's own term access.

## Terminology
- Prefix membership: the reference belongs to a Namespace when its text begins with the namespace's text. The reference is the subject; the namespace text is the prefix. Reversing these roles is incorrect.
- Closed membership: the reference belongs to a ClosedNamespace only when it is a URIRef equal (same node type and text) to a full URI stored for a defined term. Sharing the base URI is not enough.
- Node-type-aware equality: rdflib node equality, which returns False when node types differ even if text matches.
- Closed namespace: ClosedNamespace and any subclass, including _RDFNamespace.
- Container membership property: base URI, underscore, positive integer (for example rdf _1). _RDFNamespace resolves these during term resolution, but they are not stored defined terms, so they are not members under closed membership. This is the reference behavior.

## Workflows
- When `in` has a namespace on the right-hand side:
  1. Namespace: return True when the reference's text begins with the namespace's text, else False. Pseudocode (describes operand roles only):
     input: ref (left operand), ns (Namespace; its value is the prefix)
     result = ref begins with prefix(ns)
     return result as a bool
     Apply the prefix test to the reference as given; do not convert it to text first.
  2. ClosedNamespace (including RDF): return True when the reference equals, under node-type-aware equality, one of the stored term URIs, else False. Do not convert either side to text.
  3. Do not satisfy either case through sequence iteration over item access or through term resolution; both raise errors for non-defined names.
- The result is always a boolean.

## Data model
- Namespace: no new state; its text is the prefix.
- ClosedNamespace: the stored mapping from term name to full URI is the only membership source. Compare the reference against stored URI values using node-type-aware equality.
- Container membership properties are not stored and are not members (False).

## API contracts
- Namespace membership: `in` invokes the membership hook `__contains__` with one argument, ref, and the hook returns a bool. A reference equal to the namespace text is True. A reference that is a proper prefix of the namespace text (for example the namespace text without its trailing slash) is False.
- ClosedNamespace membership: same hook name and argument, returning a bool, with closed semantics. _RDFNamespace inherits it without override.
- A plain string or Literal whose text equals a term URI returns False on a ClosedNamespace.
- Namespace instances keep their existing type; the existing type check on SH must still pass.
- Attribute and item access results, and the error types they raise for unknown term names, do not change.

## Module architecture
- Implement all membership logic in the namespace module, on classes that already own term resolution.
- Put the prefix hook on Namespace and the closed hook on ClosedNamespace, so _RDFNamespace inherits it. Do not duplicate it on the subclass.
- Do not change NamespaceManager behavior.

## Implementation constraints
- Because Namespace is a text subclass, the prefix test must treat the namespace text as the prefix argument and the reference as the tested value. Making the namespace the receiver of a prefix check on the reference reverses direction and is not allowed.
- Do not rely on Python's sequence-iteration fallback for `in`. Without a membership hook, `in` calls item access with index 0. On ClosedNamespace this raises KeyError (not IndexError, so the fallback fails); on _RDFNamespace it raises AttributeError. The hook avoids both.
- Closed checks use node-type-aware equality. Converting either side to text is not allowed.
- Add no imports or third-party dependencies.
- Term-resolution behavior is unchanged. Any refactor must return the same results and raise the same errors.

## Error handling
- For any URI reference, `in` returns True or False on every namespace type; it must not raise KeyError or AttributeError.
- Unknown term names keep their existing errors: KeyError from closed term resolution, AttributeError from attribute access.
- Non-string operands on Namespace are outside the contract.

## Compatibility
- Namespace membership changes from substring to prefix test. This is intended; repository code does not depend on substring behavior.
- `in` on ClosedNamespace previously raised; it now returns a bool. This is intended.
- Public names exported from the namespace module do not change.

## Validation
- Build term URIs with attribute or item term access, or full URIRef values, never by concatenating with `+`.
- Assert with assertTrue and assertFalse, with a message, matching the reference test style.
- Keep new lines within the 85-column limit in the repository's .pep8 file where practical.

## Behavioral acceptance criteria
- Prefix, positive: URIRef http://example.org/thing against namespace http://example.org/ is True.
- Prefix, direction: http://example.org against http://example.org/ is False. A URI that contains the namespace text but does not begin with it is False.
- Prefix, self: a reference equal to the namespace text is True.
- SH: a URI beginning with the SHACL namespace text (sh:example) is True.
- RDFS: rdfs:label is True; rdfs:example is False (shares the base but is not defined). Both return a bool without raising.
- RDF: rdf:type is True.
- Container property (rdf _1) is False under closed membership.
- On RDFS, a plain string or Literal whose text equals rdfs:label is False.
- Existing attribute and item access results are unchanged.

## Test requirements
- Add unit tests to the existing namespace test module, covering:
  - Namespace prefix: a positive case (full URI beginning with the namespace text) and a negative case (a proper prefix of the namespace text; required, because it detects reversed direction);
  - RDFS closed membership: a positive defined term and a negative term sharing the base but not defined;
  - RDF closed membership: a positive defined term.
- Recommended: non-URIRef negatives (plain string and Literal with a defined term's text) for RDFS.
- Optional container-property assertion; if present, expect False.
- Tests may go in NamespacePrefixTest or a new class in the same module.
- Namespace docstring doctests and all existing namespace tests must still pass.
