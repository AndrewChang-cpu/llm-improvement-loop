# Python type-alias documentation

## Purpose

Add a first-class `py:type` directive and matching `py:type` cross-reference role to the existing Python domain. The directive documents a type alias by its declared name and supports references to that alias. Preserve the Python domain's existing target, indexing, object-context, and cross-reference behavior for aliases and all existing Python objects.

## Behavior and interface

- Implement the directive as a Python-domain object using the shared `PyObject` behavior. Its effective options are the common `PyObject` options plus the optional `canonical` expression option. This includes the inherited `module` option. Do not add the variable-specific `type` or `value` options.
- Render the alias signature with the normal Python object name and prefix it with `type`. Represent that prefix using the same signature annotation container and spacing used by the reference behavior; it is not a keyword-specific signature node.
- When `canonical` is present, display an equals sign followed by the expression after the alias name. Parse the complete expression with the Python domain's existing annotation parser so referenced names become normal Python cross-references. When it is absent, display only the alias declaration.
- Register the Python object type with the user-facing label “type alias” and cross-reference names `type` and `obj`. Register the `py:type` directive and its role in the Python domain, and resolve references through the existing Python-domain lookup and cross-reference machinery.
- Preserve `PyObject` target registration for both the declared alias name and, when supplied, the exact canonical expression as an aliased alternate target of the same object. Do not override or bypass inherited target registration to suppress the canonical target. The visible parsed expression and the canonical alternate target serve distinct purposes.
- Keep nested directive content disabled, as inherited from `PyObject`. Alias declarations may still occur inside a documented class or other Python namespace, and their names and targets must use the inherited Python object-context handling.

## Indexing and compatibility

- Give aliases the reference's index wording. For an unqualified alias in a named module, use the ordinary module-qualified wording: the alias name followed by “in module” and the module name. For an alias nested under a dotted namespace, use the alias name followed by “type alias in” and its containing namespace. Include the module in that namespace only when Python's `add_module_names` configuration is enabled. For an unqualified alias without a module, use the alias name alone.
- Keep index message text translatable through the Python domain's existing translation function. Do not shadow that translation function with a local name. In particular, avoid the failure where a module-level alias enters the fallback index branch and calling the shadowed translation function raises `TypeError`, aborting directive processing and existing Python-domain builds.
- Respect the inherited no-index and no-index-entry options when producing targets and index entries. Do not replace the shared `PyObject` target/index workflow with a custom workflow that loses canonical target registration.
- Do not change behavior of existing Python object directives or cross-reference roles. Keep existing documentation options, including the function `module` option, in their existing documentation sections when updating Python-domain documentation.

## Acceptance criteria

- The directive's registered object type is labeled “type alias”; its role supports both `py:type` and generic `py:obj` references.
- The effective directive options include inherited common Python-object options and `canonical`, including `module`, and exclude the variable-only `type` and `value` options. Nested content remains disabled.
- The displayed signature has the reference's `type` annotation prefix structure. An optional canonical expression follows the alias name after an equals sign, and names parsed from compound expressions produce ordinary Python cross-reference nodes.
- A canonical expression also resolves as an aliased target for the declared alias through the inherited Python object registration path. Existing canonical-target lookup behavior is preserved.
- Module-level aliases, aliases nested in a class or namespace, and unqualified aliases receive the appropriate targets and index wording. Module-level aliases with a module name complete directive processing without an exception in index-text translation.
- Python-domain object and cross-reference checks continue to pass, including checks for existing objects, canonical aliases, and references created from alias expressions.
