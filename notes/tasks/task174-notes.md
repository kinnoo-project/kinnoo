# Task 174 Notes

## Summary
- Implemented feature19 AC7 scope for Go manifest validation and defaults.
- Added Go-specific entrypoint contract checks in validator logic so `runtime.language: go` accepts source entrypoints such as `main.go` and binary entrypoints such as `bin/go-agent` or `dist/agent.exe`.
- Added actionable validation failures for malformed Go declarations that point to non-Go script entrypoints (for example `main.py`, `index.ts`).
- Hardened Go manifest generator defaults so `_build_go_manifest(...)` defaults to `entrypoint: main.go` when no override is provided.
- Updated kinnoo.yaml spec docs with Go runtime language support and source vs binary entrypoint guidance.
- Added dedicated schema unit coverage file for test80: `tests/schema_unit/test_go_manifest_schema.py`.

## Teaching Notes
- Runtime schema design pattern:
  keep broad cross-runtime validation generic (required/type checks), then add runtime-specific constraints in focused helpers (here: `_collect_go_entrypoint_contract_errors`) so feature growth stays additive and regression risk remains low.
- Entry point contracts for polyglot CLIs:
  source mode and binary mode are distinct execution intents, and validation should accept both while rejecting contradictory declarations (for Go, Python/Node script suffixes are a strong mismatch signal).
- Generator default coherence:
  setting defaults at the builder API boundary (`entrypoint="main.go"`) prevents drift when future callers are added.

## Test Results
- Python environment note:
  configured workspace venv did not have pytest installed (`/Users/jerry/gh/public/kinnoo/.venv/bin/python: No module named pytest`), so execution used `python3` per requested workflow.
- Executed command: `python3 -m pytest tests --testmon tests/schema_unit/test_go_manifest_schema.py`
- Result: `251 passed, 188 skipped, 4 deselected in 91.43s`; included `tests/schema_unit/test_go_manifest_schema.py .....` (all new test80 checks passed).
- Executed command: `python3 -m pytest tests --testmon tests/schema_unit/test_go_manifest_schema.py::test_feature19_go_source_entrypoint_is_valid tests/schema_unit/test_go_manifest_schema.py::test_feature19_go_binary_entrypoint_is_valid tests/schema_unit/test_go_manifest_schema.py::test_feature19_unsupported_runtime_language_is_rejected tests/schema_unit/test_go_manifest_schema.py::test_feature19_go_rejects_non_go_script_entrypoint tests/schema_unit/test_go_manifest_schema.py::test_feature19_go_rejects_non_go_script_in_entrypoints_contract`
- Result: `255 passed, 188 skipped in 86.73s`; pytest acknowledged explicit node selectors and all 5 task174 target tests passed.
- Executed command: `python3 scripts/validate_project_manifests.py`
- Result: `Validation passed: manifests are consistent`
