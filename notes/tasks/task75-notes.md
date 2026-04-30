# Task98 Notes — Install summary + confirmation + --yes

## Scope implemented
- Added `--yes` / `-y` to `kinnoo install` CLI parsing.
- Added install-time summary before extraction/install with:
  - agent name and version,
  - runtime type,
  - dependency names from archive `requirements.txt`,
  - env var names from manifest `env_vars`.
- Added confirmation prompt when `--yes` is not provided:
  - `Continue with install? [y/N]:`
  - proceeds only on `y` / `yes`, otherwise aborts.
- Added safe EOF handling for non-interactive prompt reads: treat as user abort (no traceback).

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/install_command.py`
- `tests/test_trust_baseline.py`
- `tests/test_install.py` (automation compatibility with confirmation gate)
- `tests/test_cli_install.py` (automation compatibility with confirmation gate)
- `tests/test_pack_robustness.py` (automation compatibility with confirmation gate)

## Tests added (task75 mapping)
- `test126` -> `tests/test_trust_baseline.py::test_install_summary_and_confirmation_prompt`
- `test127` -> `tests/test_trust_baseline.py::test_install_yes_flag_bypasses_prompt`

## Test run results
- `python3 -m pytest tests/test_trust_baseline.py -q` -> `2 passed`
- `python3 -m pytest tests/test_trust_baseline.py tests/test_cli_install.py::test_install_delegates_to_install_command tests/test_install.py::test_install_extracts_to_user_specified_directory -q` -> passed for those selected tests.

## Notes
- A selected unrelated pack test (`tests/test_pack_robustness.py::test_kno_zip_format_is_canonical`) failed due archive path expectation mismatch in that test, not due task75 install prompt logic.
