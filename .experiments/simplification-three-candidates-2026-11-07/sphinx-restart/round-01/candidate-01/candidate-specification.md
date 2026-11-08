## Goals
Add Python-domain support for documenting type aliases and linking to them through existing Python cross-references. Follow the domain’s object registration and rendering conventions.

## Workflows
Support aliases at module level and inside a class context. Class context determines the alias’s qualified name but does not make the directive a container for nested object declarations. Accept an optional canonical expression: render it after the alias name, separated by “=”, and parse it as a Python annotation so referenced types use normal cross-reference resolution. Without it, still document and index the alias. Permit an optional description body, while keeping PyObject’s prohibition on nested object contents.

## Data model
Represent aliases as Python-domain objects with object type name “type”, public label “type alias”, and cross-reference types “type” and “obj”. Register each qualified name as the primary object. When canonical is supplied, register it as an alias target for that object.

## API contracts
Register the py:type directive and py:type role. The directive inherits PyObject’s shared options, including canonical, but adds neither the variable-specific type nor value option. Its signature prefix is “type”. With canonical, render “=” after the alias name and retain the annotation parser’s structure and cross-reference nodes. Resolve the role through normal Python-domain object lookup and cross-reference handling.

Use the inherited Python-object signature and target behavior for module and class context, canonical target registration, indexing, and non-nestable contents. A class-scoped alias remains supported even though the directive does not allow nested object contents.

Index text follows Python module-name configuration. A module-level alias is “Alias (in module example)” when a module is set, otherwise just “Alias”. A nested alias is “Alias (type alias in Class)” when module names are disabled. If module names are enabled and a module is set, use “Alias (type alias in example.Class)”.

## Module architecture
Implement the alias as a PyObject specialization in `sphinx/domains/python/__init__.py`. Register its object type, directive, and role in the Python domain. Reuse the existing annotation parser and cross-reference machinery; do not introduce separate rendering or resolution paths or add dependencies.

## Naming
Use “type” for the object type, directive, and role; “canonical” for the optional alias expression; and “type alias” for the public object label and nested index text.

## Documentation
Document the directive and role in the Python-domain documentation. Explain that canonical is optional, describes the represented type, and appears in the signature. Document the optional description body and role behavior. Add a feature bullet for py:type and its role under the current release’s Features added section in CHANGES.rst.

## Behavioral acceptance criteria
- Module-level and class-scoped aliases receive correct qualified names and cross-references.
- Aliases work without canonical; when supplied, the expression follows the alias name after “=” and is parsed into resolvable annotation nodes.
- The signature begins with “type”; the public label is “type alias”; the object, directive, and role names are “type”.
- The role links to a declared module-level or nested alias target.
- Index text matches the module-level and nested forms above, including module prefixes only when module names are enabled and a module is set.
- Shared PyObject options and behavior remain available, including descriptions and the prohibition on nested object contents.

## Test requirements
Add focused automated regression tests following Python-domain conventions. Cover canonical present and absent, annotation cross-references, module-level and class-scoped qualified names, signature prefix and separator, object type and registration, and module-level and nested index text with module names enabled and disabled. Exercise py:type role parsing and resolution with an inline reference that links to the declared alias target; checking registration or lookup alone is insufficient. Verify that a class-scoped alias works while the directive still rejects nested object contents. Documentation examples do not replace these tests.
