# Test 80 Test-Agent Handoff - Go Manifest Schema and Defaults

## Covers
- feature19 AC7

## Contract To Validate
- Validator accepts runtime.language: go in valid manifests.
- Generated Go manifests default to entrypoint main.go.
- Source and binary Go entrypoint variants are validated correctly.
- Invalid variants fail with actionable messages.

## Test Design Guidance
- Use focused unit tests in tests/schema_unit.
- Prefer explicit positive/negative fixtures over broad snapshots.
- Assertions should inspect specific error substrings for deterministic diagnostics.

## Execution Guidance
- Run only task174-related regression tests with python3 -m pytest tests --testmon targeted selectors.
