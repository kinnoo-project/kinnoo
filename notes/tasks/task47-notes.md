## task47 - subprocess env var injection coverage

- Confirmed runtime path in `<redacted-path>` already merges resolved declared env vars into subprocess env via `subprocess_env.update(resolved_env_vars)` and passes `env=subprocess_env` to `subprocess.Popen(...)`.
- Added `test_resolved_env_vars_injected_into_subprocess` in `tests/test_cli_env_vars.py` (test81).
- test81 validates injection success for all resolution paths:
	- process environment
	- agent-local `.env`
	- masked prompt fallback
- Security guardrail included: asserts sentinel secret values do not appear in captured output for each path.
- Validation run:
	- `python3 -m pytest tests/test_cli_env_vars.py -k "env_vars or prompt or injected or secret"` -> 6 passed
