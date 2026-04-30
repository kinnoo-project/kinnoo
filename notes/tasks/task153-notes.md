# Task396 Notes

## Summary
- Created `docs/cli-reference.md` with a structured client CLI reference.
- Documented command usage, arguments, options, environment variables, exit-code behavior, and examples for client commands.
- Included `trust` as `[planned]` to satisfy feature scope without overstating current command availability.
- Added `tests/test_feature_93.py` with other feature (unreferenced) group validation tests.

## Why
- Task396 implements other feature (unreferenced) AC1-AC3 for client command reference coverage.
- The docs intentionally separate implemented commands from planned surfaces.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature93_group1"`
- Result: 1 passed.

## Teaching Notes
- For CLI docs, capture real command contracts from `--help` output first, then add concise operational guidance.
- If a requirement mentions a command that is not currently exposed (`trust`), mark it clearly as planned rather than pretending support exists.
- Keep docs testable by using stable markers (headings and command labels) in automated acceptance tests.
