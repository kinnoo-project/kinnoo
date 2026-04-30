# Task274 Notes - Async Entrypoint and Hardcoded Input Detection

## What was implemented
- Updated `src/kinnoo/analyzer.py`:
  - Added `_detect_inputs_required()` to infer whether user input is required:
    - `True` when parameterized input signals are detected (`sys.argv`, `argparse`, `input()`).
    - `False` when hardcoded literal input is detected in `run` / `run_sync` call arguments.
  - Added `_detect_async_entrypoint()` to infer async entrypoint signals (`async def`, `asyncio.run(...)`).
  - Registered new inferred fields in analyzer output:
    - `inputs_required`
    - `async_entrypoint`
- Updated `src/kinnoo/import_command.py`:
  - Manifest generation now writes `inputs.required` based on analyzer inference.
  - Defaults to `required: true` when confidence/data is insufficient.

## Tests added
- `tests/test_validator.py::test_analyzer_input_detection` (test394)
- `tests/test_cli_install.py::test_import_input_detection_yaml` (test395)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_analyzer_input_detection or test_import_input_detection_yaml"
```
Result:
```text
2 passed, 382 deselected
```

## Manifest validation
Command:
```bash
python3 scripts/validate_project_manifests.py
```
Result:
```text
Validation passed: manifests are consistent
```

## Teaching notes
- Why split `inputs.type` and `inputs.required`:
  - `type` captures input shape (text/json/etc), while `required` captures whether caller input is needed at all. They answer different runtime questions.
- Why hardcoded-input detection matters:
  - Many demo agents run with embedded prompts. Setting `inputs.required=false` avoids forcing meaningless CLI arguments and improves UX.
- Why async detection can be informational first:
  - Detecting async patterns is useful for diagnostics/planning even when runtime execution does not need special handling yet.
- Interview angle (AI agent tooling):
  - This is lightweight static semantic analysis: infer interface contract from code intent (parameterized vs embedded prompt), then project it into machine-readable manifest metadata.
