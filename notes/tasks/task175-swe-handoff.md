# Task 175 SWE Handoff - Go Source Run and Preflight

## Task Linkage
- Task: task175
- Feature: feature19 (AC8, AC9)
- Primary test: test81

## What To Implement
- Extend run execution for Go source agents using go run semantics with manifest entrypoint.
- Ensure stdout/stderr streaming and exit-code propagation parity with current runtimes.
- Add preflight checks for Go source agents:
  - Go toolchain availability
  - entrypoint existence
  - module readiness (e.g., go.mod expectations)
- Emit clear fail/warn diagnostics with remediation guidance.

## Files Expected
- src/kinnoo/run_command.py
- src/kinnoo/cli.py
- src/kinnoo/preflight.py
- tests/client_cli_run/
- tests/client_cli_check/

## Acceptance Mapping
- AC8: kinnoo run executes Go source and preserves process IO/exit semantics.
- AC9: kinnoo run --preflight validates Go source readiness before run.

## Design Notes
- Reuse existing run process abstraction where possible.
- Avoid introducing side effects in preflight mode.
- Keep diagnostics deterministic for tests.

## Done Definition
- test81 implemented/updated and passing.
- task175 status moved to needs-review.
- Teaching notes added to notes/tasks/task175-notes.md.
