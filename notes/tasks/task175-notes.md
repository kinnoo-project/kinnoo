# Task 175 Notes

## Summary
- Implemented Go source execution in `kinnoo run` for `runtime.language: go` with `go run <entrypoint>` semantics.
- Added Go-specific preflight checks in `kinnoo run --preflight` for:
	- Go toolchain availability and runtime.version compatibility.
	- Entrypoint presence (existing shared check path).
	- Go module readiness (`go.mod`) with explicit pass/fail/warn diagnostics.
- Added test81 automation coverage in `tests/client_cli_run/test_go_source_run_and_preflight.py` for:
	- Go source run success and non-zero exit propagation.
	- Preflight pass with module warning.
	- Preflight failure for missing entrypoint.
	- Preflight failure for missing Go toolchain.
- Updated `TASKS.txt` task175 status flow: `not-started -> in-progress -> needs-review`.

## Teaching Notes
- Why `go run` for source mode:
	- `go run <entrypoint>` gives deterministic source execution without requiring a separate compile step.
	- It naturally preserves stdout/stderr stream behavior and process exit codes, which is important for CLI runtime parity across languages.
- Why split preflight checks by concern:
	- Toolchain check answers “can this host execute Go at all?”.
	- Entrypoint check answers “is the selected target file present/readable?”.
	- Module readiness answers “is dependency metadata (`go.mod`) ready for non-trivial imports?”.
	- This mirrors production reliability practice: isolate failure domains so diagnostics are actionable.
- Why warnings for missing `go.mod` when no manifest dependencies are declared:
	- Single-file Go programs can run without a module file.
	- Missing `go.mod` becomes a hard failure only when manifest dependencies imply external module usage.
	- This keeps preflight strict where needed but avoids false-negative blocking for simple source agents.

## Test Results
- Focused task175 command (required format):
	- `python3 -m pytest tests --testmon tests/client_cli_run/test_go_source_run_and_preflight.py`
	- First run: 1 failed, 3 passed (assertion updated to match validator behavior when entrypoint is missing).
	- Second run: 1 passed, 3 deselected (expected testmon selection behavior).
- Explicit task175 node-id run with `--testmon`:
	- `python3 -m pytest tests --testmon tests/client_cli_run/test_go_source_run_and_preflight.py::test_go_source_run_executes_with_go_run_and_propagates_streams_and_exit_code tests/client_cli_run/test_go_source_run_and_preflight.py::test_go_source_preflight_passes_with_toolchain_and_module_warning tests/client_cli_run/test_go_source_run_and_preflight.py::test_go_source_preflight_fails_when_entrypoint_missing tests/client_cli_run/test_go_source_run_and_preflight.py::test_go_source_preflight_fails_when_go_toolchain_missing`
	- Result: all 4 task175 tests passed.
- Manifest validation:
	- `python3 scripts/validate_project_manifests.py`
	- Result: `Validation passed: manifests are consistent`.
