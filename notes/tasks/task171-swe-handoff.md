# Task498 SWE Handoff - Web Auth Migration to Kinde Redirects

## Objective
Migrate web auth UX and API routes from local credential forms to provider-hosted redirect/callback/logout flow.

## Contract
- Login starts with redirect CTA, not local password POST.
- Callback and logout paths are deterministic and user-safe.
- Protected layout redirects unauthenticated users to `/login`.

## Primary Files
- `web/app/(public)/login/`
- `web/app/(public)/signup/`
- `web/app/api/login/route.ts`
- `web/app/api/logout/route.ts`
- `web/lib/auth-client.ts`

## Required Tests
- `test709`

## Execution Guidance
1. Centralize web auth interaction in existing auth service/hook boundaries.
2. Ensure signup/reset routes are either provider-routed or intentionally hidden.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `cd web && npm test`
