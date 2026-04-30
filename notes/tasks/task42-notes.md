## task42 implementation notes

- Implemented V1 compatibility regression coverage for feature9 by adding:
	- `tests/test_validator.py::test_feature9_v1_manifest_compatibility` (test73)
- Coverage in test73:
	- Confirms a V1 manifest with no `description/author/license/env_vars` remains valid.
	- Confirms a legacy-invalid V1 manifest (missing `entrypoint`) stays invalid for legacy reasons.
	- Confirms no optional feature9 field errors are emitted on the V1 path.
- Status updates:
	- `task42` moved `not-started -> in-progress -> needs-review` in `TASKS.txt`.
- Verification:
	- `python3 -m pytest tests/test_validator.py -k "feature9_v1_manifest_compatibility"` → pass
	- `python3 -m pytest tests/test_validator.py` → pass
	- `python3 scripts/validate_project_manifests.py` → pass
