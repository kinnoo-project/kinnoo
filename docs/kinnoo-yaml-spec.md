# kinnoo.yaml Specification

This document defines the current `kinnoo.yaml` manifest contract used by Kinnoo CLI validation and runtime behavior.

## Scope and Version

- Schema source of truth: `src/kinnoo/schema.py` and `src/kinnoo/validator.py`
- Manifest schema version key: none (no `schema_version` field required)
- Backward compatibility posture:
  - existing manifests remain valid when optional fields are omitted
  - selected legacy values and aliases are still accepted
  - some historical metadata keys are intentionally rejected

## Where the File Lives

- Path: `<agent-root>/kinnoo.yaml`
- Used by commands:
  - `kinnoo init` writes it
  - `kinnoo inspect` reads and validates it
  - `kinnoo run` validates it before execution
  - `kinnoo pack` validates it before packaging
  - `kinnoo publish` reads metadata from packaged archives

## Required Fields (Current)

All fields below are required by the current validator contract.

| Field | Type | Required | Default | Validation rules |
| --- | --- | --- | --- | --- |
| [name](#field-name) | string | yes | none | must match `^[a-z0-9][a-z0-9-_]*$` |
| [version](#field-version) | string | yes | none | must be valid semantic version |
| [entrypoint / entrypoints](#field-entrypoint-contract) | string or list[string] | yes (one of the two) | none | `entrypoint` and `entrypoints` are mutually exclusive |
| [runtime.language](#field-runtime-language) | string | yes | none | enum-constrained |
| [runtime.version](#field-runtime-version) | string | yes | none | non-empty string expected |
| [runtime.type](#field-runtime-type) | string | yes | none | enum-constrained |
| [dependencies](#field-dependencies) | list | yes | `[]` if omitted during normalization | must be a list |
| [inputs.type](#field-inputs-type) | list[string] | yes | `['string']` after normalization | enum-constrained |
| [outputs.type](#field-outputs-type) | list[string] | yes | `['string']` after normalization | enum-constrained |

## Optional Fields (Current)

The table below reflects optional fields currently recognized by schema constants and runtime/command behavior.

| Field | Type | Required | Default | Validation rules |
| --- | --- | --- | --- | --- |
| [framework](#field-framework) | string | no | none | framework-specific checks apply for `openclaw` |
| [type](#field-type) | string | no | `agent` (implicit behavior) | enum-constrained |
| [description](#field-description) | string | no | none | free text |
| [author](#field-author) | string | no | none | free text |
| [license](#field-license) | string | no | none | free text |
| [env_vars](#field-env-vars) | list[string] | no | none | entries must be non-empty strings |
| [model](#field-model) | string | no | none | non-empty string if present |
| [entrypoints](#field-entrypoint-contract) | list[string] | no | none | non-empty list of non-empty strings |
| [runtime.path](#field-runtime-path) | string | no | none | non-empty string |
| [runtime.run_command](#field-runtime-run-command) | string | no | none | string |
| [runtime.package_manager](#field-runtime-package-manager) | string | no | none | enum-constrained |
| [inputs.required](#field-inputs-required) | bool | no | none | boolean |
| [assets](#field-assets) | object | no | none | nested field checks apply |
| [assets.paths](#field-assets-paths) | list[string] | no | `[]` after normalization | non-empty strings |
| [assets.bundle](#field-assets-bundle) | bool | no | `true` after normalization | boolean |
| [assets.max_bundle_size_mb](#field-assets-max-bundle-size-mb) | int or float | no | `100` after normalization | numeric, not bool |
| [services](#field-services) | list[object] | no | none | schema + enum + health check validation |
| [permissions](#field-permissions) | object | no | none | validated against feature39/legacy mcp schema |
| [tests](#field-tests) | list | no | none | tests document validation applies |
| [tests_file](#field-tests-file) | string | no | none | non-empty string |
| [tests_version](#field-tests-version) | int or string | no | `1` used when omitted in tests evaluation | type-constrained |
| [provenance](#field-provenance) | object | no | none | nested provenance checks apply |
| [provenance.source_registry](#field-provenance-source-registry) | string | no | none | required when `provenance` object exists |
| [provenance.source_slug](#field-provenance-source-slug) | string | no | none | at least one of slug/url required when provenance exists |
| [provenance.source_url](#field-provenance-source-url) | string | no | none | at least one of slug/url required when provenance exists |
| [provenance.source_version](#field-provenance-source-version) | string | no | none | required when `provenance` object exists |
| [visibility](#field-visibility) | string | no | defaults to public behavior in pack/publish flows when omitted | command/server behavior field |

## Detailed Field Reference

<a id="field-name"></a>
### name

- Description:
  - Canonical package identifier for the agent.
- Supported values:
  - lowercase alphanumeric, hyphen, underscore.
- Format:
  - regex: `^[a-z0-9][a-z0-9-_]*$`
- Examples:

```yaml
name: support-agent
```

```yaml
name: data_router_v2
```

```yaml
name: mcpbridge
```

- Notes:
  - Must start with a letter or digit.

<a id="field-version"></a>
### version

- Description:
  - Semantic version for release and package resolution.
- Supported values:
  - semver: `MAJOR.MINOR.PATCH` with optional pre-release/build metadata.
- Format:
  - examples: `1.0.0`, `2.1.0-rc.1`, `1.4.2+build.7`
- Examples:

```yaml
version: 1.0.0
```

```yaml
version: 2.0.0-beta.2
```

```yaml
version: 3.1.4+meta.9
```

- Notes:
  - Invalid semver fails validation.

<a id="field-entrypoint-contract"></a>
### entrypoint or entrypoints

- Description:
  - Declares executable script path(s).
  - Exactly one contract is allowed: single `entrypoint` or list `entrypoints`.
- Supported values:
  - `entrypoint`: one non-empty string path.
  - `entrypoints`: non-empty list of non-empty string paths.
- Format:
  - relative file paths within agent directory.
  - `entrypoint` and `entrypoints` are mutually exclusive.
- Examples:

```yaml
entrypoint: run.py
```

```yaml
entrypoints:
  - scripts/main.py
  - scripts/alt.py
```

```yaml
entrypoint: src/index.ts
```

- Notes:
  - If `entrypoints` is used, default run selection is the first item unless `--entrypoint` is passed.
  - For `runtime.language: go`, use `main.go` for source-mode agents generated by `kinnoo init --language go`.
  - For precompiled Go binaries, set `entrypoint` to the executable artifact path (for example `bin/agent` or `dist/agent.exe`).

<a id="field-runtime-language"></a>
### runtime.language

- Description:
  - Runtime language selector.
- Supported values:
  - `python`
  - `nodejs`
  - `javascript`
  - `typescript`
  - `go`
- Format:
  - lowercase string enum.
- Examples:

```yaml
runtime:
  language: python
```

```yaml
runtime:
  language: nodejs
```

```yaml
runtime:
  language: typescript
```

```yaml
runtime:
  language: go
```

- Notes:
  - `openclaw` framework requires `nodejs`.
  - Go scaffolds generated by `kinnoo init --language go` default to `entrypoint: main.go`.

<a id="field-runtime-version"></a>
### runtime.version

- Description:
  - Declares runtime version constraint or runtime baseline.
- Supported values:
  - any non-empty string (validator checks type; empty values are not useful and should be avoided).
- Format:
  - quote range-like values.
- Examples:

```yaml
runtime:
  version: ">=3.10"
```

```yaml
runtime:
  version: ">=20"
```

```yaml
runtime:
  version: "3.12"
```

- Notes:
  - Use quoted strings for portability.

<a id="field-runtime-type"></a>
### runtime.type

- Description:
  - Declares runtime execution mode.
- Supported values:
  - `one-shot`
  - `mcp-server`
  - `daemon`
- Format:
  - lowercase string enum.
- Examples:

```yaml
runtime:
  type: one-shot
```

```yaml
runtime:
  type: mcp-server
```

```yaml
runtime:
  type: daemon
```

- Notes:
  - `openclaw` framework requires `daemon`.

<a id="field-dependencies"></a>
### dependencies

- Description:
  - Declarative dependency list.
- Supported values:
  - list entries (commonly package specifier strings).
- Format:
  - YAML list.
- Examples:

```yaml
dependencies: []
```

```yaml
dependencies:
  - requests>=2.31.0
  - pydantic>=2.8
```

```yaml
dependencies:
  - "@modelcontextprotocol/sdk@^1.0.0"
```

- Notes:
  - Validator enforces list type; package-spec format is command/runtime-specific.

<a id="field-inputs-type"></a>
### inputs.type

- Description:
  - Declares accepted input contract type(s).
- Supported values:
  - `text`
  - `string`
  - `file`
  - `json`
- Format:
  - canonical format is list of strings.
  - single-string form is normalized to list.
- Examples:

```yaml
inputs:
  type: string
```

```yaml
inputs:
  type:
    - json
```

```yaml
inputs:
  type:
    - text
    - file
```

- Notes:
  - If omitted, normalization injects `string`.

<a id="field-outputs-type"></a>
### outputs.type

- Description:
  - Declares produced output contract type(s).
- Supported values:
  - `text`
  - `string`
  - `file`
  - `json`
- Format:
  - canonical format is list of strings.
  - single-string form is normalized to list.
- Examples:

```yaml
outputs:
  type: string
```

```yaml
outputs:
  type:
    - json
```

```yaml
outputs:
  type:
    - text
```

- Notes:
  - If omitted, normalization injects `string`.

<a id="field-framework"></a>
### framework

- Description:
  - Framework hint used by init/import/template/runtime conventions.
- Supported values:
  - No strict global enum in validator.
  - Common current values include `chatgpt`, `gemini`, `claude-chat`, `pydantic-ai`, `langgraph`, `openai-agents`, `mcp-server`, `openclaw`, `no-framework`.
- Format:
  - string.
- Examples:

```yaml
framework: langgraph
```

```yaml
framework: openclaw
```

```yaml
framework: chatgpt
```

- Notes:
  - If set to `openclaw`, runtime constraints are enforced.

<a id="field-type"></a>
### type

- Description:
  - Manifest package type.
- Supported values:
  - `agent`
- Format:
  - lowercase enum string.
- Examples:

```yaml
type: agent
```

```yaml
type: agent
```

- Notes:
  - Use `agent` for all packages.

<a id="field-description"></a>
### description

- Description:
  - Human-readable summary text.
- Supported values:
  - any string.
- Format:
  - plain string or YAML multiline block.
- Examples:

```yaml
description: Answers registry support questions.
```

```yaml
description: "Fetches status and generates concise summaries."
```

```yaml
description: |
  Multi-step operations assistant for internal support triage.
```

- Notes:
  - Displayed in inspect/list/search contexts.

<a id="field-author"></a>
### author

- Description:
  - Author/owner metadata.
- Supported values:
  - any string.
- Format:
  - plain string.
- Examples:

```yaml
author: Kinnoo Team
```

```yaml
author: jerry@example.com
```

```yaml
author: Agent Platform Group
```

- Notes:
  - Informational metadata only.

<a id="field-license"></a>
### license

- Description:
  - Package license metadata.
- Supported values:
  - any string, commonly SPDX identifier.
- Format:
  - plain string.
- Examples:

```yaml
license: Apache-2.0
```

```yaml
license: MIT
```

```yaml
license: Proprietary
```

- Notes:
  - Informational metadata in manifest context.

<a id="field-env-vars"></a>
### env_vars

- Description:
  - Declares required environment variable names (not values).
- Supported values:
  - list of non-empty strings.
- Format:
  - YAML list of variable names.
- Examples:

```yaml
env_vars: []
```

```yaml
env_vars:
  - OPENAI_API_KEY
  - KINNOO_REGISTRY_URL
```

```yaml
env_vars:
  - BACKEND_URL
```

- Notes:
  - Values should never be stored in manifest.

<a id="field-model"></a>
### model

- Description:
  - Model hint used by framework templates and runtime logic.
- Supported values:
  - non-empty string.
- Format:
  - plain string.
- Examples:

```yaml
model: gpt-4o-mini
```

```yaml
model: claude-3-5-sonnet
```

```yaml
model: gemini-1.5-pro
```

- Notes:
  - Empty string fails validation when field is present.

<a id="field-runtime-path"></a>
### runtime.path

- Description:
  - Optional runtime path override.
- Supported values:
  - non-empty string.
- Format:
  - relative path string.
- Examples:

```yaml
runtime:
  path: .venv/bin/python
```

```yaml
runtime:
  path: node
```

```yaml
runtime:
  path: ./bin/runner
```

- Notes:
  - Use relative, deterministic paths where possible.

<a id="field-runtime-run-command"></a>
### runtime.run_command

- Description:
  - Explicit runtime command override.
- Supported values:
  - string.
- Format:
  - shell command string.
- Examples:

```yaml
runtime:
  run_command: python run.py
```

```yaml
runtime:
  run_command: node dist/index.js
```

```yaml
runtime:
  run_command: pnpm start
```

- Notes:
  - Keep command portable and deterministic.

<a id="field-runtime-package-manager"></a>
### runtime.package_manager

- Description:
  - Node package manager selector used by runtime readiness/install paths.
- Supported values:
  - `npm`
  - `pnpm`
- Format:
  - lowercase enum string.
- Examples:

```yaml
runtime:
  package_manager: npm
```

```yaml
runtime:
  package_manager: pnpm
```

```yaml
runtime:
  package_manager: npm
```

- Notes:
  - Values outside this set fail validation.

<a id="field-inputs-required"></a>
### inputs.required

- Description:
  - Declares whether caller must provide input payload.
- Supported values:
  - `true` or `false`.
- Format:
  - boolean.
- Examples:

```yaml
inputs:
  required: true
```

```yaml
inputs:
  required: false
```

```yaml
inputs:
  required: true
  type: string
```

- Notes:
  - Optional schema field; behavior is command/runtime-specific.

<a id="field-assets"></a>
### assets

- Description:
  - Packaging asset policy container.
- Supported values:
  - object containing optional `paths`, `bundle`, `max_bundle_size_mb`.
- Format:
  - YAML object.
- Examples:

```yaml
assets:
  paths:
    - prompts/
```

```yaml
assets:
  bundle: true
```

```yaml
assets:
  paths:
    - data/
  bundle: false
  max_bundle_size_mb: 250
```

- Notes:
  - If `assets` exists, missing nested defaults are injected.

<a id="field-assets-paths"></a>
### assets.paths

- Description:
  - Additional file/directory paths to include in package bundle.
- Supported values:
  - list of non-empty strings.
- Format:
  - YAML list.
- Examples:

```yaml
assets:
  paths:
    - prompts/
    - data/
```

```yaml
assets:
  paths:
    - tools/
```

```yaml
assets:
  paths: []
```

- Notes:
  - Normalized to empty list when omitted under `assets`.

<a id="field-assets-bundle"></a>
### assets.bundle

- Description:
  - Controls whether declared assets are bundled.
- Supported values:
  - `true` or `false`.
- Format:
  - boolean.
- Examples:

```yaml
assets:
  bundle: true
```

```yaml
assets:
  bundle: false
```

```yaml
assets:
  bundle: true
  paths:
    - prompts/
```

- Notes:
  - Defaults to `true` when omitted under `assets`.

<a id="field-assets-max-bundle-size-mb"></a>
### assets.max_bundle_size_mb

- Description:
  - Bundle size budget value in MB.
- Supported values:
  - int or float.
- Format:
  - numeric (not boolean).
- Examples:

```yaml
assets:
  max_bundle_size_mb: 100
```

```yaml
assets:
  max_bundle_size_mb: 250
```

```yaml
assets:
  max_bundle_size_mb: 75.5
```

- Notes:
  - Defaults to `100` when omitted under `assets`.

<a id="field-services"></a>
### services

- Description:
  - Declares dependent service components and health checks.
- Supported values:
  - list of service objects.
  - `services[].type` allowed values:
    - canonical: `mcp-server`, `vector-db`, `database`, `api`, `local-process`
    - aliases accepted: `postgres`, `redis`, `http-api`, `process`
  - `health_check.method` allowed values: `tcp`, `http`, `process`
- Format:
  - each service object requires `name` and `type`.
  - `health_check` object has method-specific required fields:
    - `tcp` requires `port`
    - `http` requires `url`
    - `process` requires `process_name`
- Examples:

```yaml
services:
  - name: registry-db
    type: database
    health_check:
      method: tcp
      port: 5432
```

```yaml
services:
  - name: embeddings
    type: vector-db
    health_check:
      method: http
      url: http://localhost:6333/health
```

```yaml
services:
  - name: worker
    type: local-process
    health_check:
      method: process
      process_name: node
```

- Notes:
  - Duplicate `services[].name` values are rejected.

<a id="field-permissions"></a>
### permissions

- Description:
  - Permission policy object for runtime controls.
- Supported values:
  - feature39 schema keys:
    - `network` (bool)
    - `filesystem_scope` (`none`, `read-only`, `workspace-write`, `full`)
    - `shell` (bool)
    - `browser` (bool)
    - `env_access` (list[string])
  - legacy mcp-server schema keys still accepted in mcp-specific contract paths:
    - `read_only`, `allow_write`, `allow_create` (bool)
    - `allowed_paths` (list[string])
- Format:
  - object with key-specific value types.
- Examples:

```yaml
permissions:
  network: true
  filesystem_scope: read-only
  shell: false
  browser: false
  env_access:
    - OPENAI_API_KEY
```

```yaml
permissions:
  network: false
  filesystem_scope: none
  shell: false
  browser: false
  env_access: []
```

```yaml
permissions:
  read_only: true
  allow_write: false
  allow_create: false
  allowed_paths:
    - .
```

- Notes:
  - Validator applies feature39 enforcement for explicit sandbox policy keys.

<a id="field-tests"></a>
### tests

- Description:
  - Inline declarative test cases embedded directly in `kinnoo.yaml`.
- Supported values:
  - list structure validated by test document validator.
- Format:
  - list under `tests`, with optional companion `tests_version`.
- Examples:

```yaml
tests:
  - name: smoke
    input: hello
    expected_contains: hello
```

```yaml
tests_version: 1
tests:
  - name: basic-json
    input:
      foo: bar
    expected_type: json
```

```yaml
tests:
  - name: simple
    input: ping
    expected_contains: pong
```

- Notes:
  - You can also declare tests externally via `tests_file`.

<a id="field-tests-file"></a>
### tests_file

- Description:
  - Pointer to external declarative tests file.
- Supported values:
  - non-empty string path.
- Format:
  - path string (relative to agent dir or absolute in CLI usage context).
- Examples:

```yaml
tests_file: kinnoo.tests.yaml
```

```yaml
tests_file: tests/agent.tests.yaml
```

```yaml
tests_file: ./qa/regression.yaml
```

- Notes:
  - Empty string fails validation.

<a id="field-tests-version"></a>
### tests_version

- Description:
  - Version selector for tests document interpretation.
- Supported values:
  - int or string.
- Format:
  - scalar value.
- Examples:

```yaml
tests_version: 1
```

```yaml
tests_version: "1"
```

```yaml
tests_version: "v1"
```

- Notes:
  - If omitted when evaluating inline tests, validator/test logic uses version `1`.

<a id="field-provenance"></a>
### provenance

- Description:
  - Source metadata object for imported or mirrored artifacts.
- Supported values:
  - object with provenance nested fields.
- Format:
  - YAML object.
- Examples:

```yaml
provenance:
  source_registry: github
  source_url: https://github.com/acme/agent-repo
  source_version: v1.2.0
```

```yaml
provenance:
  source_registry: registry-archive
  source_slug: org/shared-assistant
  source_version: 1.2.3
```

```yaml
provenance:
  source_registry: internal
  source_slug: team/agent
  source_url: https://git.example.com/team/agent
  source_version: 2026.04
```

- Notes:
  - If provenance is present, additional required nested values apply.

<a id="field-provenance-source-registry"></a>
### provenance.source_registry

- Description:
  - Name of source registry/origin.
- Supported values:
  - non-empty string.
- Format:
  - scalar string.
- Examples:

```yaml
provenance:
  source_registry: github
```

```yaml
provenance:
  source_registry: registry-archive
```

```yaml
provenance:
  source_registry: internal
```

- Notes:
  - Required when `provenance` is declared.

<a id="field-provenance-source-slug"></a>
### provenance.source_slug

- Description:
  - Source-specific short identifier.
- Supported values:
  - string (commonly non-empty when used as provenance selector).
- Format:
  - scalar string.
- Examples:

```yaml
provenance:
  source_slug: org/my-agent
```

```yaml
provenance:
  source_slug: org/shared-assistant
```

```yaml
provenance:
  source_slug: team/assistant
```

- Notes:
  - At least one of `source_slug` or `source_url` is required when `provenance` exists.

<a id="field-provenance-source-url"></a>
### provenance.source_url

- Description:
  - Canonical source URL.
- Supported values:
  - string URL.
- Format:
  - scalar string.
- Examples:

```yaml
provenance:
  source_url: https://github.com/acme/agent
```

```yaml
provenance:
  source_url: https://registry.example.com/agents/org/shared-assistant
```

```yaml
provenance:
  source_url: https://git.example.com/team/assistant
```

- Notes:
  - At least one of `source_slug` or `source_url` is required when `provenance` exists.

<a id="field-provenance-source-version"></a>
### provenance.source_version

- Description:
  - Upstream source version label.
- Supported values:
  - non-empty string.
- Format:
  - scalar string.
- Examples:

```yaml
provenance:
  source_version: v1.0.0
```

```yaml
provenance:
  source_version: 1.2.3
```

```yaml
provenance:
  source_version: 2026.04.01
```

- Notes:
  - Required when `provenance` is declared.

<a id="field-visibility"></a>
### visibility

- Description:
  - Distribution visibility hint used in pack/publish and registry flows.
- Supported values:
  - practical values are `public` and `private`.
- Format:
  - scalar string.
- Examples:

```yaml
visibility: private
```

```yaml
visibility: public
```

```yaml
visibility: private
```

- Notes:
  - Current packaging/publish behavior defaults to public semantics when omitted.
  - CLI flags can enforce private/public behavior during pack/publish.

## Validation Rules (High Signal)

- Manifest must parse as a YAML mapping.
- Required fields must exist with expected types.
- `entrypoint` or `entrypoints` contract must be satisfied.
- `version` must be semver.
- `runtime.language`, `runtime.type`, `inputs.type`, `outputs.type`, and several optional fields are enum-constrained.
- Services and permissions have nested schema checks.
- OpenClaw contracts add framework/runtime/provenance constraints.
- Deferred fields `channels`, `skills`, and `state_dirs` are rejected.

## Framework Examples

### Generic

```yaml
name: generic-agent
version: 1.0.0
entrypoint: run.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies: []
inputs:
  type: string
outputs:
  type: string
```

### OpenClaw Agent Workspace

```yaml
name: workspace-agent
version: 1.2.3
framework: openclaw
type: agent
entrypoint: index.js
runtime:
  language: nodejs
  version: ">=20"
  type: daemon
dependencies: []
inputs:
  type: string
outputs:
  type: string
provenance:
  source_registry: github
  source_slug: org/workspace-agent
  source_version: 1.2.3
```

### Multi-entrypoint Python Agent

```yaml
name: multi-script-agent
version: 1.0.0
entrypoints:
  - scripts/main.py
  - scripts/alt.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies: []
inputs:
  type: string
outputs:
  type: string
```

## Related Documentation

- CLI reference: `docs/cli-reference.md`
- Security model: `docs/security-model.md`
- Getting started: `docs/getting-started.md`
- Registry guide: `docs/registry-guide.md`
