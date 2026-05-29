# Test 81 Test-Agent Handoff - Go Source Run and Preflight

## Covers
- feature19 AC8, AC9

## Contract To Validate
- kinnoo run executes Go source agents via go run entrypoint semantics.
- stdout/stderr and exit code behavior matches established runtime contract.
- preflight validates go toolchain availability, entrypoint presence, and module readiness.
- failure diagnostics are actionable and deterministic.

## Test Design Guidance
- Use integration fixtures under tests/client_cli_run and/or tests/client_cli_check.
- Include positive path and at least two failure paths (missing entrypoint, missing toolchain simulation).
- Prefer monkeypatching PATH/tool resolution for deterministic missing-toolchain tests.

## Execution Guidance
- Run only task175-related regression tests using python3 -m pytest tests --testmon with targeted selectors.
