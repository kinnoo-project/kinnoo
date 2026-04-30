# Task46 / Test69 — Offline install hardening and messaging

## What was implemented
- Updated `src/kinnoo/install_command.py` to support deterministic offline behavior via environment controls:
	- `KINNOO_OFFLINE=1` or `PIP_NO_INDEX=1` now signals explicit offline mode.
- Hardened fallback logic:
	- install continues to use local bundled wheels first,
	- if fallback to PyPI would be needed while offline mode is enabled, install now fails fast with actionable error messaging instead of attempting network.
- Added explicit operator-facing signal when install is fully local and network fallback is not required:
	- `[kinnoo install] Offline-ready install path used (no network fallback required).`

## Test69 implementation
- Added `tests/test_cli_install.py::test_install_offline_succeeds_with_complete_wheels`.
- Test fixture uses pinned transitive dependencies exactly per handoff:
	- `requests==2.31.0`
	- `httpx==0.27.0`
- Test flow:
	- Creates fixture agent and builds `.kno` using `kinnoo pack` (complete wheel set).
	- Runs `kinnoo install` with offline env (`PIP_NO_INDEX=1`, `KINNOO_OFFLINE=1`).
	- Asserts install succeeds, no PyPI fallback warning is emitted, and installed venv imports `requests` and `httpx`.

## Test runs
- `python3 -m pytest tests/test_cli_install.py::test_install_offline_succeeds_with_complete_wheels tests/test_cli_install.py::test_install_falls_back_to_pypi_when_wheel_missing`
	- Result: `2 passed`
- `python3 -m pytest tests/test_install.py tests/test_cli_install.py tests/test_cli_install_extract.py tests/test_cli_install_wheels.py tests/test_pack_robustness.py`
	- Result: `10 passed`
