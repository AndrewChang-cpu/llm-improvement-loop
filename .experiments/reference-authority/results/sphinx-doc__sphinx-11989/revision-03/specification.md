# Python type-alias documentation

## Purpose — Goals
Add type-alias documentation to the existing Python domain. Users can document aliases, optionally display the represented type, and cross-reference aliases through the Python domain’s established object and reference behavior.

## Purpose — Scope
Support the `py:type` directive and `py:type` cross-reference role for aliases documented at module level or within a class. Preserve the existing Python-domain object handling.

## Interfaces — APIs
- Register `type` as a Python-domain object type, directive, and cross-reference role. Identify the object type as “type alias” and retain the standard generic object cross-reference behavior.
- The directive accepts an alias name and an optional `canonical` option containing the represented type expression. Accept the option text unchanged and parse it with the existing Python annotation parser when supplied.
- Prefix the signature with “type”. When `canonical` is present, render an equals separator followed by the parsed annotation content, including normal Python-domain cross-reference behavior for names in the expression. When omitted or empty, display no represented-type expression.
- Use inherited Python-object naming, target, indexing, and lookup machinery so aliases are recorded and resolvable by their documented names, including nested names.

## Architecture — Responsibilities
Implement type-alias behavior in the existing Python-domain component alongside its object directives. Extend `PyObject`, use the existing annotation parser, and register the object type, directive, and role through the Python domain. Do not add a separate rendering, indexing, or cross-reference path or external dependencies.

## Behavior — business rules
- An alias without a nonempty `canonical` option still has a type-prefixed signature and no displayed represented-type expression.
- For a module-level alias, use the inherited Python-object index wording: include the module context when a module is present; without a module, use the inherited built-in-variable wording.
- For an alias nested in a class, use type-alias-specific index wording identifying the alias as being in its containing class. Include the module name in that class context only when a module is present and the existing module-name configuration enables it.
- Preserve standard Python-object nesting, target creation, object registration, and cross-reference behavior.

## Acceptance — acceptance criteria
- The Python domain registers the `type` object type, directive, and cross-reference role; the object type is labeled “type alias”.
- Module-level and class-nested aliases can be documented with or without `canonical`. Signatures use the “type” prefix, and a nonempty expression is rendered as parsed annotation content.
- A module-level alias receives inherited module or built-in-variable index wording. A nested alias receives type-alias-specific index wording that identifies its containing class and respects the module-name configuration.
- Alias names and names within canonical expressions follow existing Python-domain cross-reference behavior.

## Conventions — documentation
Document the `py:type` directive, its optional `canonical` option, and the `py:type` cross-reference role in the Python-domain documentation. Explain that `canonical` gives the represented type expression and can be omitted.
