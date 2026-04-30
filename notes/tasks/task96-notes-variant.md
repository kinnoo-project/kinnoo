# Task271 Notes - Subdirectory Entrypoint Detection Improvement

## What was implemented
- Updated `<redacted-path>` to improve Python entrypoint selection for nested projects:
  - Added depth-limited entrypoint scanning up to 4 directory levels.
  - Added deterministic candidate scoring that prioritizes:
    1. `__main__` guard presence,
    2. conventional directories (`src`, `source`, `app`, `backend`, `python-backend`, `lambda`, `lib`),
    3. conventional file names (`main.py`, `run.py`, `app.py`),
    4. shallower depth.
  - Added heuristic fallback for conventional filenames when no `__main__` guard exists.
- Updated `<redacted-path>` to set `PYTHONPATH` for Python subdirectory entrypoints by prepending:
  - agent root directory, and
  - entrypoint parent directory.

## Tests added
- `tests/test_validator.py::test_analyzer_subdirectory_entrypoint` (test388)
- `tests/test_cli_install_runnable.py::test_run_subdirectory_entrypoint` (test389)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_analyzer_subdirectory_entrypoint or test_run_subdirectory_entrypoint"
```
Result:
```text
2 passed, 376 deselected
```

## Manifest validation
Command:
```bash
python3 <redacted-path>
```
Result:
```text
Validation passed: manifests are consistent
```

## Teaching notes
- Why depth-limited scan matters:
  - Many real repos place entrypoints under `<redacted-path>, `source/`, or `backend/` paths. A shallow or unordered search can pick non-runnable helper files.
- Why weighted scoring is better than first-match:
  - A deterministic scoring function creates reproducible behavior and avoids brittle path-order dependencies from filesystem traversal.
- Why `PYTHONPATH` adjustment matters for subdirectory scripts:
  - Running `python source/main.py` makes `sys.path[0] = source/`; imports like `from source.helper import ...` require the parent directory (agent root) to be importable.
- Interview angle (AI <redacted-path>):
  - This is a classic "convention-over-configuration" tradeoff. Smart defaults reduce user friction, but deterministic fallback logic and confidence metadata keep behavior debuggable.
