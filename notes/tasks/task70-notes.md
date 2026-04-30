# Task92 — Add --preflight CLI mode wiring

## Summary
- Added `--preflight` flag to `kinnoo run` argument parsing in `src/kinnoo/cli.py`.
- Added explicit run-mode branching so preflight requires only `<agent-dir>`, while normal run still requires `<agent-dir> '<input>'`.
- Implemented preflight-only execution path in `src/kinnoo/run_command.py` via `run_preflight(...)`.
- Preflight flow prints deterministic checklist lines, validates `kinnoo.yaml`, and exits without invoking the entrypoint subprocess.

## Test120 implementation
- Added `tests/test_run_preflight.py::test_preflight_runs_checks_without_entrypoint_execution`.
- Test covers:
	- passing preflight case with checklist output and zero exit,
	- failing preflight case (missing manifest) with non-zero exit,
	- explicit verification that entrypoint side effect file is never created in either preflight run.

## Commands and results
- `python3 -m pytest tests/test_run_preflight.py -q` -> `1 passed`
- `python3 -m pytest tests/test_cli.py::test_run_missing_args -q` -> `1 passed`
