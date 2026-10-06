# Add Python type-alias documentation support

### Feature or Bugfix
Feature.

### Purpose — Goals and scope
Add support for documenting Python type aliases as first-class Python-domain objects. Implement this in the existing Python-domain component and preserve the domain’s existing behavior for other objects.

### Interfaces — APIs and input/output contracts
Provide the `py:type` directive and `py:type` cross-reference role. The directive accepts an alias name, an optional `value` option containing the aliased type expression, and body content for its description. Keep the alias expression out of the directive signature. When the value is omitted, the alias can still be documented and referenced.

### Behavior — Capabilities and workflows
Represent aliases through the existing `PyObject` and Python-domain object registration, annotation parsing, indexing, and cross-reference machinery. Support aliases at module scope and nested within classes or other supported Python scopes. Enable nesting for the new directive in the same way as the existing class-like Python directive that supports nested objects.

Register the object type, directive, and cross-reference role with the Python domain. Alias references must resolve using the domain’s standard Python cross-reference behavior. Do not create a separate rendering or reference-resolution path.

### Data — Invariants
The alias name is the documented object identity. The optional alias expression is annotation-parsed using the existing Python annotation parser. Omitting the expression must not prevent indexing or cross-referencing the alias.

### Architecture — File placement and responsibilities
Keep implementation in the existing Python-domain component. Follow its established object, directive, and role extension points and dependency direction; do not add external dependencies.

### Compatibility — Backward compatibility
Keep existing Python-domain object behavior intact. This new directive is separate from the data and attribute directives; do not repurpose their options or change their existing interpretation.

### Conventions — Documentation
Document the directive and role in the Python-domain reference, including the optional alias expression and nested alias support. Follow nearby domain documentation conventions.

### Acceptance — Acceptance criteria
- The Python domain registers the `py:type` object, directive, and cross-reference role.
- An alias with a value and an alias without a value can both be documented, indexed, and cross-referenced.
- Aliases declared inside supported nested scopes are accepted and discoverable through normal Python-domain references.
- The alias expression is parsed through the existing annotation parser, and behavior uses the existing Python object and cross-reference machinery.
- Existing Python-domain behavior and targeted type-alias and cross-reference checks continue to pass.
