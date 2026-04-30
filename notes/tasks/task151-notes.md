# Task394 Notes

## Summary
- Created `docs/kinnoo-yaml-spec.md` as a technical manifest reference.
- Documented required and optional fields, validation constraints, and framework examples.
- Added feature-level tests in `tests/test_feature_92.py`.
- Added cross-reference links to `README.md` and CLI help text in `src/kinnoo/cli.py`.

## Why
- Feature92 AC1-AC3 requires a complete manifest spec and examples.
- AC4-AC5 require version/compatibility notes and project cross-references.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature92_group1 or test_feature92_group2"`
- Result: 2 passed.

## Teaching Notes
- For schema docs, write from executable sources (`schema.py`, `validator.py`) first, then add narrative.
- Keep field tables explicit (`type`, `required`, `default`, `validation`) so docs are testable.
- If docs become acceptance criteria, add lightweight tests that check for durable anchors (headings/section names) instead of fragile full-text snapshots.
