# Task 386 Notes - Add install-time integrity and signature verification (--strict, --skip-verify)

## What was implemented
- Added `--skip-verify` install CLI flag in <redacted-path> and propagated it to install command flow.
- Added embedded verification pipeline in <redacted-path>
  - Verifies META-INF/integrity.json against extracted files.
  - In strict mode, verifies META-INF/signature.json signature over integrity.json payload.
  - Uses publisher public key resolution from:
    1) expected publisher key (registry association),
    2) embedded `public_key_pem` (if present),
    3) detached sidecar metadata fallback.
- Preserved existing detached checksum/signature gates when verification is enabled.
- Added skip path: `--skip-verify` bypasses checksum, detached signature, and embedded verification checks.

## Why this design
- Maintains compatibility with existing strict-mode/deployed signature sidecar flows while adding the new embedded verification contract for Phase 8.
- Verification remains fail-closed on mismatch and strict-signature failure paths.

## Targeted tests added/run
- Added tests/test_feature_88.py::test_feature88_group1
- Command: python3 -m pytest tests/test_feature_88.py -k test_feature88_group1 --testmon
- Result: 1 passed, 1 deselected

## Teaching notes
- Security checks should be layered and composable, not mutually exclusive. Here, detached and embedded verification can coexist during migration.
- `--skip-verify` is a deliberate tradeoff flag: useful for development diagnostics but dangerous for production supply-chain trust.
