# Task 182 SWE Handoff - Skip Creation of Existing Directories

## Task Linkage
- Task: task182
- Feature: feature20 (AC5)
- Primary test: test88

## What To Implement
- When creating scaffold directories (tools/, prompts/, evals/, tests/, data/), use `mkdir(exist_ok=True)` instead of bare `mkdir()`.
- This ensures that if a directory already exists (common in existing repos), it is left untouched.
- Also apply to OpenClaw-specific directories (skills/, memory/).

## Files Expected
- src/kinnoo/init_command.py
- tests/client_cli_init/test_init_feature20.py

## Acceptance Mapping
- AC5: Existing directories not overwritten.

## Design Notes
- The current code uses `(agent_dir / folder_name).mkdir()` in a loop — just add `exist_ok=True`.
- For OpenClaw `skills/` and `memory/`, same treatment.
