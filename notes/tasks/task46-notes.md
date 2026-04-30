## task46 - masked prompt fallback and cancel handling

- Implemented masked prompt fallback in `<redacted-path>` using `getpass.getpass()` for unresolved declared `env_vars` after environment and `.env` checks.
- Added cancel/decline handling for prompt path (`KeyboardInterrupt` / `EOFError` or empty input) with error output that includes only the variable name.
- Added tests in `tests/test_cli_env_vars.py`:
	- `test_missing_env_var_uses_masked_prompt` (test80)
	- `test_prompt_cancel_aborts_with_missing_var_name` (test82)
- Security guardrail verified: sentinel secret values are not printed in stdout/stderr in prompt path tests.
- Validation run:
	- `python3 -m pytest tests/test_cli_env_vars.py -k "env_vars or prompt or secret"` -> 5 passed
