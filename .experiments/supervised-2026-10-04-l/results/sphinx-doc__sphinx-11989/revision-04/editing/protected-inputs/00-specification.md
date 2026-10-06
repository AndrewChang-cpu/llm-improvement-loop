# Python type-alias documentation

## Purpose and scope
Add support for documenting Python type aliases as Python-domain objects and cross-referencing them. Keep the feature within the existing Python-domain object, annotation, and cross-reference machinery.

## Directive and signature behavior
Register the `py:type` directive as a Python object kind whose localized object-kind label is “type alias.” Its signature prefix is “type.” The directive accepts an alias name and an optional description body, but does not allow nested contents. It inherits the Python-object options, including module context, the `canonical` option, annotation metadata, and index controls.

Display the `type` prefix before the alias name. The alias may be documented without a canonical expression. When the inherited `canonical` option is supplied, treat its value as the type expression represented by the alias. Display that expression after an equals sign and parse it with the existing Python annotation parser so referenced Python types become normal cross-references. Preserve inherited behavior that registers the canonical expression as an aliased Python-domain target for lookup.

Use inherited Python-object name handling and target registration. An alias documented in a class context includes that containing class in its full name and target, even though the alias directive does not allow nested contents.

## Cross-reference behavior
Register the `py:type` role for references to type aliases. The `type` object kind must also be addressable through the generic `py:obj` role. Resolve references through the Python domain’s existing object lookup and resolution machinery, honoring module and class context and resolving aliases by their documented name or registered canonical target. A resolved reference links to the alias’s registered target; tests must verify resolution rather than only pending cross-reference creation.

## Index entries
Preserve inherited index controls. For a module-level alias, format the entry as the alias name followed by “(in module …)” when a module is available; without a module, use the alias name alone. Do not label a module-less alias as a built-in type alias.

For an alias documented in a class context, format the entry as the alias name followed by “(type alias in …)” and identify the containing class. Include the module in that class qualification only when the configuration to add module names is enabled.

## Architecture and dependencies
Implement the alias as a Python-domain object using the existing `PyObject` behavior, annotation parser, and Python-domain cross-reference machinery. Register the object kind, directive, and roles in the Python domain, including both the type-specific and generic object roles. Add no external dependencies or separate rendering or resolution path.

## Documentation and compatibility
Document the directive, its optional description body, the `canonical` option as the represented type expression, and the cross-reference role on the Python-domain user documentation page. Include explanatory usage examples and the feature’s version note consistently with the surrounding documentation. Add a feature entry to `CHANGES.rst` following the project’s new-feature convention. Preserve existing Python-domain behavior.

## Acceptance criteria
Add regression tests for directive and role registration; the “type” signature prefix and “type alias” object-kind label; aliases with and without a canonical expression; parsed annotation expressions; canonical-target lookup; generic `py:obj` lookup; module-level and class-context aliases; rejection of nested contents; exact index wording with and without a module and in class context with module-name configuration both enabled and disabled; and resolution of both type-specific and generic object references to a documented alias. Ensure the user documentation describes the `canonical` option as the represented type expression, and that the changelog describes the feature. Verify existing Python-domain behavior remains covered.
