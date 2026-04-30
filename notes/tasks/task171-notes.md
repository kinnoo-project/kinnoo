# Task498 Notes

## Summary
- Migrated login UX in `web/app/(public)/login/page.tsx` from password form to hosted redirect CTA.
- Updated auth client behavior in `web/lib/auth-client.ts` to use redirect-style login and logout-compatible behavior.
- Updated signup/verify public pages to provider-hosted guidance instead of local password confirmation flow.
- Added/updated web tests for redirect auth flow and protected layout behavior (`web/__tests__/login-page.test.tsx`, `web/__tests__/other feature (unreferenced)-auth-flow.test.tsx`).

## Teaching Notes
- In redirect-based auth, frontend should initiate auth but avoid storing bearer tokens in browser storage; session continuity is best done with secure cookies.
- Keep API proxy boundaries stable (`/api/login`, `/api/logout`) so frontend route changes don’t require broad backend URL rewrites.
- UI migration should explicitly remove obsolete inputs (password fields) and test for their absence.
