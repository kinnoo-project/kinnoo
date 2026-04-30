# Task 434 Notes

## Summary
Completed feature17 AC4-AC7 verification and compatibility updates.

## What changed
- Kept login redirect behavior (`/registry`) and registry dashboard rendering flow unchanged.
- Added/updated regression checks to confirm no `Email us` or `mailto:` contact path appears in first-party web source.
- Updated static export acceptance wording in manifests to match Next.js 16 behavior (where `next export` was removed).
- Extended `tests/test_feature_110.py::test_feature110_group2` to verify:
  - login redirect marker
  - registry view markers
  - no mailto/email-us flow in app/components/lib source
  - `npm run build` success in `web/`

## Targeted test runs
- `cd web && npm run test -- __tests__/signup-page.test.tsx __tests__/login-page.test.tsx __tests__/registry-dashboard.test.tsx` -> passed (14 tests)
- `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests --testmon -k test_feature110_group2` -> passed (1 selected)

## Bug encountered and resolution
- Attempt 1 failure: `test_feature110_group2` scanned all files under `web/` and matched `mailto:` in dependency code.
- Fix: restricted scan scope to first-party sources (`web/app`, `web/components`, `web/lib`).
- Re-run passed.

## Teaching notes
- For UI policy checks (like banning `mailto` flows), scope source scans to owned code roots to avoid third-party false positives.
- Keep acceptance criteria synced with framework version changes. In Next.js 16, static export is configured at build time; `next export` is no longer the command path.
- Preserve behavior by default when a task is verification-heavy; add focused tests first, then only change code if behavior is actually missing.
