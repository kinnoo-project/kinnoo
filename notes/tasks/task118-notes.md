# Task296 Notes - Secure Login Submission and Redirect

## What I changed
- Added `web/lib/auth-client.ts` with `loginWithPassword()` to centralize login requests.
- Updated login submit flow in `web/app/(public)/login/page.tsx` to use the auth client.
- Configured request with `credentials: "include"` and `cache: "no-store"` to align with cookie-session auth flow.
- Added success-path navigation to `/registry` via Next router push.
- Added proxy rewrite in `web/next.config.ts` from `/api/bff/login` to backend `/login`.
- Extended `web/__tests__/login-page.test.tsx` with task118 checks for fetch options and redirect behavior.

## Why this approach
- Auth request details in one helper reduces accidental drift across components.
- Browser-managed session cookies are safer than manually storing tokens in web storage for this project pattern.
- A dedicated frontend proxy path keeps backend base URL concerns in app config, not component code.

## Tests run
Command:
```bash
cd web && npm run test -- --environment jsdom login-page.test.tsx -t "credentials include|redirects to /registry"
```

Result:
```text
2 passed, 3 skipped
```

Command:
```bash
cd web && npm run build
```

Result:
```text
build passed
```

Command:
```bash
python3 scripts/validate_project_manifests.py
```

Result:
```text
Validation passed: manifests are consistent
```

## Learning note
- For interviews: BFF + cookie session design helps reduce token exfiltration surface in browsers and simplifies revocation/session lifecycle controls at the server boundary.
