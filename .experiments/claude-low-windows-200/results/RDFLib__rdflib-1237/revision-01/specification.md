# Namespace membership with `in` (Namespace and closed namespaces)

## Goals
- Let callers test whether a URI reference belongs to a namespace object with the `in` operator, and get a boolean back, for every namespace type defined in the namespace module: open prefix namespaces (Namespace) and closed term namespaces (ClosedNamespace and its subclass _RDFNamespace).
- Replace manual string-prefix checks with a membership test whose semantics match each namespace type.

## Scope
- In scope: the Namespace class, the ClosedNamespace class, the _RDFNamespace subclass, and the module-level instances of these classes (for example SH, RDF, RDFS, FOAF, SKOS, PROV, GEO).
- Not required: membership on NamespaceManager. The originating request lists it only as a possible extension. If an implementer adds it, the hook must be spelled correctly and must actually be invoked by `in`.
- Out of scope: changes to term generation, graph, store, parser, or serializer code.

## Assumptions
- A URI reference is a string subclass, so membership compares string values.
- A ClosedNamespace is constructed once from a base URI and a fixed list of term names, and each term maps to one full URI.

## Terminology
- Prefix membership: a URI belongs to a Namespace when its string value begins with the namespace's string value.
- Closed membership: a URI belongs to a ClosedNamespace only when it equals one of the full URIs stored for that namespace's defined terms. Sharing the base URI is not enough.
- Closed namespace: ClosedNamespace and any subclass, including _RDFNamespace.
- Container membership property: a URI of the form base URI, then an underscore, then a positive integer. _RDFNamespace resolves these dynamically during term resolution, but they are not stored as defined terms.

## Workflows
- Evaluating `in` with a namespace on the right-hand side:
  1. If the right-hand side is a Namespace, return True when the reference's string value begins with the namespace's string value, otherwise False.
  2. If the right-hand side is a ClosedNamespace (including the RDF namespace), return True when the reference equals one of the stored term URIs, otherwise False.
  3. Do not satisfy either case through sequence iteration over item access or through term resolution. Those paths raise errors for names that are not defined terms.
- The result is always a boolean.

## Data model
- Namespace: no new state. Its string value is the prefix.
- ClosedNamespace: the stored mapping from term name to full URI is the only source for membership. Membership is decided by comparing the reference against those stored URI values.
- Container membership properties (for example the rdf container-property form) are not stored and are therefore not members. Membership for them is False.

## API contracts
- Namespace membership: the `in` operator invokes Python's standard membership hook (`__contains__`) with one argument, named `ref`, and returns a bool. Semantics are prefix membership as described in Workflows.
- ClosedNamespace membership: same hook name and parameter name, returns a bool, and uses closed membership. _RDFNamespace inherits this behavior without overriding it.
- Namespace instances keep their existing type. The existing type check on SH must still pass.
- Attribute access and item access results, and the error types they raise for unknown term names, do not change.

## Module architecture
- Implement all membership logic in the namespace module, on the classes that already own term resolution.
- Place the closed-namespace hook on ClosedNamespace so _RDFNamespace inherits it. Do not duplicate it on the subclass.
- Do not change the behavior of the NamespaceManager class for this feature.

## Implementation constraints
- Do not rely on Python's sequence-iteration fallback for `in`. Without a membership hook, `in` calls item access with index 0. On ClosedNamespace, term resolution raises KeyError for index 0, and KeyError is not IndexError, so the fallback fails. On _RDFNamespace, term resolution calls string methods on the integer and raises AttributeError. Implementing the hook on ClosedNamespace avoids both failures.
- Add no imports and no third-party dependencies.
- Keep term-resolution behavior unchanged. Any refactor must return the same results and raise the same errors.

## Error handling
- For any valid URI reference, `in` must return True or False on every namespace type. It must not raise KeyError or AttributeError.
- Unknown term names keep their existing errors: KeyError from closed-namespace term resolution, and AttributeError from attribute access.
- Behavior for non-string inputs is not part of the contract.

## Compatibility
- Namespace membership changes from a substring test to a prefix test. This is intended. Repository code does not depend on the old substring behavior.
- `in` on ClosedNamespace objects previously raised. It now returns a bool. This is intended.
- Public names exported from the namespace module do not change.

## Behavioral acceptance criteria
- SH: a URI beginning with the SHACL namespace string (sh:example) is a member, so `in` returns True.
- Prefix rule: a URI that contains the Namespace string but does not begin with it returns False.
- RDFS: the rdfs:label URI returns True. The rdfs:example URI returns False, because it shares the RDF Schema base but is not a defined term. Both must return a bool without raising.
- RDF: the rdf:type URI returns True.
- Container membership property (for example the rdf container form _1) returns False under closed membership.
- Existing attribute and item term access produces the same results as before.

## Test requirements
- Add unit tests to the existing namespace test module. They must cover prefix membership for Namespace (positive and negative cases), closed membership for RDFS (a positive case and an out-of-namespace negative case), and closed membership for RDF (a positive case).
- The Namespace class docstring doctests must still pass.
- All existing namespace tests must still pass.
