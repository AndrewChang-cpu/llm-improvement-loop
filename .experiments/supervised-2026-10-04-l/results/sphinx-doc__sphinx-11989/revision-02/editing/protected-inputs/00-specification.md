# Python type-alias documentation

## Purpose
Add Python-domain support for documenting type aliases and cross-referencing them as Python objects. Keep alias documentation within the existing Python-domain object and cross-reference machinery.

## Directive and role
Register the `py:type` directive as a Python object type displayed as “type alias,” and register the `py:type` cross-reference role. The directive accepts an alias name and an optional description body, but does not allow nested contents. It supports the inherited Python-object options, including module context, canonical naming, annotation metadata, and index controls.

The signature displays the `type` prefix before the alias name. An alias can be documented without a canonical expression. When the inherited `canonical` option is supplied, display its value after an equals sign and parse it with the existing Python annotation parser so referenced Python types become ordinary Python cross-references. The canonical name is also registered as an aliased target for the Python domain.

## Naming, nesting, and cross-references
Use inherited Python-object name handling and domain registration. An alias documented in a class context retains the containing class in its full name and target. This class context support does not permit nested contents within the alias directive. Preserve normal Python-domain resolution for the `py:type` role, including module and class context and cross-references to aliases.

## Index entries
Preserve inherited index controls. For an alias without a containing class, use its bare name when no module is available; when a module is available, identify the name as being in that module. For an alias in a containing class, identify it as a type alias in that class. Include the module in that class qualification only when module names are configured to be added. Do not label an alias with no module as a built-in type alias.

## Architecture and compatibility
Implement the alias as a Python-domain object using the existing `PyObject` behavior, annotation parser, and domain cross-reference machinery. Register the object type, directive, and role in the Python domain. Preserve existing Python-domain behavior and introduce no external dependency.

## Acceptance criteria
Add regression coverage for directive and role registration; aliases with and without a canonical expression; annotation expressions that produce cross-reference nodes; canonical-name lookup; module-level and class-context aliases; rejection of nested contents within an alias directive; and index text for aliases with and without a module and with a containing class. Verify that existing Python-domain tests continue to pass.
