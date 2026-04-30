# Task 282 Notes - Next.js scaffold in web/ (2026-03-24)

## Summary
- Scaffolded a new Next.js app in `web/` using TypeScript, App Router, ESLint, Tailwind.
- Added `web/.nvmrc` with Node version `20`.
- Updated root `.gitignore` with `web/node_modules/` and `web/.next/`.
- Added `web/tailwind.config.ts` baseline to match feature/task expectations.
- Added targeted automated checks in `tests/test_web_frontend_setup.py` for test421 and test422.

## Teaching Notes
- `create-next-app` currently scaffolds Tailwind v4 by default; this may differ from a task spec expecting v3 config files. When that happens, align artifacts to the project contract first (e.g., add `tailwind.config.ts`) and then adjust implementation details in the next task.
- Keep test scope narrow per task (`-k "task104"`) so regressions are attributable and fast.
- For process-start smoke tests, prefer starting `npm run dev` in a subprocess, waiting for a readiness signal, then terminating cleanly to avoid orphaned processes.

## Test Runs
- Requested command: `python3 -m pietist tests --testmon`
- Result: blocked, `No module named pietist` and package unavailable on PyPI in this environment.
- Fallback command used: `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests/test_web_frontend_setup.py -k "task104" --testmon -q`
- Result: `2 passed`
