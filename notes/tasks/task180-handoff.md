# Task 180 SWE Handoff - Rename README.md to README.kinnoo.md

## Task Linkage
- Task: task180
- Feature: feature20 (AC3)
- Primary test: test86

## What To Implement
- Change all instances of `(agent_dir / "README.md").write_text(...)` to `(agent_dir / "README.kinnoo.md").write_text(...)`.
- This applies to all framework branches and the default no-framework branch.

## Files Expected
- src/kinnoo/init_command.py
- tests/client_cli_init/test_init_feature20.py

## Acceptance Mapping
- AC3: README.kinnoo.md created instead of README.md.

## Design Notes
- Simple find/replace of the filename in all write_text calls for README.
- The content stays the same; only the filename changes.
