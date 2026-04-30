# task139 notes

## Summary
- Added experimental OpenClaw run adapter gate (`--experimental-openclaw-adapter`) in CLI.
- Added `openclaw-skill` routing in run flow with version-aware backend selection.
- Implemented backend detection in health checks (`native-skills-run` for >=0.3.0, `legacy-run` for >=0.2.0).
- Added structured run diagnostics for backend category and invocation details.

## Files changed
- src/kinnoo/run_command.py
- src/kinnoo/cli.py
- src/kinnoo/health_check.py
- tests/test_cli.py

## Validation
- `python3 -m pytest tests --testmon -k test_feature66_run_adapter_backend_selection_and_gate`
