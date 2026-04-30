# Task107 Notes — Enforce checksum verification on install

## Scope implemented
- Added checksum sidecar verification to `kinnoo install` when `<archive>.kno.sha256` exists.
- Verification now runs before extraction or any install write side effects.
- Mismatch path fails with exact required message:
  - `Archive integrity check failed — the file may be corrupted or tampered with`

## Implementation details
- Updated `<redacted-path>` to use shared checksum helpers from `<redacted-path>`:
  - `read_checksum_sidecar(...)`
  - `verify_archive_checksum(...)`
  - `checksum_sidecar_path_for_archive(...)`
  - `ChecksumParseError`
- Added sidecar validation flow:
  - parse sidecar content,
  - ensure sidecar filename token matches archive filename,
  - verify digest against archive bytes,
  - abort on any verification failure before extraction.
- Added success signal line on verified archives:
  - `[kinnoo install] Archive checksum verified.`
- Learning note: this is a supply-chain integrity checkpoint pattern (verify artifact hash before execution/extraction), which is also foundational in agentic AI deployment pipelines for trusted artifact promotion.

## Tests implemented
- `tests/test_archive_integrity.py::test_install_verifies_checksum_when_present` (test138)
  - Creates archive + valid sidecar, verifies install succeeds and checksum verification line is present.
- `tests/test_archive_integrity.py::test_install_aborts_on_checksum_mismatch` (test139)
  - Creates archive + deliberately incorrect sidecar digest, verifies exact integrity-failure message and no extraction target directory creation.

## Test results
- `python3 -m pytest tests/test_archive_integrity.py -q` -> `5 passed`
- `python3 -m pytest tests/test_cli_install.py::test_install_delegates_to_install_command -q` -> `1 passed`

## Notes
- This keeps task82 tightly scoped to sidecar-present verification behavior; missing-sidecar warning semantics remain for task83.
