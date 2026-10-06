# Python type-alias documentation

## Purpose — Goals
Add type-alias documentation to the Python domain. A documented alias may show its represented type, and aliases must participate in the Python domain’s object indexing and cross-reference behavior.

## Purpose — Scope
Provide the `py:type` directive and `py:type` cross-reference role for aliases documented at module level or inside a class. The directive supports an optional description body and inherits the standard Python-object behavior for naming, targets, indexing, and lookup.

## Interfaces — APIs
- Register `type` as a Python-domain object type, directive, and cross-reference role. Label the object type “type alias”; its cross-reference role uses the standard Python object-reference behavior.
- The directive accepts an alias name and an optional `canonical` text option. Preserve the option text as entered and parse it using the Python domain’s existing annotation parser.
- Prefix the signature with “type”. If `canonical` is nonempty, render an equals separator and the parsed annotation after the alias name. Names in that annotation use normal Python-domain cross-reference behavior. If the option is absent or empty, render no represented-type expression.
- Use the inherited Python-object behavior for signature names, target creation, registration, and lookup, including nested names.

## Behavior — business rules
- A module-level alias has the inherited Python-object index wording: with a module name, include the module context; without a module name, use the alias name alone. Do not use the built-in-variable wording for an unqualified alias with no module.
- A class-nested alias has type-alias-specific index wording that identifies the alias and its containing class. Include the module name in the class context only when a module is present and the existing module-name configuration enables it.
- Preserve standard Python-object nesting, target creation, object registration, and cross-reference behavior.

## Architecture — responsibilities
Implement the alias directive in the existing Python-domain component alongside its other object directives. Extend the shared Python-object directive behavior, use the existing annotation parser, and register the object type, directive, and role through the Python domain. Keep indexing, rendering, and cross-reference resolution within those existing extension points; add no separate path or external dependency.

## Conventions — documentation
Document the `py:type` directive, its optional `canonical` text option, and the `py:type` cross-reference role in the Python-domain documentation. Describe the option as the canonical type represented by the alias, and note that it may be omitted.

## Acceptance — acceptance criteria
- The Python domain registers the `type` object type, directive, and cross-reference role; the object type is labeled “type alias”.
- Module-level and class-nested aliases can be documented with or without `canonical`, and may include a description body.
- Signatures use the “type” prefix. A nonempty canonical expression renders after an equals separator as parsed annotation content with normal Python-domain references; an absent or empty option renders no expression.
- Module-level index entries include module context when available and otherwise use the alias name alone. Nested entries identify the alias as a type alias in its containing class and include module context only under the existing configuration rule.
- Alias names and names in canonical expressions follow existing Python-domain registration and cross-reference behavior.
