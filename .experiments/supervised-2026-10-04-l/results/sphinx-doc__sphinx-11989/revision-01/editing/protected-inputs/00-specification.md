# Python type-alias documentation

## Purpose
Add Python-domain support for documenting type aliases and cross-referencing them as Python objects. Keep alias documentation within the existing Python-domain object and cross-reference machinery.

## Directive and role
Register the `py:type` directive as a Python object type displayed as “type alias,” and register the `py:type` cross-reference role. The directive accepts an alias name and an optional description body. It supports the standard options inherited from Python objects, including module context, canonical naming, annotation metadata, and index controls.

The directive signature displays the `type` prefix before the alias name. An alias can be documented without an alias expression.

## Alias expression and cross-references
Use the inherited `canonical` option as the optional alias expression. When present, display it after an equals sign and parse it with the existing Python annotation parser so that referenced Python types become ordinary Python cross-references. Do not substitute a separate `value` option for this contract.

The inherited Python-object behavior also registers a supplied canonical name in the Python domain as an aliased target. Preserve normal Python-domain resolution for the `py:type` role, including module and class context and cross-references to aliases.

## Nesting and index entries
Allow aliases to be documented in module and class contexts. An alias declared in a class context must retain that containing class in its full name and index entry. Index text for a nested alias identifies it as a type alias in its containing class, qualified by the module when module names are configured. A module-level alias uses the existing module-level index convention. Preserve inherited index controls.

## Architecture and compatibility
Implement the alias as a Python-domain object using the existing `PyObject` behavior, annotation parser, and domain cross-reference machinery. Register the object type, directive, and role in the Python domain. Preserve existing Python-domain behavior and introduce no external dependency.

## Acceptance criteria
Add regression coverage for directive and role registration; aliases with and without a canonical expression; annotation expressions that produce cross-reference nodes; canonical-name lookup; module-level and class-nested aliases; and index text that retains the containing class for nested aliases. Verify that the existing Python-domain tests continue to pass.
