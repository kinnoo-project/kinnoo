## Task40 Summary — Global CLI Version Flag

### Implementation
- Added canonical version export in `src/kinnoo/__init__.py`:
  - `__version__` is resolved from installed package metadata via `importlib.metadata.version("kinnoo")`.
  - Added development fallback to `pyproject.toml` parsing (via `tomllib`) when package metadata is unavailable.
- Added parser-level global flag in `src/kinnoo/cli.py`:
  - `parser.add_argument("--version", action="version", version=KINNOO_VERSION)`
  - Works without requiring a subcommand and exits with code `0`.

### Test62
- Added `test_cli_version_flag` in `tests/test_cli.py`.
- Test invokes CLI via script path (`python src/kinnoo/cli.py --version`) and asserts:
  - exit code is `0`
  - output contains a semantic version pattern (`X.Y.Z`).

### Validation Runs
- Attempted handoff targeted command:
  - `python3 -m pytest tests/test_cli_install.py tests/test_cli.py tests/test_suite_integrity.py tests/test_regression_v1.py`
  - Result: failed because `tests/test_suite_integrity.py` is not present yet (task41 scope).
- Ran existing relevant tests:
  - `python3 -m pytest tests/test_cli.py::test_cli_version_flag tests/test_cli_install.py::test_install_delegates_to_install_command tests/test_cli.py`
  - Result: `11 passed`.
- Manifest validation after task status updates:
  - `python3 scripts/validate_project_manifests.py`
  - Result: `Validation passed: manifests are consistent`.
