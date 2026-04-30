# Task118 Notes - CLI --no-guard and run_command integration

## Scope implemented
- Added `--no-guard` flag to `kinnoo run` CLI.
- Wired `--no-guard` through CLI dispatch into runtime execution (`run_agent`).
- Integrated input safety guard evaluation into `run_agent(...)` after env-var resolution and before entrypoint execution.
- Added integration tests for all task91 scenarios (`test160`-`test163`).

## Code changes

### 1) CLI flag and dispatch wiring
- Updated `<redacted-path>`:
  - Added run-subparser argument:
    - `--no-guard` (store_true)
  - Updated pre-parse run usage guard to avoid false usage on `--no-guard` invocations.
  - Passed `no_guard=bool(getattr(args, "no_guard", False))` to `run_agent(...)`.

### 2) Runtime guard integration
- Updated `<redacted-path>`:
  - Extended `run_agent` signature with `no_guard: bool = False`.
  - Inserted guard block after:
    - env-var resolution and
    - forbidden trace-value extension,
    and before entrypoint path/python execution.
  - Behavior implemented:
    - If `no_guard` is true: skip guard completely.
    - If unsafe input detected:
      - print warning header + category messages to stderr,
      - interactive stdin (`isatty=True`): prompt `Proceed anyway? [y/N]:`
        - proceed only when response is exactly `y` (lowercased)
        - otherwise abort with non-zero
      - non-interactive stdin: abort with message
        - `Non-interactive mode: aborting due to input safety warning.`

## Tests implemented
- Added new file `tests/test_input_guard_integration.py` with:
  - `test_no_guard_flag_skips_check` (test160)
  - `test_malicious_input_abort_on_reject` (test161)
  - `test_malicious_input_proceed_on_accept` (test162)
  - `test_non_interactive_auto_aborts` (test163)

### Testing approach details
- Used `python <redacted-path> ...` path-based CLI invocation per project test convention.
- Used a PTY-backed helper for interactive prompt simulation so `sys.stdin.isatty()` is true in reject/accept scenarios.
- Used `stdin=subprocess.DEVNULL` to assert non-interactive auto-abort behavior.

## Validation results
- `python3 -m pytest tests/test_input_guard_integration.py -q` -> `4 passed`
- `python3 -m pytest -q` -> `155 passed, 1 skipped`

## Teaching notes
- **Safety UX pattern:** This design uses a soft gate (warn + confirm) rather than hard reject, which is a practical risk-balancing pattern for developer tooling where false positives are expected.
- **CI-safe behavior:** Non-interactive auto-abort is a strong default for unattended pipelines. The explicit `--no-guard` flag creates a deliberate and auditable escape hatch.
- **Agentic AI perspective:** This mirrors layered governance in AI systems:
  1. fast deterministic policy checks (regex guard),
  2. human-in-the-loop override in interactive contexts,
  3. explicit policy bypass for trusted automation contexts.
  This layered control model is common in production agent platforms before adding model-based classifiers.
