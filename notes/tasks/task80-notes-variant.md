# Task105 Notes — Generate checksum sidecar during pack

## Scope implemented
- Extended `kinnoo pack` to compute SHA256 for the final stored `.kno` archive.
- Added sidecar write behavior to emit `<archive>.kno.sha256` adjacent to the archive.
- Sidecar content uses stable format: `<sha256>  <archive-filename>`.
- Added explicit pack output line showing sidecar location.

## Implementation details
- Updated `src/kinnoo/pack_command.py`:
  - Added `_compute_sha256(file_path: Path) -> str` (streaming hash computation).
  - Added `_write_checksum_sidecar(archive_path: Path) -> Path` (writes deterministic sidecar text).
  - After archive storage, writes sidecar next to canonical archive path.
  - On sidecar write failure, prints actionable error and exits non-zero.

## Notes
- Quick learning note: writing the checksum as <digest> <filename> mirrors common sha256sum conventions, making verification deterministic and human/tool-friendly.

## Tests implemented
- `tests/test_archive_integrity.py::test_pack_generates_checksum_sidecar` (test135)
  - Verifies sidecar creation, format validity, digest correctness, and output line.
- `tests/test_archive_integrity.py::test_pack_stores_checksum_with_local_archive` (test136)
  - Verifies local archive destination contains both `.kno` and `.kno.sha256` as siblings.

## Test results
- `python3 -m pytest tests/test_archive_integrity.py -q` -> `2 passed`
- `python3 -m pytest tests/test_pack_refactor.py -q` -> `2 passed`
