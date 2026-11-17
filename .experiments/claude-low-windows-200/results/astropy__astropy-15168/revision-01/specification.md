Cosmology parameter mapping attributes

## Goals
- Give `Cosmology` two public, read-only mapping attributes: `parameters` (the non-derived parameters) and `derived_parameters` (the derived parameters, for example the Ode0 parameter of flat cosmologies).
- Provide a supported way to reach the Parameter object for a named parameter through the mapping, so that users do not depend on class-level attribute access to a Parameter.

## Scope
- The feature applies to the `Cosmology` base class and is therefore inherited by every subclass.
- Direct class-level access to Parameter objects (for example the H0 attribute on the class) keeps working in this version and is not removed.
- Internal refactors are not required by this feature: changing how parameters are stored internally, changing the repr output, migrating the I/O modules, or removing existing internal name tuples are all out of scope.

## Terminology
- Non-derived parameter: a Parameter declared on a cosmology class that is not marked derived.
- Derived parameter: a Parameter declared on a cosmology class that is marked derived.
- Read-only mapping: an immutable mapping from parameter name to value. Item assignment and item deletion on the returned mapping are rejected.

## Workflows
- Class access: reading `parameters` or `derived_parameters` from the class returns a read-only mapping from parameter name to the Parameter object itself.
- Instance access: reading either attribute from an instance returns a read-only mapping from parameter name to that instance's current parameter value.
- Ordering: non-derived names follow the order of the constructor signature, with any names not in the signature placed at the end.
- Subclass access: a subclass sees the parameters of its whole class hierarchy, including parameters inherited from parent cosmology classes.

## Data model
- The non-derived and derived name sets are computed when each cosmology class is created, using the full class hierarchy. Inherited derived parameters must remain in the derived set for subclasses; for example, a subclass of a flat cosmology must still report Ode0 under derived_parameters.
- The two sets are disjoint, and their union is the complete set of parameters for the class.
- The new attributes do not store a copy of parameter values. Values are read through the instance's own parameter attributes at access time.

## API contracts
- `parameters` and `derived_parameters` are attributes available on `Cosmology` and on every subclass, both from the class and from instances.
- Reading either attribute returns an immutable mapping keyed by strings.
- Assigning a value to either attribute on any instance is rejected and must not replace or shadow the attribute. After a rejected assignment, reading the attribute still returns the read-only mapping.
- No other public names are added by this feature.

## Module architecture
- Implement both attributes with one shared descriptor mechanism. The descriptor may live in the parameter package or in the cosmology core module; either placement is acceptable.
- The descriptor must read the name sets that the class already computes from its hierarchy. It must not introduce a second registry of parameters.
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
- Each attribute has a docstring stating that it returns an immutable mapping, and describing the difference between class access (Parameter objects) and instance access (values).
- Add a changelog fragment in the cosmology changes directory of the docs, named with the pull request number and typed as a feature. It describes the two properties, that they return read-only dictionaries, and the class versus instance difference.

## Compatibility
- Class-level access to Parameter objects, such as the H0 attribute on the class, continues to work unchanged.
- Reading parameter values from instances is unchanged.
- Future removal or dataclass-based replacement of class-level Parameter access is out of scope for this feature.

## Behavioral acceptance criteria
- From the class, `parameters` returns a read-only mapping whose values are Parameter objects, and `derived_parameters` returns the same kind of mapping for derived parameters.
- From an instance, both attributes return read-only mappings whose values equal the instance's parameter values.
- For a subclass of a flat cosmology, `derived_parameters` includes Ode0.
- Assigning to `parameters` or `derived_parameters` on an instance raises AttributeError with the message described under Error handling, and the attribute still behaves as before afterwards.
- The returned mappings reject item assignment.
- Class-level access to a Parameter by its name still returns the Parameter object.

## Test requirements
- Tests cover class and instance reads of both attributes, the derived split, inheritance into subclasses, and rejected instance assignment for both names.
- Tests are placed next to the existing cosmology parameter tests, following their layout.
