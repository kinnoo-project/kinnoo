# Task47 / Test70 — Platform-specific wheel warning

## What was implemented
- Updated `src/kinnoo/pack_command.py` to detect platform-specific wheel artifacts by parsing wheel filename tags.
- Added `_is_platform_specific_wheel(...)` helper that treats wheel platform tag `any` as universal and non-`any` tags as platform-specific.
- During `kinnoo pack`, added a non-fatal warning when platform-specific wheels are present:
	- `Warning: Platform-specific wheels detected; bundled wheels may not be portable across operating systems: ...`
- Warning is explicit and stable for test assertions, while archive creation remains successful.

## Test70 implementation
- Added `tests/test_pack_robustness.py::test_pack_warns_on_platform_specific_wheels`.
- Fixture includes:
	- `orjson==3.10.6` (as requested in handoff)
	- `psutil==7.0.0` (deterministic platform-wheel availability in this environment)
- Assertions verify:
	- `kinnoo pack` exits `0`,
	- portability warning text is emitted,
	- `.kno` archive is still created.

## Bug encountered and fix
- Initial test70 attempt failed because `orjson==3.10.6` wheel build failed on this environment, so no platform wheel existed to trigger the warning.
- Fix: retained `orjson` in fixture and added `psutil==7.0.0` to guarantee a platform-specific wheel is present.
- Attempts used for the same bug: `1` (within requested max of 5).

## Test runs
- `python3 -m pytest tests/test_pack_robustness.py::test_pack_warns_on_platform_specific_wheels tests/test_pack_robustness.py::test_pack_includes_transitive_wheels_for_pinned_deps tests/test_pack_robustness.py::test_pack_continues_on_per_dependency_wheel_failure`
	- Result: `3 passed`
- `python3 -m pytest tests/test_pack.py tests/test_pack_robustness.py tests/test_cli_install.py`
	- Result: `15 passed`
