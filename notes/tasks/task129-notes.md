# Task308 Notes - CSRF Pass-through for Login and Authenticated POST

## Summary
- Reworked web auth client flow in `<redacted-path>`:
  - fetches login CSRF nonce via `GET /api/login`
  - submits login as form-encoded `POST /api/login` including `csrf_token`
  - adds session-CSRF helper that reads `kinnoo_csrf` and forwards it as both form field and `X-CSRF-Token` header
  - adds `logoutWithSessionCsrf()` using `POST /api/logout`
- Updated `<redacted-path>` to invoke CSRF-protected logout helper.
- Updated `<redacted-path>` to support callback-based logout action.
- Added task-scoped tests in `tests/test_registry.py`:
  - `test_feature55_login_csrf_passthrough`
  - `test_feature55_session_csrf_forwarding`

## Why this implementation
- Aligns web login/logout behavior with FastAPI's existing form+CSRF requirements instead of introducing browser token storage.
- Keeps session cookie flow intact and explicit for authenticated POSTs.

## Teaching Notes
- For cookie-based auth systems, CSRF defense should be explicit for every authenticated POST.
- Sending CSRF in both a header and a form field improves compatibility with backend validators and progressive form flows.
- Parsing a server-rendered hidden CSRF field can bridge modern frontend pages with legacy form-based auth backends.

## Task-scoped regression
- Command: `python3 -m pytest tests --testmon -k "test_feature55_login_csrf_passthrough or test_feature55_session_csrf_forwarding"`
- Result: pass (`2 passed`)
