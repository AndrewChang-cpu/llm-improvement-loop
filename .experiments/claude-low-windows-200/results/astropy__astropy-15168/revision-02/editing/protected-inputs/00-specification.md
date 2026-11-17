Cosmology parameter mapping attributes

## Goals
- Give `Cosmology` two public, read-only mapping attributes: `parameters` (the non-derived parameters) and `derived_parameters` (the derived parameters, for example Ode0 for flat cosmologies, including flat cosmologies' subclasses).
- Provide a supported way to reach the Parameter object for a named parameter through the mapping, so that users do not depend on class-level attribute access to a Parameter.

## Scope
- The feature applies to the `Cosmology` base class and is inherited by every subclass.
- Direct class-level access to Parameter objects (for example the H0 attribute on the class) keeps working and is not removed.
- Required work is limited to: the two attributes, computing their contents when each class is created, a changelog entry, and tests.
- The repr and str output are not part of this feature's contract. The reference reformats them to iterate over the new mapping; doing so is permitted but not required.
- Replacing the existing internal name tuples is permitted but not required. An implementation that keeps them must leave their current meaning unchanged. An implementation that replaces them must migrate every internal consumer, including the I/O modules, so that their behavior is unchanged.

## Terminology
- Non-derived parameter: a Parameter definition that is not marked derived.
- Derived parameter: a Parameter definition that is marked derived.
- Read-only mapping: an immutable mapping from parameter name to value. Item assignment and item deletion on the returned mapping are rejected.
- Effective definition: for a name defined in more than one class of a cosmology's class hierarchy, the definition found in the class nearest the cosmology class in method resolution order. Its derived status decides which mapping the name belongs to.

## Workflows
- Class access: reading `parameters` or `derived_parameters` from the class returns a read-only mapping from parameter name to the Parameter object itself.
- Instance access: reading either attribute from an instance returns a read-only mapping from parameter name to that instance's current parameter value.
- Ordering: non-derived names follow the order of the constructor signature, with any names not in the signature placed at the end.
- Subclass access: a subclass sees the parameters of its whole class hierarchy, including parameters inherited from grandparent and further-up cosmology classes.
- Ode0 membership: for a non-flat FLRW cosmology such as LambdaCDM, Ode0 is a non-derived parameter. It appears in `parameters` and not in `derived_parameters`. For a flat FLRW cosmology such as FlatLambdaCDM, Ode0 is derived. It appears in `derived_parameters` and not in `parameters`. Subclasses of a flat cosmology report Ode0 in `derived_parameters` in the same way.

## Data model
- The non-derived mapping and the derived mapping are computed when each cosmology class is created. Each is a read-only mapping from name to the effective Parameter definition.
- The collection must consider Parameter definitions from every class in the cosmology class's method resolution order, including classes that are not direct parents. It must not be limited to the class's own namespace, nor to the parent's already-computed non-derived names. Limiting it that way drops derived parameters inherited from a grandparent, such as Ode0 for a subclass of FlatLambdaCDM.
- When a name is defined in more than one class of the hierarchy, the effective definition applies, as defined in Terminology. For example, the derived Ode0 defined by the flat mixin overrides the non-derived Ode0 defined by the FLRW base class for flat cosmologies.
- The two mappings are disjoint, and their union is the complete set of parameters for the class.
- The non-derived mapping keeps the constructor-signature ordering described under Workflows.
- The new attributes do not store a copy of parameter values. Values are read through the instance's own parameter attributes at access time.

## API contracts
- `parameters` and `derived_parameters` are attributes available on `Cosmology` and on every subclass, both from the class and from instances.
- Reading either attribute returns an immutable mapping keyed by strings. Its keys are exactly the names in that mapping.
- Assigning a value to either attribute on any instance is rejected and must not replace or shadow the attribute. After a rejected assignment, reading the attribute still returns the read-only mapping.
- No other public names are added by this feature.

## Module architecture
- Implement both attributes with one shared descriptor mechanism. The descriptor may live in the parameter package or in the cosmology core module; either placement is acceptable.
- The descriptor must read the parameter mappings that each class computes from its hierarchy at creation time, stored on the class under underscore-prefixed private names. It must not introduce a second registry of parameters.
- A small helper that gathers class-namespace entries across the method resolution order may live in the cosmology utilities module.
- Dependency direction must be preserved: the cosmology core may use the parameter package, and the parameter package must reference the cosmology class only for type checking, not at runtime.

## Implementation constraints
- The descriptor must be a data descriptor, meaning it defines both the read and the write hooks. A descriptor that defines only the read hook is not acceptable, because an instance attribute of the same name would shadow it.
- The read hook must return Parameter objects when accessed from the class and parameter values when accessed from an instance.
- The descriptor must learn its public attribute name from the owning class when the class is created, using the standard descriptor naming mechanism. The name must not be supplied by hand as a separate string.
- Use the standard library only. No new dependency is permitted.

## Naming
- The public names are exactly `parameters` and `derived_parameters`.
- Any private helper names use a leading underscore.
- The error message for rejected writes must quote the public attribute name.

## Error handling
- Any attempt to set `parameters` or `derived_parameters` on an instance raises AttributeError.
- The message begins with "cannot set", then the quoted attribute name, then "of", followed by the instance representation. This follows the convention already used by Parameter for rejected writes.
- Reads on valid instances must not raise.

## Documentation
- Each public attribute is documented by a docstring placed directly beneath its definition in the Cosmology class body, so that documentation tools pick it up. The docstring states that the attribute returns an immutable mapping and describes the difference between class access (Parameter objects) and instance access (values). Attaching documentation at runtime is not acceptable.
- Add a changelog fragment in the cosmology changes directory of the docs, named with the pull request number and typed as a feature. It describes the two properties, that they return read-only dictionaries, and the class versus instance difference.

## Compatibility
- Class-level access to Parameter objects, such as the H0 attribute on the class, continues to work unchanged.
- Reading parameter values from instances is unchanged.
- The Ode0 definition on the FLRW base class remains a non-derived parameter for non-flat cosmologies.
- Future removal or dataclass-based replacement of class-level Parameter access is out of scope for this feature.

## Operations
- No operational changes are required.

## Behavioral acceptance criteria
- From the class, `parameters` returns a read-only mapping whose values are Parameter objects, and `derived_parameters` returns the same kind of mapping for derived parameters.
- From an instance, both attributes return read-only mappings whose values equal the instance's parameter values.
- For a flat cosmology class, `derived_parameters` includes Ode0.
- For a subclass of a flat cosmology, and for a subclass of that subclass, `derived_parameters` includes Ode0.
- For a non-flat cosmology class such as LambdaCDM, `parameters` includes Ode0 and `derived_parameters` does not.
- Assigning to `parameters` or `derived_parameters` on an instance raises AttributeError with the message described under Error handling, and the attribute still behaves as before afterwards.
- The returned mappings reject item assignment.
- Class-level access to a Parameter by its name still returns the Parameter object.

## Test requirements
- Tests cover class and instance reads of both attributes, the derived split, inheritance into subclasses (including a grandchild of a flat cosmology), and rejected instance assignment for both names.
- Tests are placed next to the existing cosmology parameter tests, following their layout.
- Every fixture a test uses must be available to that test: either defined in the same test class, inherited from a shared mixin, or provided by an existing shared conftest. Do not reference a fixture that exists only as a method of an unrelated test class.
- A test that defines a new cosmology subclass must remove the registration it creates, using the registry-cleanup fixture from the cosmology test helper, as the neighboring tests do.
- Mixin tests run for every cosmology test class, including classes with no derived parameters. They must not call next() on an iterator over the derived mapping, because an empty mapping raises StopIteration, which pytest.raises(TypeError) does not catch. Compare key sets, or iterate in a way that is safe for empty mappings.
- Assertions about Ode0 must follow the rule in Workflows: Ode0 is in `parameters` for non-flat classes and in `derived_parameters` for flat classes and their subclasses. Assertions must match the behavior the implementation is required to produce, so that a test would pass when the code is correct.

