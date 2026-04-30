# Task336 Notes

## Summary
Implemented Feature63 mirror storage foundations by adding a dedicated ClawHub mirror metadata model with deterministic upsert/list behavior under tenant slug `clawhub`, plus regression coverage for tenant ownership and source attribution persistence.

## What Changed
- `<redacted-path>`
  - Added `CLAW_HUB_TENANT_SLUG = "clawhub"` as a canonical tenant constant for mirror storage.

- `<redacted-path>`
  - Added `ClawHubMirrorRecord` dataclass for normalized mirror metadata transport.
  - Added `RegistryService.upsert_clawhub_mirror_record(...)`.
  - Added `RegistryService.list_clawhub_mirror_records()`.
  - Added deterministic normalization fallback when backend returns dict payloads.

- `<redacted-path>`
  - Added `LocalRegistryBackend.upsert_clawhub_mirror_record(...)` with deterministic JSON persistence.
  - Added `LocalRegistryBackend.list_clawhub_mirror_records()`.
  - Added `LocalRegistryBackend.get_clawhub_mirror_record(...)` for future import bridge lookup.
  - Added deterministic mirror root layout: `tenants/clawhub/mirror/<owner>/<slug>/<version>/mirror-record.json`.
  - Added stable slug normalization and UTC timestamp helper for sync metadata.

- `<redacted-path>`
  - Added `fetch_clawhub_mirror_record(slug=...)` helper to support remote mirror lookup contract in upcoming tasks.

- `tests/test_registry.py`
  - Added `test_feature63_clawhub_tenant_mirror_ownership` (test495).
  - Verifies mirrored records persist under `tenant_slug=clawhub`, include source attribution fields, and are listable without interactive auth/login flow.

## Teaching Notes
- A good mirror design separates **source identity** (`source_registry`, `source_slug`, `source_version`) from **local ownership** (`tenant_slug`) so provenance remains auditable.
- Idempotent sync pipelines are easiest when write paths are deterministic (`<slug>/<version>/mirror-record.json`) and upserts rewrite that canonical location.
- Designing service-layer APIs (`RegistryService`) before command UX keeps later tasks (search/import/sync) composable and easier to test.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k "test_feature63_clawhub_tenant_mirror_ownership"`
- Result:
  - `1 passed, 457 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task136-smoke-tests.md`.
