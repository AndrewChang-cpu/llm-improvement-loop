### Goals
Add Python-domain support for documenting type aliases and linking to them, including aliases declared at module and nested scopes.

### Scope
Support the `py:type` directive and `py:type` cross-reference role. The alias expression is optional. Do not use the variable directive’s `value` option as the alias-expression contract.

### Terminology
A type alias is a Python-domain object with object type `type alias`. The directive’s optional `canonical` option supplies the displayed alias expression. The `py:type` role links to a documented alias.

### Workflows
A document can declare an alias with or without an expression. A reader can use the `py:type` role to link to the alias by its Python-domain name. Alias expressions can refer to types that should resolve through the existing Python cross-reference system. These workflows apply to module-level and nested aliases.

### Data model
Register each alias under its fully qualified Python-domain object name and the `type` object type. Preserve the standard Python-object handling of module and class context. Preserve the inherited `canonical` option’s Python-domain object handling as well as its use to display the alias expression.

### API contracts
The directive is `py:type`; the role is `py:type`. The directive inherits the common Python-object options and adds the optional `canonical` option. Its signature displays the `type` marker before the alias name. When `canonical` is present, display it after an equals sign and parse it with the existing Python annotation parser so component type names become Python-domain cross-references. When it is absent, display only the alias name and marker.

Index text distinguishes a nested alias from a module-level alias. For a nested alias, identify the containing class and the alias name; include the module in the class context when the existing `add_module_names` setting calls for it. For a module-level alias, use the existing module-qualified index form when a module is known, and the bare name when it is not.

### Module architecture
Implement the directive in the existing Python-domain component. Register its object type, directive, and role in the Python domain, using the domain’s established object lookup and cross-reference behavior.

### Implementation constraints
Use the common Python-object behavior for signature context, target registration, canonical-name registration, indexing, and nesting context. Use the existing Python annotation parser for the optional alias expression; do not render that expression as plain text or route it through variable-value rendering.

### Documentation
Document the directive, role, and optional `canonical` expression using prose. Do not document `value` as the alias-expression option.

### Behavioral acceptance criteria
The directive works for module-level and nested aliases, with and without an expression. An expression renders with the `type` marker and equals sign, and its type names participate in Python cross-reference resolution. The role resolves aliases through the Python domain. Nested index text identifies the containing class; module-level index text follows the existing module naming behavior.

### Test requirements
Add focused regression coverage for the directive with and without `canonical`, parsed and cross-referenceable expression components, the `py:type` role, module-level and nested aliases, and nested index text. Run the focused Python-domain checks and preserve existing Python-domain cross-reference behavior.
