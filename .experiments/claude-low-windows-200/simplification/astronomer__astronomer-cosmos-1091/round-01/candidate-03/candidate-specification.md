## Goals

- Add OAuth authentication for Databricks Airflow connections as a new dbt profile mapping. A Databricks connection whose credentials are an OAuth client id and client secret converts to a dbt profile without a personal access token.
- Keep token-based Databricks profile selection and output unchanged.

## Scope

In scope:
- A new Databricks OAuth profile-mapping class in the Databricks profile package, beside the token mapping module.
- Registration in the ordered profile-mapping list used for automatic selection, and in the export lists of the Databricks package and the profiles package.
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

- Automatic selection: the OAuth mapping sits immediately after the token mapping. Any connection the token mapping claims resolves to the token mapping, including connections that also set a login value.
- The token mapping claims a connection when host, schema, and http path are present and a password or extra token is set. So a connection with login, password, host, schema, and http path still resolves to the token mapping.
- The OAuth mapping is selected only when the token mapping does not claim the connection, for example when no password is set and an extra client secret is supplied.
- Constructed directly, the OAuth mapping's claim result depends only on its own required fields.

## Data model

Field sources, first non-empty wins:

| dbt field | Airflow sources | Notes |
|---|---|---|
| host | host | Passed through unchanged. No scheme stripping. |
| schema | schema | Required. |
| http_path | extra http_path | Required. |
| client_id | login, then extra client_id | Secret field. |
| client_secret | password, then extra client_secret | Secret field. |

- Required fields for the claim check: host, schema, http_path, client_id, client_secret.
- The profile is built in this order, later entries winning: mapped fields, then caller-supplied profile arguments, then the fixed auth type, then the environment-variable references for client_secret and client_id. Profile arguments may override ordinary mapped fields, but never the auth type or the secret fields.
- The profile must not set a dbt method key.

## API contracts

- The class subclasses the shared profile-mapping base and is constructed like the other mappings (connection identifier plus profile arguments). It adds no public methods or constructor parameters.
- Airflow connection type: databricks. dbt profile type: databricks.
- The class is importable from the Databricks profile package and the profiles package under the same name.
- Profile output contains: the dbt type, the mapped fields, the profile-argument overrides, auth_type set to oauth, client_secret and client_id as environment-variable references.
- Environment-variable names follow the base rule: prefix COSMOS_CONN_, upper-cased Airflow connection type, underscore, upper-cased field name. The names are COSMOS_CONN_DATABRICKS_CLIENT_SECRET and COSMOS_CONN_DATABRICKS_CLIENT_ID.
- The environment-variable outputs contain both names, with the resolved client secret and client id as values.
- No plaintext client id or client secret appears in the profile output.

## Module architecture

- A new module beside the token module in the Databricks profile package holds one class subclassing the shared base.
- All behavior is declared on the class: required fields, secret fields, the Airflow-to-dbt field mapping, and the profile property. The class supplies only the profile property beyond the base contract.
- The registry module gains an import and an ordered-list entry directly after the token entry. The package export lists gain the new name.
- The Databricks package initializer gains the import and export.

## Implementation constraints

- Do not override the claim check, add a host transform hook, or set the dbt method attribute.
- Do not change the token mapping, the base class, or the automatic-selection loop.
- Precedence between the token and OAuth mappings comes only from list order. Add no second precedence mechanism.
- Docstrings describe the mapping and state that the client id and client secret are stored in environment variables. Link the same dbt Databricks setup page and Airflow Databricks connection page the token mapping uses.
- Imports follow the sorted style of the registry and package initializers.

## Dependencies

- Use only the shared profile base and the standard typing module. Add no third-party package.

## Naming

- Module: oauth, in the Databricks profile package.
- Class: DatabricksOauthProfileMapping, following the DatabricksTokenProfileMapping pattern.
- Test file: test_dbr_oauth.py in the Databricks profiles test directory, beside the token test file.

## Validation

- Validation comes only from the base class's required-field checks. Add no custom validation.
- A connection is claimed only when its type is databricks and every required field resolves to a truthy value.

## Error handling

- Add no new exception types or try/except blocks.
- When the OAuth mapping does not claim a connection, existing selection behavior applies, including the existing error raised when no mapping claims it.

## Documentation

- Docstrings as described under Implementation constraints. Documentation pages and changelog entries are not required.

## Compatibility

- Non-breaking. Every connection the token mapping claims today still resolves to the token mapping, including connections with a login value.
- The token mapping, its profile output, and its tests are unchanged.
- Only connections the token mapping does not claim and that supply OAuth credentials newly resolve to the OAuth mapping.

## Behavioral acceptance criteria

- A connection with host, schema, http path, login, and password resolves by automatic selection to the token mapping.
- A connection with host, schema, http path, extra client id, and extra client secret, and no password or extra token, is claimed by and selected as the OAuth mapping.
- The OAuth mapping does not claim a connection missing any of host, schema, http path, client id, or client secret. Client id and client secret are each checked against both sources.
- The OAuth profile sets auth_type to oauth, carries both secrets as environment-variable references, keeps the host unchanged, and its environment-variable outputs contain both secret names.
- Profile arguments cannot override auth_type or the two secret fields.

## Test requirements

- Tests live in test_dbr_oauth.py in the Databricks profiles test directory, following the token test file's layout.
- Claim test: start from a fully populated connection, remove each required input in turn, and assert no claim. With all inputs and a schema present, assert a claim.
- Selection test: a login-plus-password connection with host, schema, and http path selects the token mapping.
- Selection test: a connection with extra credentials and no password or token selects the OAuth mapping.
- Profile test: auth_type is oauth, both secrets are environment-variable references, the host is unchanged, and the environment-variable outputs contain both names.
- Expected values must match what the code produces. Do not assert a plaintext client id.
- Patch the connection lookup as the token test does; do not fetch connections from a real backend.
