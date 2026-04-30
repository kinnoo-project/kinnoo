# task141 notes

## Summary
- Updated landing hero and supporting copy in <redacted-path>)/page.tsx to better reflect Phase 6 runtime/testing/provenance messaging.
- Updated feature cards in <redacted-path> to include explicit ClawHub mirror provenance messaging and stronger trust framing.
- Added Feature70 Phase 6 command matrix section to README.md with high-signal operational commands.
- Added explicit clawhub tenant attribution/provenance model notes in README.
- Added regression test test_feature70_landing_and_readme_phase6_messaging in tests/test_docs.py.

## Teaching Notes
- Product copy should map directly to executable commands; this keeps docs marketing claims verifiable and testable.
- For trust-heavy tooling, provenance language must be explicit (source + tenant model), not implied.
- Landing copy can still be concise while communicating operational concepts by anchoring to concrete nouns: OpenClaw, ClawHub, signed packages, provenance.
- Docs tests for copy are useful when they check capability intent (keywords and command contracts), not pixel-level wording.

## Validation
- python3 -m pytest tests --testmon -k test_feature70_landing_and_readme_phase6_messaging
