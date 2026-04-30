## 2026-03-05 — SWE Progress Summary (Feature11 task49 / test90)

- Implemented `task49` in `src/kinnoo/inspect_command.py` with deterministic inspect target detection.
- Added target branching for:
	- directory targets
	- `.kno` file targets (archive branch handoff for task50)
	- unsupported files / invalid targets
- Added directory required-file checks before manifest processing:
	- missing `kinnoo.yaml` prints stdout guidance and a minimal manifest example, exits non-zero
	- missing `requirements.txt` prints stdout guidance and robust generation commands (`pip install uv`, `uv export --format requirements-txt > requirements.txt`), exits non-zero
- Added safe manifest-read path when both required files exist for downstream inspect stages.

### Test coverage (test90)

- Extended `tests/test_cli_inspect.py` with:
	- `test_inspect_missing_required_files_prints_guidance`
- The test covers both task49 required guidance scenarios and asserts graceful non-zero exits with no traceback output.

### Validation results

- `python3 -m pytest tests/test_cli_inspect.py -k "inspect_missing_target_prints_usage or inspect_missing_required_files_prints_guidance"` → passed
- `python3 scripts/validate_project_manifests.py` → Validation passed

### Bookkeeping

- Updated `TASKS.txt`: `task49` status set to `needs-review`.
