# Task276 Notes - PydanticAI deps_type Detection and JSON Inputs

## What was implemented
- Updated `<redacted-path>`:
  - Added `_extract_pydanticai_deps_signature()` to detect `Agent(deps_type=...)` usage in PydanticAI code.
  - Added `_detect_pydanticai_deps_type()` detector and exposed it as inferred field `deps_type`.
    - Returned shape: `{class_name: <deps class>, fields: [<field names>]}`.
  - Updated `_detect_input_type()` to infer `inputs.type = json` when `deps_type` is detected.
- Updated `<redacted-path>`:
  - Manifest generation now enforces `inputs.type: json` when analyzer reports a `deps_type` class.

## Tests added
- `tests/test_validator.py::test_analyzer_pydanticai_deps` (test398)
- `tests/test_cli_install_runnable.py::test_run_json_input_pydanticai` (test399)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_analyzer_pydanticai_deps or test_run_json_input_pydanticai"
```
Result:
```text
2 passed, 386 deselected
```

## Teaching notes
- Why infer JSON for deps injection:
  - `deps_type` represents structured dependency context, so scalar text input is a poor default.
  - Mapping to `inputs.type=json` aligns CLI contract with the runtime object shape expected by PydanticAI patterns.
- Why capture class + fields:
  - Class name gives a stable contract anchor (`MyDeps`), and fields provide explainable evidence for analyzer output.
- Interview angle (agentic systems):
  - This is an example of static contract extraction: infer agent invocation schema from source AST and project it into deployment/runtime metadata.
