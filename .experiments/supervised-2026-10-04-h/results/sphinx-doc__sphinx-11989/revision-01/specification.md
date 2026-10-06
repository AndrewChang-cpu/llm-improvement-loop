# Python type-alias documentation

## Purpose

Add a first-class `py:type` directive and matching `py:type` cross-reference role to the existing Python domain so documentation can describe and link to type aliases. Preserve the Python domain's normal object indexing, target generation, and cross-reference resolution.

## Behavior and interface

- The directive documents a type alias by its name. It accepts the common Python-object options inherited from `PyObject` and one alias-expression option named `canonical`; it does not inherit the variable-only `type` or `value` options.
- The `canonical` option is optional. When present, render it after the alias name as an equals expression, and parse the entire expression with the Python domain's existing annotation parser so names within it become ordinary Python cross-references. When omitted, render only the alias declaration.
- Prefix the displayed declaration with the Python keyword `type`.
- Register `py:type` as a Python-domain object type with `type` and generic-object cross-reference names, and register its role using the Python domain's existing cross-reference machinery. Alias references must resolve like other Python objects, including module-level and nested aliases.
- Use the existing `PyObject` behavior for signature name handling, object targets, indexing, and nested-object context. Do not use the variable directive's rendering path.

## Indexing and compatibility

- Give aliases their own index wording. A module-level alias uses the existing module-qualified object wording. A nested alias identifies its containing class or namespace and labels the item as a type alias; include the module in that containing name when the Python domain's module-name configuration requests it. An unqualified top-level alias uses its name alone.
- Keep nested content disabled, as in the common Python-object behavior.
- Do not change behavior of existing Python object directives or cross-reference roles.

## Acceptance criteria

- The alias expression is optional and, when present, its parsed annotation nodes include cross-reference nodes for names in compound expressions.
- Both module-level and nested aliases receive Python-domain targets, index entries, and resolvable `py:type` references.
- Existing Python-domain cross-reference checks continue to find all references, including references created by alias expressions.
- The documented directive contract names `canonical` as the expression option and does not describe `value` as an alias option.
