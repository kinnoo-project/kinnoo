# CLI Reference

This reference documents the current Kinnoo command-line interfaces.

- Client CLI: `kinnoo`
- Server CLI: `kinnoo-server`

## Conventions

- Exit code `0`: command completed successfully.
- Exit code non-zero: command failed validation, trust checks, network/auth checks, or runtime execution.
- Most examples assume you run from repository root or a workspace where agent paths are valid.

## Common Environment Variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `KINNOO_REGISTRY_URL` | `login`, `publish`, `install`, `list`, `search`, `fetch` | Remote registry base URL override |
| `KINNOO_REGISTRY_TOKEN` | `publish`, `install`, `list`, `search`, `fetch` | Remote auth token override |
| `KINNOO_TENANT_SLUG` | `publish`, `install`, `list`, `search`, `fetch` | Tenant context override |

## Client Commands (`kinnoo`)

### init

- Usage: `kinnoo init [framework] [--language {python,javascript,typescript}] [--minimal] [agent_name]`
- Description: Scaffold a new agent directory.
- Arguments:
  - `framework` (optional): framework template.
  - `agent_name` (optional): destination folder name.
- Options:
  - `--language`: choose scaffold language when framework supports multiple runtimes.
  - `--minimal`: generate minimal scaffold only (skip extra `tools/`, `prompts/`, `evals/`, `tests/`, `data/` extras).
- Practical notes:
  - If both `framework` and `agent_name` are omitted in an interactive terminal, Kinnoo opens an interactive wizard.
  - Legacy `kinnoo init <agent_name>` remains backward-compatible.
- Exit codes: non-zero on invalid names, unsupported framework/language combinations, or existing target directory.

Examples:

If you want to quickly scaffold a chat agent with explicit framework choice:

```bash
kinnoo init chatgpt my-agent
```

If you want a barebones template and control language explicitly:

```bash
kinnoo init no-framework --language python my-bare-agent
```

If you want only minimal files for a fast prototype:

```bash
kinnoo init chatgpt --minimal my-prototype
```

Follow-up command you usually run next:

```bash
kinnoo run ./my-agent --preflight
```

### run

- Usage: `kinnoo run [options] <agent_dir> [input]`
- Description: Execute an agent locally.
- Arguments:
  - `agent_dir`: path to agent directory.
  - `input` (optional): input string.
- Options:
  - `--entrypoint`: select a specific declared script when manifest uses `entrypoints`; for legacy `entrypoint` manifests, value must match declared script.
  - `--preflight`: validate readiness only; do not execute entrypoint.
  - `--no-guard`: disable input guard checks for CI/automation.
  - `--json-input`: provide inline JSON payload.
  - `--json-file`: provide JSON payload from file.
  - `--enforce-policy`: enforce manifest-declared runtime permission policy checks.
  - `--dry-run`: preview runtime behavior without full side effects.
  - `--json`: machine-readable output envelope (or passthrough for OpenClaw mode).
  - `--max-seconds`, `--max-cpu-seconds`, `--max-memory-mb`: runtime resource/time limits.
- Exit codes: non-zero on manifest/runtime validation failures or runtime process failures.

Examples:

If you want a normal local run with string input:

```bash
kinnoo run ./my-agent "hello"
```

If your manifest declares multiple scripts and you need a non-default script:

```bash
kinnoo run ./my-agent --entrypoint scripts/alt.py "hello"
```

Entrypoint selection contract:

- Legacy mode: `entrypoint: run.py`
- Multi-entrypoint mode: `entrypoints: [scripts/main.py, scripts/alt.py]`
- `entrypoint` and `entrypoints` are mutually exclusive.
- In `entrypoints` mode, default selection is the first list item when `--entrypoint` is omitted.

If you want to validate runtime readiness in CI without executing business logic:

```bash
kinnoo run ./my-agent --preflight
```

If you want structured input and structured output for automation pipelines:

```bash
kinnoo run ./my-agent --json-input '{"task":"ping"}' --json
```

If you want policy enforcement plus hard execution limits:

```bash
kinnoo run ./my-agent "summarize this" --enforce-policy --max-seconds 30 --max-memory-mb 512
```

### test

- Usage: `kinnoo test [--tests-file <path>] [--validate-only] [--json] [--verbose] [--create [file]] [--append] [agent_dir]`
- Description: Run declarative tests for an agent, or create/update a tests file interactively.
- Options:
  - `--tests-file`: path to `kinnoo.tests.yaml` (relative to agent dir or absolute).
  - `--validate-only`: parse and validate test declarations without execution.
  - `--json`: machine-readable results.
  - `--verbose`: include per-test diagnostics.
  - `--create [file]`: interactively create tests file (default `kinnoo.tests.yaml`).
  - `--append`: append new cases during interactive create flow.
- Exit codes: non-zero when declarations are invalid or tests fail.

Examples:

If you want to fail fast on schema/test file problems before runtime execution:

```bash
kinnoo test ./my-agent --validate-only
```

If you want rich diagnostics while iterating locally:

```bash
kinnoo test ./my-agent --verbose
```

If you want CI-friendly machine-readable results:

```bash
kinnoo test ./my-agent --json
```

If you want to bootstrap a new test suite interactively:

```bash
kinnoo test ./my-agent --create
```

### check

- Usage: `kinnoo check [target]`
- Description: Run import + inspect + preflight compatibility checks for a local path or GitHub URL.
- Exit codes: non-zero on compatibility or validation failures.

Examples:

If you want a single-command compatibility check before onboarding a project:

```bash
kinnoo check ./my-agent
```

If you want to evaluate a repository before importing or packaging:

```bash
kinnoo check https://github.com/org/repo
```

### import

- Usage: `kinnoo import [target] [import_path] [--force] [--from {langchain,langgraph,openai,openclaw}]`
- Description: Import an existing project in-place and prepare Kinnoo metadata.
- Options:
  - `--force`: overwrite existing `kinnoo.yaml`.
  - `--from`: apply framework-aware adapter hints.
- Exit codes: non-zero on import/validation failures.

Examples:

If you want to convert an existing local project to a Kinnoo-compatible structure:

```bash
kinnoo import ./existing-project --force
```

If you want to import a GitHub repo into a local folder:

```bash
kinnoo import https://github.com/org/repo ./imported-agent
```

If you want to import an OpenClaw workspace into a target directory:

```bash
kinnoo import --from openclaw ./my-openclaw-target ~/.openclaw/workspace-my-agent
```

### pack

- Usage: `kinnoo pack [options] <agent_dir>`
- Description: Package an agent directory into a `.kno` archive.
- Options:
  - `--public`: normalize to default-public semantics by removing `visibility: private` override when present.
  - `--private`: force `visibility: private` before packaging.
  - `--bump [patch|minor|major]`: bump version before packaging. `--bump` with no value defaults to `patch`.
  - `--sign SIGNING_KEY`: sign archive with Ed25519 private key PEM.
  - `--preflight`: show files/estimated size/destination without creating archive.
  - `--include`: include additional paths relative to agent root (repeatable).
  - `--exclude`: exclude paths relative to agent root (repeatable).
  - `--json`: machine-readable output and suppressed progress logs.
- Env vars: `KINNOO_ARCHIVE_ROOT`.
- Exit codes: non-zero on manifest/file validation or packaging failure.

Examples:

If you want the default public package artifact:

```bash
kinnoo pack ./my-agent
```

If you want to force private visibility for this packaged artifact:

```bash
kinnoo pack ./my-agent --private
```

If you want to bump patch version and sign before publishing:

```bash
kinnoo keygen
kinnoo pack ./my-agent --bump --sign ./kinnoo-ed25519-private.pem
```

If you want to validate what will be packaged before committing to archive output:

```bash
kinnoo pack ./my-agent --preflight --include data --exclude tests
```

Follow-up command commonly used for signed artifacts:

```bash
kinnoo publish ./my-agent --pack --strict --remote
```

### diff

- Usage: `kinnoo diff <archive_a> <archive_b> [--json]`
- Description: Compare two `.kno` archives and report manifest/file differences.
- Options:
  - `--json`: machine-readable diff payload.

Example:

If you want to review exactly what changed between two packaged versions:

```bash
kinnoo diff ./dist/agent-1.0.0.kno ./dist/agent-1.1.0.kno
```

### publish

- Usage: `kinnoo publish [--local | --remote] [--pack] [--private] [--bump {major,minor,patch}] [--strict] [--json] <target>`
- Description: Publish an archive, an archive source by agent name, or pack-then-publish from an agent directory.
- Target behavior:
  - Without `--pack`: target is agent name or `.kno` path.
  - With `--pack`: target must be an agent directory path.
- Options:
  - `--local` / `--remote`: choose registry backend (mutually exclusive).
  - `--pack`: package first, then publish.
  - `--private`: with `--pack`, enforce `visibility: private` before packaging.
  - `--bump`: with `--pack`, apply version bump before publish.
  - `--strict`: require strict trust/signature gates before upload.
  - `--json`: machine-readable publish result.
- Exit codes: non-zero for auth/config/publish/trust failures.

Examples:

If you already packaged and just want to publish by agent name:

```bash
kinnoo publish my-agent --remote
```

If you want a single command to package, bump, and publish remotely:

```bash
kinnoo publish ./my-agent --pack --bump patch --remote
```

If you want strict trust gating and machine-readable output in CI:

```bash
kinnoo publish ./my-agent --pack --strict --remote --json
```

### list

- Usage: `kinnoo list [--local | --remote] [--json]`
- Description: List local archive entries or remote registry summaries.
- Options:
  - `--local` / `--remote`: backend selection.
  - `--json`: machine-readable list payload.

Examples:

If you want to inspect what is available in your remote registry tenant:

```bash
kinnoo list --remote
```

If you want local archive inventory for cleanup/automation scripts:

```bash
kinnoo list --local --json
```

### search

- Usage: `kinnoo search [--local | --remote] [--json] <query>`
- Description: Search agent names/descriptions in local archive or remote registry.
- Options:
  - `--local` / `--remote`: backend selection.
  - `--json`: machine-readable search payload.

Examples:

If you want to discover candidate agents in remote registry by keyword:

```bash
kinnoo search mcp --remote
```

If you want automation-friendly local search results:

```bash
kinnoo search writer --local --json
```

### fetch

- Usage: `kinnoo fetch [--local | --remote] [--strict] [--json] <name|name==version>`
- Description: Download an agent archive from registry into local archive storage without unpacking.
- Options:
  - `--local` / `--remote`: backend selection.
  - `--strict`: require signature verification in addition to integrity checks.
  - `--json`: machine-readable fetch result.
- Exit codes: non-zero on selector, auth, download, or trust validation failures.

Examples:

If you want to mirror an archive locally for offline inspection:

```bash
kinnoo fetch my-agent --remote
```

If you want to enforce strict trust checks while fetching:

```bash
kinnoo fetch my-agent==1.2.3 --remote --strict
```

Follow-up command typically used after fetch:

```bash
kinnoo install my-agent==1.2.3 --local --strict
```

### install

- Usage: `kinnoo install [options] <agent[==version]|archive.kno> [target_dir]`
- Description: Install from archive path or registry selector.
- Options:
  - `-y`, `--yes`: skip confirmation prompt.
  - `--accept-permissions`: acknowledge manifest permissions in non-interactive mode.
  - `--allow-unverified-publisher`: allow non-interactive install when signature metadata is absent.
  - `--strict`: require strict signature + integrity verification.
  - `--skip-verify`: skip verification checks (development-only).
  - `--frozen`: require lockfile-only reproducible install.
  - `--local` / `--remote`: backend selection for registry selectors.
  - `--json`: machine-readable install result (requires `-y`).
- Exit codes: non-zero on trust, validation, or install failures.

Examples:

If you want to install from a local archive file into default location:

```bash
kinnoo install ./dist/my-agent-1.0.0.kno
```

If you want to install from remote registry with strict trust checks:

```bash
kinnoo install my-agent==1.2.0 --remote --strict
```

If you want non-interactive CI install output as JSON:

```bash
kinnoo install my-agent --remote -y --json
```

### inspect

- Usage: `kinnoo inspect [--full] [--raw] [--json] [--update KEY NEW_VALUE] [--skip-warnings] <target>`
- Description: Inspect or update manifest metadata in an agent directory or `.kno` archive.
- Options:
  - `--full`: include all known metadata fields, including N/A values.
  - `--raw`: print dotted-path key/value fields.
  - `--json`: machine-readable inspect output.
  - `--update KEY NEW_VALUE`: update a manifest field.
  - `--skip-warnings`: bypass interactive warnings for update operations.
- Exit codes: non-zero on invalid target or failed validation/update.

Examples:

If you want a fast human-readable metadata check before packaging:

```bash
kinnoo inspect ./my-agent
```

If you want automation-friendly metadata extraction:

```bash
kinnoo inspect ./my-agent --json
```

If you want to patch manifest metadata in place:

```bash
kinnoo inspect ./my-agent --update runtime.language javascript
```

### uninstall

- Usage: `kinnoo uninstall [-y|--yes] <name|name==version|archive.kno==version>`
- Description: Remove installed agent and/or archived versions.
- Options:
  - `-y`, `--yes`: skip confirmation prompt.
- Exit codes: non-zero on invalid target, not-found, or aborted operation.

Examples:

If you want to remove all versions for one installed/archive target:

```bash
kinnoo uninstall my-agent -y
```

If you want to remove only one version:

```bash
kinnoo uninstall my-agent==1.2.3 -y
```

If you want to remove the latest archived version selector:

```bash
kinnoo uninstall my-agent==latest -y
```

### keygen

- Usage: `kinnoo keygen [--private-key <path>] [--public-key <path>]`
- Description: Generate Ed25519 keypair for signing workflows.
- Options:
  - `--private-key`: private key output path (default `kinnoo-ed25519-private.pem`).
  - `--public-key`: public key output path (default `kinnoo-ed25519-public.pem`).
- Exit codes: non-zero when key generation/write fails.

Example:

If you want signing keys for strict package/publish workflows:

```bash
kinnoo keygen
```

### login

- Usage: `kinnoo login`
- Description: Authenticate to registry and persist auth state locally.
- Exit codes: non-zero on auth/network failures.

Examples:

If you want interactive login for local development:

```bash
kinnoo login
```

If you want non-interactive automation, preconfigure hosted auth env and run `kinnoo login` to complete browser-based auth.

### logout

- Usage: `kinnoo logout`
- Description: Clear persisted local registry auth state.
- Exit codes: zero even when no stored auth exists.

Example:

If you want to clear local auth state before switching accounts/tenants:

```bash
kinnoo logout
```

## Other Notes

- Use trust controls through current command flags (`install --strict`, `fetch --strict`, `pack --sign`, `publish --strict`).
