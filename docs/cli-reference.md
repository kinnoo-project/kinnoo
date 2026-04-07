# CLI Reference

This reference documents the current Kinnoo command-line interfaces.

- Client CLI: `kinnoo`
- Server CLI: `kinnoo-server`

## Conventions

- Exit code `0`: command completed successfully.
- Exit code non-zero: command failed validation or runtime execution.
- Most command examples assume you run from repository root or a workspace where agent paths are valid.

## Common Environment Variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `KINNOO_REGISTRY_URL` | login/publish/install/list/search/sync | Remote registry base URL override |
| `KINNOO_REGISTRY_TOKEN` | publish/install/list/search | Remote auth token override |
| `KINNOO_TENANT_SLUG` | publish/install/list/search | Tenant context override |
| `KINNOO_ARCHIVE_ROOT` | pack/publish/install/list/search | Local archive root override |
| `KINNOO_REGISTRY_ROOT` | publish/list/search/sync | Local mock registry root override |
| `KINNOO_HTTP_USER_AGENT` | login/publish auth calls | HTTP User-Agent override |

## Client Commands (`kinnoo`)

### init

- Usage: `kinnoo init [--framework <framework>] [--language <language>] <agent_name>`
- Description: Scaffold a new agent directory.
- Arguments: `agent_name`.
- Options:
  - `--framework {gemini,chatgpt,claude-chat,pydantic-ai,langgraph,openai-agents,mcp-client,mcp-server,openclaw}`
  - `--language {python,js,javascript,ts,typescript}`
- Env vars: none required.
- Exit codes: non-zero on invalid name or existing target directory.
- Examples:
  - `kinnoo init my-agent`
  - `kinnoo init --framework chatgpt my-chat-agent`

### run

- Usage: `kinnoo run [options] <agent_dir> [input]`
- Description: Execute an agent locally.
- Arguments: `agent_dir`, optional `input`.
- Options: `--preflight`, `--no-guard`, `--json-input`, `--json-file`, `--sandbox`, `--dry-run`, `--thinking`, `--json`, `--max-seconds`, `--max-cpu-seconds`, `--max-memory-mb`.
- Env vars: command-specific runtime env vars declared in `kinnoo.yaml` may be required.
- Exit codes: propagates runtime or validation failures.
- Examples:
  - `kinnoo run ./my-agent "hello"`
  - `kinnoo run ./my-agent --preflight`

### test

- Usage: `kinnoo test [--tests-file <path>] [--validate-only] [--json] <agent_dir>`
- Description: Run declarative tests for an agent.
- Arguments: `agent_dir`.
- Options: `--tests-file`, `--validate-only`, `--json`.
- Env vars: none required.
- Exit codes: non-zero when declarations are invalid or tests fail.
- Examples:
  - `kinnoo test ./my-agent --validate-only`

### check

- Usage: `kinnoo check <target>`
- Description: Run import + inspect + preflight checks for a local target or GitHub URL.
- Arguments: `target` (path or URL).
- Options: none.
- Env vars: none required.
- Exit codes: non-zero when compatibility checks fail.
- Examples:
  - `kinnoo check ./my-agent`

### import

- Usage: `kinnoo import [options] [target] [import_path]`
- Description: Import an existing project and prepare Kinnoo metadata.
- Arguments: `target`, optional `import_path` for URL imports.
- Options: `--force`, `--source`, `--live-fallback`, `--from`.
- Env vars: depends on source workflow.
- Exit codes: non-zero on import/validation failure.
- Examples:
  - `kinnoo import ./existing-project --force`
  - `kinnoo import --source clawhub weather/weather-skill`

### pack

- Usage: `kinnoo pack [--bump {patch,minor,major}] [--sign] [--signing-key <path>] [--preflight] <agent_dir>`
- Description: Package an agent directory into a `.kno` archive.
- Arguments: `agent_dir`.
- Options: `--bump`, `--sign`, `--signing-key`, `--preflight`, `--public`.
- Env vars: `KINNOO_ARCHIVE_ROOT`.
- Exit codes: non-zero on manifest/file validation or packaging failure.
- Examples:
  - `kinnoo pack ./my-agent`
  - `kinnoo pack ./my-agent --sign --signing-key ./keys/private.pem`

### install

- Usage: `kinnoo install [options] <agent[==version]|archive.kno> [target_dir]`
- Description: Install from archive path or registry selector.
- Arguments: install target and optional output directory.
- Options: includes `--yes`, `--strict`, `--skip-verify`, `--frozen`, `--local`, `--remote`, and OpenClaw/Node-focused options.
- Env vars: `KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, `KINNOO_TENANT_SLUG`, `KINNOO_ARCHIVE_ROOT`, `KINNOO_REGISTRY_ROOT`.
- Exit codes: non-zero on trust/validation/install failure.
- Examples:
  - `kinnoo install ./dist/my-agent-1.0.0.kno`
  - `kinnoo install my-agent==1.2.0 --remote`

### publish

- Usage: `kinnoo publish [--local|--remote] [--pack] [--bump {major,minor,patch}] [--strict] [--public] <target>`
- Description: Publish an archive or latest local archive source to registry backend.
- Arguments: agent name, archive path, or with `--pack` an agent directory path.
- Options: `--local`, `--remote`, `--pack`, `--bump`, `--strict`, `--public`.
- Env vars: `KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, `KINNOO_TENANT_SLUG`, `KINNOO_REGISTRY_ROOT`.
- Exit codes: non-zero for config/auth/publish failures.
- Examples:
  - `kinnoo publish my-agent --remote`
  - `kinnoo publish ./my-agent --pack --bump patch --public --remote`

### list

- Usage: `kinnoo list [--local|--remote]`
- Description: List local archive entries or remote registry summaries.
- Arguments: none.
- Options: `--local`, `--remote`.
- Env vars: remote mode uses registry env vars.
- Exit codes: non-zero when remote configuration/auth is missing.
- Examples:
  - `kinnoo list --remote`

### search

- Usage: `kinnoo search [--local|--remote] [--openclaw-skill] [--json] <query>`
- Description: Search local archive, remote registry, or OpenClaw skills.
- Arguments: `query`.
- Options: `--local`, `--remote`, `--openclaw-skill`, `--json`.
- Env vars: remote mode uses registry env vars.
- Exit codes: non-zero on invalid query or remote config/auth errors.
- Examples:
  - `kinnoo search writer --remote`

### sync

- Usage: `kinnoo sync [--full] [--since <iso8601>] [--local|--remote] clawhub`
- Description: Sync source metadata into local mirror.
- Arguments: source (currently `clawhub`).
- Options: `--full`, `--since`, `--local`, `--remote`.
- Env vars: remote sync uses registry env vars.
- Exit codes: non-zero on sync failures.
- Examples:
  - `kinnoo sync clawhub --full`

### login

- Usage: `kinnoo login [--email <email>] [--password <password>]`
- Description: Authenticate to registry and persist auth state.
- Arguments: none.
- Options: `--email`, `--password`.
- Env vars: `KINNOO_REGISTRY_URL`, `KINNOO_HTTP_USER_AGENT`.
- Exit codes: non-zero on auth/network failures.
- Examples:
  - `kinnoo login`

### logout

- Usage: `kinnoo logout`
- Description: Clear persisted local registry auth state.
- Arguments: none.
- Options: none.
- Env vars: none required.
- Exit codes: zero even when no stored auth exists.
- Examples:
  - `kinnoo logout`

### keygen

- Usage: `kinnoo keygen [--private-key <path>] [--public-key <path>]`
- Description: Generate Ed25519 keypair for signing workflows.
- Arguments: none.
- Options: `--private-key`, `--public-key`.
- Env vars: none required.
- Exit codes: non-zero when key generation/write fails.
- Examples:
  - `kinnoo keygen`

### inspect

- Usage: `kinnoo inspect [--full] [--raw] [--update TARGET KEY VALUE] [--skip-warnings] <target>`
- Description: Inspect or update manifest metadata in an agent dir or `.kno` archive.
- Arguments: `target`.
- Options: `--full`, `--raw`, `--update`, `--skip-warnings`.
- Env vars: none required.
- Exit codes: non-zero on invalid targets or validation/update failures.
- Examples:
  - `kinnoo inspect ./my-agent`

### uninstall

- Usage: `kinnoo uninstall <agent_name>`
- Description: Remove installed agent with confirmation.
- Arguments: `agent_name`.
- Options: none.
- Env vars: install-root-related env vars may affect location resolution.
- Exit codes: non-zero on not-found or aborted confirmation.
- Examples:
  - `kinnoo uninstall my-agent`

### trust [planned]

- Status: Planned command surface in phase plans.
- Current state: not exposed as a top-level `kinnoo trust` subcommand in current CLI help.
- Use current trust controls via existing command flags (for example `install --strict`, `pack --sign`, `publish --strict`).

## Server CLI Reference

Server-side CLI documentation has been moved to `notes/server-cli-reference.md`.