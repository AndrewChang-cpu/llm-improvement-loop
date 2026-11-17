## Goals
Add a helper that computes the endpoint-ruleset builtin values (the builtins that endpoint rulesets consume) for one client creation. It is a public helper on the client-args creator plus a named registry of builtin names. It is standalone: client creation does not call it, and no existing argument output changes. A later change will consume it.

## Scope
In scope:
- A new public helper on the client-args creator class in botocore/args.py.
- A new str-valued enumeration of builtin names in botocore/regions.py.
- A change to the existing STS global-endpoint predicate so it accepts an absent endpoint configuration.
- Unit tests in tests/unit/test_args.py.

Out of scope:
- Changes to compute_client_args, get_client_args, the client-creation path, ClientCreator, or botocore/client.py.
- New keys in any existing return value.
- Event hooks, handler registration, the endpoint provider, the endpoint resolver, or the endpoint bridge.

## Assumptions
- The endpoint bridge already resolves FIPS and DualStack variants: a variant lookup that gives client config precedence and then the config store, and a DualStack lookup that applies S3 dualstack handling only for the s3 and s3-control services.
- The client-args creator already provides S3 and STS global-endpoint predicates. Reuse them.
- The endpoint resolver exposes a flag saying whether it uses bundled endpoint data.
- The caller supplies the S3 configuration as a mapping, possibly empty. The helper does not build it.

## Terminology
- Builtin: a named input that endpoint rulesets consume.
- Client endpoint URL: the endpoint URL passed to client creation.
- Legacy endpoint URL: the endpoint produced by legacy endpoint resolution.
- Custom endpoint data: the resolver's bundled-data flag is false.

## Workflows
The helper computes all eleven builtins on every call, regardless of service name:
1. SDK::Endpoint: if the client endpoint URL is truthy, use it. Otherwise, if the resolver does not use bundled data, use the legacy endpoint URL (which may be absent). Otherwise, the value is absent.
2. AWS::UseFIPS: the bridge's use_fips_endpoint variant lookup. A falsy result becomes false. A custom endpoint does not suppress this value. The reference contains a suppression clause, but due to operator precedence it never takes effect.
3. AWS::UseDualStack: the bridge's DualStack lookup for the service name. A falsy result becomes false. The same non-suppression rule applies.
4. AWS::STS::UseGlobalEndpoint: call the STS predicate with the region name, no endpoint URL, and no endpoint configuration. Do not check the service name.
5. AWS::S3::UseGlobalEndpoint: call the S3 predicate with the region name and the S3 configuration.
6. AWS::S3::Accelerate: S3 configuration key use_accelerate_endpoint, default false.
7. AWS::S3::ForcePathStyle: true exactly when S3 configuration key addressing_style equals path; otherwise false.
8. AWS::S3::UseArnRegion: key use_arn_region, default true, passed through unchanged.
9. AWS::S3Control::UseArnRegion: the same key, default false, passed through unchanged.
10. AWS::S3::DisableMultiRegionAccessPoints: key s3_disable_multiregion_access_points, default false.
11. AWS::Region: the region name argument exactly as given, not a region taken from a resolved endpoint.

## Data model
An enumeration named EndpointResolverBuiltins in botocore/regions.py. It mixes in str, so each member compares equal to its string value. Members, values, and types:

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

Each member has a comment stating its meaning and type. The helper returns a mapping keyed by the eleven members.

## API contracts
- A public method named compute_endpoint_resolver_builtin_defaults on the ClientArgsCreator class. Its required parameters, in this order, are region_name, service_name, s3_config, endpoint_bridge, client_endpoint_url, and legacy_endpoint_url. Tests pass these exact names as keyword arguments. It returns the mapping described in Data model.
- The existing STS predicate accepts an absent endpoint configuration, treated as having no variant tags. Results for present inputs do not change.
- No other existing public name or signature changes.

## Module architecture
- botocore/args.py: the helper is a method of ClientArgsCreator, added after the existing boolean-coercion helper at the end of the class. Import the enumeration after the botocore.endpoint import, under the alias in Naming. regions.py does not import args, so no cycle arises.
- botocore/regions.py: add a standard-library enum import at the top, and append the enumeration after the template-expansion helper.
- botocore/client.py is not modified.

## Implementation constraints
- Use the bridge's variant and DualStack lookups for FIPS and DualStack. Do not read Config attributes or config-store entries directly for these, and do not reimplement S3 DualStack scoping.
- Reuse the existing S3 and STS predicates. Do not restate their rules or duplicate boolean parsing.
- The helper performs no I/O or writes and keeps no cache. It reads configuration only through the bridge and the predicates. Do not describe it as pure in code comments or documentation.
- Do not add the result to compute_client_args, change get_client_args, or call the helper from the client-creation path.
- Refer to builtins through the enumeration, not repeated string literals.

## Naming
- Enumeration name EndpointResolverBuiltins. Member names and string values exactly as in the Data model table, including the "::" separators and the SDK prefix.
- In botocore/args.py, import the enumeration under the alias EPRBuiltins and refer to members through it. The alias keeps builtin keys within the line-length limit.

## Validation
- Every added line in the three touched modules, including comments, docstrings, and test code, fits within 79 columns. Wrap longer expressions the way black would.
- Imports follow the repo's isort configuration (profile black). The botocore imports form one block sorted by module path, with plain module imports before from-imports. In botocore/args.py, the enumeration import goes after botocore.endpoint and before botocore.signers. In tests/unit/test_args.py, if the enumeration is imported, it goes after botocore.model, the last botocore import, and before the tests package import.
- Test code may assert on string values or enumeration members. Prefer string values, which need no new import, as the reference does.

## Performance
- The helper is off the client-creation path, so existing client creation gains no cost. No caching is needed.

## Reliability
- The helper must not fail when the STS predicate receives no endpoint configuration.
- FIPS and DualStack are never absent: a falsy bridge result becomes false.
- Errors raised by the reused predicates for invalid STS or S3 regional-endpoint settings propagate unchanged. The helper does not catch them.

## Maintainability
- Precedence rules live only in the bridge and the existing predicates. The helper composes them and does not restate them.
- Builtin names are defined once, in the enumeration.

## Documentation
- Add no docstring or comment to the helper or enumeration that asserts purity or any read or write guarantee the code does not provide.
- Comments may describe actual behavior: the SDK endpoint precedence, and each member's meaning and type.

## Compatibility
- Existing behavior is unchanged: client-creation arguments and existing tests produce the same results. The STS change only adds acceptance of an absent configuration.

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
- Add a test class named TestEndpointResolverBuiltins to tests/unit/test_args.py. It derives directly from the standard unit-test case class, not from the existing args test class, which would re-run all its tests.
- setUp: build a ClientArgsCreator with a mock event emitter spec'd on the hierarchical emitter, absent user agent, response parser factory, loader, exceptions factory, and a config value store as the config store. Build a ClientEndpointBridge with a mock endpoint resolver, no scoped config, a default client config, no default endpoint, no signing name, and the same config store. The resolver's bundled-data flag defaults to true.
- Each behavioral criterion above has a test.
- The S3 predicate test mocks the predicate and asserts it is called once.
- Name each test for the scenario its body actually sets up. Do not name a test for a flag value or input other than the one it sets.
- For legacy SDK endpoint scenarios, use exactly one test for the custom-data case (bundled-data flag false, legacy URL returned) and exactly one for the bundled-data case (flag true, value absent). No two tests may share a body.
- All existing tests in tests/unit/test_args.py continue to pass.
