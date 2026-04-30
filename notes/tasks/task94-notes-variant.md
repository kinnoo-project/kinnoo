# Task269 Notes - Auto-wrapper generation for class-only Python agents

Date: 2026-03-23

## Scope Completed
- Implemented class-only agent detection fallback in analyzer entrypoint inference.
- Added import-time class-wrapper generation for detected class-only agents.
- Added framework-specific wrapper templates for LangChain and OpenAI Agents SDK.
- Added and ran task-mapped tests `test384` and `test385`.

## Code Changes

### 1) Analyzer class-only entrypoint detection
- Updated `src/kinnoo/analyzer.py`:
  - Added `_name_from_ast_node(...)` helper to resolve class base names from AST nodes.
  - Added `_detect_class_entrypoint(...)` fallback detector used when no standard `__main__` entrypoint is found.
  - Detection criteria:
    - known base classes (`BaseSingleActionAgent`, `BaseMultiActionAgent`, `Agent`), or
    - class name ending with `Agent` plus framework import signal (`langchain*` or `agents`).
  - Returns structured entrypoint metadata:
    - single candidate: `{entrypoint: None, entrypoint_type: class, agent_class, agent_module}` with confidence `0.60`
    - multiple candidates: `{entrypoint_type: class, candidates: [...]}` with confidence `0.40`

### 2) Import flow class-wrapper generation
- Updated `src/kinnoo/import_command.py`:
  - Added template loading/rendering helpers:
    - `_load_wrapper_template(...)`
    - `_render_wrapper_template(...)`
  - Added `_generate_class_wrapper_entrypoint(...)`:
    - writes `run.py` from selected template
    - supports force overwrite behavior aligned with import `--force`
  - Integrated into `import_agent(...)` flow:
    - when analyzer reports `entrypoint_type == class`, prompt user:
      - `Generate class-based run.py wrapper entrypoint? [y/N]:`
    - if accepted, generate wrapper and inject `entrypoint: run.py` into manifest build inputs.

### 3) Wrapper templates
- Added `src/kinnoo/wrapper_templates/langchain_wrapper.py.j2`
- Added `src/kinnoo/wrapper_templates/openai_agents_wrapper.py.j2`

These templates are intentionally minimal and runnable, focusing on syntactic validity and basic invocation behavior.

## Tests Added
- `tests/test_validator.py::test_analyzer_class_only_detection` (test384)
- `tests/test_cli_install.py::test_import_class_only_wrapper` (test385)

## Targeted Regression Run
Command:
```bash
/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests --testmon -k "test_analyzer_class_only_detection or test_import_class_only_wrapper"
```

Result:
```text
2 passed, 374 deselected
```

Manifest validation:
```bash
/Users/jerry/.pyenv/versions/3.11.12/bin/python scripts/validate_project_manifests.py
```

Result:
```text
Validation passed: manifests are consistent
```

## Teaching Notes
- **AST-first detection is safer for onboarding**: class-only agents can be recognized without executing untrusted code.
- **Confidence-tiered fallback helps UX**: returning `0.60` for a single clear class and `0.40` for multiple candidates lets import flows decide when to prompt for human confirmation.
- **Template-based wrappers are a practical bridge**: many OSS agent repos expose reusable classes, not CLI entrypoints. Wrappers translate library patterns into Kinnoo's one-shot execution contract while preserving agent code as-is.
- **Framework-specific wrappers reduce coupling**: different ecosystems (LangChain vs OpenAI Agents SDK) require different invocation semantics, so splitting templates keeps extension points clear and maintainable.
