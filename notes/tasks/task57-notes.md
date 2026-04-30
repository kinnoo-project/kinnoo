## 2026-03-05 — SWE Progress Summary (Feature12 task57 / test100)

- Implemented `task57` registry version resolution logic in `src/kinnoo/registry_backends.py` and `src/kinnoo/registry.py`.
- Updated local backend resolution behavior:
	- exact resolution (`<name>==<version>`) now returns explicit, actionable not-found errors including available versions when applicable,
	- latest resolution (`<name>`) now uses deterministic semver-aware ordering,
	- latest resolution scans published versions deterministically and returns the first installable archive,
	- error message is explicit when published version folders exist but no installable archives are present.
- Added semver-aware sorting support in backend:
	- `_parse_semver(...)` and `_version_sort_key(...)` now prioritize valid semver values with correct precedence,
	- release versions sort higher than prereleases,
	- non-semver directory names remain deterministically ordered behind semver entries.
- Added backend-agnostic service helper `RegistryService.resolve_with_error(...)` in `src/kinnoo/registry.py` for consistent consumer-facing error handling.

### Test coverage (test100)

- Added `tests/test_registry.py::test_registry_version_resolution_latest_and_exact`.
- Test verifies:
	- latest resolution for `<name>` selects highest published version,
	- exact resolution for `<name>==<version>` returns requested version,
	- unknown agent and unknown version return clear actionable errors.

### Validation results

- `/Users/jerry/gh/kinnoo/.venv/bin/python -m pytest tests/test_registry.py tests/test_cli_registry.py` → passed (`5 passed`)
- `/Users/jerry/gh/kinnoo/.venv/bin/python scripts/validate_project_manifests.py` → Validation passed

### Bookkeeping

- Updated `TASKS.txt`: `task57` status set to `needs-review`.
