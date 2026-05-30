# Task 174 SWE Handoff - Go Runtime Schema and Validator

## Task Linkage
- Task: task174
- Feature: feature19 (AC7)
- Primary test: test80

## What To Implement
- Extend schema/validator support for runtime.language: go.
- Enforce/confirm generated Go manifests default to entrypoint: main.go.
- Validate Go manifest permutations for source entrypoint and binary entrypoint modes.
- Update docs/kinnoo-yaml-spec.md with Go runtime examples and guidance.

## Files Expected
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- src/kinnoo/templates.py (only if generator defaults require adjustment)
- docs/kinnoo-yaml-spec.md
- tests/schema_unit/

## Acceptance Mapping
- AC7: kinnoo.yaml validation supports go and generator defaults to main.go.

## Design Notes
- Keep existing language validations backward compatible.
- Binary entrypoint for Go should be represented as executable path and validated with clear errors on malformed declarations.
- Keep validator error messages actionable and field-specific.

## Done Definition
- test80 implemented/updated and passing.
- task174 status moved to needs-review.
- Teaching notes added to notes/tasks/task174-notes.md.
