# Task380 Notes

## Summary
Implemented Feature85 task144 by deprecating bridge-era feature metadata (other feature (unreferenced)-other feature (unreferenced)), cleaning up stale CLI help exposure for legacy adapter flow, and documenting migration paths to Phase 7 wrapper commands.

## What Was Implemented
- Updated `FEATURES.txt`:
  - marked other feature (unreferenced)-other feature (unreferenced) as `deprecated`
  - added replacement guidance pointing to other feature (unreferenced)-other feature (unreferenced) wrapper-era flows
- Updated `src/kinnoo/cli.py`:
  - kept `--experimental-openclaw-adapter` for compatibility but suppressed it from `run --help`
- Updated `README.md`:
  - added "OpenClaw Bridge Deprecation and Migration (Feature85)" section
  - documented wrapper command equivalents for run/logs/install/search flows
- Updated `docs/CHANGELOG.md`:
  - added unreleased note for deprecation metadata and migration messaging updates

## Test Coverage
- Added/validated:
  - `tests/test_docs.py::test_feature85_deprecation_metadata_and_help_cleanup`
- Verifies:
  - other feature (unreferenced)-other feature (unreferenced) deprecation markers exist in `FEATURES.txt`
  - replacement mapping text includes `replacements: other feature (unreferenced)`
  - `kinnoo run --help` no longer shows `--experimental-openclaw-adapter`
  - README includes migration guidance and replacement command examples

## Smoke Tests
- `notes/tasks/task144-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why hide instead of hard-remove legacy flags in this task:
  - Feature85 requires non-breaking migration. Suppressing legacy help text reduces new adoption of deprecated paths while preserving backward compatibility until other task (unreferenced) adds explicit runtime warnings.
- Why this test lives in docs coverage:
  - Task380 acceptance criteria are metadata/help/documentation focused, so an integration-style docs/help assertion gives stable, high-signal regression coverage.
