# Security Model

This document describes the current security architecture implemented in Kinnoo.

## Scope

- Client-side security features in `src/kinnoo/*`.
- Server-side auth, upload, and rate-limit controls in `server/*`.

## Threat Model

### Main threats

- Archive tampering between publish and install.
- Malicious or accidental publish of invalid archives.
- Credential theft or replay of stolen tokens/cookies.
- Cross-tenant data exposure.
- Brute-force login attempts.
- API abuse through high request rates.

### Current mitigations

- Integrity manifest verification and optional signature verification.
- Server-side upload validation (type/size/manifest/integrity checks).
- Password hashing with Argon2 when available (scrypt fallback).
- HMAC-signed JWT-compatible tokens with expiration and denylist revocation support.
- Signed session cookies plus CSRF token enforcement for web session flows.
- Tenant-scoped authorization checks.
- Endpoint-group rate limiting with response headers and retry guidance.

## Signing Model (Ed25519)

Signing helpers live in `src/kinnoo/signing.py`.

- Key generation: `kinnoo keygen` writes Ed25519 private/public key files.
- Signing: `kinnoo pack --sign --signing-key <private.pem>` creates detached signature artifacts.
- Verification:
  - client-side strict workflows validate signature artifacts,
  - signature metadata includes public key and fingerprint for trust decisions.

Algorithm and metadata behavior:

- Detached signatures use Ed25519.
- Signature metadata includes:
  - `algorithm: ed25519`
  - archive checksum
  - public key PEM
  - public-key fingerprint

## Integrity Verification

Integrity helpers live in `src/kinnoo/integrity.py`.

- `kinnoo pack` writes `META-INF/integrity.json`.
- Integrity manifest records per-file checksums.
- `kinnoo install` verifies integrity manifest content before trusting archive content.
- Strict mode (`install --strict`) and strict publish checks require stronger trust gates.

## Authentication and Session Security

### Passwords

- User password hashing uses `server/models/user.py`:
  - Preferred: Argon2 (`argon2-cffi` runtime availability).
  - Fallback: scrypt with per-password salt.

### Token-based API auth

- `server/auth/token.py` issues and validates HMAC-signed JWT-compatible bearer tokens.
- Token claims include issuer, subject, tenant slug, scopes, issue time, and expiry.
- Token revoke support exists via token-id denylist.
- Login lockout is enforced through failed-attempt tracking in user store.

### Web session auth

- `server/auth/session.py` provides signed cookie sessions.
- Session POST validation requires CSRF token match.
- Session invalidation supported on logout and user-session invalidation flows.

## Auth Flow Summary

Current flow components:

1. Registration: invite/registration token helpers exist in `server/auth/tokens.py` and related web routes.
2. Login: credential exchange at auth endpoints issues bearer token (API) and/or web session.
3. JWT issuance: access tokens include scope + tenant claims.
4. Token refresh: no dedicated JWT refresh endpoint is currently exposed; clients re-authenticate when needed.
5. Logout: persisted client auth state can be cleared (`kinnoo logout`), and server token/session invalidation paths are implemented.

## Authorization and Tenant Isolation

- Authorization is scope-based for API actions (`registry:read`, `registry:publish`, `registry:admin`).
- Tenant identity is part of token/session context.
- Private data access is checked against tenant ownership in list/search/download/agent detail paths.

## Upload Validation

Publish endpoints validate archives before accepting storage writes:

- file extension and zip format checks,
- max upload size checks,
- manifest presence/shape checks,
- manifest validation checks,
- integrity-manifest verification when provided.

## Rate Limiting and Abuse Protection

Rate-limiting middleware is in `server/middleware.py` with defaults from `server/config.py`.

Default policy:

- Auth endpoints: 5 requests per 60 seconds per IP.
- Publish endpoints: 10 requests per hour per tenant.
- Search endpoints: 60 requests per 60 seconds per IP.

Responses include:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `Retry-After` on `429` responses

## Transport and Deployment Notes

- Production-oriented CORS configuration exists in server config.
- Expected deployment posture uses HTTPS fronted by edge/network controls.
- Exact TLS/edge policy depends on deployment environment configuration.

## Responsible Disclosure

Until a dedicated security process file exists, report suspected vulnerabilities directly to project maintainers through private channels instead of public issues.