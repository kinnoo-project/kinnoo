# Task316 Notes - Auth Route Loading and Error UX

## Summary
- Added protected-route loading UI in `web/app/(auth)/loading.tsx`.
- Added protected-route error boundary UI in `web/app/(auth)/error.tsx` with actionable guidance and retry/login actions.
- Updated `web/app/(auth)/layout.tsx` to:
  - redirect on 401
  - throw explicit 429 and generic unavailability errors for error-boundary handling
- Extended `web/__tests__/auth-layout.test.tsx` to cover:
  - 401 redirect semantics
  - 429 error path
  - loading UX
  - 429 and generic error UI guidance

## Why this implementation
- Keeps auth failure UX centralized in route-group boundaries while preserving existing redirect behavior for unauthenticated sessions.
- Makes 429/downtime states user-visible and recoverable instead of silently failing.

## Teaching Notes
- In App Router, route-group `loading.tsx` and `error.tsx` provide resilient UX boundaries around async auth checks.
- Use explicit error codes/messages from layout/auth checks to map failures into user-friendly guidance.
- Testing redirect behavior in Next layouts often requires modeling redirect-as-throw semantics.

## Task-scoped regression
- Command: `cd web && npm run test -- __tests__/auth-layout.test.tsx`
- Result: pass (`6 passed`)
