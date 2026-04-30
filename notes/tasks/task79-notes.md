# Task103 Notes — Env var exposure heuristic sweep in inspect and pack

## Scope implemented
- Added new scanner module `src/kinnoo/code_sweep.py`.
- Implemented `sweep_env_var_exposure(agent_dir: Path, declared_env_vars: list[str]) -> list[str]`.
- Scanner behavior:
  - recursively scans `*.py` under agent directory,
  - excludes files under `.venv/`,
  - matches configured heuristic patterns for `print/log/write` with `os.environ` / `os.getenv`,
  - returns warnings as `"<file>:<line>: <description>"`.

## Integration
- `kinnoo inspect` (`src/kinnoo/inspect_command.py`):
  - runs sweep for directory targets,
  - prints `Security sweep:` warning list when matches exist,
  - prints clean message when no matches:
    - `Security sweep: no env var exposure patterns detected (heuristic)`
  - prints required disclaimer:
    - `(heuristic scan — may produce false positives; not a substitute for code review)`
- `kinnoo pack` (`src/kinnoo/pack_command.py`):
  - runs sweep before packaging,
  - prints warnings to stderr when matches exist,
  - does not block packaging.

## Security handling
- Added inline invariant comment at code-sweep output sites:
  - `# [agent] SECURITY INVARIANT: only env var NAMES, never values`
- Sweep output is path/line/description only; no env var values are emitted.

## Notes
- Quick interview takeaway: this is a classic defense-in-depth pattern for agent systems—heuristic static checks as advisory guardrails plus non-blocking UX, backed by integration tests that prove both safety signaling and operational continuity

## Tests implemented
- `test132`: `tests/test_trust_baseline.py::test_inspect_security_sweep`
  - verifies clean vs dirty inspect output,
  - verifies `.venv/` exclusion,
  - verifies disclaimer output.
- `test133`: `tests/test_trust_baseline.py::test_pack_security_sweep_non_blocking`
  - verifies pack prints warnings on dirty fixture but still succeeds,
  - verifies clean fixture packs with no sweep warnings.

## Test results
- `python3 -m pytest tests/test_trust_baseline.py::test_inspect_security_sweep tests/test_trust_baseline.py::test_pack_security_sweep_non_blocking -q` -> `2 passed`
- `python3 -m pytest tests/test_trust_baseline.py -q` -> `8 passed`
