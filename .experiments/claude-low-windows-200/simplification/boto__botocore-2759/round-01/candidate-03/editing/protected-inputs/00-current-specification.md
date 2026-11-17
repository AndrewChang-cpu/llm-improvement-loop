## Goals
Add a helper that computes the endpoint-ruleset builtin parameter values (the "builtins" that endpoint rulesets consume) for one client creation. The feature is a public helper on the client-args creator plus a named registry of builtin names. It is standalone: it is not called during client creation and it does not change any existing argument-computation output. A later change will consume it, so this change adds code that nothing calls.

## Scope
In scope:
- A new public helper on the client-args creator class in botocore/args.py.
- A new str-valued enumeration of builtin names in botocore/regions.py.
- A change to the existing STS global-endpoint predicate so it accepts an absent endpoint configuration (see Compatibility).
- Unit tests in tests/unit/test_args.py.

Out of scope:
- Changes to compute_client_args, get_client_args, the client-creation path, ClientCreator, or botocore/client.py.
- Adding keys to any existing return value.
- Event hooks, handler registration, or the endpoint provider itself.
- Changes to the endpoint resolver or to the endpoint bridge.

## Assumptions
- The endpoint bridge already resolves the FIPS and DualStack variants: a variant lookup that gives client config precedence and then the config store, and a DualStack lookup that applies S3 dualstack handling for the s3 and s3-control services only.
- The client-args creator already provides an S3 global-endpoint predicate and an STS global-endpoint predicate. Both are reused, not reimplemented.
- The endpoint resolver exposes a flag saying whether it uses bundled endpoint data.
- The caller supplies the S3 configuration as a mapping, which may be empty. The helper does not compute it.

## Terminology
- Builtin: a named input that endpoint rulesets consume.
- Client endpoint URL: the endpoint URL passed to client creation.
- Legacy endpoint URL: the endpoint produced by legacy endpoint resolution.
- Custom endpoint data: the resolver's bundled-data flag is false.

## Workflows
The helper computes all eleven builtins on every call, using these rules:
1. SDK::Endpoint: if the client endpoint URL is truthy, use it. Otherwise, if the resolver does not use bundled data, use the legacy endpoint URL (which may be absent). Otherwise, the value is absent.
2. AWS::UseFIPS: take the bridge's use_fips_endpoint variant lookup. If the result is falsy, use false. A custom endpoint does not suppress this value. (The reference contains a suppression clause, but due to operator precedence it never takes effect, so the value is always the bridge result or false.)
3. AWS::UseDualStack: take the bridge's DualStack lookup for the service name. Falsy becomes false. Same non-suppression rule as FIPS.
4. AWS::STS::UseGlobalEndpoint: call the existing STS predicate with the region name, no endpoint URL, and no endpoint configuration. The service name is not checked.
5. AWS::S3::UseGlobalEndpoint: call the existing S3 predicate with the region name and the S3 configuration.
6. AWS::S3::Accelerate: the S3 configuration key use_accelerate_endpoint, default false.
7. AWS::S3::ForcePathStyle: true exactly when the S3 configuration key addressing_style equals path; otherwise false.
8. AWS::S3::UseArnRegion: the S3 configuration key use_arn_region, default true, passed through unchanged.
9. AWS::S3Control::UseArnRegion: the same key, default false, passed through unchanged.
10. AWS::S3::DisableMultiRegionAccessPoints: the S3 configuration key s3_disable_multiregion_access_points, default false.
11. AWS::Region: the region name argument exactly as given (not a region taken from a resolved endpoint).

All eleven entries are always present, regardless of the service name.

## Data model
- An enumeration named EndpointResolverBuiltins in botocore/regions.py. It mixes in str, so each member compares equal to its string value. Members and values:

| Member | Value | Type |
|---|---|---|
| AWS_REGION | AWS::Region | string |
| AWS_USE_FIPS | AWS::UseFIPS | boolean |
| AWS_USE_DUALSTACK | AWS::UseDualStack | boolean |
| AWS_STS_USE_GLOBAL_ENDPOINT | AWS::STS::UseGlobalEndpoint | boolean |
| AWS_S3_USE_GLOBAL_ENDPOINT | AWS::S3::UseGlobalEndpoint | boolean |
| AWS_S3_ACCELERATE | AWS::S3::Accelerate | boolean |
| AWS_S3_FORCE_PATH_STYLE | AWS::S3::ForcePathStyle | boolean |
| AWS_S3_USE_ARN_REGION | AWS::S3::UseArnRegion | boolean by default; raw config value otherwise |
| AWS_S3CONTROL_USE_ARN_REGION | AWS::S3Control::UseArnRegion | boolean by default; raw config value otherwise |
| AWS_S3_DISABLE_MRAP | AWS::S3::DisableMultiRegionAccessPoints | boolean |
| SDK_ENDPOINT | SDK::Endpoint | string, or absent |

- Each member has a comment stating its meaning and type.
- The helper's return value is a mapping whose keys are the eleven members.

## API contracts
- A public method named compute_endpoint_resolver_builtin_defaults on the ClientArgsCreator class. It takes these required parameters, in this order: region_name, service_name, s3_config, endpoint_bridge, client_endpoint_url, legacy_endpoint_url. Tests call it with keyword arguments using these exact names. It returns the mapping described in Data model.
- The existing STS predicate must accept an absent endpoint configuration. When the configuration is absent, treat it as having no variant tags. Results for present inputs must not change.
- No other existing public name or signature changes.

## Module architecture
- botocore/args.py: the helper is a method of ClientArgsCreator, added after the existing boolean-coercion helper at the end of the class. Add an import of the enumeration from botocore.regions after the existing endpoint import, under the alias defined in Naming. regions.py does not import args, so this creates no cycle.
- botocore/regions.py: add a standard-library enum import at the top, and append the enumeration at the end of the module after the template-expansion helper.
- botocore/client.py is not modified.

## Implementation constraints
- Reuse the bridge's variant lookup and DualStack lookup for FIPS and DualStack. Do not read Config attributes or config-store entries directly for these, and do not reimplement the S3 DualStack scoping.
- Reuse the existing S3 and STS predicates. Do not reimplement their rules.
- Do not duplicate boolean parsing; the bridge and predicates already coerce values.
- The helper performs no I/O and no writes, keeps no cache, and has no side effects. It reads configuration only through the bridge's lookups and the existing S3 and STS predicates, which read the config store. Do not describe the helper as pure in code comments or documentation.
- Do not add the result to the return value of compute_client_args, do not change get_client_args, and do not call the helper from the client-creation path.
- The helper takes the S3 configuration as given; it does not build it.

## Naming
- Enumeration name EndpointResolverBuiltins. Member names and string values exactly as in the Data model table, including the "::" separators and the SDK prefix.
- In botocore/args.py, import the enumeration under the alias EPRBuiltins and refer to members through that alias. The alias keeps the builtin keys on lines within the line-length limit in Validation.
- Implementation code refers to builtins through the enumeration, not through repeated string literals.

## Validation
- Every added line in botocore/args.py, botocore/regions.py, and tests/unit/test_args.py, including comments, docstrings, and test code, must fit within the repo's black line length of 79 columns. Wrap any longer expression the way black would wrap it.
- Import blocks in every touched module must be ordered as the repo's isort configuration (profile black) requires. In each module, the botocore imports form one block sorted by module path, with plain module imports listed before from-imports. Place each added botocore import at its alphabetical position by module path:
  - In botocore/args.py, the enumeration import goes after the botocore.endpoint import and before the botocore.signers import.
  - In tests/unit/test_args.py, if the enumeration is imported, that import goes after the botocore.model import (the last botocore import in that module) and before the tests package import. It must not be placed before the botocore.hooks or botocore.model imports.
- The test module may assert on the builtin string values or on the enumeration members; either is acceptable. Asserting on the string values needs no new import in the test module, and the reference does this, so prefer it unless the enumeration members are needed.

## Performance
- The helper is not on the client-creation path, so it adds no cost to existing client creation. No caching is needed.

## Reliability
- The helper must not fail when the STS predicate receives no endpoint configuration.
- FIPS and DualStack are never absent: a falsy bridge result becomes false.
- Errors raised by the reused predicates for invalid STS or S3 regional-endpoint settings propagate unchanged. The helper does not catch them.

## Maintainability
- Precedence rules live only in the bridge and the existing predicates. The helper composes them and does not restate them.
- Builtin names are defined once, in the enumeration.

## Documentation
- Do not add a docstring or comment to the helper or the enumeration that asserts purity, or any guarantee about reads or writes that the code does not provide.
- Explanatory comments are allowed where they describe behavior the code actually has, such as the precedence for the SDK endpoint value and each enumeration member's meaning and type.

## Compatibility
- Existing behavior is unchanged: client-creation arguments and existing tests produce the same results.
- The STS predicate change only adds acceptance of an absent configuration; behavior for present configurations is identical.

## Behavioral acceptance criteria
- Default case (region ca-central-1, service fooservice, empty S3 configuration, resolver with bundled data, legacy URL https://my.legacy.endpoint.com, no client URL): AWS::Region ca-central-1; UseFIPS false; UseDualStack false; STS true; S3 global false; Accelerate false; ForcePathStyle false; S3 UseArnRegion true; S3Control UseArnRegion false; MRAP false; SDK::Endpoint absent.
- Config store use_fips_endpoint true gives UseFIPS true; false gives false.
- Service s3-control with client config s3 use_dualstack_endpoint true gives UseDualStack true; false gives false. Service other-service with the same s3 setting true gives UseDualStack false.
- Region us-west-2 with default STS configuration gives STS true. Region eu-south-1 gives STS false. Region us-west-2 with sts_regional_endpoints set to regional gives STS false.
- When the S3 predicate returns true, S3 global is true and the predicate is called exactly once.
- S3 configuration use_accelerate_endpoint true and false pass through to Accelerate.
- addressing_style path gives ForcePathStyle true; auto and virtual give false.
- use_arn_region false gives both S3 and S3Control UseArnRegion false; true gives both true.
- s3_disable_multiregion_access_points true and false pass through to MRAP.
- SDK endpoint: a client URL is returned even when custom data and a legacy URL are present. With no client URL and custom data, the legacy URL is returned. With no client URL and bundled data, the value is absent even when a legacy URL is present.

## Test requirements
- Add a test class named TestEndpointResolverBuiltins to tests/unit/test_args.py. It derives directly from the standard unit-test case class. It must not derive from the existing args test class, because that re-runs all of its tests.
- setUp: build a ClientArgsCreator with a mock event emitter spec'd on the hierarchical emitter, absent user agent, response parser factory, loader, and exceptions factory, and a config value store as the config store. Build a ClientEndpointBridge with a mock endpoint resolver, no scoped config, a default client config, no default endpoint, no signing name, and the same config store. Set the resolver's bundled-data flag to true by default.
- Each behavioral criterion above has a test.
- The S3 predicate test mocks the predicate and asserts it is called once.
- Name each test for the scenario its body actually sets up. Do not give a test a name that describes a different flag value or input than the one it sets.
- For the legacy SDK endpoint scenarios, use exactly one test for the custom-data case (bundled-data flag false, legacy URL returned) and exactly one test for the bundled-data case (flag true, value absent). Do not add a second test with the same body as another test.
- All existing tests in tests/unit/test_args.py continue to pass.
