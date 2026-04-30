# Task88 — Preserve file-path install compatibility

## What was implemented
- Added task68 compatibility coverage in `tests/test_install_refactor.py`:
	- Implemented `test_install_file_path_mode_preserved` (test116) to verify `kinnoo install <file-path/file.kno>` remains on direct archive-path flow.
	- Test creates a conflicting mock-registry record for the same agent name to ensure file-path mode is not misrouted to registry selector install logic.
	- Test asserts install output does not include registry selector resolution messaging, confirms archive extraction path behavior, and verifies runtime output comes from file-path artifact (not registry artifact).
- Added helper `_write_archive_at_path(...)` for deterministic creation of a `.kno` archive at an explicit filesystem path used by file-path mode tests.

## Tests added/updated
- Added `tests/test_install_refactor.py::test_install_file_path_mode_preserved` (test116).

## Commands and results
- `python3 -m pytest tests/test_install_refactor.py tests/test_publish_refactor.py tests/test_cli_registry_modes.py -q`
	- Result: `8 passed`

## Additional regression note
- Broader install regression sweep included one unrelated failure:
	- `tests/test_cli_install.py::test_install_offline_succeeds_with_complete_wheels`
	- Failure reason: expected generated archive file was missing at test runtime (`.../offline-ready-agent.kno does not exist`).
	- This does not touch task68 file-path selector routing and was not modified in this task.

## Status updates
- Updated `TASKS.txt`: `task68` status moved to `needs-review`.

# Bugfix — offline install test archive path mismatch

## Root cause
- `tests/test_cli_install.py::test_install_offline_succeeds_with_complete_wheels` assumed `pack` wrote `<tmp>/<agent>.kno`.
- After feature13 archive-first refactor, `pack` writes to archive backend path (`<archive-root>/<agent>/<version>/<agent>.kno`).

## Fix
- Updated helper `_create_packed_archive_with_complete_transitive_wheels(...)` in `tests/test_cli_install.py` to:
	- set isolated `KINNOO_ARCHIVE_ROOT` for `pack` execution
	- resolve and return canonical archive path `<archive-root>/<agent>/1.0.0/<agent>.kno`
	- assert that canonical archive path exists

## Validation
- `python3 -m pytest tests/test_cli_install.py::test_install_offline_succeeds_with_complete_wheels -q`
	- Result: `1 passed`
- `python3 -m pytest tests/test_cli_install.py tests/test_install_refactor.py tests/test_cli_install_extract.py tests/test_cli_install_manifest.py tests/test_cli_install_invalid.py tests/test_cli_install_runnable.py -q`
	- Result: `12 passed`
