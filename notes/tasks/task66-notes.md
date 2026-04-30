# Task86 — Refactor list with default local and source flags

## What was implemented
- Refactored list source behavior in `src/kinnoo/list_command.py`:
	- Default source is local archive (`kinnoo list` and `kinnoo list --local`).
	- Remote source uses mock registry (`kinnoo list --remote`).
	- Output schema remains stable: `name | latest: <version> | description: <description>`.
- Added local archive latest-summary support in `src/kinnoo/archive.py`:
	- Introduced `ArchiveAgentSummary`.
	- Added `LocalArchiveBackend.list_latest_agents()`.
	- Reads latest archive manifest description from `.kno` to populate output description.
- Updated CLI wiring in `src/kinnoo/cli.py`:
	- Added mutually exclusive `list` flags `--local` and `--remote`.
	- Routed source mode into `list_agents(source=...)` with default local behavior.

## Tests added/updated
- Added `tests/test_cli_registry_modes.py` with:
	- `test_list_default_local_and_remote_modes` (test114)
- Coverage includes:
	- default `kinnoo list` equals `kinnoo list --local`
	- local mode reads local archive latest inventory
	- remote mode reads mock registry inventory
	- output schema consistency across source modes

## Commands and results
- `python3 -m pytest tests/test_cli_registry_modes.py tests/test_publish_refactor.py tests/test_install_refactor.py -q`
	- Result: `6 passed`

## Status updates
- Updated `TASKS.txt`: `task66` status moved to `needs-review`.
