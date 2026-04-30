# task142 notes

## Summary
- Added strict publish enforcement via a new publish CLI flag: --strict.
- Extended publish command to require detached signature artifacts (.sig and .sig.json) and verify signatures before upload in strict mode.
- Added deterministic remediation diagnostics for unsigned and invalidly signed publish candidates.
- Added strict publish regression test test_feature71_strict_publish_and_docs in tests/test_cli_registry.py.
- Added CI strict-mode rollout guidance in README for staged adoption and fail-closed expectations.

## Teaching Notes
- Publish-time trust checks should run before backend writes to prevent unsafe artifacts from entering registry state.
- Strict policy should be explicit and opt-in at command level first, then promoted to required CI gates.
- Docs rollout guidance reduces adoption friction by defining transition phases (audit mode then enforcement mode).
- Regression tests that combine behavior checks with docs anchors help keep CI examples and runtime behavior in sync.

## Validation
- python3 -m pytest tests --testmon -k test_feature71_strict_publish_and_docs
