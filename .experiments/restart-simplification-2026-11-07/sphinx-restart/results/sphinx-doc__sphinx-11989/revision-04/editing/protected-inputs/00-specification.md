## Goals
Add support in the Python domain for documenting type aliases and referring to them through the existing Python cross-reference system. Preserve the domain’s existing object handling and registration conventions.

## Workflows
A type alias can be declared at module level or within a class context. A class-scoped alias is an alias whose declaration appears in that class context; this does not make the alias directive a container for nested object declarations. The alias expression is optional. When supplied through the canonical option, render it after the alias name, separated by an equals sign, and parse it as a Python annotation so referenced types participate in normal cross-reference resolution. A declaration without an expression still documents and indexes the alias. The directive may contain a description body, while retaining the inherited PyObject behavior that disallows nested object contents.

## Data model
Treat each alias as a Python-domain object with the object type name “type”. Its public object-type label is “type alias”, and its cross-reference types include “type” and “obj”. Register its qualified name as the primary object. When canonical is present, register that name as an aliased target for the same object.

## API contracts
Provide the py:type directive and the py:type cross-reference role. The directive retains the shared PyObject options, including the optional canonical option, and does not add the variable-specific type or value options. Its signature begins with the prefix “type”. When canonical is present, render an equals sign between the alias name and expression, parse the expression with the existing annotation parser, and retain its annotation structure and cross-reference nodes. The role resolves aliases through the Python domain’s normal object lookup and cross-reference resolution. The directive retains PyObject’s non-nestable behavior: it does not allow nested object contents, even though an alias may be declared within a class context.

Index text follows the Python domain’s existing module-name configuration. A module-level alias uses the form “Alias (in module example)” when a module is set, and otherwise uses the alias name. A nested alias uses the form “Alias (type alias in example.Class)”; include the module prefix on the containing class when module names are configured.

## Module architecture
Implement the alias object in the existing Python-domain component as a PyObject specialization, and register its object type, directive, and role in the Python domain. Use inherited Python-object signature and target handling, including module and class context, indexing hooks, canonical alias registration, and non-nestable behavior. Use the existing annotation parser and Python-domain cross-reference machinery; do not create a separate rendering or cross-reference path.

## Naming
Use “type” for the Python-domain object type, directive, and role, and “canonical” for the optional alias expression. Use “type alias” as the public object-type label and in user-visible index entries for nested aliases.

## Documentation
Document the py:type directive and py:type role in the Python-domain documentation. Explain that canonical describes the represented type, is optional, and is rendered in the directive signature. Document that the directive supports an optional description body and describe the alias cross-reference role. Add a feature bullet to CHANGES.rst under the current release’s Features added section identifying the directive and role.

## Behavioral acceptance criteria
- Module-level and class-scoped aliases are documented with the correct qualified names and Python-domain cross-references.
- A class-scoped alias is supported without making the alias directive itself permit nested object contents.
- Omitting canonical remains valid and does not prevent documenting or cross-referencing the alias.
- When present, canonical is rendered after the alias name with an equals sign, and its expression is parsed into annotation nodes so referenced types can resolve through normal Python-domain cross-referencing.
- Module-level and nested index text follows the reference forms and respects the configured module-name behavior for nested aliases.
- The public object-type label is “type alias”, while the object type name and directive and role name are “type”.
- Existing Python-domain behavior and shared PyObject options remain available.
- A py:type reference to a declared module-level or nested alias resolves to that alias’s target.

## Test requirements
Add focused regression coverage for the directive and role, including aliases with and without canonical, annotation cross-references in the expression, module-level and class-scoped names, signature prefix and separator, module-level and nested index text with module-name configuration, object-type label and registration, and role resolution. Include an inline py:type reference to a declared module-level or nested alias and verify that resolution produces a link to the alias target; checking role registration or domain lookup alone does not cover role parsing and resolution. Verify that the directive disallows nested object contents while a type alias declared within a class context is still handled correctly. Exercise the behavior through the existing Python-domain test conventions; documentation examples alone are insufficient regression tests.
