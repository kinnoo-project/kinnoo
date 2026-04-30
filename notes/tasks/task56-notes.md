## 2026-03-05 — SWE Progress Summary (Feature12 task56 / test99)

- Implemented `task56` selector parsing while preserving existing file-path install behavior.
- Added install target parsing contract in `src/kinnoo/registry.py`:
	- `InstallTargetSpec` dataclass for deterministic routing metadata.
	- `parse_install_target_spec(target)` to classify targets as:
		- `archive-path` (filesystem path / `.kno` path semantics),
		- `registry-latest` (`<name>`),
		- `registry-exact` (`<name>==<version>`),
		- `invalid` (clear parse error).
	- Validation uses existing `NAME_PATTERN` and `SEMVER_PATTERN` for selector correctness.
- Updated `src/kinnoo/install_command.py` to route through parser:
	- preserves direct archive install flow unchanged for file paths,
	- returns explicit deterministic error for registry selector installs (deferred to upcoming integration tasks),
	- returns clear parse errors for invalid selector forms.

### Test coverage (test99)

- Added `tests/test_cli_registry.py::test_install_selector_parsing_preserves_file_install`.
- Test verifies:
	- filesystem `.kno` install still succeeds and extracts as before,
	- `<name>` and `<name>==<version>` are routed to registry selector path with clear non-zero error,
	- invalid selector format reports deterministic parse error.

### Validation results

- `/Users/jerry/gh/kinnoo/.venv/bin/python -m pytest tests/test_cli_registry.py tests/test_cli_install.py` → passed (`7 passed`)
- `/Users/jerry/gh/kinnoo/.venv/bin/python scripts/validate_project_manifests.py` → Validation passed

### Bug/Error handling note

- Encountered one test collection `IndentationError` while adding test99.
- Resolved in 1 fix attempt (below the 5-attempt cap).

### Bookkeeping

- Updated `TASKS.txt`: `task56` status set to `needs-review`.
