Cosmology parameter mapping attributes

## Goals
- Give `Cosmology` two public, read-only mapping attributes: `parameters` (non-derived parameters) and `derived_parameters` (derived parameters, such as Ode0 for flat cosmologies, including their subclasses).
- Provide a supported way to reach the Parameter object for a named parameter through the mapping.
- Make the new mappings the single source of truth for parameter names, so the new attributes and every existing consumer (equality, cloning, non-flat conversion, string output, I/O writers) agree.

## Scope
- The feature applies to `Cosmology` and is inherited by every subclass.
- Direct class-level access to Parameter objects (for example the H0 attribute) keeps working.
- Required work: both attributes; computing their contents at class creation; replacing the legacy classification; migrating every repository use, including source and test modules, with unchanged observable behavior for existing classes; a changelog entry; tests.
- Repr and str output are not part of the contract, but must iterate over the same parameter set as the new mappings.

## Terminology
- Non-derived parameter: a Parameter definition not marked derived. Derived parameter: one marked derived.
- Read-only mapping: an immutable mapping from name to value; item assignment and deletion are rejected.
- Effective definition: for a name defined in several classes of a cosmology's hierarchy, the definition in the class nearest the cosmology class in method resolution order (MRO). Its derived status decides the mapping.
- Legacy classification: the existing class-creation step that builds per-class tuples of names from the parent's tuple and the class's own namespace only, exposed as double-underscore tuple attributes. This feature replaces it.

## Workflows
- Class access: reading `parameters` or `derived_parameters` from the class returns a read-only mapping from name to the Parameter object.
- Instance access: reading either from an instance returns a read-only mapping from name to that instance's current value.
- Ordering of `parameters`: constructor-signature names first, in signature order; remaining names follow in first-appearance order walking the hierarchy from the most basic class toward the cosmology class.
- Ordering of `derived_parameters`: same first-appearance order, with no signature reordering.
- Subclasses see their whole hierarchy, including names inherited from grandparent and further-up cosmology classes.
- Ode0: for non-flat FLRW cosmologies such as LambdaCDM, Ode0 is non-derived: in `parameters`, not `derived_parameters`. For flat FLRW cosmologies such as FlatLambdaCDM, and their subclasses, Ode0 is derived: in `derived_parameters`, not `parameters`.

## Data model
- Both mappings are computed once, at class creation, by a single classification pass over the whole hierarchy. Each maps name to the effective Parameter definition.
- The pass gathers namespace entries from every class in the MRO, including non-direct parents and non-cosmology mixins. It must not be limited to the class's own namespace, the parent's computed names, or names starting with an underscore. That limitation drops derived parameters inherited from a grandparent, such as Ode0 for a subclass of FlatLambdaCDM; fixing it is the purpose of this feature.
- When a name is defined in several classes, the effective definition applies. For example, the derived Ode0 from the flat mixin overrides the non-derived Ode0 from the FLRW base for flat cosmologies.
- The two mappings are disjoint; their union is the complete parameter set, stored privately per class. Equality and equivalence compare this union.
- The new attributes store no copy of values; values are read through the instance's own parameter attributes at access time.
- Remove the legacy classification. No second discovery algorithm may run at class creation, and the legacy double-underscore tuple attributes are deleted. Every reader, in source or tests, must read the new mappings. No reference to removed attributes remains and no compatibility alias is added.

## API contracts
- `parameters` and `derived_parameters` are available on `Cosmology` and every subclass, from both class and instances.
- Reading either returns an immutable mapping keyed by strings.
- Assigning either attribute on any instance is rejected and must not replace or shadow it. Reads still return the read-only mapping afterward.
- No other public names are added.

## Module architecture
- Implement both attributes with one shared data descriptor, which may live in the parameter package or the cosmology core module. It reads the mappings each class stores at creation under underscore-prefixed private names, and must not introduce a second registry.
- The MRO namespace-gathering helper lives in the private module `astropy/cosmology/_utils.py`, not in the public `astropy/cosmology/utils.py`, which is a deprecation shim that only forwards deprecated names. The cosmology core imports the helper from the private module.
- Dependency direction: the cosmology core may use the parameter package and the private helper. The parameter package references the cosmology class only for type checking. The helper must not import the cosmology core.

## Implementation constraints
- The descriptor must define both read and write hooks. A read-only descriptor is unacceptable because an instance attribute of the same name would shadow it.
- The read hook returns Parameter objects from the class and parameter values from an instance.
- The descriptor learns its public name from the owning class through the standard descriptor naming mechanism. Do not pass the name as a separate hand-written string.
- Migrate every internal consumer in the same change: equality and equivalence, string output, cloning and argument building, non-flat conversion, and the table, mapping, model, HTML, LaTeX, and YAML-style I/O writers. Also migrate existing test modules that read the legacy classification, such as the realization parameters test and the per-format and per-class parameter tests. Every consumer must produce the same results for every existing class as before.
- Annotations in the helper module and any new module must resolve on import at the minimum supported Python version: import every referenced name or postpone annotation evaluation. The core imports the helper at import time, so an unresolved name breaks the whole package.
- Standard library only.

## Naming
- Public names are exactly `parameters` and `derived_parameters`.
- Private helper and storage names start with an underscore.
- The rejected-write error message quotes the public attribute name.

## Validation
- New and changed source and test modules must pass the repository's ruff hook from the pre-commit configuration. No import may be unused.
- Ruff ignores E501, but the black hook enforces 88 columns. Every line the change adds or modifies must be black-stable: a statement that fits within 88 columns when joined stays on one line unless a trailing comma keeps it split; a longer statement is wrapped the way black wraps it. This includes single-line return expressions. Untouched lines are not reformatted.
- The cosmology package must import on Python 3.9, the minimum supported version.

## Error handling
- Setting `parameters` or `derived_parameters` on an instance raises AttributeError.
- The message begins with "cannot set", then the quoted attribute name, then "of", then the instance representation, and ends with a period.
- Reads on valid instances must not raise.

## Documentation
- Each public attribute has a docstring directly beneath its definition in the Cosmology class body. It states the attribute returns an immutable mapping and describes class access (Parameter objects) versus instance access (values). Runtime-attached documentation is not acceptable.
- Add a changelog fragment in the cosmology changes directory, named with the pull request number and typed as a feature, stating both properties return read-only dictionaries and describing the class versus instance difference.

## Compatibility
- Class-level Parameter access and instance value reads are unchanged. Ode0 on the FLRW base remains non-derived for non-flat cosmologies.
- Removing the legacy tuples is not a public contract change. For every shipped class, equality, equivalence, cloning, non-flat conversion, and every I/O writer must produce the same results as before.
- Replacing class-level Parameter access with a dataclass-based scheme is out of scope.

## Operations
- No operational changes are required.

## Behavioral acceptance criteria
- From the class, both attributes return read-only mappings whose values are Parameter objects. From an instance, both return read-only mappings whose values equal the instance's parameter values.
- For a flat cosmology class, `derived_parameters` includes Ode0; so does a subclass of it and a subclass of that subclass. For LambdaCDM, `parameters` includes Ode0 and `derived_parameters` does not.
- Assigning either attribute on an instance raises AttributeError with the Error handling message, and the attribute still behaves as before. Returned mappings reject item assignment.
- For a Parameter defined on a non-cosmology mixin, the mappings, equality, cloning, and I/O writers treat that name as a parameter of the class.
- For every shipped class, equality, equivalence, cloning, non-flat conversion, and table, mapping, and model I/O outputs match pre-change results. No reads of the removed legacy tuples remain, and the realization parameter-values test still checks every value against the realization's parameter mapping.
- The cosmology package imports on Python 3.9.

## Test requirements
- Tests cover class and instance reads of both attributes, the derived split, inheritance into subclasses (including a grandchild of a flat cosmology), and rejected instance assignment for both names. Place them beside the existing cosmology parameter tests, following their layout.
- Migrate existing tests that read the legacy classification to the new mappings. Each keeps its original assertions in the same method and is not deleted or weakened. For example, the realization test iterates the realization's parameter mapping and compares each value with the mapping's entry for that name.
- Keep assertions in the method whose name and docstring describe them. Do not move existing assertions into new methods or repurpose existing methods; existing method bodies change only for the migration. For example, the check that a subclass may not take Ode0 in its initializer stays in the existing flat-subclass initialization test, while checks for subclasses of flat cosmologies go in a new method.
- Run rejected-assignment tests only against instances created through the normal `Cosmology` initialization path. Stub classes that bypass it fail with an unrelated error, because the message formats the instance representation, which reads the instance name.
- Every fixture a test uses must be available to it: defined in the same class, inherited from a shared mixin, or provided by a shared conftest.
- A test that defines a new cosmology subclass must remove its registration with the registry-cleanup fixture from the cosmology test helper.
- Mixin tests run for every cosmology test class, including classes with no derived parameters. Do not take the first item of an iterator over the derived mapping unguarded; an empty mapping raises StopIteration, which a TypeError expectation does not catch. Compare key sets instead.
- Stub cosmologies for a non-cosmology mixin's parameter must not be cloned or rebuilt from their mapping unless their constructor accepts every name in it, because cloning passes all parameters to the constructor. For such stubs, check membership and Parameter type through the mappings.
- A stub overriding an attribute inherited from a cosmology base must keep the base's kind: a base property is overridden by a property, not a method.
- Add a direct unit test for the private MRO helper in the existing private cosmology utilities test module. It checks that base-class names are included, that a nearer definition overrides a farther one, and that the helper does not add gathered names to the subclass's own namespace.
- Ode0 assertions follow Workflows. Do not assert that the legacy tuples agree with the new mappings.
