# Task108 Notes — Missing checksum warning on install

## Scope implemented
- Implemented explicit warning behavior when checksum sidecar is absent for file-path installs.
- Install now emits required warning text:
  - `No checksum file found — archive integrity not verified`
- Missing-sidecar path remains warning-only and continues normal install flow.

## Implementation details
- Updated `<redacted-path>`:
  - Detects missing `<archive>.kno.sha256` via shared helper path resolution.
  - Prints required warning line to stderr.
  - Preserves existing trust-baseline unverified-source warning/prompt behavior.
  - Continues into normal manifest validation, extraction, and dependency installation.
- Quick AI/ML engineering tie-in: this is a “graceful degradation” trust pattern—hard fail on proven tamper, warn-and-proceed on missing proof—which is common in artifact pipelines for agent deployments

## Tests implemented
- Added `tests/test_archive_integrity.py::test_install_warns_when_checksum_missing` (test140)
  - Builds archive without sidecar.
  - Runs `kinnoo install ... --yes`.
  - Asserts warning appears and install succeeds.

## Regression fix during task
- `tests/test_trust_baseline.py::test_install_unverified_source_warning` failed because it used an intentionally invalid dummy `.sha256` sidecar string.
- Updated trust-baseline fixture/helper to generate valid sidecars using `write_checksum_sidecar_for_archive(...)`, which matches task82 strict parsing semantics.

## Test results
- `python3 -m pytest tests/test_archive_integrity.py -q` -> `6 passed`
- `python3 -m pytest tests/test_trust_baseline.py::test_install_unverified_source_warning -q` -> `1 passed`

## Notes
- This keeps feature15 trust messaging coherent while adding feature16 checksum-status transparency for missing sidecars.
