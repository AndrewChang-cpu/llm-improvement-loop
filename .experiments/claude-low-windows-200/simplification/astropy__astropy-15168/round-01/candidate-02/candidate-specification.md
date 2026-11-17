Cosmology parameter mapping attributes

## Goals
- Give `Cosmology` two public, read-only mapping attributes: `parameters` (non-derived parameters) and `derived_parameters` (derived parameters, such as Ode0 for flat cosmologies, including subclasses of flat cosmologies).
- Provide a supported way to reach the Parameter object for a named parameter through the mapping, instead of class-level attribute access.
- Make the new mappings the single source of truth for parameter names, so the new attributes and every existing consumer (equality, cloning, non-flat conversion, string output, I/O writers) agree on the same names.

## Scope
- The feature applies to `Cosmology` and is inherited by every subclass.
- Direct class-level access to Parameter objects (for example the H0 attribute on the class) keeps working.
- Required work: the two attributes; computing their contents at class creation; replacing the legacy classification (see Data model); migrating every use of it in the repository, including source and existing test modules; a changelog entry; and tests.
- Repr and str output are not part of the contract. Their formatting may change, provided they iterate over the same parameter set as the new mappings.

## Terminology
- Non-derived parameter: a Parameter definition not marked derived. Derived parameter: one marked derived.
- Read-only mapping: an immutable mapping from name to value; item assignment and deletion are rejected.
- Effective definition: for a name defined in several classes of a cosmology's hierarchy, the definition in the class nearest the cosmology class in method resolution order (MRO). Its derived status decides which mapping the name belongs to.
- Legacy classification: the existing class-creation step that builds per-class tuples of names from the parent's tuple and the class's own namespace only, exposed as double-underscore tuple attributes for non-derived and all parameter names. This feature replaces it.

## Workflows
- Class access: reading `parameters` or `derived_parameters` from the class returns a read-only mapping from name to the Parameter object.
- Instance access: reading either from an instance returns a read-only mapping from name to that instance's current value.
- Ordering of `parameters`: names in the constructor signature come first, in signature order. Remaining names follow, in first-appearance order when walking the hierarchy from the most basic class toward the cosmology class.
- Ordering of `derived_parameters`: first-appearance order by the same walk. No signature reordering applies.
- Subclasses see the parameters of their whole hierarchy, including grandparents and further-up classes.
- Ode0: for a non-flat FLRW cosmology such as LambdaCDM, Ode0 is non-derived: it is in `parameters`, not `derived_parameters`. For a flat cosmology such as FlatLambdaCDM, and any subclass of one, Ode0 is derived: it is in `derived_parameters`, not `parameters`.

## Data model
- The non-derived and derived mappings are computed once, when each cosmology class is created, by a single classification pass over the whole hierarchy. Each maps name to the effective Parameter definition.
- The pass gathers namespace entries from every class in the MRO, including non-direct parents and non-cosmology mixins. It must not be limited to the class's own namespace, the parent's computed names, or names starting with an underscore. That limitation drops derived parameters inherited from a grandparent, such as Ode0 for a subclass of FlatLambdaCDM; correcting it is the point of this feature.
- When a name is defined in several classes, the effective definition applies. For example, the derived Ode0 from the flat mixin overrides the non-derived Ode0 of the FLRW base for flat cosmologies.
- The two mappings are disjoint. Their union is the complete parameter name set for the class, stored privately per class; equality and equivalence compare it.
- The new attributes store no copies of values. Values are read through the instance's parameter attributes at access time.
- The legacy classification must be removed. No second discovery algorithm may run at class creation, and the legacy double-underscore tuple attributes are removed with no compatibility alias. Every reader of them, in source and tests, must read the new mappings instead, and no reference to them may remain in the tree.

## API contracts
- `parameters` and `derived_parameters` are available on `Cosmology` and every subclass, from the class and from instances.
- Reading either returns an immutable mapping keyed by strings, whose keys are that mapping's parameter names.
- Assigning either attribute on any instance is rejected and does not replace or shadow it; afterwards reads still return the read-only mapping.
- No other public names are added. The removed legacy tuples were internal.

## Module architecture
- Implement both attributes with one shared descriptor, placed in the parameter package or the cosmology core module.
- The descriptor reads the mappings each class computes at creation, stored on the class under underscore-prefixed private names. It must not introduce a second registry.
- The MRO namespace-gathering helper lives in the private helper module `astropy/cosmology/_utils.py`, not in the public shim `astropy/cosmology/utils.py`, which only forwards deprecated names. The cosmology core imports it from the private module.
- Dependency direction: the cosmology core may use the parameter package and the private helper. The parameter package references the cosmology class only for type checking, never at runtime. The helper must not import the cosmology core.

## Implementation constraints
- The descriptor must be a data descriptor, defining both read and write hooks. A read-only descriptor is unacceptable, because an instance attribute of the same name would shadow it.
- Read hook: Parameter objects when accessed from the class; parameter values when accessed from an instance.
- The descriptor learns its public name from the owning class at creation, through the standard descriptor naming mechanism. Do not pass the name as a separate hand-written string.
- Migrate every internal consumer in the same change: equality and equivalence, string output, cloning and argument building, non-flat conversion, and the table, mapping, model, HTML, LaTeX, and YAML-style I/O writers. Equality and equivalence compare the union of names from the new mappings. Each consumer must give the same results for every existing cosmology class as before.
- Migrate existing test modules that read the legacy classification, such as the realization parameters test and the per-format and per-class parameter tests, in the same change.
- Annotations in the helper module and any new module must resolve at import on the minimum supported Python version (3.9). Either import every referenced name or postpone annotation evaluation. The core imports the helper at import time, so an unresolved name breaks the whole cosmology package.
- Standard library only. No new dependency.

## Naming
- Public names are exactly `parameters` and `derived_parameters`.
- Private helper and storage names start with an underscore.
- The rejected-write error message quotes the public attribute name.

## Validation
- New and changed source and test modules must pass the repository's ruff hook from the pre-commit configuration. No import may be unused.
- Ruff ignores E501, but the black hook enforces 88 columns. Every line the change adds or modifies must be black-stable: a statement that fits in 88 columns when joined onto one line stays joined (unless a trailing comma keeps it split), and an overlong statement is wrapped the way black wraps it. This includes single-line return expressions such as equality comparisons. Untouched lines are not reformatted.
- The cosmology package must import on Python 3.9.

## Error handling
- Setting `parameters` or `derived_parameters` on an instance raises AttributeError.
- The message begins with "cannot set", then the quoted attribute name, then "of", then the instance representation, and ends with a period.
- Reads on valid instances never raise.

## Documentation
- Each public attribute has a docstring placed directly beneath its definition in the Cosmology class body, stating that it returns an immutable mapping and describing class access (Parameter objects) versus instance access (values). Runtime-attached documentation is not acceptable.
- Add a changelog fragment in the cosmology changes directory, named with the pull request number and typed as a feature. It describes both properties, that they return read-only dictionaries, and the class versus instance difference.

## Compatibility
- Class-level Parameter access (for example `H0` on the class) and instance value reads are unchanged.
- The FLRW base Ode0 remains non-derived for non-flat cosmologies.
- For every shipped cosmology class, equality, equivalence, cloning, non-flat conversion, and every I/O writer produce the same results as before.
- Replacing class-level Parameter access with a dataclass-based design is out of scope.

## Operations
- No operational changes are required.

## Behavioral acceptance criteria
- From the class, `parameters` and `derived_parameters` return read-only mappings with Parameter object values.
- From an instance, both return read-only mappings whose values equal the instance's parameter values.
- For a flat cosmology class, `derived_parameters` includes Ode0; the same holds for a subclass and a subclass of that subclass.
- For LambdaCDM, `parameters` includes Ode0 and `derived_parameters` does not.
- Assigning either attribute on an instance raises AttributeError with the Error handling message, and the attribute still behaves as before.
- Returned mappings reject item assignment.
- Class-level access to a Parameter by name still returns the Parameter object.
- For a Parameter defined on a non-cosmology mixin in the hierarchy, the mappings, equality, cloning, and I/O writers treat the name as a class parameter.
- For every shipped cosmology class, equality, equivalence, cloning, non-flat conversion, and table, mapping, and model I/O outputs are unchanged.
- No reads of the removed legacy tuples remain, and the realization parameter-values test still checks every value against the realization's parameter mapping.
- The cosmology package imports on Python 3.9.

## Test requirements
- Tests cover class and instance reads of both attributes, the derived split, inheritance (including a grandchild of a flat cosmology), and rejected instance assignment for both names.
- Place tests next to the existing cosmology parameter tests, following their layout.
- Migrate existing tests that read the legacy classification to the new mappings. Each keeps its original assertions in the same method, and none is deleted or weakened. For example, the realization parameters test iterates the realization's parameter mapping and compares each value with the mapping's entry for that name.
- Keep assertions in the method whose name and docstring describe them. Do not move existing assertions into new methods or repurpose existing methods. Add a new, named and documented method for each new behavior. For example, the check that a subclass may not take Ode0 in its initializer stays in the existing flat-subclass initialization test, and checks for subclasses of flat cosmologies go in a new method.
- Rejected-assignment tests run only against instances built through the normal `Cosmology` initialization path, not stubs in parameter test classes that bypass it. The error message formats the instance representation, which reads the instance name; a stub that never sets it fails unrelatedly.
- Every fixture a test uses must be available to it: defined in the same class, inherited from a shared mixin, or provided by a shared conftest. Do not reference a fixture defined only as a method of an unrelated class.
- A test defining a new cosmology subclass must remove its registration with the registry-cleanup fixture from the cosmology test helper, as neighboring tests do.
- Mixin tests run for every cosmology test class, including those with no derived parameters. Do not take the first item of an iterator over the derived mapping unguarded, since an empty mapping raises StopIteration, which a TypeError expectation does not catch. Compare key sets or iterate safely on empty mappings.
- Stub cosmologies for a non-cosmology mixin must not be cloned or rebuilt from their mapping unless their constructor accepts every name in it. Cloning passes all parameters, including inherited base ones, so a narrower constructor raises an unrelated TypeError. Check membership and Parameter type through the mappings instead.
- A stub overriding an attribute inherited from a base keeps the base's kind: a base property is overridden by a property, not called as a method.
- A direct test of the private MRO helper goes in the existing private cosmology utilities test module. It checks that base-class names are included, that a nearer definition overrides a farther one, and that the helper adds nothing to the subclass's own namespace.
- Ode0 assertions follow the Workflows rule, so they pass when the code is correct.
- Tests must not assert agreement with the legacy tuples, which this feature removes.
