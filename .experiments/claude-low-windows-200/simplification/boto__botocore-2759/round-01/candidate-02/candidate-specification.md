## Goals
Add a public helper on ClientArgsCreator that computes the eleven endpoint-ruleset builtin parameter values for one client creation, plus a named registry of builtin names. The helper is standalone: client creation does not call it, and no existing argument-computation output changes. A later change will consume it.

## Scope
In scope:
- The new helper in botocore/args.py.
- The new builtin-name enumeration in botocore/regions.py.
- Accepting an absent endpoint configuration in the existing STS global-endpoint predicate (see Compatibility).
- Unit tests in tests/unit/test_args.py.

Out of scope:
- Changes to compute_client_args, get_client_args, the client-creation path, ClientCreator, or botocore/client.py.
- New keys in any existing return value.
- Event hooks, handler registration, the endpoint provider, the endpoint resolver, and the endpoint bridge.

## Assumptions
- The endpoint bridge provides a FIPS variant lookup and a DualStack lookup for the service name. The variant lookup gives client config precedence over the config store. The DualStack lookup applies S3 dualstack handling to s3 and s3-control only.
- ClientArgsCreator already has S3 and STS global-endpoint predicates. Reuse both.
- The endpoint resolver exposes a flag saying whether it uses bundled endpoint data.
- The caller supplies the S3 configuration as a mapping, possibly empty. The helper does not build it.

## Terminology
- Builtin: a named input that endpoint rulesets consume.
- Client endpoint URL: the endpoint URL passed to client creation.
- Legacy endpoint URL: the endpoint produced by legacy endpoint resolution.
- Custom endpoint data: the resolver's bundled-data flag is false.

## Workflows
The helper computes all eleven builtins on every call:
1. SDK::Endpoint: a truthy client endpoint URL wins. Otherwise, if the resolver uses custom endpoint data, use the legacy endpoint URL (which may be absent). Otherwise the value is absent.
2. AWS::UseFIPS: the bridge's FIPS variant lookup for the endpoint; a falsy result becomes false. A custom endpoint does not suppress this value, so it is always the bridge result or false.
3. AWS::UseDualStack: the bridge's DualStack lookup for the service name; falsy becomes false. Same non-suppression rule as FIPS.
4. AWS::STS::UseGlobalEndpoint: the existing STS predicate with the region name, no endpoint URL, and no endpoint configuration. The service name is not checked.
5. AWS::S3::UseGlobalEndpoint: the existing S3 predicate with the region name and the S3 configuration.
6. AWS::S3::Accelerate: S3 configuration key use_accelerate_endpoint, default false.
7. AWS::S3::ForcePathStyle: true exactly when S3 configuration key addressing_style equals path; otherwise false.
8. AWS::S3::UseArnRegion: key use_arn_region, default true, passed through unchanged.
9. AWS::S3Control::UseArnRegion: the same key, default false, passed through unchanged.
10. AWS::S3::DisableMultiRegionAccessPoints: key s3_disable_multiregion_access_points, default false.
11. AWS::Region: the region name argument exactly as given.

All eleven entries are always present, whatever the service name.

## Data model
- Enumeration EndpointResolverBuiltins in botocore/regions.py. It mixes in str, so each member equals its string value. Members, in order:

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
- The helper returns a mapping keyed by the eleven members.

## API contracts
- Public method compute_endpoint_resolver_builtin_defaults on ClientArgsCreator. Required parameters, in this order: region_name, service_name, s3_config, endpoint_bridge, client_endpoint_url, legacy_endpoint_url. Tests pass keyword arguments with these names. It returns the mapping described in Data model.
- The STS predicate accepts an absent endpoint configuration, treated as having no variant tags. Results for present inputs do not change.
- No other public name or signature changes.

## Module architecture
- botocore/args.py: the helper is a ClientArgsCreator method added after the existing boolean-coercion helper at the end of the class. Import the enumeration from botocore.regions after the endpoint import, under the alias in Naming. regions.py does not import args, so no cycle is created.
- botocore/regions.py: add a standard-library enum import at the top, and append the enumeration after the template-expansion helper.
- botocore/client.py is not modified.

## Implementation constraints
- Get FIPS and DualStack values only through the bridge's lookups. Do not read Config attributes or config-store entries for them, and do not reimplement S3 DualStack scoping.
- Reuse the existing S3 and STS predicates. Do not restate their rules.
- Do not duplicate boolean parsing; the bridge and predicates coerce values.
- The helper keeps no cache and has no side effects of its own. It reads configuration only through the bridge lookups and the predicates.
- Do not change the output of compute_client_args, change get_client_args, or call the helper from the client-creation path.
- Take the S3 configuration as given; do not build it.

## Naming
- Enumeration name EndpointResolverBuiltins. Member names and string values exactly as in the Data model table, including the "::" separators and the SDK prefix.
- In botocore/args.py, import the enumeration as EPRBuiltins and refer to members through that alias, which keeps builtin keys within the line-length limit.
- Code refers to builtins through the enumeration, never through repeated string literals.

## Validation
- Every added line in the three touched modules, including comments, docstrings, and test code, fits within 79 columns. Wrap longer expressions the way black would.
- Imports follow isort with profile black. In each module, botocore imports form one block sorted by module path, with plain module imports before from-imports.
  - botocore/args.py: the enumeration import goes after the botocore.endpoint import and before the botocore.signers import.
  - tests/unit/test_args.py: if the enumeration is imported, the import goes after the botocore.model import (the last botocore import) and before the tests package import.
- The test module may assert on builtin string values or on enumeration members. Prefer string values, which needs no new import.

## Performance
- The helper is not on the client-creation path, so existing client creation gains no cost. No caching is needed.

## Reliability
- The helper must not fail when the STS predicate receives no endpoint configuration.
- FIPS and DualStack are never absent: a falsy bridge result becomes false.
- Errors raised by the reused predicates for invalid STS or S3 regional-endpoint settings propagate unchanged.

## Maintainability
- Precedence rules live only in the bridge and the existing predicates. The helper composes them without restating them.
- Builtin names are defined once, in the enumeration.

## Documentation
- Do not describe the helper or the enumeration as pure, and make no claim about reads or writes that the code does not provide.
- Comments may describe actual behavior: the SDK endpoint precedence and each member's meaning and type.

## Compatibility
- Existing client-creation arguments and existing tests produce the same results.
- The STS predicate change only adds acceptance of an absent configuration; behavior for present configurations is identical.

## Behavioral acceptance criteria
- Default (region ca-central-1, service fooservice, empty S3 configuration, bundled data, legacy URL https://my.legacy.endpoint.com, no client URL): Region ca-central-1; FIPS false; DualStack false; STS true; S3 global false; Accelerate false; ForcePathStyle false; S3 UseArnRegion true; S3Control UseArnRegion false; MRAP false; SDK::Endpoint absent.
- Config store use_fips_endpoint true gives FIPS true; false gives false.
- Service s3-control with client config s3 use_dualstack_endpoint true gives DualStack true; false gives false. Service other-service with the same true setting gives DualStack false.
- Region us-west-2 with default STS configuration gives STS true. Region eu-south-1 gives STS false. Region us-west-2 with sts_regional_endpoints set to regional gives STS false.
- When the S3 predicate returns true, S3 global is true and the predicate is called exactly once.
- use_accelerate_endpoint true and false pass through to Accelerate.
- addressing_style path gives ForcePathStyle true; auto and virtual give false.
- use_arn_region false gives both S3 and S3Control false; true gives both true.
- s3_disable_multiregion_access_points true and false pass through to MRAP.
- SDK endpoint: a client URL is returned even when custom data and a legacy URL are present. With no client URL and custom data, the legacy URL is returned. With no client URL and bundled data, the value is absent even when a legacy URL is present.

## Test requirements
- Add a class named TestEndpointResolverBuiltins to tests/unit/test_args.py. It derives directly from the standard unit-test case class, not from the existing args test class, which would re-run all of its tests.
- setUp: build a ClientArgsCreator with a mock event emitter spec'd on the hierarchical emitter, absent user agent, response parser factory, loader, exceptions factory, and a config value store as the config store. Build a ClientEndpointBridge with a mock endpoint resolver, no scoped config, default client config, no default endpoint, no signing name, and the same config store. The resolver's bundled-data flag is true by default.
- Each behavioral criterion has a test. The S3 predicate test mocks the predicate and asserts exactly one call.
- Name each test for the scenario its body sets up. Names must match the flag values and inputs actually used.
- For legacy SDK endpoint scenarios, use exactly one test for custom data (flag false, legacy URL returned) and exactly one for bundled data (flag true, value absent). Do not add a second test with the same body.
- All existing tests in tests/unit/test_args.py still pass.
