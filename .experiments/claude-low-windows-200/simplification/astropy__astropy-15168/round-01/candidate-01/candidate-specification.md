Cosmology parameter mapping attributes

## Goals
- Give `Cosmology` two public, read-only mapping attributes: `parameters` (non-derived parameters) and `derived_parameters` (derived parameters, such as Ode0 for flat cosmologies, including subclasses of flat cosmologies).
- Provide a supported way to reach the Parameter object for a named parameter through the mapping, so users need not rely on class-level attribute access.
- Make the new mappings the single source of truth for a cosmology class's parameter names, so the new attributes and every existing consumer (equality, cloning, non-flat conversion, string output, I/O writers) agree.

## Scope
- The feature applies to `Cosmology` and is inherited by every subclass.
- Direct class-level access to Parameter objects (for example the H0 attribute on the class) keeps working.
- Required work: the two attributes; computing their contents at class creation; replacing the legacy classification (see Terminology); migrating every use of it in the repository, including source and existing test modules, with unchanged observable behavior for existing classes; a changelog entry; and tests.
- Repr and str formatting is not part of the contract, but must iterate over the same parameter set as the new mappings. Including the name in repr is permitted but not required.

## Terminology
- Non-derived parameter: a Parameter definition not marked derived. Derived parameter: one marked derived.
- Read-only mapping: an immutable mapping from parameter name to value. Item assignment and deletion are rejected.
- Parameter object: the definition instance stored as a class attribute, as returned by class access.
- Effective definition: for a name defined in several classes of a cosmology's hierarchy, the definition in the class nearest the cosmology class in method resolution order (MRO). Its derived status decides which mapping the name belongs to.
- Legacy classification: the existing class-creation step that builds per-class tuples of names from the parent's tuple and the class's own namespace only, exposed as double-underscore tuple attributes for non-derived and all parameter names. This feature replaces it.

## Workflows
- Class access: reading `parameters` or `derived_parameters` from the class returns a read-only mapping from name to the Parameter object.
- Instance access: reading either from an instance returns a read-only mapping from name to that instance's current parameter value.
- Ordering of `parameters`: names in the constructor signature come first, in signature order. Remaining names follow in first-appearance order when walking the hierarchy from the most basic class toward the cosmology class.
- Ordering of `derived_parameters`: first-appearance order in the same walk. No signature reordering applies.
- Subclasses see the parameters of their whole hierarchy, including those inherited from grandparent and further-up classes.
- A class with no derived parameters has an empty `derived_parameters` mapping. This is valid, not an error.
- Ode0: for non-flat FLRW cosmologies such as LambdaCDM, Ode0 is non-derived, so it is in `parameters` and not `derived_parameters`. For flat FLRW cosmologies such as FlatLambdaCDM, and their subclasses, Ode0 is derived, so it is in `derived_parameters` and not `parameters`.

## Data model
- The two mappings are computed once per class, at class creation, by one classification pass over the whole hierarchy. Each maps name to the effective Parameter definition.
- The pass gathers namespace entries from every class in the MRO, including non-direct parents and non-cosmology mixins. It must not be limited to the class's own namespace, the parent's computed names, or names starting with an underscore. That limitation drops derived parameters inherited from a grandparent (such as Ode0 for a subclass of FlatLambdaCDM) and is the defect this feature corrects.
- Where a name is defined in several classes, the effective definition applies. For example, the derived Ode0 from the flat mixin overrides the non-derived Ode0 of the FLRW base for flat cosmologies.
- Remove the legacy classification entirely: no second discovery algorithm runs at class creation, the double-underscore tuple attributes are removed, every reader of them in source and tests reads the new mappings, and no compatibility alias is added. No reference to the removed attributes may remain in the tree.
- The two mappings are disjoint. Their union is the complete parameter name set, stored privately per class; equality and equivalence compare this union.
- Every class, including one with no parameters of its own, gets both mappings, so no class lacks the attributes.
- The new attributes store no copies of values. Instance reads go through the instance's own parameter attributes at access time.

## API contracts
- `parameters` and `derived_parameters` are available on `Cosmology` and every subclass, from both class and instance.
- Reads return an immutable mapping keyed by strings.
- Keys of each mapping are exactly the names in that mapping, and no name appears in both.
- Assigning either attribute on any instance is rejected and must not replace or shadow it. After a rejected assignment, reads still return the read-only mapping.
- No other public names are added. The removed legacy tuples were internal.

## Module architecture
- Implement both attributes with one shared descriptor, which may live in the parameter package or the cosmology core module.
- The descriptor reads per-class mappings computed at creation and stored under underscore-prefixed private names. No second parameter registry.
- The descriptor is a single class-level object shared by all instances; it is not copied per instance.
- The MRO namespace-gathering helper lives in the private module `astropy/cosmology/_utils.py`, not in the public deprecation shim `astropy/cosmology/utils.py`. The cosmology core imports it from the private module.
- Dependency direction: the cosmology core may use the parameter package and the private helper. The parameter package references the cosmology class only for type checking, never at runtime. The helper must not import the cosmology core.

## Implementation constraints
- The descriptor must be a data descriptor, defining both read and write hooks. A read-only descriptor is unacceptable because an instance attribute of the same name would shadow it.
- Reads from the class return Parameter objects; reads from an instance return parameter values.
- The descriptor learns its public name from the owning class at creation, through the standard descriptor naming mechanism. Do not supply the name as a separate string.
- Migrate every internal consumer in the same change: equality and equivalence, string output, cloning and argument building, non-flat conversion, and the table, mapping, model, HTML, LaTeX, and YAML-style writers. Migrate existing tests that read the legacy classification, such as the realization parameters test and the per-format and per-class parameter tests. Each consumer must produce identical results for every existing class.
- Annotations in the helper and any new module must resolve on the minimum supported Python version: import every referenced name or postpone annotation evaluation. The core imports the helper at import time, so an unresolved name breaks the whole package.
- Standard library only. No new dependency is permitted.

## Naming
- Public names are exactly `parameters` and `derived_parameters`.
- Private helper and storage names start with an underscore.
- The rejected-write error message quotes the public attribute name.
- Private storage is never exposed under the public names.

## Validation
- New and changed source and test modules must pass the repository's ruff hook from the pre-commit configuration. No import may be unused.
- Ruff ignores E501, but the black hook enforces 88 columns. For every line the change adds or modifies in source and test modules that exceeds 88 columns, rewrap it as black would, including single-line return expressions such as equality comparisons. A statement that fits within 88 columns when joined must not stay split unless a trailing comma keeps it split. Untouched lines are not reformatted.
- The cosmology package must import on the minimum supported Python, 3.9. A module that fails at import time breaks every cosmology test.
- Check each added or modified line against the 88-column limit before finishing; a missed line fails the black hook.

## Error handling
- Setting `parameters` or `derived_parameters` on an instance raises AttributeError.
- The message begins with "cannot set", then the quoted attribute name, then "of", then the instance representation, and ends with a period.
- Reads on valid instances never raise.
- Rejection applies to every assigned value, including one equal to the current value.

## Documentation
- Each public attribute gets a docstring directly beneath its definition in the Cosmology class body. It states that the attribute returns an immutable mapping and describes class access (Parameter objects) versus instance access (values). Attaching documentation at runtime is not acceptable. Both descriptions must be accurate for class and instance access.
- Add a changelog fragment in the cosmology docs changes directory, named with the pull request number and typed as a feature. It describes both properties, that they return read-only dictionaries, and the class versus instance difference.

## Compatibility
- Class-level Parameter access (such as H0 on the class) and instance value reads are unchanged.
- Ode0 on the FLRW base remains non-derived for non-flat cosmologies.
- Removing the legacy tuples is not a public contract change. For every shipped class, equality, equivalence, cloning, non-flat conversion, and every I/O writer must match prior results.
- Replacing class-level Parameter access (for example with dataclasses) is out of scope.

## Operations
- No operational changes are required.

## Behavioral acceptance criteria
- From the class, `parameters` and `derived_parameters` return read-only mappings with Parameter values.
- From an instance, both return read-only mappings whose values equal the instance's parameter values.
- For a flat cosmology class, `derived_parameters` includes Ode0. The same holds for its subclasses and their subclasses.
- For LambdaCDM, `parameters` includes Ode0 and `derived_parameters` does not.
- Assigning either attribute on an instance raises AttributeError with the Error handling message, and the attribute still works afterwards.
- Returned mappings reject item assignment.
- Class-level access to a Parameter by name still returns the Parameter object.
- A Parameter defined on a non-cosmology mixin in the hierarchy is treated as a parameter of the class by the new mappings, equality, cloning, and I/O writers.
- For every shipped class, equality, equivalence, cloning, non-flat conversion, and table, mapping, and model I/O outputs match prior results.
- No reads of the removed tuples remain. The realization parameter-values test still checks every value against the realization's parameter mapping.
- The package imports on Python 3.9.

## Test requirements
- Tests cover class and instance reads of both attributes, the derived split, subclass inheritance (including a grandchild of a flat cosmology), and rejected instance assignment for both names.
- Place tests next to existing cosmology parameter tests, following their layout.
- Migrate existing legacy-reading tests. Each keeps its original assertions in the same method; do not delete or weaken them. For example, the realization test iterates the realization's parameter mapping and compares each value with the mapping's entry for that name.
- Keep assertions in the method whose name and docstring describe them. Do not move existing assertions or repurpose existing methods. Add new methods, named and documented for new behavior, and leave existing bodies unchanged apart from migration. For example, the check that a subclass may not take Ode0 in its initializer stays in the existing flat-subclass initialization test; checks for subclasses of flat cosmologies go in a new method.
- Rejected-assignment tests run only against instances created through normal `Cosmology` initialization, not stub cosmologies that bypass it. The error message formats the instance name, which a stub without a name cannot supply.
- Every fixture a test uses must be available to it: defined in the same class, inherited from a shared mixin, or in a shared conftest. Do not reference a fixture defined only as a method of an unrelated class.
- A test that defines a new cosmology subclass must remove its registration with the registry-cleanup fixture from the cosmology test helper, as neighboring tests do.
- Mixin tests run for every cosmology test class, including those with no derived parameters. Do not take the first item of an iterator over the derived mapping without a guard, since an empty mapping raises StopIteration, which a TypeError expectation does not catch. Compare key sets or iterate in a way safe for empty mappings.
- Stub cosmologies for a non-cosmology mixin's parameter must not be cloned or rebuilt from their mapping unless the constructor accepts every name in it, because cloning passes all parameters, including inherited ones. Such stubs check membership and Parameter type through the mappings.
- A stub overriding an inherited base attribute must keep the same kind: a base property is overridden by a property, not called as a method.
- A direct unit test for the private MRO helper goes in the existing private cosmology utilities test module. It checks that base class names are included, that a nearer definition overrides a farther one, and that the helper does not add gathered names to the subclass's own namespace.
- Ode0 assertions follow the Workflows rule, matching what a correct implementation produces.
- Existing parameter-value tests remain valid; only their source of parameter names changes.
- Tests must not assert agreement with the legacy tuples.
