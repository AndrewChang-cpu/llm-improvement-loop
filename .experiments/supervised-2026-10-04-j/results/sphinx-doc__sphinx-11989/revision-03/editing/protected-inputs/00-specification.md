# Python type-alias documentation

## Purpose — Goals and scope

Add first-class type-alias documentation to the existing Python domain. The feature consists of the `py:type` directive and matching `py:type` cross-reference role. Preserve the Python domain’s existing object registration, target, index, context, and cross-reference behavior.

## Behavior — Capabilities and business rules

- Implement the directive as a `PyObject` subclass in the existing Python-domain component. Its effective options are the inherited Python-object options, including `module`, plus the optional `canonical` expression option. It does not have the variable-specific `type` or `value` options. Nested directive content remains disabled.
- Render the alias name using the normal Python-object signature handling, prefixed by `type` in the same annotation container and spacing used by the reference.
- If `canonical` is supplied, append an equals sign and parse the complete expression with the existing Python annotation parser. Names in the expression must become ordinary Python cross-reference nodes. Without `canonical`, render only the alias declaration.
- Register the object type with the label “type alias” and cross-reference names `type` and `obj`. Register the `py:type` directive and role with the Python domain’s existing lookup and cross-reference machinery.
- Preserve inherited `PyObject` target handling. Register the declared alias name as the object target and, when `canonical` is present, register its exact expression as an aliased target for the same object. The displayed parsed expression and the canonical alternate target serve distinct purposes.
- Preserve Python object-context behavior so aliases can be declared at module level or inside documented namespaces. Respect inherited `no-index`, `no-index-entry`, and other shared options; do not replace the shared target and index workflow.

## Behavior — Indexing and edge cases

- Use the reference’s translatable index wording and punctuation:
  - For an unqualified alias with a module, the label is “name (in module module-name)”.
  - For an alias nested under a dotted namespace, the label is “name (type alias in namespace)”. Include the module name in that namespace only when `add_module_names` is enabled.
  - For an unqualified alias without a module, the label is just the alias name.
- Preserve the reference’s module and namespace resolution when constructing index labels and targets. Do not shadow the Python domain’s translation function when producing translated index text.

## Compatibility — Backward compatibility

Do not change existing Python object directives, cross-reference roles, or their options and behavior.

## Acceptance — Test requirements

- Add focused regression coverage for directive registration and effective options, signature structure with and without `canonical`, expression cross-reference nodes, canonical alias lookup, module-level and nested aliases, target registration, and the three index-label cases above.
- Verify the nested index label includes parentheses around “type alias in namespace”.
- Verify existing Python-domain object and cross-reference behavior remains covered and passes.
