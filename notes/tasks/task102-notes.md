# Task278 Notes - Streamlit/Gradio UI Agent Support

## What was implemented
- Updated `<redacted-path>`:
  - Added framework detection patterns for `streamlit` and `gradio` imports.
- Updated `<redacted-path>`:
  - For detected Streamlit/Gradio frameworks, force `runtime.type: daemon`.
  - For Streamlit, set `runtime.run_command: streamlit run <entrypoint>`.
  - For UI frameworks, set `inputs.required: false` by default (UI apps are not CLI input-driven).
  - Added manifest serialization for `runtime.run_command`.
- Updated `<redacted-path>`:
  - Added `runtime.run_command` to optional schema fields and type enforcement.
- Updated `<redacted-path>`:
  - Added support for `runtime.run_command` overrides via shell-like tokenization (`shlex.split`).
  - Added `{entrypoint}` token replacement support in custom runtime commands.
  - Skipped Python venv bootstrap when custom `runtime.run_command` is configured.

## Tests added
- `tests/test_validator.py::test_streamlit_detection` (test402)
- `tests/test_validator.py::test_gradio_detection` (test403)
- `tests/test_cli.py::test_streamlit_import_daemon` (test404)
- `tests/test_cli.py::test_streamlit_run_command` (test405)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_streamlit_detection or test_gradio_detection or test_streamlit_import_daemon or test_streamlit_run_command"
```
Result:
```text
4 passed, 390 deselected
```

## Teaching notes
- Why `runtime.run_command` is useful:
  - Some frameworks are launched by framework CLIs (`streamlit run`) rather than `python <entrypoint>`; storing that explicitly in manifest preserves execution intent.
- Why daemon runtime for UI apps:
  - Streamlit/Gradio host long-running web servers and should not be treated as one-shot jobs.
- Interview angle (agent platform design):
  - This is contract-driven runtime orchestration: static framework inference informs deployment mode and execution command, reducing manual ops configuration.
