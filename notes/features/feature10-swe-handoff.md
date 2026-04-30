# Feature 87 — SWE Handoff: Embedded Signature

## Context
When `kinnoo pack --sign` is used, sign the integrity manifest and embed the signature in `META-INF/signature.json`. This builds on the Ed25519 signing infrastructure already in `<redacted-path>` and the integrity manifest from feature9.

## Files to Modify
- `<redacted-path>` — After generating `META-INF/integrity.json` (feature9), if `--sign` flag is set:
  1. Read the raw bytes of `integrity.json`
  2. Sign using Ed25519 private key via `signing.py`
  3. Write `META-INF/signature.json` to the archive
- `<redacted-path>` (~350 lines) — Reuse existing `sign_data()` and `load_private_key()` functions. May need a convenience wrapper for signing file contents.

## Signature Format
```json
{
  "version": 1,
  "algorithm": "ed25519",
  "signature": "<base64-encoded-signature>",
  "public_key_fingerprint": "<hex-sha256-of-public-key>",
  "signed_at": "2026-04-04T12:00:00Z"
}
```

## Implementation Notes
- The signature covers the **exact bytes** of `META-INF/integrity.json` (no canonicalization needed — JSON is already deterministic from feature9)
- `--sign` requires a key pair to exist (generated via `kinnoo keygen`). Fail with a clear error if no key found.
- `kinnoo pack` without `--sign` must NOT produce `signature.json` (integrity.json is still always generated)
- Public key fingerprint = SHA-256 of the raw public key bytes, hex-encoded

## Testing
- Test that `kinnoo pack --sign` produces both `integrity.json` and `signature.json`
- Test that `kinnoo pack` (no --sign) produces only `integrity.json`
- Test that the signature validates against the integrity manifest bytes
- Test that signing fails gracefully when no key pair exists

## Dependencies
- feature9 (integrity manifest must exist to sign)
- `<redacted-path>` already has Ed25519 key generation and signing

## Acceptance Criteria Summary
1. `kinnoo pack --sign` produces `META-INF/signature.json`
2. Signature covers integrity.json bytes
3. signature.json has: signature, public_key_fingerprint, signed_at
4. Without `--sign`, no signature.json generated
5. No new crypto dependencies
