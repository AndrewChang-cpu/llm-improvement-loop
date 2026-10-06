# Python type-alias documentation

## Purpose — Goals
Add type-alias documentation to the existing Python domain. Users can document aliases, optionally show the represented type, and cross-reference aliases using the Python domain’s established object and reference behavior.

## Purpose — Scope
Support the `py:type` directive and `py:type` cross-reference role for module-level and nested aliases. Preserve existing Python-domain behavior.

## Interfaces — APIs
- The directive name is `py:type`; its object type is `type`, and its cross-reference role is `py:type`.
- The directive documents an alias by name and accepts an optional `canonical` option containing the represented type expression. The alias remains documentable when this option is omitted.
- Render the declaration with the `type` prefix. When `canonical` is present, render an equals separator followed by the expression as parsed Python annotation content, so names in it receive normal Python-domain annotation rendering and cross-reference behavior.
- Use the existing Python object naming, indexing, and cross-reference machinery. Aliases must be indexable and resolvable by their documented names, including names nested within a documented Python object.

## Architecture — Responsibilities
Implement the directive in the existing Python-domain component using the `PyObject` extension point and the existing annotation parser. Register the object type, directive, and role in the Python domain. Do not introduce a separate rendering or indexing path, or external dependencies.

## Behavior — business rules
- An omitted `canonical` option leaves the alias declaration without a displayed represented type.
- Module-level aliases use the existing module-aware index text convention.
- Nested aliases use type-alias-specific index text that identifies the containing object; include the module name according to the existing module-name configuration.
- Alias descriptions support normal nested object documentation and cross-references.

## Acceptance — acceptance criteria
- A module-level alias can be documented with or without a canonical expression and referenced through `py:type`.
- A nested alias can be documented, indexed with type-alias-specific parent context, and referenced through `py:type`.
- A canonical expression is rendered as annotation content, not plain text, and follows existing Python annotation cross-reference behavior.
- Existing Python-domain object registration, indexing, and cross-reference behavior remains intact.

## Conventions — documentation
Document the directive, optional `canonical` option, and role in the Python-domain documentation. Explain that `canonical` names the represented type and may be omitted.
