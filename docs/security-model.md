# Security Model

Kinnoo’s security model is built around the developer workflow you already use: package, publish, fetch/install, and run.

The goal is straightforward: make it hard for tampered or untrusted artifacts to slip through your pipeline while keeping normal developer workflows practical.

## What Kinnoo Protects Against

Kinnoo is designed to reduce risk from:

- Archive tampering between publish and install
- Accidental or malicious publication of invalid artifacts
- Unauthorized registry access
- Cross-tenant access to private artifacts
- Abuse patterns (for example brute-force auth and high-rate API traffic)

## Security Across the Normal Lifecycle

### 1) During `kinnoo pack`

When you package an agent, Kinnoo produces integrity metadata inside the archive so files can be checked later.

If you also sign during pack:

```bash
kinnoo keygen
kinnoo pack ./my-agent --sign ./kinnoo-ed25519-private.pem
```

Kinnoo creates signature artifacts that can be used for publisher verification:

- Embedded signature metadata inside the `.kno` archive (`META-INF/signature.json`)
- Detached sidecars next to the archive (`.sig` and `.sig.json`)

The detached metadata includes algorithm, archive checksum, and publisher key/fingerprint data needed for trust decisions.

### 2) During `kinnoo publish`

Before accepting uploads, registry-side checks validate archive shape and metadata (including manifest and integrity-related checks).

For stronger guarantees, publish with strict trust gating:

```bash
kinnoo publish ./my-agent --pack --strict --remote
```

### 3) During `kinnoo fetch` and `kinnoo install`

Kinnoo verifies integrity before trusting downloaded artifacts.

With strict mode:

```bash
kinnoo fetch my-agent==1.2.3 --remote --strict
kinnoo install my-agent==1.2.3 --remote --strict
```

Strict verification behavior:

- Detached signatures are verified when present.
- If detached artifacts are missing, install can fall back to embedded signature verification.
- If required signature/integrity checks cannot be satisfied, strict mode fails closed.

## Signing and Verification Model

- Signature algorithm: **Ed25519**
- Recommended workflow: sign at pack time, then publish/install with `--strict`
- Trust context: signature metadata carries publisher key identity material (for example public key and fingerprint)

This gives teams a practical way to enforce “known publisher” and “artifact unchanged” checks in CI/CD and local installs.

## Auth, Authorization, and Session Protections

Registry access is protected through authenticated sessions/tokens and scoped authorization checks.

At a high level:

- Login issues authenticated state used by CLI registry operations.
- Authorization scopes gate sensitive actions (for example publish/admin operations).
- Tenant context is part of access decisions for private artifacts.
- Session/token invalidation paths are supported for logout/revocation scenarios.

## Abuse Resistance and Operational Safety

The hosted service applies request-throttling controls and returns standard rate-limit headers so clients can back off safely.

Typical protections include:

- Auth endpoint throttling
- Publish endpoint throttling
- Search/list endpoint throttling

## Privacy and Secrets Baseline

- Secrets are not expected in `kinnoo.yaml`; manifests should list variable names only.
- Credentials should be provided via environment variables or secret management systems.
- Use strict verification for production installs and shared registries.

## Recommended Secure Defaults

For most teams, this is a strong baseline:

1. `kinnoo keygen`
2. `kinnoo pack --sign ...`
3. `kinnoo publish --pack --strict --remote`
4. `kinnoo install --remote --strict`

## Responsible Disclosure

If you suspect a security vulnerability, report it privately to project maintainers instead of opening a public issue with exploit details.
