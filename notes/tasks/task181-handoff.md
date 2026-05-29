# Task 181 SWE Handoff - Move Entrypoint to src/ Subdirectory

## Task Linkage
- Task: task181
- Feature: feature20 (AC4)
- Primary test: test87

## What To Implement
- Create `agent_dir / "src"` directory (with exist_ok=True) before writing entrypoint files.
- Write entrypoint files (main.py, index.js, index.ts, main.go) to `agent_dir / "src" / filename` instead of `agent_dir / filename`.
- Update the kinnoo.yaml manifest `entrypoint` field to include the `src/` prefix (e.g., `src/main.py`).
- For Go, `main.go` moves to `src/main.go`, but `go.mod` stays at `agent_dir` root.
- For OpenClaw, `index.mjs` should also move to `src/index.mjs`.

## Files Expected
- src/kinnoo/init_command.py
- tests/client_cli_init/test_init_feature20.py

## Acceptance Mapping
- AC4: Entrypoint inside src/ subdirectory.

## Design Notes
- The `entrypoint_name` variable becomes `src/{entrypoint_name}` in the manifest.
- When writing the file, use `(agent_dir / "src" / entrypoint_name).write_text(...)`.
- The _standardize_readme function receives the updated entrypoint path with src/ prefix.
- Go module init still uses `agent_dir` as cwd (go.mod at root level).
