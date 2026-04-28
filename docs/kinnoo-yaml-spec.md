# kinnoo.yaml Specification

This document defines the `kinnoo.yaml` manifest format used by Kinnoo agents.

## Scope and Version

- Manifest schema version: current CLI schema (no explicit `schema_version` field in `kinnoo.yaml`)
- Primary implementation source:
  - `src/kinnoo/schema.py`
  - `src/kinnoo/validator.py`
- Backward compatibility:
  - Existing manifests that satisfy required fields continue to work when optional fields are omitted.
  - Some historical metadata keys are intentionally not supported and are rejected by validation.

## Where the File Lives

- Path: `<agent-root>/kinnoo.yaml`
- Used by commands:
  - `kinnoo init` writes it
  - `kinnoo inspect` reads and validates it
  - `kinnoo run` validates it before execution
  - `kinnoo pack` validates it before packaging
  - `kinnoo publish` reads metadata from packed archives

## Required Fields

All required fields must be present and correctly typed.

| Field | Type | Required | Default | Validation rules | Notes |
| --- | --- | --- | --- | --- | --- |
| `name` | `string` | yes | none | must match project name pattern (`NAME_PATTERN`) | Lowercase package-style name.
| `version` | `string` | yes | none | must be valid semantic version (`x.y.z` with optional pre-release/build) | Used in archive naming and publish/install selectors.
| `entrypoint` | `string` | yes | none | non-empty path | Must point to a file in the agent directory.
| `runtime.language` | `string` | yes | none | supported values: `python`, `nodejs` | Determines runtime behavior.
| `runtime.version` | `string` | yes | none | non-empty string constraint in validator | Quote version strings in YAML.
| `runtime.type` | `string` | yes | none | supported values are controlled by schema constants | Runtime execution mode.
| `dependencies` | `list` | yes | none | must be a list | For Python agents, package dependencies are typically mirrored in `requirements.txt` for pack/install flows.
| `inputs.type` | `list` (normalized from string) | yes | normalized to `['string']` when defaulted | supported values include `text`, `string`, `file`, `json` | CLI normalizes string forms.
| `outputs.type` | `list` (normalized from string) | yes | normalized to `['string']` when defaulted | supported values include `text`, `string`, `file`, `json` | CLI normalizes string forms.

## Optional Fields

Optional fields may be present depending on runtime, framework, and workflow needs.

| Field | Type | Required | Default | Validation rules | Notes |
| --- | --- | --- | --- | --- | --- |
| `framework` | `string` | no | none | additional rules apply for some frameworks (for example `openclaw`) | Used by init/import/template flows.
| `type` | `string` | no | `agent` (implicit) | supported values defined in schema | `openclaw-skill` has extra contract checks.
| `description` | `string` | no | none | free text | Displayed in inspect/list/search outputs.
| `author` | `string` | no | none | free text | Used as metadata.
| `license` | `string` | no | none | free text | Used as metadata.
| `env_vars` | `list[string]` | no | `[]` (runtime behavior) | entries must be non-empty names | Names only; values are never stored in manifest.
| `model` | `string` | no | none | free text | Commonly set by template frameworks.
| `runtime.path` | `string` | no | none | relative path semantics validated by command paths | Runtime override path.
| `runtime.run_command` | `string` | no | none | free text | Explicit run command override.
| `runtime.package_manager` | `string` | no | none | limited values for Node runtimes | Used by runtime/preflight/install.
| `inputs.required` | `bool` | no | none | boolean type | Declares input requirement semantics.
| `assets` | `object` | no | none | nested keys validated when present | Packaging asset controls.
| `assets.paths` | `list[string]` | no | `[]` (normalization) | each path must be safe/relative | Additional bundled files.
| `assets.bundle` | `bool` | no | `true` (normalization) | boolean type | Controls asset bundling.
| `assets.max_bundle_size_mb` | `int/float` | no | `100` (normalization) | numeric | Size budget warning/guard.
| `services` | `list` | no | none | service schema validation applies | Runtime service declarations.
| `permissions` | `object` | no | none | permission-key and value validation applies | Used by sandbox and install consent flow.
| `tests` | `list` | no | none | test document validation applies | Declarative agent tests.
| `tests_file` | `string` | no | none | path/value checks in test command | External tests file pointer.
| `tests_version` | `int/string` | no | none | type validation | Test schema coordination.
| `provenance` | `object` | no | none | nested string fields validated when present | Source metadata for imported agents.
| `provenance.source_registry` | `string` | no | none | non-empty when present | Source origin.
| `provenance.source_slug` | `string` | no | none | non-empty when present | Upstream identifier.
| `provenance.source_url` | `string` | no | none | non-empty when present | Upstream URL.
| `provenance.source_version` | `string` | no | none | non-empty when present | Upstream version label.
| `visibility` | `string` | no | `private` on server publish when omitted | server-side behavior key | Use `public` when you want cross-tenant discovery.

## Validation Rules (High Signal)

- Manifest must parse as a YAML mapping/object.
- Required fields must exist with expected types.
- `version` must be semver.
- `runtime.language`, `runtime.type`, and some nested fields are enum-constrained.
- IO types are enum-constrained.
- Some metadata keys are intentionally disallowed in current schema versions.
- `openclaw-skill` manifests have additional framework/runtime/provenance constraints.

## Framework Examples

Examples below are intentionally minimal and accurate to current command behavior.

### Generic (no framework)

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

### chatgpt

```yaml
name: chatgpt-agent
version: 1.0.0
framework: chatgpt
model: gpt-4o-mini
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

### gemini

```yaml
name: gemini-agent
version: 1.0.0
framework: gemini
model: gemini-1.5-pro
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

### openai (OpenAI Agents scaffold)

```yaml
name: openai-agents-agent
version: 1.0.0
framework: openai-agents
model: gpt-4o-mini
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

### claude (claude-chat scaffold)

```yaml
name: claude-chat-agent
version: 1.0.0
framework: claude-chat
model: claude-3-5-sonnet
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

## Notes on Defaults and Normalization

- Some defaults are introduced by normalization code when reading manifest data (`dependencies`, `inputs`, `outputs`, `assets` fields).
- YAML may allow single-string forms for `inputs.type`/`outputs.type`; runtime normalizes to list form.

## Manifest Format History

- Current format source: `src/kinnoo/schema.py` + `src/kinnoo/validator.py` in this repository state.
- No in-file manifest version key is required at this time.
- Backward-compatibility posture:
  - Older manifests that satisfy required fields remain valid.
  - Newly introduced optional fields are additive.
  - A small set of deferred/unsupported metadata keys is intentionally rejected by validator rules.

## Command Cross-Reference

- `kinnoo inspect` is the fastest way to validate and review manifest metadata in a directory or `.kno` archive.
- Default packaging behavior is public visibility when `visibility` is unset.
- `kinnoo pack --private` and `kinnoo publish --private --pack` can enforce `visibility: private` before packaging.
- `kinnoo pack --public` normalizes to default-public behavior by removing a `visibility: private` override.

## Related Documentation

- CLI reference: `docs/cli-reference.md`
- Security model: `docs/security-model.md`
- Getting started: `docs/getting-started.md`
- Registry guide: `docs/registry-guide.md`