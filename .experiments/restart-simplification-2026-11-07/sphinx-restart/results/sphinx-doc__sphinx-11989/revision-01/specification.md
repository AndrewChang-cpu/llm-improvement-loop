## Goals
Add Python-domain support for documenting type aliases and referring to them through the existing Python cross-reference system. Preserve the domain’s existing object handling and registration conventions.

## Workflows
A document can declare a type alias at module level or within a class context. Its alias expression is optional. When supplied through the `canonical` option, render it as part of the signature and parse it as a Python annotation so referenced types participate in normal cross-reference resolution. A declaration without an expression still documents and indexes the alias.

## Data model
Treat each alias as a Python-domain object with the `type` object type. Register its qualified name as the primary object. When `canonical` is present, also register that name as an aliased target for the same object.

## API contracts
Provide the `py:type` directive and the `py:type` cross-reference role. The directive accepts the shared `PyObject` options, including `canonical`; do not substitute a `value` option or add variable-specific options. The signature begins with the type-alias prefix. The optional canonical expression follows the alias name, is parsed by the existing annotation parser, and retains its annotation structure and cross-reference nodes. The role resolves aliases through the Python domain’s normal object lookup.

## Module architecture
Implement the alias object in the existing Python-domain component as a `PyObject` specialization, and register it in the domain’s object types, directives, and roles. Use the inherited Python-object signature and target handling, including module and class context, indexing hooks, and canonical alias registration. Do not implement it as a variable specialization or create a separate rendering or cross-reference path.

## Naming
Use `type` for the Python-domain object type, directive, and role, and `canonical` for the optional alias expression. Use type-alias terminology in user-visible index entries.

## Behavioral acceptance criteria
- Module-level and class-scoped aliases are documented with the correct qualified names and Python-domain cross-references.
- Omitting `canonical` remains valid and does not prevent documenting or cross-referencing the alias.
- When present, `canonical` is rendered with a type prefix and its expression is parsed into annotation nodes, allowing referenced types to resolve through normal Python-domain cross-referencing.
- Index entries identify nested aliases as type aliases in their containing class; module-level aliases use the existing module-aware index convention.
- Existing Python-domain behavior and shared `PyObject` options remain available.

## Test requirements
Add focused regression coverage for the directive and role, including an alias with and without `canonical`, annotation cross-references in the expression, module-level and class-scoped names, and the type-alias index text. Exercise the behavior through the existing Python-domain test conventions; documentation examples alone are insufficient.
