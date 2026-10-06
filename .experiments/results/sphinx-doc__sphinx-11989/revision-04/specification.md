# Python type-alias documentation support

### Purpose — Goals and scope
Add first-class documentation for Python type aliases in the existing Python domain. Support aliases with or without a publicly documented aliased expression, including module-level and supported nested scopes. Preserve existing Python-domain object, indexing, and cross-reference behavior.

### Interfaces — APIs and input/output contracts
Provide a `py:type` directive and a `py:type` cross-reference role. The directive takes the alias name and accepts an optional `value` option containing the aliased type expression. Keep the expression out of the directive signature; when supplied, parse and display it after the alias name using the type-alias-specific signature prefix. When omitted, the alias remains documentable, indexable, and referenceable. Do not use `canonical` as the public option name.

### Behavior — Capabilities and workflows
Implement the alias description as a Python-domain object based on `PyObject`. Parse a supplied `value` expression with the existing Python annotation parser and attach the parsed annotation nodes to the signature.

Register the object type, directive, and cross-reference role through the Python domain’s existing registration and resolution mechanisms. Support module-level and supported nested aliases. Use the shared `PyObject` target and index path; do not replace it with custom target creation or object registration. Customize only the alias-specific index text hook as needed.

Index text must identify a nested alias’s containing class and module context according to existing Python-domain conventions. In particular, a nested alias in `example.Class` must identify `example.Class` as its context rather than describing it as an alias merely in module `example`. Module-level index text must follow the corresponding existing convention. Use the established translation and index-entry conventions.

### Data — Invariants
The alias name is its object identity. The optional `value` expression is parsed as a Python annotation. An omitted expression does not prevent object registration, indexing, or cross-reference resolution. Index text reflects whether the alias is module-level or nested in a class, and nested text retains the containing class context.

### Architecture — File placement and responsibilities
Keep the implementation in the existing Python-domain component. Use its established Python object, annotation parsing, target/index, registration, and cross-reference extension points. Add no external dependencies.

### Compatibility — Backward compatibility
Keep this directive distinct from data and attribute directives. Do not change their options or interpretation. Preserve existing Python-domain signature, indexing, and cross-reference behavior for other object types.

### Conventions — Documentation
Update the Python-domain reference to describe the directive, its optional `value` option, the role, and nested alias support. Follow nearby documentation conventions and do not document `canonical` as the option name.

### Acceptance — Acceptance criteria
- The Python domain registers the `py:type` object, directive, and cross-reference role.
- A supplied `value` expression is parsed and rendered after the alias name with the type-alias-specific prefix; an omitted expression remains valid.
- Module-level and nested aliases use the shared Python-object target and index path. Nested index text identifies the containing class and module context according to the existing convention.
- Alias references resolve through standard Python-domain cross-reference behavior, and existing cross-reference behavior remains intact.
- Add or update focused coverage for signature structure and rendered output, `value` option handling, aliases with no expression, module-level and nested indexing, references, and preservation of existing cross-reference behavior. Retain existing alias regression coverage, including the nested-index expectation, and ensure the relevant checks pass.
