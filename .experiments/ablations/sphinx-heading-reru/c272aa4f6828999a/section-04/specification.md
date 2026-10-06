### Goals
Add Python-domain support for documenting type aliases and linking to them, including aliases declared at module and nested scopes.

### Scope
Support the `py:type` directive and `py:type` cross-reference role. The alias expression is optional and is supplied with the `canonical` option. Do not treat the variable directive’s `value` option as the alias-expression contract.

### Terminology
A documented alias is stored in the Python domain with object type key `type`; its human-readable object-type label is `type alias`. The inherited `canonical` option both displays the optional alias expression and registers its value as an aliased Python-domain target.

### Workflows
A document can declare an alias with or without an expression. Readers can link to an alias with the `py:type` role or generic Python-domain object lookup. Expression components are parsed so type names can resolve through the existing Python cross-reference system. These workflows apply to module-level aliases and aliases declared within a containing class. An alias can occur inside a class, but it does not establish a further nested namespace for its own body.

### API contracts
Register `py:type` as a directive and `py:type` as a cross-reference role in the Python domain. The directive inherits `PyObject` options, including the optional `canonical` option. Its signature displays the `type` marker before the alias name. When `canonical` is present, display it after an equals sign and parse it with the existing Python annotation parser so component type names become Python-domain cross-references. When absent, display only the marker and alias name.

Retain inherited description-body support, but do not enable nested contents or make the alias a nestable object. The containing class supplies the context for a nested alias.

For index entries, a qualified alias name uses the final component as the alias name and identifies the preceding class context with the wording “alias (type alias in containing class)”. Include the module in that class context when a module is known and `add_module_names` is enabled. For a module-level alias, use “alias (in module module-name)” when a module is known, and the bare alias name otherwise.

Register the Python object type under the key `type`, with the display label `type alias` and the existing `type` and `obj` cross-reference roles. This alignment must allow both `py:type` references and generic object references to find the stored alias.

### Module architecture
Implement the directive in the existing Python-domain component. Register its object type, directive, and role through the Python domain’s established object lookup and cross-reference mechanisms.

### Implementation constraints
Use `PyObject` behavior for signature context, target registration, canonical-name registration, indexing, and class/module context. Keep the alias non-nestable by retaining the inherited `allow_nesting` behavior. Use the existing Python annotation parser for the optional alias expression; do not render that expression as plain text or route it through variable-value rendering.

### Documentation
Document the directive, role, and optional `canonical` expression in the Python-domain documentation. Do not describe `value` as the alias-expression option. Add the project-required `CHANGES.rst` note for this nontrivial feature.

### Behavioral acceptance criteria
The directive works for module-level and class-nested aliases, with and without an expression. An expression renders with the `type` marker and equals sign, and its type names participate in Python cross-reference resolution. The `py:type` role and generic object lookup resolve aliases. Stored alias entries use object type key `type`, while the object-type display label remains `type alias`. The alias supports inherited description-body behavior but does not create a nested namespace. Nested and module-level index entries follow the wording and module-name rules specified above.

### Test requirements
Add focused regression coverage for aliases with and without `canonical`, parsed and cross-referenceable expression components, direct `py:type` references, generic object references, stored object type keys, module-level and class-nested aliases, nested index wording, and module-qualified index behavior. Preserve existing Python-domain cross-reference behavior.
