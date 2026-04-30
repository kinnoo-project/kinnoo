# Task87 — Refactor search with default local and source flags

## What was implemented
- Refactored search source behavior in `src/kinnoo/search_command.py`:
	- Default source is local archive (`kinnoo search <query>` and `kinnoo search --local <query>`).
	- Remote source uses mock registry (`kinnoo search --remote <query>`).
	- Case-insensitive substring matching applies to both agent name and description across both sources.
	- Output schema remains stable: `name | latest: <version> | description: <description>`.
- Updated CLI wiring in `src/kinnoo/cli.py`:
	- Added mutually exclusive `search` flags `--local` and `--remote`.
	- Updated search usage string to `Usage: kinnoo search [--local | --remote] <query>` when query is missing.
	- Routed source mode into `search_agents(query=..., source=...)` with default local behavior.

## Tests added/updated
- Added `test_search_default_local_and_remote_modes` in `tests/test_cli_registry_modes.py` (test115).
- Coverage includes:
	- default `kinnoo search <query>` equals `kinnoo search --local <query>`
	- local mode filters local archive latest inventory only
	- remote mode filters mock registry inventory only
	- case-insensitive matching for name/description across both modes

## Commands and results
- `python3 -m pytest tests/test_cli_registry_modes.py tests/test_publish_refactor.py tests/test_install_refactor.py -q`
	- Result: `7 passed`

## Status updates
- Updated `TASKS.txt`: `task67` status moved to `needs-review`.
