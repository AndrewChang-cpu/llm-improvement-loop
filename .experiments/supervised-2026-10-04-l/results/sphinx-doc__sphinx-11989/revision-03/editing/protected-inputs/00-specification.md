# Python type-alias documentation

## Purpose and scope
Add support for documenting Python type aliases as Python-domain objects and cross-referencing them. Keep the feature within the existing Python-domain object, annotation, and cross-reference machinery.

## Directive and signature behavior
Register the `py:type` directive as a Python object type displayed as “type alias.” It accepts an alias name and an optional description body, but does not allow nested contents. It inherits the Python-object options, including module context, canonical naming, annotation metadata, and index controls.

Display the `type` prefix before the alias name. The alias may be documented without a canonical expression. When the inherited `canonical` option is supplied, display its value after an equals sign and parse it with the existing Python annotation parser so referenced Python types become normal cross-references. Preserve inherited behavior that registers the canonical value as an aliased Python-domain target.

Use inherited Python-object name handling and registration. An alias documented in a class context includes that containing class in its full name and target, even though alias directive contents cannot be nested.

## Cross-reference behavior
Register the `py:type` role for references to type aliases. Resolve references through the Python domain’s existing object lookup and resolution machinery, honoring module and class context and resolving aliases by their documented name or registered canonical target. Tests must verify that a reference to a documented alias resolves to a link to that alias’s target; checking only that role parsing creates a pending cross-reference is insufficient.

## Index entries
Preserve inherited index controls. For a module-level alias, format the entry as the alias name followed by “(in module …)” when a module is available; without a module, use the alias name alone. Do not label a module-less alias as a built-in type alias.

For an alias documented in a class context, format the entry as the alias name followed by “(type alias in …)” and identify the containing class. Include the module in that class qualification only when the configuration to add module names is enabled.

## Architecture and dependencies
Implement the alias as a Python-domain object using the existing `PyObject` behavior, annotation parser, and Python-domain cross-reference machinery. Register the object type, directive, and role in the Python domain. Add no external dependencies or separate rendering or resolution path.

## Documentation and compatibility
Document the directive, its optional description body, the canonical option, and the cross-reference role on the Python-domain user documentation page. Include explanatory usage examples and the feature’s version note consistently with the surrounding documentation. Add a feature entry to `CHANGES.rst` following the project’s new-feature convention. Preserve existing Python-domain behavior.

## Acceptance criteria
Add regression tests for directive and role registration; aliases with and without a canonical expression; parsed annotation expressions; canonical-target lookup; module-level and class-context aliases; rejection of nested contents; exact index wording with and without a module and in class context with module-name configuration both enabled and disabled; and resolution of a `py:type` reference to a documented alias. Ensure the user documentation and changelog describe the feature, and verify existing Python-domain behavior remains covered.
