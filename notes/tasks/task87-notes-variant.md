# Task113 Notes - Inspect displays archive size metadata

## Scope implemented
- Extended archive-target inspect output to include human-readable archive size metadata.
- Kept inspect output additive and non-breaking for existing fields.

## Implementation details
- Updated `<redacted-path>`:
  - imported shared formatter `format_size_human_readable` from `<redacted-path>`.
  - extended `_print_inspect_output(...)` with optional `archive_size_human` parameter.
  - in `_inspect_archive_target(...)`, resolved archive byte size from `archive_path.stat().st_size` and formatted it for display.
  - prints the required additive line for archive targets:
    - `- Archive Size: <human-readable>`

## Tests implemented
- Added `tests/test_pack_size_reporting.py::test_inspect_displays_archive_size_for_archive_target` (test146).
- Test flow:
  - create minimal agent fixture,
  - run `kinnoo pack`,
  - discover packed `.kno` under archive root,
  - run `kinnoo inspect <archive.kno>`,
  - assert archive-size line exists with deterministic units.

## Test results
- `python3 -m pytest tests/test_pack_size_reporting.py -q` -> `3 passed`

## Teaching notes
- This task demonstrates a good incremental API pattern: add optional output metadata while preserving existing output contracts.
- Reusing `size_format.py` avoids drift between pack/inspect/list and keeps formatting logic centralized for future changes.
- Interview framing: this is a practical example of observability-oriented UX with low-risk additive behavior and fast, deterministic CLI integration testing.
