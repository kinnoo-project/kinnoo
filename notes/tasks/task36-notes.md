# Task44 / Test67 — Non-fatal wheel build warnings

## What was implemented
- Updated `src/kinnoo/pack_command.py` so wheel builds run per dependency instead of one all-or-nothing `pip wheel -r` invocation.
- Individual dependency wheel failures are now non-fatal:
	- emits a warning naming the failed dependency,
	- continues packaging,
	- still returns success when archive creation succeeds.
- Added recording for downstream install handling:
	- writes failed dependency specs to `wheels/missing_wheels.txt` inside the `.kno` archive.

## Test67 implementation
- Added `tests/test_pack_robustness.py::test_pack_continues_on_per_dependency_wheel_failure`.
- Test fixture uses:
	- valid pinned dependency: `requests==2.31.0`
	- intentionally invalid dependency: `nonexist-pkg-kinnoo-test==0.0.1`
- Assertions cover AC3 behavior:
	- `kinnoo pack` exits `0`,
	- warning includes failed dependency name,
	- archive is created,
	- `wheels/missing_wheels.txt` exists and lists failed dependency.

## Test runs
- `python3 -m pytest tests/test_pack_robustness.py::test_pack_continues_on_per_dependency_wheel_failure tests/test_pack_robustness.py::test_pack_includes_transitive_wheels_for_pinned_deps tests/test_pack_robustness.py::test_kno_zip_format_is_canonical`
	- Result: `3 passed`
- `python3 -m pytest tests/test_pack.py tests/test_pack_robustness.py`
	- Result: `10 passed`
