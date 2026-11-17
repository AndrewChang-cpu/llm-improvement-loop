## Goals
Add a public helper on ClientArgsCreator that computes the eleven endpoint-ruleset builtin values for one client creation, plus a named registry of builtin names. Nothing calls the helper yet, and no existing argument output changes.

## Scope
In scope:
- A new public helper on ClientArgsCreator in botocore/args.py.
- A new str-valued enumeration in botocore/regions.py.
- Accepting an absent endpoint configuration in the existing STS global-endpoint predicate.
- Unit tests in tests/unit/test_args.py.

Out of scope: the existing argument-computation and client-creation paths, ClientCreator, botocore/client.py, the endpoint provider, resolver, and bridge, event hooks, and new keys in existing return values.

## Assumptions
- The endpoint bridge already resolves FIPS and DualStack: its variant lookup gives client config precedence over the config store, and its DualStack lookup applies S3 dualstack handling only to the s3 and s3-control services.
- ClientArgsCreator already has S3 and STS global-endpoint predicates. Reuse them.
- The endpoint resolver exposes a flag saying whether it uses bundled endpoint data.
- The caller supplies the S3 configuration as a mapping, possibly empty.

## Terminology
- Builtin: a named input that endpoint rulesets consume.
- Client endpoint URL: the URL passed to client creation.
- Legacy endpoint URL: the URL produced by legacy endpoint resolution.
- Custom endpoint data: the resolver's bundled-data flag is false.

## Workflows
Every call computes all eleven builtins, regardless of service name:
1. SDK::Endpoint: a truthy client endpoint URL wins. Otherwise, if custom endpoint data is in use, use the legacy endpoint URL (possibly absent). Otherwise the value is absent.
2. AWS::UseFIPS: the bridge's use_fips_endpoint variant lookup, or false if falsy. A custom endpoint does not suppress it; the reference's suppression clause never takes effect.
3. AWS::UseDualStack: the bridge's DualStack lookup for the service name, or false if falsy. Same non-suppression rule.
4. AWS::STS::UseGlobalEndpoint: call the STS predicate with the region name, no endpoint URL, and no endpoint configuration. Do not check the service name.
5. AWS::S3::UseGlobalEndpoint: call the S3 predicate with the region name and the S3 configuration.
6. AWS::S3::Accelerate: S3 configuration key use_accelerate_endpoint, default false.
7. AWS::S3::ForcePathStyle: true exactly when S3 configuration key addressing_style equals path; otherwise false.
8. AWS::S3::UseArnRegion: key use_arn_region, default true, passed through unchanged.
9. AWS::S3Control::UseArnRegion: same key, default false, passed through unchanged.
10. AWS::S3::DisableMultiRegionAccessPoints: key s3_disable_multiregion_access_points, default false.
11. AWS::Region: the region name argument exactly as given.

## Data model
- Enumeration EndpointResolverBuiltins in botocore/regions.py, mixing in str so each member compares equal to its value. Each member has a comment giving its meaning and type. The helper returns a mapping whose keys are the eleven members.

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

## API contracts
- Public method compute_endpoint_resolver_builtin_defaults on ClientArgsCreator, with required parameters in this order: region_name, service_name, s3_config, endpoint_bridge, client_endpoint_url, legacy_endpoint_url. Tests use these exact keyword names. It returns the Data model mapping.
- The STS predicate accepts an absent endpoint configuration, treated as having no variant tags. Results for present inputs do not change.
- No other existing public name or signature changes.

## Module architecture
- botocore/args.py: add the helper as a ClientArgsCreator method after the existing boolean-coercion helper at the end of the class. Import the enumeration under the alias in Naming, after the botocore.endpoint import. regions.py does not import args, so no cycle arises.
- botocore/regions.py: add a standard-library enum import at the top, and append the enumeration after the template-expansion helper.
- botocore/client.py is not modified.

## Implementation constraints
- Get FIPS and DualStack only from the bridge's lookups. Do not read Config attributes or config-store entries directly, and do not reimplement S3 DualStack scoping.
- Reuse the existing S3 and STS predicates. Do not restate their rules or parse booleans again; they already coerce values.
- The helper only reads configuration through those lookups and predicates. It performs no writes, keeps no cache, and has no side effects.
- Do not add the result to compute_client_args, change get_client_args, or call the helper from the client-creation path.

## Naming
- Enumeration name EndpointResolverBuiltins. Member names and values exactly as in the Data model table, including the "::" separators and the SDK prefix.
- In botocore/args.py, import the enumeration as EPRBuiltins and refer to members through it, keeping lines within the length limit.
- Implementation refers to builtins through the enumeration, not repeated string literals.

## Validation
- Every added line in the three touched modules, including comments, docstrings, and test code, fits within 79 columns. Wrap as black would.
- Imports follow isort with profile black. In botocore/args.py the new import goes after botocore.endpoint and before botocore.signers. In tests/unit/test_args.py, any enumeration import goes after botocore.model and before the tests package import.
- Tests may assert on builtin string values, which need no new import, unless members are needed.

## Performance
- The helper is off the client-creation path, so creation cost is unchanged. No caching.

## Reliability
- The helper must not fail when the STS predicate receives no endpoint configuration.
- FIPS and DualStack are never absent: falsy bridge results become false.
- Errors from the reused predicates for invalid STS or S3 regional-endpoint settings propagate unchanged.

## Documentation
- Do not describe the helper or enumeration as pure, or promise any read or write guarantee the code does not provide.
- Comments describe actual behavior: SDK endpoint precedence and each member's meaning and type.

## Compatibility
- Existing client-creation arguments and tests produce the same results. The STS change only accepts an absent configuration.

## Behavioral acceptance criteria
- Default (region ca-central-1, service fooservice, empty S3 config, bundled data, legacy URL https://my.legacy.endpoint.com, no client URL): AWS::Region ca-central-1; UseFIPS and UseDualStack false; STS true; S3 global, Accelerate, and ForcePathStyle false; S3 UseArnRegion true; S3Control UseArnRegion false; MRAP false; SDK::Endpoint absent.
- Config store use_fips_endpoint true gives UseFIPS true; false gives false.
- Service s3-control with client config s3 use_dualstack_endpoint true gives UseDualStack true; false gives false. Service other-service with true gives UseDualStack false.
- Region us-west-2 with default STS configuration gives STS true. Region eu-south-1 gives STS false. Region us-west-2 with sts_regional_endpoints set to regional gives STS false.
- When the S3 predicate returns true, S3 global is true and the predicate is called exactly once.
- use_accelerate_endpoint true and false pass through to Accelerate.
- addressing_style path gives ForcePathStyle true; auto and virtual give false.
- use_arn_region false gives both UseArnRegion values false; true gives both true.
- s3_disable_multiregion_access_points true and false pass through to MRAP.
- SDK endpoint: a client URL is returned even when custom data and a legacy URL are present. With no client URL and custom data, the legacy URL is returned. With no client URL and bundled data, the value is absent even when a legacy URL is present.

## Test requirements
- Add class TestEndpointResolverBuiltins to tests/unit/test_args.py, deriving from the standard unit-test case class rather than the existing args test class, which would re-run its tests.
- setUp: a ClientArgsCreator with a mock event emitter spec'd on the hierarchical emitter, absent user agent, response parser factory, loader, exceptions factory, and a config value store as the config store. A ClientEndpointBridge with a mock endpoint resolver (bundled-data flag true by default), no scoped config, default client config, no default endpoint, no signing name, and the same config store.
- Each behavioral criterion has a test. The S3 predicate test mocks the predicate and asserts exactly one call.
- Name each test for the scenario its body sets up.
- Exactly one test covers the custom-data legacy case and exactly one covers the bundled-data case. No two tests have the same body.
- All existing tests in tests/unit/test_args.py continue to pass.
