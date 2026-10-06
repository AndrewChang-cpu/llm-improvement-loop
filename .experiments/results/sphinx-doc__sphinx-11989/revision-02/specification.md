# Add Python type-alias documentation support

### Feature or Bugfix
Feature.

### Purpose — Goals and scope
Add first-class documentation for Python type aliases in the existing Python domain. Support declarations with or without a public alias expression, at module level and in supported nested scopes. Preserve existing Python-domain object and cross-reference behavior.

### Interfaces — APIs and input/output contracts
Provide a `py:type` directive and a `py:type` cross-reference role. The directive accepts the alias name, an optional `value` option containing the aliased type expression, and description content. Keep the expression out of the directive’s input signature; when supplied, render it as the alias value after the alias name. When omitted, still document, index, and resolve references to the alias.

### Behavior — Capabilities and workflows
Implement the alias description as a `PyObject`-based Python-domain object. Use the existing annotation parser to parse a supplied alias expression and attach the resulting annotation nodes to the signature so the expression is rendered according to the expected Python-domain output structure. Give the signature the type-alias-specific prefix.

Allow aliases in module and supported nested scopes. Ensure alias indexing distinguishes module-level aliases from aliases nested in classes, using the containing class context for nested index text. Supply type-alias-specific index text for both cases; do not rely on generic object index text.

Register the object type, directive, and cross-reference role with the Python domain. Use the domain’s existing object registration and cross-reference resolution machinery. Check that registering the new role preserves existing Python cross-reference nodes and expectations.

### Data — Invariants
The alias name is the object identity. The optional expression is parsed as a Python annotation. An absent expression does not prevent object registration, indexing, or cross-reference resolution. Index text reflects the alias’s module or nested-class context.

### Architecture — File placement and responsibilities
Keep the implementation in the existing Python-domain component. Use its established object, directive, annotation parsing, registration, and cross-reference extension points. Add no external dependencies.

### Compatibility — Backward compatibility
Keep this directive distinct from data and attribute directives. Do not alter their options or interpretation. Preserve existing Python-domain signature, indexing, and cross-reference behavior for other object types.

### Conventions — Documentation
Update the Python-domain reference to describe the directive, role, optional value, and nested alias support. Follow nearby documentation conventions.

### Acceptance — Acceptance criteria
- The Python domain registers the `py:type` object, directive, and cross-reference role.
- A supplied alias expression is parsed and rendered in the alias signature with the type-alias-specific prefix; an omitted expression remains valid.
- Module-level and nested aliases receive appropriate alias-specific index text and can be indexed.
- Alias references resolve through standard Python-domain cross-reference behavior, and existing Python cross-reference behavior remains intact.
- Type-alias tests cover signature structure, rendered output, indexing at module and nested scope, optional values, and references. Retain relevant reference behavior coverage, and ensure the targeted checks pass.
