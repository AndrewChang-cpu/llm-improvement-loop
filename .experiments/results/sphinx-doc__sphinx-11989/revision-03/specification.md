# Add Python type-alias documentation support

### Purpose — Goals and scope
Add first-class documentation for Python type aliases in the existing Python domain. Support aliases with or without a publicly documented aliased expression, at module level and in supported nested scopes. Preserve existing Python-domain object and cross-reference behavior.

### Interfaces — APIs and input/output contracts
Provide a `py:type` directive and a `py:type` cross-reference role. The directive takes the alias name and accepts an optional `canonical` option containing the aliased type expression. Keep the expression out of the directive’s input signature; when present, render it after the alias name with the type-alias signature prefix. When omitted, the alias must still be documented, indexed, and referenceable. The `canonical` option is the directive’s option name; do not substitute `value`.

### Behavior — Capabilities and workflows
Implement the alias description as a `PyObject`-based Python-domain object. Parse a supplied canonical expression with the existing Python annotation parser and attach the parsed annotation nodes to the signature. Give the signature the type-alias-specific prefix.

Allow aliases in module and supported nested scopes. Provide type-alias-specific index text for module-level and nested aliases. For nested aliases, include the containing class context, with the module name when the existing module-name setting calls for it. Ensure index text generation follows the existing translation and index-entry conventions and does not shadow names needed by those conventions.

Register the object type, directive, and cross-reference role with the Python domain using its existing object registration and cross-reference resolution machinery. Preserve existing Python cross-reference nodes and expectations.

### Data — Invariants
The alias name is the object identity. The optional canonical expression is parsed as a Python annotation. An absent expression does not prevent object registration, indexing, or cross-reference resolution. Index text reflects whether the alias is module-level or nested in a class.

### Architecture — File placement and responsibilities
Keep the implementation in the existing Python-domain component. Use its established object, directive, annotation parsing, registration, and cross-reference extension points. Add no external dependencies.

### Compatibility — Backward compatibility
Keep this directive distinct from data and attribute directives. Do not alter their options or interpretation. Preserve existing Python-domain signature, indexing, and cross-reference behavior for other object types.

### Conventions — Documentation
Update the Python-domain reference to describe the directive, its optional canonical expression, the role, and nested alias support. Follow nearby documentation conventions.

### Acceptance — Acceptance criteria
- The Python domain registers the `py:type` object, directive, and cross-reference role.
- A supplied canonical expression is parsed and rendered after the alias name with the type-alias-specific prefix; an omitted expression remains valid.
- Module-level and nested aliases receive alias-specific index text that reflects their context.
- Alias references resolve through standard Python-domain cross-reference behavior, and existing Python cross-reference behavior remains intact.
- Add or update focused tests for signature structure and rendered output, canonical-option handling, aliases with no expression, module and nested indexing, references, and preservation of existing cross-reference behavior. Ensure the relevant checks pass.
