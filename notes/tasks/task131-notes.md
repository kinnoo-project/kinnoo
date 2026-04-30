# Task315 Notes - Next.js Security Headers Middleware

## Summary
- Added `<redacted-path>` to apply production-hardening response headers.
- Implemented required baseline headers:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'`
- Added production-gated HSTS header:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Added `buildSecurityHeaders()` helper for deterministic unit testing.
- Added `<redacted-path>` covering baseline headers and HSTS gating.

## Why this implementation
- Central middleware keeps security policy consistent across app routes.
- Small pure helper function avoids brittle request mocking and makes header policy tests stable.

## Teaching Notes
- Security middleware should encode policy once and apply globally to reduce drift.
- Keep CSP restrictive by default, then relax intentionally only when specific assets require it.
- Production-only HSTS is important for avoiding local-development HTTPS friction while enforcing strict transport in production.

## Task-scoped regression
- Command: `cd web && npm run test -- __tests__/security-headers.test.ts`
- Result: pass (`2 passed`)
