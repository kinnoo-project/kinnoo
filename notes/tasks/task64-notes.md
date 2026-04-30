# Task84 — Implement publish mock registry target and rollover

## What was implemented
- Implemented mock-registry publish rollover behavior in `src/kinnoo/registry_backends.py` via `MockFilesystemRegistryBackend.publish` override.
	- Publish target is canonical: `registry-scratch/jerry/<agent>/<version>/<agent>.kno` (or `KINNOO_REGISTRY_ROOT` override in tests).
	- If tagged target already exists, backend now preserves the prior artifact in deterministic slot `untagged-<n>` under the same agent root (e.g., `.../<agent>/untagged-1/<agent>.kno`) before writing new tagged payload.
	- Existing metadata file is also preserved alongside rollover archive when present.
- Updated `src/kinnoo/publish_command.py` to emit rollover outcome details:
	- Source archive path
	- Target tagged registry path
	- Rollover archive path when an existing tagged artifact was moved to untagged slot

## Tests added/updated
- Added `test_publish_rolls_existing_tagged_to_untagged` in `tests/test_publish_refactor.py` (test110):
	- Publishes same `agent/version` twice with different payloads.
	- Verifies first payload is preserved in `untagged-1`.
	- Verifies tagged destination contains second payload.
	- Verifies publish output reports rollover archive path.

## Commands and results
- `python3 -m pytest tests/test_publish_refactor.py -q`
	- Result: `3 passed`

## Status updates
- Updated `TASKS.txt`: `task64` status moved to `needs-review`.
