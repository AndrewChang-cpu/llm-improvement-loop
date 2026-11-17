## Goals
Add three keyword-triggered lint rules that check relationships between an ECS service, the task definition it references, and that task definition's own port mappings. The rules report under the public IDs E3052, E3053 and E3054. Each rule fires only on the relationship described under Workflows.

## Scope
In scope:
- Three new rule modules in the existing ECS rules package, one check each.
- Three new unit-test modules covering those checks.

Out of scope:
- Any change to the existing E3048 Fargate rule or any other existing rule.
- JSON schema extension files, the schema data directory, and docs/rules.md. The reference change does not touch these.
- Any check not listed under Workflows, including a Fargate NetworkMode rule, a Fargate privileged-container rule, a LaunchType-driven NetworkConfiguration rule, or a duplicate of the existing Fargate CPU/memory checks.

## Assumptions
- Template input is the parsed CloudFormation template, including intrinsic-function dicts and Fn::If branches.
- Value lookups are performed through the shared path-resolution helper. That helper evaluates each Fn::If branch under its own condition scope and treats a Ref to AWS::NoValue as an absent value. The rules rely on that behavior and do not re-evaluate intrinsic functions themselves.
- Rule discovery is by module presence in the ECS rules package; no registry edit is needed.

## Terminology
- Awsvpc network mode: a task definition's top-level NetworkMode property equal to the exact string "awsvpc".
- FARGATE launch type: a service's LaunchType property equal to the exact string "FARGATE".
- Resolvable task reference: a service's TaskDefinition value that is a Ref whose value is a string, or a Fn::GetAtt whose first element, cut at its first dot, is a string. The resulting name is a logical resource ID. Any other form (literal string, Fn::Sub, Ref to a parameter or pseudo parameter) is not resolvable and that service is skipped.
- Absent value: a lookup that yields a value of None. This happens when the key is missing, when the containing value is not a mapping (for example a string or a list), or when the value is a Ref to AWS::NoValue. Absent is not the same as unresolved: where a workflow says absent produces a finding, it must produce one; where it says skip, it must skip.
- Unresolved value: an intrinsic-function dict that the path helper cannot evaluate, such as a Ref to a parameter. If the lookup must continue through it, nothing is produced. If it is the final value, it is not a string or integer and is skipped.
- Boolean values are integers for the purpose of port comparison (a boolean is an integer subtype).

## Workflows
Lookup chaining (applies to E3052 and E3054): every lookup returns a value together with a validator. Each later lookup and each resource lookup in the same chain must use the validator returned by the previous lookup, so that Fn::If condition scopes accumulate. Do not fall back to the keyword-level validator in the middle of a chain.

E3052 (service requires NetworkConfiguration when its task definition uses awsvpc):
1. For each AWS::ECS::Service resource, read its TaskDefinition from the service Properties. Skip any resolved value that is not a resolvable task reference.
2. Read NetworkConfiguration from the service Properties using the validator produced in step 1.
3. For each NetworkConfiguration value produced in step 2, look up the referenced resource by logical name with the type filter AWS::ECS::TaskDefinition, using that step's validator. The resource-lookup helper handles the resource's Condition (evaluated with the condition assumed true; the lookup yields nothing if the condition is unsatisfiable), missing names, type mismatches, and falsy resources by yielding nothing. Skip when nothing is returned.
4. From the resource's Properties, read NetworkMode using the lookup's validator. For each NetworkMode value exactly equal to "awsvpc", if the NetworkConfiguration value from step 2 is absent, emit one required-property error. Do not de-duplicate: emit one error for each absent NetworkConfiguration branch for each awsvpc NetworkMode branch. An Fn::If that yields awsvpc in two branches can therefore produce the same error twice.

E3053 (awsvpc host port must equal container port):
1. For each AWS::ECS::TaskDefinition resource, read NetworkMode at the top level of its Properties, per branch. Only branches whose value is exactly "awsvpc" trigger steps 2 and 3, and steps 2 and 3 run once per such branch.
2. Traverse ContainerDefinitions (each element), then each container's PortMappings (each element). For each mapping, read HostPort with the mapping's validator. Skip the mapping if HostPort is absent, unresolved, or not a string or integer (a boolean counts as an integer). Read ContainerPort using the validator produced by the HostPort read. Skip the mapping if ContainerPort is absent, unresolved, or not a string or integer.
3. Compare the two values by their string form. If they differ, emit one error for that mapping, with the path override at the HostPort location (the Fn::If branch location when HostPort is conditional).

E3054 (service using FARGATE must reference a task definition that allows FARGATE):
1. For each AWS::ECS::Service resource, read TaskDefinition from the service Properties and skip unresolvable values as in E3052 step 1.
2. Read LaunchType from the service Properties using the TaskDefinition step's validator. For each LaunchType branch exactly equal to "FARGATE", continue with the validator produced by that LaunchType read. Other branches are skipped.
3. Look up the referenced resource by logical name with the type filter AWS::ECS::TaskDefinition, using the LaunchType branch's validator, with the same resource-lookup behavior as E3052 step 3. Skip when nothing is returned.
4. Read RequiresCompatibilities from the resource's Properties using the lookup's validator. For each value:
   a. Absent (including a missing Properties block or a Properties value that is not a mapping, and including AWS::NoValue): emit one required-property error.
   b. Not a list (for example a plain string or an unresolved intrinsic dict): skip.
   c. A list: evaluate each element through the path helper's wildcard so that Fn::If elements resolve per branch. If any resolved element is a dict (any dict, intrinsic or not) or is exactly "FARGATE", produce no error for this value. Otherwise emit one contains-style error. An empty list produces this error.

## Data model
Template fields read (no new data is stored):
- Service Properties: TaskDefinition, LaunchType, NetworkConfiguration.
- Task definition Properties: NetworkMode, RequiresCompatibilities, ContainerDefinitions (list), each element's PortMappings (list), each mapping's HostPort and ContainerPort.
- Resources map: logical name to a resource with a Type and an optional Condition. The resource-lookup helper returns the resource only when the type matches the requested type list, and applies condition handling as described under Workflows.
- Path lookups produce zero or more (value, validator) pairs. Multiple pairs arise from Fn::If branches.

## Module architecture
- Each rule is a keyword-triggered rule. It extends the existing keyword-based rule base, not the JSON-schema rule base. The schema base sees only a single resource and cannot resolve a service's reference to another resource, so E3052 and E3054 must use cross-resource lookup.
- Cross-resource lookup uses the shared template helpers for resource-by-name (with type filter and condition handling) and path-value retrieval (with intrinsic and conditional handling). Do not reimplement these helpers.
- E3053 is single-resource and uses the path-retrieval helper against the task definition's Properties.
- Each rule owns only its single check. Shared logic for resolving references may be a private helper inside the module or reuse of the shared helpers. Do not move logic into the existing E3048 rule.

## Implementation constraints
- Use the same module header, future-annotations import, and import style as the sibling ECS rule modules.
- Do not edit the rule base class, the helpers, any registry, or any schema extension file.
- Do not add a new dependency or a new layer; imports must only point at the existing cfnlint packages already used by sibling ECS rules.

## Dependencies
- Allowed: the existing error and result types from the jsonschema package, the validator protocol, the rules helpers package (resource lookup, path retrieval), the keyword-rule base, the general helpers used for function detection and list wrapping, and standard-library typing and collections.
- Not allowed: any third-party package or new cfnlint subpackage.

## Naming
- Rule module file names equal their class names: ServiceNetworkConfiguration, TaskDefinitionAwsVpc, ServiceFargate. All three are placed in the existing ECS rules package directory.
- Test module file names: test_service_network_configuration.py, test_task_definition_aws_vpc.py, test_service_fargate.py, placed in the existing ECS unit-test directory.
- Rule IDs: E3052 for the service NetworkConfiguration rule, E3053 for the awsvpc port rule, E3054 for the service FARGATE compatibility rule.

## Validation
- Values of unexpected type and unresolved values are skipped silently and must not raise exceptions. Absent values are handled only as Workflows and Terminology state: E3052 and E3054 treat an absent value as a finding, and E3053 treats it as a skip. A non-mapping Properties value on a referenced task definition is an absent value, not a malformed value to skip.
- Only the exact strings "awsvpc" and "FARGATE" trigger their checks; comparisons are case-sensitive.
- Booleans are integers for the E3053 type check.

## Error handling
- Report problems by yielding validation errors, not by raising.
- Each error carries the rule instance and a validator kind: "required" for absence errors, "const" for the port mismatch, "contains" for the compatibility list error.
- Messages, exactly:
  - E3052: "'NetworkConfiguration' is a required property"
  - E3053: "<host> does not equal <container>", where each side is formatted with Python's repr of the value, so strings are quoted and integers and booleans are bare (for example '80' does not equal 8080, and True does not equal 8080).
  - E3054 absent: "'RequiresCompatibilities' is a required property"
  - E3054 list: "<list> does not contain items matching 'FARGATE'", where the list is formatted with Python's repr (for example ['EC2', 'EXTERNAL']).
- Format values with the standard repr directly, as the sibling rules do. Do not introduce a custom display or quoting helper, because repr escaping differs from a hand-written quoting function for strings containing quotes or backslashes.
- Path overrides:
  - E3053: the HostPort location of the mismatched mapping.
  - E3054 absent: the location reached by the RequiresCompatibilities lookup with its last path segment removed. In practice: when the RequiresCompatibilities key is missing from a mapping Properties block, this is the Properties location; when Properties is missing or is not a mapping, this is the TaskDefinition resource location; when the value is AWS::NoValue, this is the RequiresCompatibilities location.
  - E3054 list: the RequiresCompatibilities location.
  - E3052: no path override.
- Messages must never render the text "None" for a missing value.

## Documentation
- Each rule has a short description and a long description. The short description names the check; the long description states the condition in one sentence. Tags are exactly "resources" and "ecs".
- Do not edit docs/rules.md or any other documentation file for this change.

## Maintainability
- Code is formatted to the repository's black and ruff style with an 88-column limit, including test files.
- The three checks must not duplicate any check already done by E3048 or another rule.

## Compatibility
- The IDs E3052, E3053 and E3054 are new public identifiers; they must not be reassigned to other behavior.
- No existing rule's ID, behavior or messages change.

## Behavioral acceptance criteria
- E3052: a service whose TaskDefinition resolves to a task definition with NetworkMode "awsvpc" and no NetworkConfiguration produces exactly one required-property error. The same service with NetworkConfiguration produces none. A task definition with a different NetworkMode, or an unresolvable TaskDefinition reference (literal or parameter Ref), produces none. A task definition reached only through a non-awsvpc Fn::If branch produces none.
- E3053: an awsvpc task definition with HostPort "80" and ContainerPort 8080 produces one const-style error with the HostPort path, reading "'80' does not equal 8080". HostPort true with ContainerPort 8080 produces one error reading "True does not equal 8080". Matching values, or a missing HostPort or ContainerPort, produce none.
- E3054: a FARGATE service whose task definition has RequiresCompatibilities ["EC2", "EXTERNAL"] produces one contains-style error at RequiresCompatibilities. A task definition whose Properties mapping lacks RequiresCompatibilities produces one required-property error at the Properties location. A task definition with no Properties block, or with a non-mapping Properties value, produces one required-property error at the TaskDefinition resource location. A task definition whose RequiresCompatibilities is AWS::NoValue produces one required-property error at the RequiresCompatibilities location. A RequiresCompatibilities list containing "FARGATE", a list containing any dict element, or an unresolved intrinsic dict value, produces none. A non-FARGATE launch type produces none. A FARGATE branch inside a LaunchType Fn::If is checked only when that branch is selected.

## Test requirements
- Add three unit-test modules named as in Naming. Each parametrizes template inputs and compares the full list of produced validation errors (including message, validator kind, rule, and path override) against the expected list with equality.
- The tests must cover at least: an AWS::NoValue RequiresCompatibilities case expecting the RequiresCompatibilities path override; a task definition with no Properties block; a RequiresCompatibilities list containing a non-intrinsic dict; a boolean HostPort; and a LaunchType Fn::If in which only one branch is FARGATE.
- Tests import the rule classes from the rule modules named in Naming, so the module and class names are part of the contract.
- The patch must apply cleanly, and the three new test modules together with the existing ECS tests must pass in the reference environment.
