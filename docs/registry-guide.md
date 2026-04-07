# Registry Guide

This guide covers invite-only registry usage for publishing and consuming agents.

## 1) Invite-Only Account Setup

The registry is invite-only. An operator must create your account/invite before you can log in.

## 2) Configure Registry Endpoint

```bash
export KINNOO_REGISTRY_URL=https://dev-api.kinnoo.ai
```

## 3) Log In

Interactive login:

```bash
kinnoo login
```

Expected output (example):

```text
Login successful.
Registry: https://dev-api.kinnoo.ai
Tenant: <your-tenant>
```

Non-interactive login:

```bash
kinnoo login --email user@example.com --password 'your-password'
```

## 4) Publish an Agent

Publish latest archive source by name:

```bash
kinnoo publish my-agent --remote
```

Expected output (example):

```text
Published my-agent==<version> (remote)
Remote publish result: ...
```

Pack and publish from directory:

```bash
kinnoo publish ./my-agent --pack --bump patch --remote
```

Make visibility public during pack/publish:

```bash
kinnoo publish ./my-agent --pack --public --remote
```

## 5) Search and List

```bash
kinnoo list --remote
kinnoo search my-agent --remote
```

Expected output (example):

```text
Remote registry agents:
- my-agent  <latest-version>
```

## 6) Install from Registry

Latest version:

```bash
kinnoo install my-agent --remote
```

Expected output (example):

```text
[kinnoo install] Installing my-agent...
[kinnoo install] Completed.
```

Exact version:

```bash
kinnoo install my-agent==1.2.3 --remote
```

Strict trust install:

```bash
kinnoo install my-agent --remote --strict
```

## 7) Sign and Verify (Recommended)

```bash
kinnoo keygen
kinnoo pack ./my-agent --sign --signing-key ./kinnoo-ed25519-private.pem
kinnoo publish ./my-agent --pack --strict --remote
```

## 8) Log Out

```bash
kinnoo logout
```