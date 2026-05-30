# Test 82 Test-Agent Handoff - Go Binary Run and Preflight

## Covers
- feature19 AC10, AC11

## Contract To Validate
- kinnoo run executes compatible compiled Go binaries from manifest entrypoint.
- preflight validates binary format, OS/arch compatibility, and executable readiness.
- incompatible binaries fail early with deterministic, actionable diagnostics.

## Test Design Guidance
- Use fixture binaries or mocked binary-inspection metadata for deterministic tests.
- Cover success path + mismatch failures (arch mismatch, unsupported format, non-executable).
- Keep tests platform-aware and avoid brittle assumptions on host type.

## Execution Guidance
- Run task176-focused regression tests only via python3 -m pytest tests --testmon targeted selectors.
