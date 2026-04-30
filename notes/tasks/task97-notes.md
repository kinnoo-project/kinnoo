# Task272 Notes - Requirements Auto-Inference from Python Imports

## What was implemented
- Added curated import-to-PyPI mapping in `src/kinnoo/analyzer.py` as `IMPORT_TO_PYPI`.
- Added `_infer_requirements(project_dir)` in analyzer to infer dependencies from imports while excluding:
  - standard library modules (`sys.stdlib_module_names` or fallback set), and
  - local project modules.
- Updated dependency detector fallback in analyzer to use `_infer_requirements`.
- Updated `src/kinnoo/import_command.py` so when `requirements.txt` is missing and inferred dependencies exist, import flow prompts:
  - `No requirements.txt found. Generate one from inferred imports? [Y/n]`

## Tests added
- `tests/test_validator.py::test_analyzer_requirements_inference` (test390)
- `tests/test_cli_install.py::test_import_infer_requirements` (test391)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_analyzer_requirements_inference or test_import_infer_requirements"
```
Result:
```text
2 passed, 378 deselected
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
- Why map imports to package names:
  - Python import names and PyPI package names often differ (`pydantic_ai` -> `pydantic-ai`, `langchain_core` -> `langchain-core`), so explicit mapping avoids invalid `requirements.txt` content.
- Why exclude stdlib/local modules:
  - Requirement inference should capture installable third-party deps only. Including stdlib/local names creates noisy or broken dependency lists.
- Why prompt before generating:
  - Inference is heuristic. A quick human confirmation keeps onboarding fast while preserving user control over dependency files.
- Interview angle (AI platform tooling):
  - This is a practical static-analysis pipeline: parse code -> normalize symbols -> apply mapping -> remove false positives -> produce actionable artifact.
