# Task295 Notes - Client Validation and Loading State

## What I changed
- Added shared login validation helper in `web/lib/auth-validation.ts`.
- Updated `web/app/(public)/login/page.tsx` to use client state and submit handling.
- Implemented pre-submit checks for required email/password and valid email format.
- Added inline field-level errors (`role="alert"`) and submit-level safe error messaging.
- Added pending request behavior: submit button disables and label changes to `Logging in...`.
- Expanded `web/__tests__/login-page.test.tsx` to cover validation blocking and loading-state transitions.

## Why this approach
- Validation helper keeps UI component simpler and makes validation logic reusable.
- Field errors are rendered near controls for better UX and easier automated assertions.
- Loading disable guard prevents duplicate submit attempts while request is in flight.
- Generic submit errors avoid leaking sensitive backend/auth details.

## Tests run
Command:
```bash
cd web && npm run test -- --environment jsdom login-page.test.tsx
```

Result:
```text
3 passed
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
- For interview framing: client-side validation improves responsiveness and UX, but should always be paired with server-side validation because client validation is bypassable.
