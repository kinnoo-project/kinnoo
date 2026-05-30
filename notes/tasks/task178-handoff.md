# Task 178 SWE Handoff - Allow Existing Directory and "." Target

## Task Linkage
- Task: task178
- Feature: feature20 (AC1)
- Primary test: test84

## What To Implement
- Remove the `FileExistsError` raise in `init_agent()` when `agent_dir.exists()` is True.
- Instead, just proceed with scaffolding (skip mkdir if it already exists, use `exist_ok=True`).
- When `agent_name` is ".", resolve it to mean "init in the current working directory" — i.e., `agent_dir = target_dir` rather than `target_dir / "."`.
- In cli.py, the `NAME_PATTERN` regex may reject ".". Add a special case to allow "." before the regex check, and resolve it to the directory name for display purposes.

## Files Expected
- src/kinnoo/init_command.py
- src/kinnoo/cli.py
- tests/client_cli_init/test_init_feature20.py

## Acceptance Mapping
- AC1: kinnoo init succeeds on existing dirs and with "." target.

## Design Notes
- When "." is used, the agent_dir should be target_dir itself (i.e., `Path.cwd()`).
- The manifest `name` field should use the directory name (e.g., `Path.cwd().name`).
- Keep backward compat: if dir doesn't exist, still create it as before.
