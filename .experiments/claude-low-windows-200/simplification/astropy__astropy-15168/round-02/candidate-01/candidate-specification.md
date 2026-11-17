Cosmology parameter mapping attributes

## Goals
- Give `Cosmology` two public, read-only mapping attributes: `parameters` (non-derived parameters) and `derived_parameters` (derived parameters, such as Ode0 for flat cosmologies, including their subclasses).
- Provide a supported way to reach the Parameter object for a named parameter through the mapping, so users need not rely on class-level attribute access.
- Make the new mappings the single source of truth for a cosmology class's parameter names. Equality, cloning, non-flat conversion, string output, and I/O writers must all agree with them.

## Scope
- The attributes belong to the `Cosmology` base class and are inherited by every subclass.
- Direct class-level access to Parameter objects, such as the H0 attribute on the class, keeps working.
- Required work: the two attributes; computing their contents at class creation; replacing the legacy classification; migrating every repository use of it, including source and existing test modules; a changelog entry; and tests.
- Repr and str formatting is not part of the contract. It may change, provided it iterates over the same parameter set as the new mappings.

## Terminology
- Non-derived parameter: a Parameter definition not marked derived.
- Derived parameter: a Parameter definition marked derived.
- Read-only mapping: an immutable mapping from name to value. Item assignment and deletion are rejected.
- Effective definition: for a name defined in several classes of a cosmology's hierarchy, the definition in the class nearest the cosmology class in method resolution order (MRO). Its derived status decides which mapping the name belongs to.
- Legacy classification: the existing class-creation step that builds per-class tuples of parameter names from the parent's tuple and the class's own namespace only, exposed as double-underscore tuple attributes for non-derived and all names. This feature replaces it.

## Workflows
- Class access: reading `parameters` or `derived_parameters` from the class returns a read-only mapping from name to the Parameter object.
- Instance access: reading either from an instance returns a read-only mapping from name to that instance's current value.
- Ordering of `parameters`: names in the constructor signature come first, in signature order. Remaining names follow in first-appearance order when walking the hierarchy from the most basic class toward the cosmology class.
- Ordering of `derived_parameters`: first-appearance order in the same walk, with no signature reordering.
- Subclasses see the parameters of their whole hierarchy, including those inherited from grandparent and further-up cosmology classes.
- Ode0: for non-flat FLRW cosmologies such as LambdaCDM, Ode0 is non-derived and appears in `parameters` only. For flat FLRW cosmologies such as FlatLambdaCDM, and their subclasses, Ode0 is derived and appears in `derived_parameters` only.

## Data model
- The non-derived mapping and the derived mapping are computed once, at class creation, by a single classification pass over the whole hierarchy. Each maps name to the effective Parameter definition and is read-only.
- The pass gathers namespace entries from every class in the MRO, including non-direct parents and non-cosmology mixins. It must not be limited to the class's own namespace, the parent's computed names, or names starting with an underscore. The legacy limitation drops derived parameters inherited from a grandparent, such as Ode0 for a subclass of FlatLambdaCDM; fixing that is the purpose of this feature.
- When a name is defined in several classes, the effective definition applies. For example, the derived Ode0 from the flat mixin overrides the non-derived Ode0 from the FLRW base for flat cosmologies.
- The two mappings are disjoint. Their union is the complete parameter set for the class and is stored privately per class. Equality and equivalence compare this union.
- The attributes store no copy of parameter values. Values are read through the instance's own parameter attributes at access time.
- The legacy classification must be removed. No second discovery algorithm may run at class creation, and the legacy double-underscore tuples are deleted. Every reader of them, in source or tests, must use the new mappings. No reference to the removed attributes and no compatibility alias may remain.

## API contracts
- `parameters` and `derived_parameters` are available on `Cosmology` and every subclass, from both the class and instances.
- Reading either returns an immutable mapping keyed by strings.
- Assigning either attribute on any instance is rejected and must not replace or shadow it. After a rejected assignment, reads still return the read-only mapping.
- No other public names are added. The removed legacy tuples were internal.

## Module architecture
- Implement both attributes with one shared data descriptor. It may live in the parameter package or in the cosmology core module.
- The descriptor reads the mappings each class computes at creation, stored on the class under underscore-prefixed private names. It must not introduce a second registry.
- The MRO namespace-gathering helper lives in the private module `astropy/cosmology/_utils.py`. The public `astropy/cosmology/utils.py` is a deprecation shim that only forwards deprecated names and must not hold it. The cosmology core imports the helper from the private module.
- Dependency direction: the cosmology core may use the parameter package and the private helper. The parameter package references the cosmology class only for type checking, never at runtime. The helper must not import the cosmology core.

## Implementation constraints
- The descriptor must be a data descriptor, defining both read and write hooks. A read-only descriptor is unacceptable because an instance attribute of the same name would shadow it.
- The read hook returns Parameter objects when accessed from the class and parameter values when accessed from an instance.
- The descriptor learns its public name from the owning class through the standard descriptor naming mechanism. Do not pass the name as a separate hand-written string.
- Migrate every internal consumer in the same change: equality and equivalence, string output, cloning and argument building, non-flat conversion, and the table, mapping, model, HTML, LaTeX, and YAML-style I/O writers that read parameter names. Also migrate existing test modules that read the legacy classification, such as the realization parameters test and the per-format and per-class parameter tests. Every consumer must produce the same results for every existing cosmology class as before.
- Annotations in the private helper and in any new module must resolve on import at the minimum supported Python version. Either import every referenced name or postpone annotation evaluation. The cosmology core imports the helper at import time, so an unresolved name breaks the whole package.
- Standard library only. No new dependency is permitted.

## Naming
- The public names are exactly `parameters` and `derived_parameters`.
- Private helper and storage names start with an underscore.
- The rejected-write error message quotes the public attribute name.

## Validation
- New and changed source and test modules must pass the repository's ruff hook from the pre-commit configuration. No import may be unused.
- Ruff ignores E501, but the black hook enforces 88 columns. For every line the change adds or modifies, the statement must be black-stable: a statement that fits within 88 columns when joined stays on one line unless a trailing comma keeps it split, and a longer statement is wrapped the way black wraps it. This includes single-line return expressions such as the equality and equivalence comparisons. Untouched lines are not reformatted.
- Importing the cosmology package must succeed on Python 3.9, the minimum supported version.

## Error handling
- Setting `parameters` or `derived_parameters` on an instance raises AttributeError.
- The message begins with "cannot set", then the quoted attribute name, then "of", then the instance representation, and ends with a period.
- Reads on valid instances must not raise.

## Documentation
- Each public attribute has a docstring placed directly beneath its definition in the Cosmology class body. It states that the attribute returns an immutable mapping and describes class access (Parameter objects) versus instance access (values). Runtime-attached documentation is not acceptable.
- Add a changelog fragment in the cosmology changes directory, named with the pull request number and typed as a feature. It states that both properties return read-only dictionaries and describes the class versus instance difference.

## Compatibility
- Class-level Parameter access and instance value reads are unchanged.
- Ode0 on the FLRW base remains non-derived for non-flat cosmologies.
- Removing the legacy tuples is not a public contract change. For every shipped cosmology class, equality, equivalence, cloning, non-flat conversion, and every I/O writer must produce the same results as before.
- Replacing class-level Parameter access with a dataclass-based scheme is out of scope.

## Operations
- No operational changes are required.

## Behavioral acceptance criteria
- From the class, `parameters` and `derived_parameters` return read-only mappings whose values are Parameter objects.
- From an instance, both return read-only mappings whose values equal the instance's parameter values.
- For a flat cosmology class, `derived_parameters` includes Ode0. The same holds for its subclass and for a subclass of that subclass.
- For LambdaCDM, `parameters` includes Ode0 and `derived_parameters` does not.
- Assigning either attribute on an instance raises AttributeError with the Error handling message, and the attribute still behaves as before.
- Returned mappings reject item assignment.
- Class-level access to a Parameter by name still returns the Parameter object.
- For a Parameter defined on a non-cosmology mixin in the hierarchy, the mappings, equality, cloning, and I/O writers all treat that name as a parameter of the class.
- For every shipped cosmology class, equality, equivalence, cloning, non-flat conversion, and table, mapping, and model I/O outputs match pre-change results.
- No reads of the removed legacy tuples remain in the repository. The realization parameter-values test still checks every parameter value against the realization's parameter mapping.
- The cosmology package imports on Python 3.9.

## Test requirements
- Tests cover class and instance reads of both attributes, the derived split, inheritance into subclasses (including a grandchild of a flat cosmology), and rejected instance assignment for both names.
- Place tests beside the existing cosmology parameter tests, following their layout.
- Migrate existing tests that read the legacy classification to the new mappings. Each keeps its original assertions in the same method and is not deleted or weakened. For example, the realization test iterates the realization's parameter mapping and compares each value with the mapping's entry for that name.
- Keep assertions in the method whose name and docstring describe them. Existing method bodies change only for the migration. New checks go in a new method named and documented for that behavior. For example, the check that a subclass may not take Ode0 in its initializer stays in the existing flat-subclass initialization test, while checks for subclasses of flat cosmologies go in a new method.
- Run rejected-assignment tests only against instances created through the normal `Cosmology` initialization path. Stub classes that bypass it are not allowed, because the error message formats the instance representation, which reads the instance name; an unset name causes an unrelated error.
- Every fixture a test uses must be available to it: defined in the same class, inherited from a shared mixin, or provided by a shared conftest. Do not reference a fixture that exists only as a method of an unrelated test class.
- A test that defines a new cosmology subclass must remove its registration with the registry-cleanup fixture from the cosmology test helper, as neighboring tests do.
- Mixin tests run for every cosmology test class, including classes with no derived parameters. Do not take the first item of an iterator over the derived mapping unguarded, since an empty mapping raises StopIteration, which a TypeError expectation does not catch. Compare key sets or iterate in a way safe for empty mappings.
- Stub cosmologies for a non-cosmology mixin's parameter must not be cloned or rebuilt from their mapping unless their constructor accepts every name in it. Cloning passes all parameters, including inherited base-class ones, so a narrower constructor raises an unrelated TypeError. For such stubs, check membership and Parameter type through the mappings.
- A stub that overrides an attribute inherited from a cosmology base must keep the base's kind: a base property is overridden by a property, and the stub must not call it as a method.
- Add a direct unit test for the private MRO helper in the existing private cosmology utilities test module. It checks that base-class names are included, that a nearer definition overrides a farther one, and that the helper does not add gathered names to the subclass's own namespace.
- Ode0 assertions follow Workflows: in `parameters` for non-flat classes, in `derived_parameters` for flat classes and their subclasses.
- Do not assert that the legacy tuples agree with the new mappings.
