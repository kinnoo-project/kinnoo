# Task99 Notes — Unverified source confirmation prompt

## Scope implemented
- Added unverified-source detection for archive installs using `<archive>.sha256` sidecar presence.
- If missing, install now prints warning:
  - `This agent is from an unverified source.`
- If missing and `--yes`/`-y` is NOT set, install prompts:
  - `This agent is from an unverified source. Continue? (y/n):`
  - proceeds only on `y` / `yes`, otherwise aborts non-zero.
- If `--yes`/`-y` is set and checksum is missing, warning is still shown but prompt is skipped.
- If `<archive>.sha256` exists, unverified warning is not shown.

## Files changed
- `src/kinnoo/install_command.py`
- `tests/test_trust_baseline.py`
- `TASKS.txt`

## Tests
- Added/implemented `test128`:
  - `tests/test_trust_baseline.py::test_install_unverified_source_warning`

## Validation
- `python3 -m pytest tests/test_trust_baseline.py -q` -> `3 passed`

## Notes
- While implementing task76, task75 tests initially failed because task76 introduced an additional prompt when checksum was absent.
- Test fixtures for task75 were updated to include `.sha256` so task75 tests remain scoped to summary/`--yes` behavior, while task76 test explicitly validates missing-checksum behavior.
