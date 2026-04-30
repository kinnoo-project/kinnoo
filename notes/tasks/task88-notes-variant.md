# Task114 Notes - List output includes archive size

## Scope implemented
- Added archive size visibility to list output for local and remote modes.
- Preserved existing list ordering and existing fields while appending size as an additive field.

## Implementation details
- Updated `src/kinnoo/archive.py`:
  - extended `ArchiveAgentSummary` with optional `archive_size_bytes`.
  - populated `archive_size_bytes` from latest archive artifact path during local summary collection.
- Updated `src/kinnoo/registry.py`:
  - extended `RegistryAgentSummary` with optional `archive_size_bytes`.
  - preserved compatibility fallback path in `RegistryService.list_latest_agents` by setting `archive_size_bytes=None`.
- Updated `src/kinnoo/registry_backends.py`:
  - populated `archive_size_bytes` for latest remote registry summary rows from the resolved archive path.
- Updated `src/kinnoo/list_command.py`:
  - reused shared formatter from `src/kinnoo/size_format.py`.
  - added `size: <human-readable>` to both local and remote list output rows.
  - added `_format_archive_size(...)` helper to keep missing-size handling deterministic (`unknown`).

## Tests implemented
- Added `tests/test_pack_size_reporting.py::test_list_includes_archive_size` (test147).
- Test validates:
  - default list and `--local` both include size field in local rows,
  - `--remote` includes size field in remote rows,
  - size values are human-readable (`B|KB|MB|GB`) in both modes.

## Test results
- `python3 -m pytest tests/test_pack_size_reporting.py tests/test_cli_registry_modes.py -q` -> `7 passed`

## Teaching notes
- This task is a good data-model evolution example: adding optional fields (`archive_size_bytes`) avoids breaking existing call sites while enabling richer output.
- Keeping size formatting centralized (`size_format.py`) is a maintainability pattern that reduces cross-command drift and regression risk.
- Interview framing: you can describe this as a backward-compatible contract extension with end-to-end validation across storage layer, service summaries, and CLI rendering.
