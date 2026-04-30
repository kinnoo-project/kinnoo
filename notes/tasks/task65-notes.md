# Task85 — Install by registry name/version using mock backend

## What was implemented
- Updated registry-selector install resolution in `src/kinnoo/install_command.py` to use `MockFilesystemRegistryBackend` (instead of local backend) while preserving existing `RegistryService` abstraction boundary.
	- `kinnoo install <name>` now resolves latest from mock registry backend root.
	- `kinnoo install <name>==<version>` now resolves exact version from mock registry backend root.
	- Resolved archives continue through existing `_install_from_archive_path(...)` pipeline (no duplicated install logic).

## Tests added/updated
- Added `tests/test_install_refactor.py` with:
	- `test_install_name_resolves_latest_from_mock_registry` (test112)
	- `test_install_name_equals_version_from_mock_registry` (test113)
- Coverage includes:
	- latest selector resolution path
	- exact selector resolution path
	- missing exact-version error behavior
	- successful installed-agent execution to verify selected artifact version

## Commands and results
- `python3 -m pytest tests/test_install_refactor.py -q`
	- Result: `2 passed`

## Status updates
- Updated `TASKS.txt`: `task65` status moved to `needs-review`.
