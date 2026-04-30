# Task100 Notes — Run trace logging

## Scope implemented
- Added run trace log writing to `~/.kinnoo/logs/run.<TIMESTAMP>.log` after non-preflight `kinnoo run` completion/failure.
- Implemented UTC-only timestamps:
  - filename: `run.YYYY-MM-DDTHH-MM-SSZ.log`
  - JSON field: `YYYY-MM-DDTHH:MM:SSZ`
- Log payload is restricted to safe fields only:
  - `timestamp`, `agent_name`, `agent-version`, `runtime_type`, `exit_code`
- Added best-effort behavior:
  - create `~/.kinnoo/logs/` if needed,
  - print warning to stderr on log directory/file write failure,
  - never crash run flow due to logging failures.

## Security handling
- Added inline security invariant comment at log write site:
  - `# [agent] SECURITY INVARIANT: only env var NAMES, never values.`
- Logging code does not include input content, env var values, stdout, or stderr.

## Files changed
- `<redacted-path>`
- `tests/test_trust_baseline.py`
- `TASKS.txt`

## Tests implemented for task77
- `test129` -> `tests/test_trust_baseline.py::test_run_trace_log_safe_fields`
- `test130` -> `tests/test_trust_baseline.py::test_run_trace_log_no_secrets`

## Test results
- `python3 -m pytest tests/test_trust_baseline.py -q` -> `5 passed`
- `python3 -m pytest tests/test_cli.py::test_run_entrypoint_with_input tests/test_cli.py::test_run_exit_code -q` -> `2 passed`
