# Registry Guide

The Kinnoo registry is where you share agents with others, and where end-user consumers discover/install versioned agent archives.

This guide covers the core workflows most developers need: authenticate, publish, search, install, and verify trust.

## 1) Account Access

You can create an account easily by signing up either via the web interface (https://kinnoo.ai) or by installing the Kinnoo CLI and typing `kinnoo login`.

## 2) Set Registry Endpoint

Point the CLI to the hosted Kinnoo API:

```bash
export KINNOO_REGISTRY_URL=https://api.kinnoo.ai
```

## 3) Authenticate

Login to the agent registry:

```bash
kinnoo login
```

## 4) Publish an Agent

If your agent is already packaged and indexed locally by name (--remote is default, but showing here explicitly for clarity):

```bash
kinnoo publish my-agent --remote
```

Pack and publish directly from an agent directory:

```bash
kinnoo publish my-agent --pack --bump patch --remote
```

Recommended for shared/team registries (enforces signature and integrity verification gates):

```bash
kinnoo publish my-agent --pack --strict --remote
```

If you need private visibility at publish time:

```bash
kinnoo publish my-agent --pack --private --remote
```

Note that CLI flags can be specified before or after the agent directory name.

## 5) Discover Agents

```bash
kinnoo list --remote
kinnoo search my-agent --remote
```

Use `list` for tenant inventory and `search` when you already know a keyword or agent name.

## 6) Install from Registry

Install latest:

```bash
kinnoo install my-agent --remote
```

Install an exact version:

```bash
kinnoo install my-agent==1.2.3 --remote
```

Install with strict verification:

```bash
kinnoo install my-agent --remote --strict
```

## 7) Fetch Without Installing (Optional)

If you want to mirror an artifact first and install later:

```bash
kinnoo fetch my-agent==1.2.3 --remote --strict
kinnoo install my-agent==1.2.3 --local --strict
```

## 8) Recommended Signing Flow

```bash
kinnoo keygen
kinnoo pack ./my-agent --sign ./kinnoo-ed25519-private.pem
kinnoo publish ./my-agent --pack --strict --remote
```

## 9) Logout

```bash
kinnoo logout
```

## Troubleshooting

- **Unauthorized / forbidden while publishing or installing**: rerun `kinnoo login`.
- **Wrong environment**: verify `KINNOO_REGISTRY_URL` is set to `https://api.kinnoo.ai`.
- **Version conflict on publish**: bump version (`--bump patch` or update `kinnoo.yaml`).
- **Strict install/publish failure**: check signing artifacts and rerun pack with `--sign`.
