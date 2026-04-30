# Task95 — Implement entrypoint and dependency checks

## Summary
- Added preflight entrypoint check in `src/kinnoo/run_command.py` to validate that manifest-declared entrypoint exists, is a file, and is readable.
- Added preflight dependency readiness check in `src/kinnoo/run_command.py` to evaluate installability readiness without running agent logic.
	- Parses installable dependency names from `requirements.txt`.
	- If dependencies exist, verifies `.venv` presence and `pip` availability.
	- Uses `pip show <package>` for each dependency to detect missing installs.
- Added deterministic actionable guidance for both failure types while keeping behavior isolated to preflight mode.

## Test123 implementation
- Added `tests/test_run_preflight.py::test_preflight_entrypoint_and_dependency_checks`.
- Test covers:
	- missing entrypoint fixture -> preflight fails with entrypoint-specific guidance,
	- dependency readiness failure fixture (requirements present, no `.venv`) -> preflight fails with dependency-specific guidance.

## Commands and results
- `python3 -m pytest tests/test_run_preflight.py -q` -> `4 passed`
