# Task106 Notes — Add checksum utility helpers

## Scope implemented
- Added shared checksum helper module at `src/kinnoo/checksum.py`.
- Centralized SHA256 compute, sidecar format/parse, sidecar path, verify, and sidecar write logic.
- Refactored command modules to consume shared helpers and remove duplicate checksum logic.

## Implementation details
- New helper APIs in `src/kinnoo/checksum.py`:
  - `checksum_sidecar_path_for_archive(archive_path)`
  - `compute_file_sha256(file_path)`
  - `format_checksum_sidecar_line(checksum_value, archive_filename)`
  - `parse_checksum_sidecar_text(sidecar_text)`
  - `read_checksum_sidecar(sidecar_path)`
  - `verify_archive_checksum(archive_path, expected_checksum)`
  - `write_checksum_sidecar_for_archive(archive_path)`
  - `ChecksumParseError` for strict parse failures
- `src/kinnoo/pack_command.py`
  - Removed in-module checksum compute/write helpers.
  - Uses `write_checksum_sidecar_for_archive(...)`.
- `src/kinnoo/install_command.py`
  - Replaced local sidecar path helper with shared `checksum_sidecar_path_for_archive(...)`.
- This is a classic software supply-chain integrity pattern used in agentic systems too: centralizing hash/parse/verify primitives prevents command drift and gives deterministic trust checks across pack/install/publish flows.

## Tests implemented
- Added `tests/test_archive_integrity.py::test_checksum_helpers_compute_and_parse` (test137):
  - Computes checksum for deterministic fixture archive bytes.
  - Formats and parses sidecar text.
  - Verifies expected-vs-actual checksum match path.

## Test results
- `python3 -m pytest tests/test_archive_integrity.py -q` -> `3 passed`
- `python3 -m pytest tests/test_pack_refactor.py tests/test_cli_install.py::test_install_delegates_to_install_command -q` -> `3 passed`

## Notes
- This foundation keeps checksum behavior deterministic and avoids command-level drift as tasks 107-110 integrate checksum validation and propagation.
