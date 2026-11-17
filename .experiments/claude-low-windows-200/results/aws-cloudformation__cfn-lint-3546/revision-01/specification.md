## Goals
Add three keyword-triggered lint rules that validate relationships between an ECS service and the ECS task definition it references, and between a task definition's own port mappings. The rules report under the public IDs E3052, E3053 and E3054. Each rule fires only on the specific relationship described under Workflows; nothing else is in scope.

## Scope
In scope:
- Three new rule modules under the existing ECS rules package, each implementing one check.
- Three new unit-test modules covering those checks.

Out of scope:
- Any change to the existing E3048 Fargate rule or any other existing rule.
- New JSON schema extension files, changes to the schema data directory, or changes to docs/rules.md. The reference change does not touch these.
- Any additional check not listed under Workflows, including: a Fargate NetworkMode rule, a Fargate privileged-container rule, a LaunchType-driven NetworkConfiguration rule, or a duplicate of the existing Fargate CPU/memory checks.

## Assumptions
- Template input is the parsed CloudFormation template, including intrinsic-function dicts and conditional (Fn::If) branches. Values that are not plain strings, integers or lists are treated as unknown and skipped unless a rule states otherwise.
- Rule discovery is by module presence in the ECS rules package; no registry edit is needed.

## Terminology
- Awsvpc network mode: a task definition's top-level NetworkMode property equal to the exact string "awsvpc".
- FARGATE launch type: a service's LaunchType property equal to the exact string "FARGATE".
- Resolvable task reference: a service's TaskDefinition value that is a Ref whose value is a string, or a Fn::GetAtt whose first element, taken before its first dot, is a string. The resulting name is the logical resource ID. Any other form (literal string, Fn::Sub, Ref to a parameter or pseudo parameter) is not resolvable and the service is skipped.
- Unknown value: a value that is an intrinsic-function dict or a missing key where the workflow says to skip.

## Workflows
E3052 (service requires NetworkConfiguration when the task uses awsvpc):
1. For each AWS::ECS::Service resource, resolve its TaskDefinition to a resource. Skip if the reference is not resolvable or the logical name does not exist or is not an AWS::ECS::TaskDefinition.
2. If that task definition has a Condition, evaluate it with the condition assumed true, using the existing resource-lookup helper. Skip if the condition is unsatisfiable.
3. Read the task definition's NetworkMode. Only the exact value "awsvpc" triggers the check.
4. Read the service's NetworkConfiguration through the existing path-resolution helper so conditional branches are evaluated per branch. For each branch where the value is absent (None), emit one error. Emit at most one error per service and task-definition pair.

E3053 (awsvpc host port must equal container port):
1. For each AWS::ECS::TaskDefinition, read NetworkMode. Only the exact value "awsvpc" triggers the check.
2. For each container definition's PortMappings entry, read HostPort and ContainerPort. Skip the pair if either is absent or is not a string or integer.
3. Compare the two values by their string form. If they differ, emit one error per mismatched mapping, with the path pointing at that mapping's HostPort.

E3054 (service using FARGATE must reference a task definition that allows FARGATE):
1. For each AWS::ECS::Service with LaunchType exactly "FARGATE", resolve its TaskDefinition as in E3052 steps 1 and 2.
2. Read the task definition's RequiresCompatibilities.
   - If absent (None), emit a required-property error whose path points at the task definition's Properties object.
   - If it is not a list (for example an intrinsic-function dict), skip.
   - If it is a list and any element is an intrinsic dict or equals "FARGATE", no error.
   - Otherwise emit one contains-style error whose path points at RequiresCompatibilities.

## Data model
Template fields read (no new data is stored):
- Service Properties: TaskDefinition, LaunchType, NetworkConfiguration.
- Task definition Properties: NetworkMode, RequiresCompatibilities, ContainerDefinitions (list), each element's PortMappings (list), each mapping's HostPort and ContainerPort.
- Resources map: logical name to a resource with a Type and an optional Condition. The lookup helper returns the resource only when the type matches the requested type list.

## Module architecture
- Each rule is a keyword-triggered rule. It extends the existing keyword-based rule base, not the JSON-schema rule base. The schema base only sees a single resource and cannot resolve a service's reference to another resource, so E3052 and E3054 must use cross-resource lookup.
- Cross-resource lookup uses the shared template helpers for resource-by-name (with type filter and condition handling) and path-value retrieval (with intrinsic and conditional handling). Do not reimplement these helpers.
- E3053 is single-resource and may use the same path-retrieval helper against the task definition's Properties.
- Each rule owns only its single check. Shared logic for resolving references may be a private helper inside the module or reuse of the shared helpers; do not move logic into the existing E3048 rule.

## Implementation constraints
- Use the same module header, future-annotations import, and import style as the sibling ECS rule modules.
- Do not edit the rule base class, the helpers, any registry, or any schema extension file.
- Do not add a new dependency or a new layer; imports must only point at the existing cfnlint packages already used by sibling ECS rules.

## Dependencies
- Allowed: the existing error and result types from the jsonschema package, the validator protocol, the rules helpers package (resource lookup, path retrieval), the keyword-rule base, and the general helpers used for function detection and list wrapping.
- Not allowed: any third-party package or new cfnlint subpackage.

## Naming
- Rule module file names equal their class names: ServiceNetworkConfiguration, TaskDefinitionAwsVpc, ServiceFargate. All three are placed in the existing ECS rules package directory.
- Test module file names: test_service_network_configuration.py, test_task_definition_aws_vpc.py, test_service_fargate.py, placed in the existing ECS unit-test directory.
- Rule IDs: E3052 for the service NetworkConfiguration rule, E3053 for the awsvpc port rule, E3054 for the service FARGATE compatibility rule.

## Validation
- Malformed, unresolved or unexpected-type values are skipped silently; they must not raise exceptions.
- Only the exact strings "awsvpc" and "FARGATE" trigger their checks; comparisons are case-sensitive.

## Error handling
- Report problems by yielding validation errors, not by raising.
- Each error carries the rule instance and a validator kind: "required" for missing-property errors, "const" for the port mismatch, "contains" for the compatibility list error.
- Messages, exactly:
  - E3052: "'NetworkConfiguration' is a required property"
  - E3053: "<host> does not equal <container>", where each side is shown as the value appears in the template: strings quoted, integers bare (for example '80' does not equal 8080).
  - E3054 missing: "'RequiresCompatibilities' is a required property"
  - E3054 list: "<list> does not contain items matching 'FARGATE'", where the list is shown in the same quoted-list style (for example ['EC2', 'EXTERNAL']).
- Path overrides:
  - E3053: the HostPort location of the mismatched mapping.
  - E3054 missing: the task definition's Properties location.
  - E3054 list: the RequiresCompatibilities location.
  - E3052: no path override.
- Messages must never render the text "None" for a missing value.

## Documentation
- Each rule has a short description and a long description. The short description names the check; the long description states the condition in one sentence. Tags are exactly "resources" and "ecs".
- Do not edit docs/rules.md or any other documentation file for this change.
- Remove any pull-request template text (issue line, description-of-changes block, licence attestation) from this specification; those are not feature requirements.

## Maintainability
- Code is formatted to the repository's black and ruff style with an 88-column limit, including test files.
- The three checks must not duplicate any check already done by E3048 or another rule.

## Compatibility
- The IDs E3052, E3053 and E3054 are new public identifiers; they must not be reassigned to other behavior.
- No existing rule's ID, behavior or messages change.

## Behavioral acceptance criteria
- E3052: a service whose TaskDefinition resolves to a task definition with NetworkMode "awsvpc" and no NetworkConfiguration produces exactly one required-property error. The same service with NetworkConfiguration produces none. A task definition with a different NetworkMode, or an unresolvable TaskDefinition reference (literal or parameter Ref), produces none.
- E3053: an awsvpc task definition with HostPort "80" and ContainerPort 8080 produces one const-style mismatch error with the HostPort path. Matching values, or a missing HostPort or ContainerPort, produce none.
- E3054: a FARGATE service whose task definition has RequiresCompatibilities ["EC2", "EXTERNAL"] produces one contains-style error at RequiresCompatibilities. A missing RequiresCompatibilities produces one required-property error at the task definition Properties. A RequiresCompatibilities list containing "FARGATE", or an intrinsic dict value, produces none. A non-FARGATE launch type produces none.

## Test requirements
- Add three unit-test modules named as in Naming. Each parametrizes template inputs and compares the full list of produced validation errors (including message, validator kind, rule, and path override) against the expected list with equality.
- Tests import the rule classes from the rule modules named in Naming, so the module and class names are part of the contract.
- The patch must apply cleanly, and the three new test modules together with the existing ECS tests must pass in the reference environment.
