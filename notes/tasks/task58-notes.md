## 2026-03-05 — SWE Progress Summary (Feature12 task58 / test101)

- Implemented `task58` by integrating registry resolution into the install flow in `src/kinnoo/install_command.py`.
- Install behavior now routes selector targets through the backend abstraction:
	- `<name>` resolves latest published archive via `RegistryService.resolve_with_error(...)`.
	- `<name>==<version>` resolves exact published archive via the same service boundary.
- After resolution, install reuses the existing archive install pipeline through a single helper (`_install_from_archive_path`) to avoid duplicated extraction/validation/venv/dependency logic.
- Added deterministic selector resolution logging and preserved existing file-path install behavior.
- Registry selector default install targets are deterministic:
	- latest selector installs to `<cwd>/<name>`,
	- exact selector installs to `<cwd>/<name>-<version>`,
	- optional user-provided target directory still takes precedence.

### Test coverage (test101)

- Added `tests/test_cli_registry.py::test_install_from_registry_name_and_version_uses_existing_pipeline`.
- Test verifies:
	- local registry can be populated with multiple versions,
	- `kinnoo install <name>` resolves latest version and installs successfully,
	- `kinnoo install <name>==<version>` resolves exact version and installs successfully,
	- both installed agents run successfully through existing `kinnoo run` flow.

### Supporting updates

- Updated `tests/test_cli_registry.py::test_install_selector_parsing_preserves_file_install` assertions to reflect that selector inputs now route through implemented registry resolution instead of placeholder "not implemented" errors.

### Validation results

- `/Users/jerry/gh/kinnoo/.venv/bin/python -m pytest tests/test_cli_registry.py tests/test_registry.py tests/test_cli_install.py` → passed (`10 passed`)
- `/Users/jerry/gh/kinnoo/.venv/bin/python scripts/validate_project_manifests.py` → Validation passed

### Bookkeeping

- Updated `TASKS.txt`: `task58` status set to `needs-review`.
