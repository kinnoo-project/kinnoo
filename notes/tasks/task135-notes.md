# Task332 Notes

## Summary
Implemented `kinnoo login` and `kinnoo logout` command surfaces with local auth-state persistence and CLI wiring.

## What Changed
- Added `login`/`logout` command parsing and dispatch in `<redacted-path>`.
- Added `<redacted-path>` for:
  - token exchange via `POST /api/auth/token`
  - interactive and flag-driven non-interactive login
  - logout state clearing
- Extended `<redacted-path>` with:
  - `save_registry_auth_state(...)`
  - `clear_registry_auth_state(...)`
  - deterministic YAML writer for persisted config values
- Added task regression test:
  - `tests/test_cli_registry.py::test_feature61_login_interactive_and_noninteractive`

## Bug Encountered and Fix
- Bug: interactive test execution hung at password prompt because `getpass` attempted TTY input, which blocks subprocess-driven test automation.
- Fix: in non-TTY contexts, fallback to `input("Password: ")`; keep `getpass.getpass(...)` for true interactive terminals.

## Teaching Notes
- CLI auth should separate concerns cleanly:
  - command parsing (`cli.py`)
  - auth flow logic (`auth_command.py`)
  - persistence (`config.py`)
- For automation-safe CLIs, avoid hard dependency on TTY-only input. A robust pattern is:
  - use secure prompt (`getpass`) when `stdin` is a TTY
  - fallback to stdin when running in pipelines/tests
- Config persistence should be deterministic so tests can assert exact behavior and diffs remain readable.
- Keep auth outputs secret-safe: print registry/tenant context, never print tokens/passwords.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k test_feature61_login_interactive_and_noninteractive`
- Result:
  - `1 passed, 451 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task135-smoke-tests.md`.
