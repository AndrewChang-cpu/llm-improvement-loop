# Python type-alias documentation

## Purpose — Goals
Add type-alias documentation to the Python domain. A documented alias has a type-prefixed signature, may display the type it represents, and participates in Python-domain indexing, object lookup, and cross-reference resolution.

## Purpose — Scope
Provide the Python-domain type-alias directive and cross-reference role for aliases documented at module level or within a class. The directive accepts an optional canonical option and description body, and uses the existing Python-object conventions for names, targets, indexing, and lookup.

## Interfaces — APIs
- Register the type-alias object type under the Python domain’s type name, with the display label “type alias”; register its directive and cross-reference role under the corresponding Python-domain name.
- The directive accepts an alias name and inherits the standard Python-object options, including the canonical option. The canonical option is text. When nonempty, parse it as a Python annotation and display it after the alias name, separated by an equals sign. Names in that annotation use normal Python-domain reference behavior.
- Preserve inherited canonical-name registration: when supplied, the canonical option also registers the canonical name as an aliased Python-domain object pointing to the documented target.
- Prefix the signature with “type”. If the canonical option is absent or empty, omit the represented-type expression.
- Allow an optional description body. Use inherited Python-object handling for signature names, target creation, registration, and lookup, including nested names.

## Behavior — business rules
- A module-level alias index entry uses the inherited Python-object wording: include module context when a module is present; otherwise use the alias name alone.
- A class-nested alias index entry identifies the alias as a type alias in its containing class. Include the module in the class context only when a module is present and the existing module-name configuration enables it.
- The canonical option has both display and registration effects: its annotation is rendered in the signature and its canonical name is registered as an alias for lookup and cross-references.
- Alias names and registered canonical names resolve through the Python domain’s normal object and cross-reference mechanisms.

## Architecture — responsibilities
Implement the alias directive in the existing Python-domain component as a Python-object description. Use the existing annotation parser for the optional represented type, and use the existing Python-domain object, indexing, and cross-reference machinery. Register the object type, directive, and role through the Python domain. Do not introduce a separate rendering or lookup path or an external dependency.

## Conventions — documentation
Document the Python-domain type-alias directive, its optional canonical text option, and its cross-reference role. Describe the option as the canonical type represented by the alias, and state that the directive supports an optional description body.

## Acceptance — acceptance criteria
- The Python domain registers the type-alias object type, directive, and cross-reference role; the object type is labeled “type alias”.
- Module-level and class-nested aliases can be documented with or without a canonical option and may include a description body.
- Signatures use the “type” prefix. A nonempty canonical option renders after an equals separator as parsed annotation content with normal Python-domain references; an absent or empty option renders no represented-type expression.
- A supplied canonical name remains registered as an aliased domain object pointing to the documented target.
- Module-level index entries include module context when available and otherwise use the alias name alone. Nested entries identify the alias as a type alias in its containing class and include module context only under the existing configuration rule.
- Alias names and canonical names participate in Python-domain object lookup and cross-reference resolution. Regression coverage verifies these behaviors for module-level and nested aliases, including expected index entries and registered objects.
