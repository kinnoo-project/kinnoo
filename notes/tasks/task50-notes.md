## 2026-03-05 — SWE Progress Summary (Feature11 task50 / test91)

- Implemented `task50` in `src/kinnoo/inspect_command.py` to read `kinnoo.yaml` directly from `.kno` archives without extracting archive contents.
- Added reusable helper `_read_manifest_from_archive(archive_path)` that:
	- opens `.kno` as zip
	- locates `kinnoo.yaml` member
	- decodes and parses manifest YAML in-memory
	- returns actionable errors for missing manifest, invalid zip, decode failure, and YAML parse failure.
- Updated archive inspect path to print human-readable metadata lines from archive manifest (`name`, `version`, `entrypoint`) and return non-zero on archive read failures.

### Test coverage (test91)

- Extended `tests/test_cli_inspect.py` with:
	- `test_inspect_reads_manifest_from_archive_without_extracting`
- Test creates a `.kno` zip fixture with `kinnoo.yaml`, runs inspect via script path, verifies metadata in output, and asserts no extraction artifacts are created.

### Validation results

- `python3 -m pytest tests/test_cli_inspect.py -k "inspect_reads_manifest_from_archive_without_extracting or inspect_missing_required_files_prints_guidance or inspect_missing_target_prints_usage"` → passed
- `python3 scripts/validate_project_manifests.py` → Validation passed

### Bookkeeping

- Updated `TASKS.txt`: `task50` status set to `needs-review`.
