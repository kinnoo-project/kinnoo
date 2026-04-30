# Task96 — Add checklist output and ready summary

## Summary
- Updated preflight output contract in `src/kinnoo/run_command.py` to always emit stable checklist sections for:
	- runtime version,
	- env vars,
	- entrypoint,
	- dependencies.
- Added final readiness summary semantics:
	- pass path prints `Ready to run` and `Preflight result: PASS`,
	- fail path prints `Not ready to run`, `Remediation summary:`, targeted remediation bullets, and `Preflight result: FAIL`.
- Preserved deterministic pass/fail indicators and per-check actionable guidance.

## Test124 implementation
- Added `tests/test_run_preflight.py::test_preflight_checklist_and_ready_summary`.
- Test covers:
	- all-checks-pass scenario includes all four `[PASS]` sections and `Ready to run`,
	- failing scenario includes `[FAIL] dependency readiness check`, `Not ready to run`, and remediation summary guidance,
	- `Ready to run` does not appear in failing output.

## Commands and results
- `python3 -m pytest tests/test_run_preflight.py -q` -> `5 passed`
