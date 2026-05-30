# Task 176 SWE Handoff - Go Binary Run and Compatibility Preflight

## Task Linkage
- Task: task176
- Feature: feature19 (AC10, AC11)
- Primary test: test82

## What To Implement
- Support kinnoo run execution of precompiled Go binaries when manifest entrypoint points to executable artifact.
- Add robust preflight checks for binary mode:
  - executable format sanity (Mach-O/ELF/PE as feasible)
  - host OS/architecture compatibility
  - executable permissions and missing-file handling
- Fail fast on hard incompatibilities with clear diagnostics.

## Files Expected
- src/kinnoo/run_command.py
- src/kinnoo/preflight.py
- src/kinnoo/binary_inspection.py
- tests/client_cli_run/
- tests/security_checks/

## Acceptance Mapping
- AC10: kinnoo run executes compatible precompiled Go binaries.
- AC11: preflight detects incompatible binaries and reports actionable errors.

## Design Notes
- Prefer parsing binary headers over filename heuristics.
- Keep source-mode and binary-mode checks clearly separated.
- Report host and target platform values in diagnostics.

## Done Definition
- test82 implemented/updated and passing.
- task176 status moved to needs-review.
- Teaching notes added to notes/tasks/task176-notes.md.
