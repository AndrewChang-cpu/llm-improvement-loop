# Type-alias documentation in the Python domain

## Purpose — Goals and scope

Add support in the existing Python domain for documenting Python type aliases and linking to them. Match the reference behavior for the directive signature, alias lookup, indexing, and Python-domain object metadata.

## Interfaces — APIs and input/output contracts

- Register the `py:type` directive, the Python-domain object type key `type`, and the `py:type` cross-reference role. The object type's user-facing label is “type alias,” and the role resolves documented aliases through normal Python-domain cross-reference handling.
- The directive documents an alias name, accepts an optional `canonical` text option for the represented type, and accepts an optional description body. Preserve the inherited `PyObject` options and controls, including module context and index-entry controls; do not add the variable directive's `value` or `type` options.
- Begin the signature with the plain text node `type` followed by signature spacing. When `canonical` is supplied, append an equals separator and parse its expression with the existing Python annotation parser so resolvable type names retain annotation cross-references. Without `canonical`, show only the alias name after the prefix.
- When `canonical` is supplied, register its text as an alternate Python-domain cross-reference name for the same alias object and target. Keep the alias's own fully qualified name as its primary object name.
- Use these index-entry rules: a module-level alias with a module context is named “Alias (in module module-name)”; without module context, use only the alias name. For an alias nested in a class, use “Alias (type alias in class-name)”. Include the module prefix in that class name only when the Python configuration to add module names is enabled.

## Architecture — Responsibilities and boundaries

- Implement the directive and register its object type and role in the existing Python-domain component. Define the directive on the `PyObject` extension point and reuse its signature handling, target registration, index controls, and module/class context. Use the domain's existing annotation parser and cross-reference machinery; do not introduce a separate rendering or lookup path.
- Preserve inherited canonical-name registration from `PyObject`; the type-alias directive must not suppress or temporarily remove the `canonical` option during object registration.
- Preserve `PyObject`'s non-nestable-content setting. This setting does not prevent a type-alias directive from appearing inside a class description; in that context, the alias's qualified name and index entry must retain the containing class.

## Acceptance — Acceptance criteria

- Module-level and class-nested aliases are documented and recorded as Python-domain objects with object type key `type` and user-facing type label “type alias.” The signature prefix is represented as plain text, followed by the alias name and, when provided, the parsed canonical expression.
- A `py:type` reference resolves an alias by its documented name. A supplied canonical expression is also registered as an alternate reference target for that alias, while names inside the expression are parsed with the normal Python annotation cross-reference behavior.
- Index entries use the module-level and nested-class wording above, including the configured module prefix for nested class names.
- Omitting the canonical expression yields a valid name-only alias declaration. Existing Python object behavior, inherited options, and dependency boundaries remain intact.
