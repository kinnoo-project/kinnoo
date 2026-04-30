# task143 notes

## Summary
- Added framework adapter architecture under src/kinnoo/framework_adapters with baseline adapters for langchain, langgraph, and openai.
- Added import CLI support for framework-aware mode via `kinnoo import --from langchain|langgraph|openai`.
- Integrated adapter merge flow into import command so adapter overrides update inferred fields and confidence metadata.
- Added deterministic fallback to generic analyzer output when adapter coverage is insufficient.
- Added regression test tests/test_cli_import.py::test_feature75_adapter_inference_and_fallback.

## Teaching Notes
- Adapter design works best when adapters only add or raise-confidence fields, while generic analysis remains the safe baseline fallback.
- Deterministic fallback messaging is important for operator trust: users should always know whether they are seeing adapter output or generic output.
- Keeping adapter merge logic separate from detector logic makes it easier to evolve adapters without destabilizing core analyzer behavior.

## Validation
- python3 -m pytest tests --testmon -k test_feature75_adapter_inference_and_fallback
