# Task 285 Notes - Install core UI dependencies (2026-03-24)

## Summary
- Installed core frontend dependencies in `web/package.json`:
  - `@radix-ui/react-dialog`
  - `@radix-ui/react-navigation-menu`
  - `@radix-ui/react-slot`
  - `lucide-react`
  - `framer-motion`
- Verified build remains green after dependency additions.
- Added targeted automated test for `test426`.

## Teaching Notes
- Installing UI primitives early (before component implementation) de-risks later UI tasks by surfacing version conflicts in isolation.
- Keep dependency-verification tests simple and explicit (key presence in `package.json`) so breakage is obvious when package names drift.
- Sequence matters for interview-style delivery: foundation setup -> token system -> route skeleton -> UI dependencies gives clean, reviewable increments.

## Test Runs
- Build: `cd /Users/jerry/gh/kinnoo/web && npm run build` -> success
- Targeted regression: `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest /Users/jerry/gh/kinnoo/tests/test_web_frontend_setup.py -k "task107" --testmon -q`
- Result: `1 passed, 5 deselected`
