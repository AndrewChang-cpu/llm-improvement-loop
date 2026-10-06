# Python type-alias documentation

## Purpose — Goals
Add type-alias documentation to the Python domain. A documented alias has a type-prefixed signature, can display the type it represents, and participates in Python-domain indexing, object lookup, and cross-reference resolution.

## Purpose — Scope
Provide the Python-domain type-alias directive and cross-reference role for aliases documented at module level or within a class. The directive accepts an alias name, an optional canonical type expression, and an optional description body. It uses existing Python-object conventions for names, targets, indexing, and lookup.

## Interfaces — APIs
- Register the Python-domain object type under the name `type`, with display label “type alias”; register the `py:type` directive and `py:type` cross-reference role.
- The directive accepts an alias name and inherits the standard Python-object options, including `canonical`. The `canonical` option is text containing the represented type expression; it is not a second object name.
- Prefix the signature with “type”. When `canonical` is nonempty, render an equals separator followed by the expression parsed as a Python annotation. Names in that annotation use normal Python-domain reference behavior. When the option is absent or empty, omit the expression.
- Use inherited Python-object handling for signature names, target creation, registration, and lookup, including nested names. Preserve the optional description body.

## Behavior — business rules
- A module-level alias index entry follows the inherited Python-object wording: include module context when a module is present; otherwise use the alias name alone.
- A class-nested alias index entry identifies the alias as a type alias in its containing class. Include the module in the class context only when a module is present and the existing module-name configuration enables it.
- The canonical expression affects signature rendering only. Do not register its text as an alternate object name or cross-reference target.
- Alias names resolve through the Python domain’s normal object and cross-reference mechanisms. References within a canonical expression follow normal Python annotation parsing and reference behavior.

## Architecture — responsibilities
Implement the alias directive in the existing Python-domain component as a Python-object description. Use the existing annotation parser for the optional represented type and the existing Python-domain object, indexing, and cross-reference machinery. Register the object type, directive, and role through the Python domain.

## Conventions — documentation
Document the Python-domain type-alias directive, its optional canonical text option, and its cross-reference role. Describe the option as the type represented by the alias, and state that the directive supports an optional description body.

## Acceptance — acceptance criteria
- The Python domain registers the type-alias object type, directive, and cross-reference role; the object type is labeled “type alias”.
- Module-level and class-nested aliases can be documented with or without a canonical expression and may include a description body.
- Signatures use the “type” prefix. A nonempty canonical option renders after an equals separator as parsed annotation content with normal Python-domain references; an absent or empty option adds no represented-type expression.
- Canonical expression text is not registered as an alternate alias target. The documented alias name is registered and available to normal Python-domain lookup and cross-reference resolution.
- Module-level index entries include module context when available and otherwise use the alias name alone. Nested entries identify the alias as a type alias in its containing class and include module context only under the existing configuration rule.
- Regression coverage checks parsed signature output, module-level and nested alias indexing, and alias object lookup and cross-reference resolution.
