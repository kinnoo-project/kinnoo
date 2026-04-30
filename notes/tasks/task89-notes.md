# Task116 Notes - InputGuard protocol, models, and factory

## Scope implemented
- Created foundational input safety guard module with pluggable architecture.
- Added result model dataclasses and threat category constants.
- Added protocol contract and default guard factory.
- Added task89 tests for model structure and factory protocol compatibility.

## Implementation details
- Added new file `<redacted-path>` with:
  - constants:
    - `SQL_INJECTION`
    - `SHELL_INJECTION`
    - `PATH_TRAVERSAL`
    - `SSRF`
    - `XSS`
    - `TEMPLATE_INJECTION`
  - dataclasses:
    - `InputWarning(threat_category, description, param_name=None)`
    - `InputGuardResult(safe, warnings)`
  - protocol:
    - `InputGuard.check(value, input_type="text") -> InputGuardResult`
    - `InputGuard.check_inputs(inputs) -> InputGuardResult`
  - placeholder implementation:
    - `RegexInputGuard.check(...)` returns safe result with no warnings
    - `RegexInputGuard.check_inputs(...)` delegates through `check(...)`
  - factory:
    - `get_default_guard() -> InputGuard` returning `RegexInputGuard()`

## Tests implemented
- Added new test file `tests/test_input_guard.py` with:
  - `test_result_models_structure` (test149)
  - `test_get_default_guard_protocol_contract` (test150)

## Validation runs
- `python3 -m pytest tests/test_input_guard.py -q` -> `2 passed`
- `python3 -m pytest tests/test_input_guard.py tests/test_cli_install.py::test_install_missing_archive_prints_usage tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q` -> `4 passed`
- `python3 -m pytest -q` -> `142 passed, 1 skipped`

## Follow-up fix captured during validation
- Updated `tests/test_cli_install.py::test_install_missing_archive_prints_usage` usage expectation to match current install usage contract that supports archive path or registry selector.

## Teaching notes
- Protocol-first design is a clean way to future-proof security components: callers depend on behavior (`check`, `check_inputs`) rather than concrete implementation (`RegexInputGuard`). This enables low-friction replacement with ML-based guards later.
- Defining stable result models (`InputGuardResult`, `InputWarning`) early gives you a durable contract for CLI/UI rendering, analytics, and test assertions even as detection logic evolves.
- Placeholder implementations are useful for phased delivery: task89 establishes architecture and test scaffolding; task90 can iterate detection depth without changing integration points.
