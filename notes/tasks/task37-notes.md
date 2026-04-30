# Task45 / Test68 — Install fallback to PyPI for missing wheels

## What was implemented
- Updated `src/kinnoo/install_command.py` to detect missing bundled wheels for requirements before dependency installation.
- Added explicit fallback behavior for install:
	- first attempts local wheel-only install using `pip install --no-index --find-links <wheels> -r requirements.txt`,
	- if required wheels are missing or local install fails, falls back to `pip install -r requirements.txt` from PyPI.
- Added stable user-facing warnings when fallback happens, including explicit internet requirement messaging.
- Preserved backward compatibility for existing wheel-only archives with empty `requirements.txt` by continuing legacy direct wheel install attempts.

## Test68 implementation
- Added `tests/test_cli_install.py::test_install_falls_back_to_pypi_when_wheel_missing`.
- Test flow:
	- Creates a valid `.kno` fixture with `requirements.txt` pinned to `requests==2.31.0`.
	- Builds wheels, removes the `requests` wheel from the archive to force fallback.
	- Runs `kinnoo install` and asserts:
		- install exits `0`,
		- warning indicates missing packaged wheel and PyPI fallback,
		- installed virtualenv can import `requests` successfully.

## Test runs
- `python3 -m pytest tests/test_cli_install.py::test_install_falls_back_to_pypi_when_wheel_missing tests/test_cli_install.py::test_install_delegates_to_install_command`
	- Result: `2 passed`
- `python3 -m pytest tests/test_install.py tests/test_cli_install.py tests/test_cli_install_extract.py tests/test_cli_install_wheels.py`
	- Initial run: `1 failed, 5 passed` (`test_install_creates_venv_and_attempts_wheel_install` expected legacy wheel-only behavior with empty requirements)
	- Fix applied: restored legacy wheel-only install path for empty requirements.
	- Re-run result: `6 passed`
