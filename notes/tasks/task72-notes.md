# Task94 — Implement env vars preflight resolution check

## Summary
- Added preflight env-var resolvability check in `<redacted-path>`.
- Preflight now reuses feature10-style resolution order (`environment` -> `agent .env`) and never prompts for values.
- Output is names-only and deterministic: declared/resolved variable names and missing variable names are shown, but no secret values are printed.
- Preflight returns non-zero when any declared `env_vars` are unresolved.

## Test122 implementation
- Added `tests/test_run_preflight.py::test_preflight_env_vars_resolution_and_secret_safety`.
- Test covers:
	- resolved case (`REDACTED_ENV_VAR` from environment + `DB_KEY` from `.env`) passes,
	- unresolved case (`REDACTED_ENV_VAR`) fails with actionable guidance,
	- secret values in env and `.env` do not appear in output.

## Commands and results
- `python3 -m pytest tests/test_run_preflight.py -q` -> `3 passed`
