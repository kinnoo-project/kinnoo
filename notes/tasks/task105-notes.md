# Task 283 Notes - Tailwind tokens and dark globals (2026-03-24)

## Summary
- Extended `web/tailwind.config.ts` with feature3 design tokens:
  - Colors: kinnoo.bg/text/accent/surface and `card-border`
  - Font family: `"Avenir Next", "Segoe UI", sans-serif`
  - Radius tokens: `card` and `button`
  - Spacing token scale aligned to project sizing units
- Updated `web/app/globals.css` to enforce dark base styles and added reusable utility classes:
  - `.glass-surface` for subtle glassmorphism backdrop blur
  - `.card-border-1` for 1px low-contrast border
- Added targeted automated test for `test423`.

## Teaching Notes
- Treat design tokens as source-of-truth primitives; pages/components should consume these tokens instead of hardcoded values. This prevents visual drift as the UI grows.
- For theme verification tests, a lightweight text-level assertion is sufficient early in scaffolding; richer snapshot/component tests are better once UI primitives exist.
- When running scoped tests in a shared terminal session, absolute paths reduce failures caused by cwd drift.

## Test Runs
- Build: `cd /Users/jerry/gh/kinnoo/web && npm run build` -> success
- Targeted regression: `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest /Users/jerry/gh/kinnoo/tests/test_web_frontend_setup.py -k "task105" --testmon -q`
- Result: `1 passed, 2 deselected`
