# Task93 — Implement runtime version preflight check

## Summary
- Added runtime-version constraint evaluation to preflight in `src/kinnoo/run_command.py`.
- Preflight now parses `runtime.version` from `kinnoo.yaml`, compares it against the active interpreter version, and emits deterministic pass/fail checklist output.
- On runtime mismatch, preflight returns non-zero and prints actionable guidance to use a compatible Python interpreter.

## Test121 implementation
- Added `tests/test_run_preflight.py::test_preflight_runtime_version_check`.
- Test covers:
	- preflight pass case when `runtime.version` is satisfied (`>=3.0`),
	- preflight fail case when `runtime.version` is not satisfied (`>=99.0`),
	- mismatch guidance text for operator actionability.

## Commands and results
- `python3 -m pytest tests/test_run_preflight.py -q` -> `2 passed`
