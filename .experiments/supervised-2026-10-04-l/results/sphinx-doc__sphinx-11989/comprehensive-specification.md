# Python type-alias documentation

## Purpose and scope
Add support for documenting Python type aliases as Python-domain objects and cross-referencing them. Keep the feature within the existing Python-domain object, annotation, indexing, and cross-reference machinery.

## Directive and signature behavior
Register the `py:type` directive as a Python object kind with the localized label “type alias.” Its signature prefix is “type.” The directive accepts an optional description body and does not allow nested contents. Its effective options must include the inherited `PyObject` options, including module context, `canonical`, annotation metadata, and index controls.

Use inherited Python-object signature parsing and name handling. An alias may be documented without a canonical expression. When `canonical` is supplied, treat its value as the represented type expression, parse it with the existing Python annotation parser, and display it after the alias name with an equals sign represented using the same signature punctuation node type as the reference implementation. Preserve the shared target-registration behavior that registers the canonical expression as an aliased Python-domain target.

Support aliases documented in ambient class context and aliases whose directive signature is class-qualified outside an ambient class context. In both cases, preserve the parsed full alias name and use it to identify the containing class for indexing. Do not require an ambient `py:class` context to recognize a dotted, class-qualified alias.

## Cross-reference behavior
Register the `py:type` role for references to type aliases. The type object kind must also be addressable through the generic `py:obj` role. Resolve references through the Python domain’s existing object lookup and resolution machinery, honoring module and class context and resolving aliases by their documented name or registered canonical target. A resolved reference links to the alias’s registered target.

## Index entries
Preserve inherited index controls. For a module-level alias with an undotted parsed name, use the alias name followed by “(in module …)” when a module is available; without a module, use the alias name alone. Do not label a module-less alias as a built-in type alias.

For an alias whose parsed name is dotted, derive the containing name from the parsed qualified alias name, including when the name was class-qualified in the directive signature outside an ambient class context. Format the entry as the final alias component followed by “(type alias in …)” and identify the preceding qualified name as its containing class. Include the module in that class qualification only when a module is available and the configuration to add module names is enabled. Apply this rule to both ambient-context and explicitly class-qualified aliases.

## Architecture and dependencies
Implement the alias as a Python-domain object using the existing `PyObject` behavior, annotation parser, target registration, and Python-domain cross-reference machinery. Register the object kind, directive, and roles in the Python domain, including both the type-specific and generic object roles. Add no external dependencies or separate rendering, naming, indexing, or resolution path.

## Documentation and compatibility
Document the directive, its optional description body, the `canonical` option as the represented type expression, and the cross-reference role on the Python-domain user documentation page. Include explanatory usage examples and the feature’s version note consistently with surrounding documentation. Add a feature entry to `CHANGES.rst` following the project’s new-feature convention. Preserve existing Python-domain behavior.

## Acceptance criteria
Add focused regression tests for directive and role registration; the “type” signature prefix and “type alias” object-kind label; effective acceptance of `canonical`; aliases with and without a canonical expression; parsed annotation expressions and canonical-target lookup; generic `py:obj` lookup; module-level and class-context aliases; rejection of nested contents; and index wording for module-level aliases, dotted class-qualified aliases outside ambient class context, and class-context aliases with module-name configuration both enabled and disabled. Verify that equals-sign rendering uses the reference signature punctuation node type and that both type-specific and generic object references resolve to the documented alias. Ensure the user documentation describes `canonical` as the represented type expression and that the changelog describes the feature. Preserve coverage of existing Python-domain behavior.
