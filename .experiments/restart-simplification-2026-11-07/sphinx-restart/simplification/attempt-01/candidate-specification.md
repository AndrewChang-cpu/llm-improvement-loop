## Goals
Add type-alias documentation and cross-references to the Python domain, following its existing object conventions.

## Workflows
Aliases may be declared at module level or in a class context. A class-scoped alias does not make its directive a container for nested objects. The optional canonical expression describes the represented type; when supplied, render it after the alias name with an equals sign and parse it as a Python annotation so its references resolve normally. Aliases without canonical expressions remain documentable and indexable. The directive accepts a description body but retains PyObject’s restriction against nested object contents.

## Data model
Use `type` as the Python-domain object type name and directive and role name. Its public label is `type alias`, and its cross-reference types are `type` and `obj`. Register the qualified alias name as the primary object. If canonical is present, also register it as an aliased target for that object.

## API contracts
Provide the py:type directive and py:type cross-reference role. The directive inherits PyObject options, including canonical, but must not add PyVariable’s type or value options. Its signature starts with `type`; when canonical is supplied, show `=` and retain the annotation parser’s nodes. The role resolves aliases through normal Python-domain object lookup and cross-reference resolution.

Use the existing index conventions: a module-level alias is “Alias (in module example)” when a module is set, otherwise just “Alias”. A nested alias is “Alias (type alias in Class)” when module names are disabled or no module is set. When module names are enabled and a module is set, include it before the class: “Alias (type alias in example.Class)”.

## Module architecture
Implement the alias as a PyObject specialization in the existing Python-domain component. Reuse inherited signature, target, module and class context, indexing, canonical alias registration, and non-nestable behavior. Use the existing annotation parser and Python-domain cross-reference machinery; do not add a separate rendering or resolution path.

## Documentation
Document the directive and role in the Python-domain documentation. Explain that canonical is optional, describes the represented type, and appears in the signature; also describe the optional body and alias role. Add a feature bullet naming the directive and role under the current release’s Features added section in CHANGES.rst.

## Behavioral acceptance criteria
- Module-level and class-scoped aliases receive correct qualified names and resolve through Python-domain cross-references.
- Missing canonical is valid; supplied canonical renders with `=` and parses into resolvable annotation nodes.
- Index text follows the stated module-level and nested forms and module-name conditions.
- The public label is `type alias`; the object type, directive, and role are named `type`.
- Shared PyObject options and behavior remain available, including description bodies and the prohibition on nested object contents.

## Test requirements
Add focused regression tests using existing Python-domain conventions. Cover aliases with and without canonical, annotation references, module-level and class-scoped names, signature prefix and separator, index forms with module names enabled and disabled, object-type registration and label, and role resolution. Include an inline py:type reference to a declared alias and verify it links to the alias target; registration or domain lookup alone does not test role parsing and resolution. Verify that class-scoped declarations work while nested object contents remain disallowed.
