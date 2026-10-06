# Python type-alias documentation

## Purpose — Goals
Add type-alias documentation to the existing Python domain. Users can document aliases, optionally show the represented type, and cross-reference aliases using the Python domain’s established object and reference behavior.

## Purpose — Scope
Support the `py:type` directive and the Python type cross-reference role for aliases documented at module level or nested within a documented object. Preserve the existing Python-domain object handling.

## Interfaces — APIs
- Register `type` as a Python-domain object type, directive, and cross-reference role.
- The directive accepts an alias name and an optional `canonical` option containing the represented type expression. The option accepts unchanged text; when present, parse and render it using the existing Python annotation parser. When omitted, show no represented-type expression.
- Render the signature with the `type` prefix. When `canonical` is present, show an equals separator followed by the parsed annotation content, including normal Python-domain cross-reference behavior for names in the expression.
- Use the inherited Python object naming, target, and indexing machinery so aliases are recorded and resolvable by their documented names, including nested names.

## Architecture — Responsibilities
Implement type-alias behavior alongside the existing Python-domain object directives, extending `PyObject`. Use the existing annotation parser and Python-domain registration mechanisms. Do not add a separate rendering, indexing, or cross-reference path or introduce external dependencies.

## Behavior — business rules
- An alias without `canonical` still has a type-prefixed signature, with no displayed represented-type expression.
- For a module-level alias, use the inherited Python-object index text: include the module context when one is present.
- For a nested alias, produce type-alias-specific index text identifying its containing object. Include the module name in that context only when a module is present and the existing module-name configuration enables it.
- Preserve standard Python-object nesting, target creation, and cross-reference behavior.

## Acceptance — acceptance criteria
- The Python domain registers the `type` object type, directive, and cross-reference role.
- A module-level alias can be documented with or without `canonical`; its signature has the `type` prefix, and a supplied expression is rendered as parsed annotation content.
- A nested alias is recorded under its containing object’s name and receives type-alias-specific index text identifying that parent.
- Alias names and names within canonical expressions follow existing Python-domain cross-reference behavior.

## Conventions — documentation
Document the `py:type` directive, its optional `canonical` option, and the type cross-reference role in the Python-domain documentation. Explain that `canonical` supplies the represented type expression and may be omitted.
