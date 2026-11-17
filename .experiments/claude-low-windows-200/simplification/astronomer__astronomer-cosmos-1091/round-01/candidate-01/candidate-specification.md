## Goals

- Add OAuth-based authentication for Databricks Airflow connections as a new dbt profile mapping. A Databricks connection whose credentials are an OAuth client id and client secret converts to a dbt profile without a personal access token.
- Keep token-based Databricks profile selection and output unchanged.

## Scope

In scope:
- A new Databricks OAuth profile-mapping class beside the existing token mapping module.
- Registration in the ordered profile-mapping list used for automatic selection, and in the package exports of the Databricks package and the profiles package.
- Tests in the existing Databricks profile test layout.

Out of scope:
- Changes to the shared profile base class, the token mapping, the automatic-selection loop, Airflow connection handling, or dbt execution.
- Documentation pages and changelog entries.

## Terminology

- Token mapping: the existing Databricks token profile mapping.
- OAuth mapping: the new Databricks OAuth profile mapping.
- Claim: a mapping's claim check returns true for a connection. Automatic selection walks the ordered list and returns the first mapping that claims the connection.
- Secret field: a field written to the profile as an environment-variable reference and listed in the environment-variable outputs.

## Workflows

- The OAuth mapping sits immediately after the token mapping in the ordered list. Any connection the token mapping claims resolves to the token mapping, including connections that also set a login value.
- The token mapping claims a connection when host, schema, and http path are present and a password or extra token is set. A connection with login, password, host, schema, and http path therefore still resolves to the token mapping.
- The OAuth mapping is selected automatically only when the token mapping does not claim the connection, for example when no password is set and an extra client secret is supplied.
- When constructed directly, the OAuth mapping's claim result depends only on its own required fields.

## Data model

Field sources, in precedence order (first non-empty value wins):

| dbt field | Airflow sources | Notes |
|---|---|---|
| host | host | Passed through unchanged. No scheme stripping. |
| schema | schema | Required. |
| http_path | extra http_path | Required. |
| client_id | login, then extra client_id | Secret field. |
| client_secret | password, then extra client_secret | Secret field. |

- Required for the claim check: host, schema, http_path, client_id, client_secret.
- The profile is built in this order, where later entries win: mapped fields, caller-supplied profile arguments, the fixed auth type, then environment-variable references for client_secret and client_id. Profile arguments may override ordinary mapped fields but never the auth type or the two secret fields.
- The profile must not set a dbt method key.

## API contracts

- The class subclasses the shared profile-mapping base and is constructed like the other mappings (connection identifier plus profile arguments). It adds no public methods or constructor parameters.
- Airflow connection type: databricks. dbt profile type: databricks.
- The class is importable from the Databricks profile package and the profiles package under the same name.
- The profile output contains: the dbt type, the mapped fields, the profile-argument overrides, auth_type fixed to oauth, and client_secret and client_id as environment-variable references.
- Environment-variable names follow the base rule: prefix COSMOS_CONN_, upper-cased Airflow connection type, underscore, upper-cased field name. For this mapping the names are COSMOS_CONN_DATABRICKS_CLIENT_SECRET and COSMOS_CONN_DATABRICKS_CLIENT_ID.
- The environment-variable outputs contain both names, with the resolved client secret and client id as values.
- No plaintext client id or client secret may appear in the profile output.

## Module architecture

- The mapping lives in a new module in the Databricks profile package, beside the token module. The module contains one class subclassing the shared base.
- All behavior is declared on the class: required fields, secret fields, the Airflow-to-dbt field mapping, and the profile property. Beyond the base contract, the class supplies only the profile property.
- The registry module gains an import and an ordered-list entry directly after the token mapping entry. Package export lists gain the new name. The Databricks package initializer gains the import and export.

## Implementation constraints

- Do not override the claim check. Claim behavior comes entirely from the base class's required-field logic.
- Do not add a transform hook for the host field.
- Do not set the dbt method attribute on this mapping.
- Do not change the token mapping, the base class, or the automatic-selection loop.
- Do not introduce a second precedence mechanism. Precedence between the token and OAuth mappings is list order only.
- Docstrings describe the mapping, state that the client id and client secret are stored in environment variables, and link to the same dbt Databricks setup page and Airflow Databricks connection page used by the token mapping.
- Imports follow the sorted style of the registry and package initializers.

## Dependencies

Use only the existing shared profile base and the standard typing module. Add no new third-party package.

## Naming

- Module: oauth, in the Databricks profile package.
- Class: DatabricksOauthProfileMapping, following the DatabricksTokenProfileMapping pattern.
- Test file: test_dbr_oauth.py in the Databricks profiles test directory, beside the token test file.

## Validation

Validation comes only from the base class's required-field checks. A connection is claimed only when its connection type is databricks and every required field resolves to a truthy value. Add no custom validation.

## Error handling

Add no new exception types and no try/except blocks. When the OAuth mapping does not claim a connection, existing selection behavior applies, including the existing error raised when no mapping claims a connection.

## Documentation

Docstrings as described under Implementation constraints. Documentation pages and changelog entries are not required.

## Compatibility

- The change is non-breaking. Every connection the token mapping claims today still resolves to the token mapping, including connections that also set a login value.
- The token mapping, its profile output, and its existing tests are unchanged.
- Only connections the token mapping does not claim and that supply OAuth credentials newly resolve to the OAuth mapping.

## Behavioral acceptance criteria

- A connection with host, schema, http path, login, and password is selected automatically as the token mapping, not the OAuth mapping.
- A connection with host, schema, http path, extra client id, and extra client secret, and no password or extra token, is claimed by the OAuth mapping and selected automatically.
- The OAuth mapping does not claim a connection when any of host, schema, http path, client id, or client secret is missing. Client id and client secret are each checked against both of their sources.
- The OAuth profile sets auth_type to oauth, carries both secrets as environment-variable references, keeps the host unchanged, and its environment-variable outputs contain both names.
- Profile arguments cannot override auth_type or the two secret fields.

## Test requirements

- Tests live in the Databricks profiles test directory, in test_dbr_oauth.py, following the token test file's layout.
- Claim test: start from a fully populated connection, remove each required input in turn, and assert no claim. With all inputs present and a schema supplied, assert a claim.
- Selection test: a login-plus-password connection with host, schema, and http path is selected as the token mapping.
- Selection test: a connection with extra credentials and no password or token is selected as the OAuth mapping.
- Profile test: auth_type is oauth, both secrets are environment-variable references, the host is unchanged, and the environment-variable outputs contain both names.
- Expected values must match the code's output. Do not assert a plaintext client id.
- Patch the connection lookup as the token test does. Do not fetch connections from a real backend.
