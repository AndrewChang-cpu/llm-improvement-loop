# Python type-alias documentation

## Purpose — Goals and scope

Add first-class type-alias documentation to the existing Python domain through the `py:type` directive and matching `py:type` cross-reference role. Preserve the Python domain’s existing object registration, target, index, context, and cross-reference behavior.

## Behavior — Capabilities and business rules

- Implement the directive as a `PyObject` subclass in the existing Python-domain component. Its effective options include inherited Python-object options, including `module`, and the optional `canonical` expression option. It does not add the variable-specific `type` or `value` options.
- Render the alias name using normal Python-object signature handling, prefixed by “type” in the same annotation container and spacing used by the reference.
- When `canonical` is supplied, append an equals sign and parse the complete expression with the existing Python annotation parser so names in the expression become ordinary Python cross-reference nodes. Without `canonical`, render only the alias declaration.
- Support an optional descriptive directive body. Preserve the inherited `ObjectDescription` content behavior; do not disable bodies.
- Keep the alias directive’s own nesting behavior inherited from `PyObject`, which does not allow the alias directive itself to establish a nested namespace. Aliases can still be declared within an enclosing nestable Python object, such as a class, and use that enclosing object’s context.
- Register the object type with the label “type alias” and cross-reference names `type` and `obj`. Register the `py:type` directive and role with the Python domain’s existing lookup and cross-reference machinery.
- Preserve inherited `PyObject` target handling. Register the declared alias name as the object target and, when `canonical` is present, register its exact expression as an aliased target for the same object. The displayed parsed expression and the canonical alternate target serve distinct purposes.
- Preserve Python object-context behavior for module-level aliases and aliases declared within an enclosing documented namespace. Respect inherited `no-index`, `no-index-entry`, and other shared options; do not replace the shared target and index workflow.

## Behavior — Indexing and edge cases

- Use the reference’s translatable index wording and punctuation:
  - For an unqualified alias with a module, the label is “name (in module module-name)”.
  - For an alias nested under a dotted namespace, the label is “name (type alias in namespace)”. Include the module name in that namespace only when `add_module_names` is enabled.
  - For an unqualified alias without a module, the label is just the alias name.
- Preserve the reference’s module and namespace resolution when constructing index labels and targets. Do not shadow the Python domain’s translation function when producing translated index text.

## Compatibility — Backward compatibility

Do not change existing Python object directives, cross-reference roles, or their options and behavior.

## Acceptance — Test requirements

- Cover directive registration and effective options; signature structure with and without `canonical`; expression cross-reference nodes; canonical alias lookup; module-level and class-nested aliases; target registration; and the three index-label cases above.
- Verify that a `py:type` directive accepts an optional descriptive body and that aliases inside a nestable enclosing object are supported while the alias directive itself retains its inherited non-nestable behavior.
- Verify the nested index label includes parentheses around “type alias in namespace”.
- Verify existing Python-domain object and cross-reference behavior remains covered and passes.
