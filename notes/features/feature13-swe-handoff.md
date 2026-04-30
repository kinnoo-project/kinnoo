# Feature 94 — SWE Handoff: Security Model Document

## Context
Document kinnoo's security architecture for transparency and trust.

## Files to Create
- `<redacted-path>`

## Content Structure
1. **Threat Model** — Key threats: supply-chain attacks, tampered archives, credential theft, abuse
2. **Signing Model** — Ed25519 key generation, signing workflow, verification, trust store
3. **Integrity Verification** — META-INF/integrity.json, file hashing, install-time checks
4. **Authentication** — JWT flow, Argon2id hashing, token lifecycle, session management
5. **Authorization** — Tenant isolation, resource ownership
6. **Transport Security** — HTTPS, CORS, Cloudflare proxy
7. **Rate Limiting** — Per-IP, per-tenant, endpoint groups
8. **Upload Validation** — Size, format, manifest, integrity checks
9. **Password Policy** — Minimum length, complexity, lockout
10. **Responsible Disclosure** — How to report vulnerabilities

## Implementation Notes
- Reference: `<redacted-path>`, `<redacted-path>`, `<redacted-path>`
- Should be accurate to the implemented state (after Phase 8 and 9)
- Include diagrams where helpful (Mermaid or ASCII art)

## Dependencies
- feature9, feature10, feature11 (integrity/signing — should be implemented for accuracy)

## Acceptance Criteria Summary
1. <redacted-path> with complete security architecture
2. Threat model with mitigations
3. Cross-referenced from README.md
