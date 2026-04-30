# Task83 — Refactor publish CLI to agent-name source

## What was implemented
- Refactored publish CLI contract to `kinnoo publish <agent-name> [--local]` in `src/kinnoo/cli.py`.
- Implemented name-based publish flow in `src/kinnoo/publish_command.py`:
	- Resolves latest local archive via `LocalArchiveBackend` from `~/.kinnoo/archive/<agent>/<version>/<agent>.kno` (or `KINNOO_ARCHIVE_ROOT` in tests).
	- Validates resolved archive manifest and enforces name/version consistency against resolved source record.
	- Publishes to mock registry backend (`MockFilesystemRegistryBackend`) and prints source/target path outcome messages.
	- Returns explicit non-zero errors for missing agent source, no versions, no publishable artifacts, unreadable archive metadata, or invalid manifest metadata.
- Preserved compatibility for legacy `publish <archive.kno>` callers by detecting `.kno` path input and publishing through the same validation/publish pipeline.

## Tests added/updated
- Added `tests/test_publish_refactor.py` with:
	- `test_publish_name_resolves_latest_local_archive` (test109)
	- `test_publish_errors_for_missing_or_invalid_archive_source` (test111)
- Updated `tests/test_cli_registry.py` usage expectation to `Usage: kinnoo publish <agent-name> [--local]`.

## Commands and results
- `python3 -m pytest tests/test_publish_refactor.py tests/test_cli_registry.py -q`
	- Result: `8 passed`
- `python3 scripts/validate_project_manifests.py`
	- Result: passed

## Status updates
- Updated `TASKS.txt`: `task63` status moved to `needs-review`.
