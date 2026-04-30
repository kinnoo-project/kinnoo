# Task 284 Notes - Route groups and placeholder pages (2026-03-24)

## Summary
- Created route-group structure under `web/app`:
  - `(public)/page.tsx`, `(public)/login/page.tsx`, `(public)/signup/page.tsx`
  - `(auth)/layout.tsx`, `(auth)/registry/page.tsx`
- Added required placeholder directories and `.gitkeep` markers:
  - `web/components/ui/`, `web/components/blocks/`, `web/lib/`, `web/__tests__/`
- Removed scaffold default `web/app/page.tsx` so `(public)/page.tsx` serves `/`.
- Added automated tests for `test424` and `test425`.

## Teaching Notes
- Next.js route groups (`(public)`, `(auth)`) shape layout composition without affecting URL path segments; this is useful for separating auth/public shell behavior early.
- Converting manual acceptance checks into automated route smoke tests (HTTP 200 + identifiable markers) gives high-signal regression protection with low maintenance.
- Keep placeholder pages intentionally minimal at foundation stage; this reduces merge conflicts when feature4 introduces shared layout/components.

## Test Runs
- Build: `cd /Users/jerry/gh/kinnoo/web && npm run build` -> success
- Targeted regression: `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest /Users/jerry/gh/kinnoo/tests/test_web_frontend_setup.py -k "task106" --testmon -q`
- Result: `2 passed, 3 deselected`
