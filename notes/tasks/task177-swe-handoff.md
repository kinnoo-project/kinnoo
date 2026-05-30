# Task 177 SWE Handoff - Go UX, Help, and Docs Finalization

## Task Linkage
- Task: task177
- Feature: feature19 (AC12)
- Primary test: test83

## What To Implement
- Update CLI help text to clearly expose --language go and supported Go framework combos.
- Document Go source vs compiled-binary run behavior.
- Document preflight pass/warn/fail expectations and remediation guidance for:
  - missing Go toolchain
  - wrong architecture/OS
  - unsupported format
  - non-executable binary
- Add docs contract tests ensuring these docs/help references remain accurate.

## Files Expected
- docs/cli-reference.md
- docs/getting-started.md
- docs/kinnoo-yaml-spec.md
- README.md
- src/kinnoo/cli.py
- tests/docs_contract/

## Acceptance Mapping
- AC12: preflight output and docs/help provide clear pass/warn/fail semantics with remediation hints.

## Design Notes
- Keep docs concise and consistent with actual implemented flags/behavior.
- Prefer contract assertions for durable docs tests (stable headings/examples/keywords).
- Avoid overpromising unsupported behaviors.

## Done Definition
- test83 implemented/updated and passing.
- task177 status moved to needs-review.
- Teaching notes added to notes/tasks/task177-notes.md.
