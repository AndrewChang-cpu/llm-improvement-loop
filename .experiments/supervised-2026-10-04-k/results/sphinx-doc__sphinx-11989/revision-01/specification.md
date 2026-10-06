## Purpose
Add Python-domain support for documenting type aliases and linking to them through cross-references.

## Behavior
- Provide the py:type directive and the py:type cross-reference role. Register the directive, object type, and role with PythonDomain so aliases participate in normal Python-domain indexing and cross-reference resolution.
- A directive names an alias and may omit its aliased expression. When the inherited canonical option is supplied, render its contents after the alias name as an equals annotation. Parse the expression with the existing Python annotation parser so type names become cross-referenceable nodes. Do not use the variable value option or render the expression as plain text.
- Preserve the common PyObject behavior: construct the fully qualified object name from the active module and class context, register the object and any canonical target through the Python domain, and honor inherited index controls. Alias directives accept description content and do not establish a new nesting scope.
- Generate type-alias-specific index text. For a name without a containing class, include the module context whenever a module is present, regardless of add_module_names; without a module, use the bare alias name. For a nested alias, identify it as a type alias in its containing class. Qualify that class with its module only when a module is present and add_module_names is enabled. This configuration condition applies only to the containing-class qualification in the nested case; it must not suppress module context for an unqualified alias.
- Use the ordinary Python-domain cross-reference machinery for the py:type role, including references to aliases and parsed type names in alias expressions.

## Architecture and conventions
Implement the directive alongside the existing Python object directives in the Python-domain component. Subclass PyObject and use its signature handling, target and index registration, and shared object options. Add only the alias-specific canonical option and signature-prefix behavior; use the existing annotation parser and Python-domain object and role registration. Do not introduce a separate rendering or resolution path or new dependencies.

## Acceptance criteria
Add regression coverage in the existing Python-domain tests for directive registration and object registration, an alias with and without a canonical expression, parsed and cross-referenceable names inside an expression, the py:type role resolving aliases, nested alias index wording, and module-level index wording with add_module_names both enabled and disabled. Verify that module context remains present for an unqualified alias in both configuration states, and that the configuration gates only module qualification of the containing class for a nested alias. Retain coverage for inherited object behavior and ensure the tests exercise the feature rather than only its displayed name.
