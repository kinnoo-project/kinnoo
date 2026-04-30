# Task90 — Harden source-mode CLI validation and errors

## What was implemented
- Implemented `test118` in `tests/test_cli_registry_modes.py` as `test_source_mode_argument_validation_errors`.
- The test verifies deterministic non-zero error behavior for:
	- invalid mutually-exclusive flags: `kinnoo list --local --remote`
	- invalid mutually-exclusive flags: `kinnoo search --local --remote <query>`
	- missing required query: `kinnoo search`
	- malformed install selector: `kinnoo install bad-agent==invalid`
- Existing CLI/parser/selector validation behavior already satisfied task69 requirements, so no source code changes were required in command modules.

## Tests added/updated
- Added `tests/test_cli_registry_modes.py::test_source_mode_argument_validation_errors` (test118).

## Commands and results
- `python3 -m pytest tests/test_cli_registry_modes.py tests/test_install_refactor.py tests/test_publish_refactor.py -q`
	- Result: `9 passed`

## Status updates
- Updated `TASKS.txt`: `task69` status moved to `needs-review`.
