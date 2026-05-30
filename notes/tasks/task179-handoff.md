# Task 179 SWE Handoff - Skip .gitignore Creation

## Task Linkage
- Task: task179
- Feature: feature20 (AC2)
- Primary test: test85

## What To Implement
- Remove all `.gitignore` file writes from `init_agent()`.
- This includes the Python, JavaScript, TypeScript, Go, and OpenClaw `.gitignore` writes.
- The gitignore template strings can remain defined (they may be used elsewhere in future), but should NOT be written.

## Files Expected
- src/kinnoo/init_command.py
- tests/client_cli_init/test_init_feature20.py

## Acceptance Mapping
- AC2: No .gitignore created by kinnoo init.

## Design Notes
- In the `if not minimal:` block, remove the `(agent_dir / ".gitignore").write_text(...)` line.
- In the openclaw block, remove the `.gitignore` write as well.
