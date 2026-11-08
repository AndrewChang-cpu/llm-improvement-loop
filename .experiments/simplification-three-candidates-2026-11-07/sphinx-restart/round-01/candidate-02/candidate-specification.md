## Goals
Add Python-domain support for documenting and cross-referencing type aliases, following existing Python object conventions.

## Workflows
Support aliases at module level and in class context. A class-scoped alias is nested by context; the directive itself must not allow nested object contents. The optional canonical expression describes the represented type: when supplied, show it after the alias name with an equals sign and parse it as a Python annotation so its referenced types use normal cross-referencing. Without it, the alias remains documentable and indexable. Allow a description body.

## Data model
Represent aliases as Python-domain objects of type “type”, with public label “type alias” and cross-reference types “type” and “obj”. Register the qualified name as the primary object and, when canonical is supplied, register it as an alias target for that object.

## API contracts
Provide the py:type directive and py:type role. Inherit shared PyObject options, including optional canonical, and do not add the variable-specific type or value options. Prefix signatures with “type”. Parse canonical using the existing annotation parser and retain its annotation structure and cross-reference nodes. Resolve role references using normal Python-domain object lookup and cross-reference resolution.

Index text must follow Python-domain module-name settings: for a module-level alias, use “Alias (in module example)” when a module is set, otherwise “Alias”. For a nested alias with module names disabled, use “Alias (type alias in Class)”; when enabled and a module is set, use “Alias (type alias in example.Class)”.

## Module architecture
Implement the alias as a PyObject specialization in the existing Python-domain component and register its object type, directive, and role there. Reuse inherited Python-object signature, target, context, indexing, canonical alias registration, and non-nestable behavior, plus existing annotation parsing and Python cross-reference machinery. Do not create a separate rendering or reference path.

## Naming
Use “type” for the object type, directive, and role; “canonical” for the optional expression; and “type alias” for the public label and nested index text.

## Documentation
Document py:type and its role in the Python-domain documentation. Explain that canonical is optional, describes the represented type, and appears in the signature; note description-body support and describe alias references. Add a feature bullet naming the directive and role under the current release’s Features added in CHANGES.rst.

## Behavioral acceptance criteria
- Module-level and class-scoped aliases have correct qualified names and Python-domain references.
- Class context supports nested aliases while the directive still rejects nested object contents.
- Omitting canonical is valid and leaves the alias documentable, indexable, and referenceable.
- A supplied canonical expression follows the name after “=” and becomes annotation nodes with resolvable type references.
- Index entries match the specified module-level and nested forms, including the module prefix only when module names are enabled and a module is set.
- The object type and directive and role are named “type”; its public label is “type alias”.
- Shared PyObject behavior and options remain available, and py:type references resolve to the declared alias target.

## Test requirements
Add focused tests following existing Python-domain conventions. Cover aliases with and without canonical; parsed annotation cross-references; module-level and class-scoped names; signature prefix and separator; module-level and nested index text with module names enabled and disabled; object type, label, and registration; and py:type parsing and resolution to the alias target. Verify both the directive’s rejection of nested object contents and declaration of an alias inside a class. Exercise these behaviors in automated tests; documentation examples, registration checks, or domain lookup alone do not establish role resolution.
