## Goals

- Add OAuth-based authentication for Databricks Airflow connections as a new dbt profile mapping, so a Databricks connection whose credentials are an OAuth client id and client secret can be converted to a dbt profile without a personal access token.
- Keep existing token-based Databricks profile selection and output unchanged.

## Scope

In scope:
- A new Databricks OAuth profile-mapping class in the Databricks profile package, placed beside the existing token mapping module.
- Registration of the new class in the ordered profile-mapping list used for automatic selection, and in the package exports of both the Databricks package and the profiles package.
- Tests for the new mapping, in the existing Databricks profile test layout.

Out of scope:
- Any change to the shared profile base class, to the token mapping, to the automatic-selection loop, to Airflow connection handling, or to dbt execution.
- Documentation pages and changelog entries.

## Terminology

- Token mapping: the existing Databricks token profile mapping.
- OAuth mapping: the new Databricks OAuth profile mapping.
- Claim: a mapping whose claim check returns true for a connection. Automatic selection walks the ordered mapping list and returns the first mapping that claims the connection.
- Secret field: a field whose value is written to the profile as an environment-variable reference and listed in the environment-variable outputs.

## Workflows

- Automatic selection: the OAuth mapping is placed immediately after the token mapping in the ordered list. For any connection the token mapping claims, the token mapping is returned, including connections that also set a login value.
- Token mapping claims a Databricks connection whenever its host, schema, and http path are present and a password or an extra token is set. Therefore a connection with login, password, host, schema, and http path resolves to the token mapping, as it does before this change.
- The OAuth mapping is selected automatically only when the token mapping does not claim the connection, for example when no password is set and an extra client secret is supplied.
- A caller may also construct the OAuth mapping directly with a connection and profile arguments. In that case the claim result depends only on the OAuth mapping's own required fields.

## Data model

Credential and field sources, in precedence order:

| dbt field | Airflow sources (first non-empty wins) | Notes |
|---|---|---|
| host | host | Passed through unchanged. No scheme stripping. |
| schema | schema | Required. |
| http_path | extra http_path | Required. |
| client_id | login, then extra client_id | Secret field. |
| client_secret | password, then extra client_secret | Secret field. |

- Required fields for the claim check: host, schema, client_secret, client_id, http_path.
- Secret fields: client_id and client_secret. Both must be present for the claim check to pass.
- The profile is built in this order, where later entries win: first the mapped fields, then the caller-supplied profile arguments, then the fixed auth type value, then the environment-variable references for client_secret and client_id. Profile arguments may override ordinary mapped fields, but never the auth type or the two secret fields.
- The profile must not set a dbt method key for this mapping.

## API contracts

- The class is a subclass of the shared profile-mapping base and is constructed the same way as the other mappings (connection identifier plus profile arguments). It adds no new public methods or constructor parameters.
- Airflow connection type: databricks. dbt profile type: databricks.
- The class is importable from the Databricks profile package and from the profiles package, with the same class name as the export name.
- The profile output contains: the dbt type, the mapped fields, the profile-argument overrides, auth_type with the fixed value oauth, client_secret as an environment-variable reference, and client_id as an environment-variable reference.
- Environment-variable names follow the base naming rule: the prefix COSMOS_CONN_, then the upper-cased Airflow connection type, then an underscore, then the upper-cased field name. For this mapping the names are COSMOS_CONN_DATABRICKS_CLIENT_SECRET and COSMOS_CONN_DATABRICKS_CLIENT_ID.
- The environment-variable outputs contain both secret names, and their values are the resolved client secret and client id.
- No plaintext client id or client secret may appear in the profile output.

## Module architecture

- The mapping lives in a new module in the Databricks profile package, next to the token module. The module contains one class that subclasses the shared base.
- All behavior is declared on the class: required fields, secret fields, the airflow-to-dbt field mapping, and the profile property. The class supplies the profile property and nothing else of the base contract.
- The registry module gains an import and an ordered-list entry. The entry sits directly after the token mapping entry. The package export lists gain the new name.
- The Databricks package initializer gains the import and export.

## Implementation constraints

- Do not override the claim check. Claim behavior comes entirely from the base class's required-field logic.
- Do not add any transform hook for the host field.
- Do not set the dbt method attribute on this mapping.
- Do not change the token mapping, the base class, or the automatic-selection loop.
- Do not introduce a second precedence mechanism. Precedence between the token and OAuth mappings is the list order only.
- Docstrings describe the mapping and state that the client id and client secret are stored in environment variables. Link to the same dbt Databricks setup page and Airflow Databricks connection page used by the token mapping.
- Import ordering follows the existing sorted style of the registry and package initializers.

## Dependencies

- Use only the existing shared profile base and the standard typing module. Do not add any new third-party package.

## Naming

- Module name: oauth, in the Databricks profile package.
- Class name: DatabricksOauthProfileMapping, following the DatabricksTokenProfileMapping pattern.
- Test file: test_dbr_oauth.py under the Databricks profiles test directory, next to the token test file.

## Validation

- Validation is done only by the base class's required-field checks on the connection and the profile. Do not add any custom validation.
- A connection is claimed only when its connection type is databricks and every required field resolves to a truthy value.

## Error handling

- Add no new exception types and no new try/except blocks.
- When the OAuth mapping does not claim a connection, the existing selection behavior applies, including the existing error raised when no mapping claims a connection.

## Documentation

- Docstrings as described under Implementation constraints.
- Documentation pages and changelog entries are not required by this feature.

## Compatibility

- The change is non-breaking. Every connection the token mapping claims today must still resolve to the token mapping through automatic selection, including connections that also set a login value.
- The token mapping, its profile output, and its existing tests are unchanged.
- Only connections that the token mapping does not claim, and that supply OAuth credentials, are newly resolved to the OAuth mapping.

## Behavioral acceptance criteria

- A Databricks connection with host, schema, http path, login (client id), and password (client secret) is resolved by automatic selection to the token mapping, not the OAuth mapping.
- A Databricks connection with host, schema, http path, and extra client id and extra client secret, with no password and no extra token, is claimed by the OAuth mapping and selected automatically.
- The OAuth mapping does not claim the connection when any one of host, schema, http path, client id, or client secret is missing. Client id and client secret are each checked against both of their sources.
- The OAuth profile sets auth_type to oauth, carries the client secret and client id as environment-variable references, keeps the host unchanged, and its environment-variable outputs contain both secret names.
- Profile arguments cannot override auth_type or the two secret fields.

## Test requirements

- Tests live in the Databricks profiles test directory in the file named test_dbr_oauth.py, following the layout of the token test file.
- Claim test: start from a fully populated connection and remove each required input in turn; assert the mapping does not claim. With all inputs present and a schema supplied, assert it claims.
- Selection test: assert that a login-plus-password connection with host, schema, and http path is selected as the token mapping by automatic selection.
- Selection test: assert that a connection with extra credentials and no password or token is selected as the OAuth mapping.
- Profile test: assert auth_type is oauth, both secrets are environment-variable references, the host is unchanged, and the environment-variable outputs contain both secret names.
- Expected values in every test must match what the code produces. Do not assert a plaintext client id.
- The tests must not depend on Airflow connection objects being fetched from a real backend; patch the connection lookup as the token test does.
