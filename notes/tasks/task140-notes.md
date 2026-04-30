# task140 notes

## Summary
- Added `kinnoo sync clawhub` command surface with incremental/full modes and optional `--since` cursor.
- Implemented `<redacted-path>` to ingest ClawHub records and upsert into the clawhub tenant mirror namespace.
- Added deterministic sync summary counters: `created`, `updated`, `skipped`, `failed`.
- Added remote client index fetch helper for future remote-backed sync.
- Added regression test `test_feature67_sync_modes_and_upsert` validating mode behavior and mirror attribution persistence.

## Teaching Notes
- Idempotent sync design: split records into `created`/`updated`/`skipped` before writing so repeated runs remain deterministic and observable.
- Operationally safe counters matter for automation: CI and operators need stable, parse-friendly summaries to detect drift and partial sync issues quickly.
- Normalization first, writes second: converting variant payload shapes (`slug` vs `source_slug`, `version` vs `source_version`) at the boundary keeps core sync logic simple.
- Mirror attribution should be immutable from the command perspective (`tenant_slug=clawhub`, `source_registry=clawhub`) so provenance stays consistent across updates.

## Validation
- `python3 -m pytest tests --testmon -k test_feature67_sync_modes_and_upsert`
