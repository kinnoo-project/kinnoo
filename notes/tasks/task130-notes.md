# Task310 Notes - Auth Guard in Protected Layout

## Summary
- Implemented protected-route auth guard in `<redacted-path>`:
  - calls `<redacted-endpoint>` on server render
  - forwards request cookies
  - redirects to `/login` on 401
- Added server-side auth helper `fetchAuthMeServer()` in `<redacted-path>`.
- Added auth layout tests in `<redacted-path>`:
  - redirect on 401 (`test457`)
  - render children on success
- Added integration contract test in `tests/test_registry.py`:
  - `test_feature55_auth_integration_suite` (`test458`)
  - validates auth-check 401 baseline, rewrite/auth-client contract markers, and no local/session storage token use.

## Why this implementation
- Keeps all protected-route gating centralized in the auth route-group layout.
- Preserves session-cookie architecture and avoids browser token persistence.

## Teaching Notes
- Route-group layouts are the best place for authorization checks in Next App Router because every protected page inherits the guard.
- Keep auth-check functions deterministic (`cache: \"no-store\"`) so stale auth results are never reused.
- Integration suite tests can combine runtime endpoint checks with static policy checks (e.g., no localStorage/sessionStorage for auth tokens).

## Task-scoped regressions
- JS test (test457): `cd web && npm run test -- __tests__/auth-layout.test.tsx` -> pass (`2 passed`)
- Python test (test458): `python3 -m pytest tests/test_registry.py --testmon -k test_feature55_auth_integration_suite` -> pass (`1 passed`)
