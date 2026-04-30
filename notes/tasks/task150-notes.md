# Task 387 Notes - Handle missing manifests, tampered files, and backward compat in install

## What was implemented
- Completed backward-compat handling in install verification flow:
  - If META-INF/integrity.json is absent and not strict mode, install continues with a clear warning.
- Added explicit verification summary logging on success:
  - "Verified <N> files, all passed."
- Added mismatch diagnostics for tampered content and enforced cleanup behavior on verification failure.
- Added/validated strict-mode failure paths for unsigned installs and skip-verify bypass behavior via feature11 tests.

## Why this design
- This balances security and migration safety: old archives still install with warnings while new archives get strong integrity checks.
- Detailed mismatch and summary logs improve operator debugging and reduce triage time.

## Targeted tests run
- python3 -m pytest tests/test_feature_88.py -k test_feature88_group2 --testmon

Result:
- 1 passed, 1 deselected

## Teaching notes
- Backward compatibility can be implemented as a policy tier:
  - strict mode = fail-closed
  - default mode = verify when possible, warn on legacy gaps
  - skip mode = explicit development override
- Logging verification counts helps operational confidence and incident response.
