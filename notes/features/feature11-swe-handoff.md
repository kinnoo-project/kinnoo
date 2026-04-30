# Feature 88 — SWE Handoff: Install-Time Integrity Verification

## Context
During `kinnoo install`, verify the integrity manifest and optionally the signature before extracting files. This is the consumer-side counterpart to features 86-87.

## Files to Modify
- `src/kinnoo/install_command.py` (~800 lines) — After extracting the `.kno` archive:
  1. Check for `META-INF/integrity.json`. If present, verify all file hashes.
  2. If `--strict` flag is set, also check for `META-INF/signature.json` and verify the signature.
  3. If `--skip-verify` flag is set, skip all verification.
  4. If archive has no integrity.json (pre-feature9 archive), print warning but continue.

## CLI Flags
- `--strict` — Require both integrity and signature verification. Fail if either is missing or invalid.
- `--skip-verify` — Skip all integrity/signature checks. Useful for development.
- Default (no flag) — Verify integrity if present, warn if missing. Ignore signature presence.

## Implementation Notes
- Use `verify_integrity_manifest()` from `src/kinnoo/integrity.py` (feature9)
- Use `verify_signature()` from `src/kinnoo/signing.py` for signature verification
- Verification happens **after extraction but before venv creation** — if verification fails, clean up extracted files
- Error messages must be specific: "File foo.py hash mismatch: expected abc..., got def..."
- Log verification results: "Verified 42 files, all passed" or "Verification FAILED: 2 files have hash mismatches"

## Testing
- Valid archive: verify passes, install succeeds
- Tampered archive: verify fails, install aborts, extracted files cleaned up
- Missing integrity.json: warning printed, install succeeds
- Unsigned archive + `--strict`: install fails with "signature required but not found"
- Invalid signature + `--strict`: install fails with "signature verification failed"
- `--skip-verify`: all verification skipped regardless of archive contents
- Backward compatibility: archives from before feature9 install with a warning

## Dependencies
- feature9 (integrity module)
- feature10 (signature format — needed for `--strict` mode)

## Acceptance Criteria Summary
1. Install verifies integrity.json by default
2. `--strict` requires both integrity + signature
3. `--skip-verify` bypasses all checks
4. Old archives (no META-INF) install with warning
5. Clear error messages on verification failure
6. Failed verification cleans up extracted files
