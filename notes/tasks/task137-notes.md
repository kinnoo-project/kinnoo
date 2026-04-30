# Task338 Notes

## Summary
Implemented the Feature64 source import bridge path for ClawHub with deterministic mirror resolution, canonical openclaw-skill manifest scaffolding, and persisted local import reports.

## What Changed
- `src/kinnoo/cli.py`
  - Added import flags:
    - `--source clawhub`
    - `--live-fallback`
  - Wired these flags into import command dispatch.

- `src/kinnoo/registry.py`
  - Added `RegistryService.get_clawhub_mirror_record(...)` for deterministic slug lookup in mirror index.

- `src/kinnoo/import_command.py`
  - Added source-mode branch in `import_agent(...)` for `--source clawhub`.
  - Implemented slug normalization (`<owner>/<slug>`), deterministic destination resolution, and mirror lookup.
  - Added deterministic missing-slug error guidance: run `kinnoo sync clawhub`.
  - Added canonical scaffold generation for `openclaw-skill` manifests with `provenance` object fields:
    - `source_registry`
    - `source_version`
    - `source_slug`
    - optional `source_url`
  - Added local report artifact generation (`kinnoo-import-report.json`) with inferred/unresolved guidance.

- `src/kinnoo/analyzer.py`
  - Added `build_clawhub_import_report_template(...)` helper to centralize deterministic report structure.

- `tests/test_cli_import.py`
  - Added `test_feature64_clawhub_import_scaffold` (test497).
  - Verifies successful source import scaffold and deterministic missing-slug failure output.

## Teaching Notes
- Source-import workflows are safer when lookup and scaffold contracts are explicit and deterministic: the same slug and mirror state should always produce the same manifest/report.
- A report artifact is valuable because it captures what was inferred vs unresolved at import-time, which reduces ambiguity during install/run debugging.
- Keeping provenance fields canonical at creation time prevents schema drift and avoids migration cleanup later.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k "test_feature64_clawhub_import_scaffold"`
- Result:
  - `1 passed, 459 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task137-smoke-tests.md`.
