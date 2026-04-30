# Task476 - disable sync/stop/attach/logs and daemon help section

## Summary
- Commented out parser registrations for `sync`, `stop`, `attach`, and `logs` while preserving disabled code blocks with `[agent]` annotations.
- Commented out dispatch branches for the same commands, preserving code for future re-enable.
- Removed daemon section and sync listing from top-level help output path while keeping explicit `[agent]` notes.
- Added regression test to verify disabled commands are rejected and daemon help section is absent.

## Files changed
- src/kinnoo/cli.py
- tests/test_cli.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli.py --testmon -k "test_disabled_commands_not_accessible"
- Result:
  - 1 passed, 94 deselected

## Teaching notes
- Temporarily disabling command surfaces is safest when both parser registration and dispatch routes are disabled, so dead command paths cannot be reached accidentally.
- Keeping disabled code in commented blocks with clear markers preserves implementation context and lowers re-enable cost in future iterations.
