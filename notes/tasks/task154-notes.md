# Task398 Notes

## Summary
- Created `<redacted-path>` covering current Kinnoo security architecture.
- Included threat model, mitigations, signing model (Ed25519), integrity verification, auth/session controls, authorization, upload validation, and rate limiting.
- Added `tests/test_feature_94.py` for grouped feature acceptance validation.

## Why
- Task398 implements feature13 AC1-AC3 (complete security architecture + threat model + signing model).
- Content is grounded in current code paths (`signing.py`, `integrity.py`, `<redacted-path>`, `<redacted-path>`) and avoids unsupported claims.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature94_group1"`
- Result: 1 passed.

## Teaching Notes
- Security docs should separate implemented controls from desired controls and explicitly call out gaps (for example, no dedicated JWT refresh endpoint).
- A useful pattern is threat-first writing: list threats, map each to current controls, then map controls to source files.
- For cryptographic workflows, document artifact boundaries (what gets signed, where metadata is stored, how verification is enforced) so operators can reason about trust failures.
