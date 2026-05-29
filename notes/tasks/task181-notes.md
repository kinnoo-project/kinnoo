# Task 181 Post-Implementation Notes

## Summary
Moved entrypoint files into a `src/` subdirectory within the agent directory.

## Key Changes
- Added `(agent_dir / "src").mkdir(exist_ok=True)` before writing entrypoints.
- Changed all entrypoint writes from `agent_dir / filename` to `agent_dir / "src" / filename`.
- Updated manifest `entrypoint` field to use `src/` prefix (e.g., `src/main.py`).
- For templates with hardcoded entrypoint (KINNOO_YAML_TEMPLATE, MCP_SERVER), used string replace post-format.
- For Go, `go.mod` stays at agent_dir root; only `main.go` moves to `src/`.

## Teaching Notes
- The manifest entrypoint field is the source of truth for where the runtime should look for the entry file.
- When using string templates with hardcoded paths, prefer post-format replacement over modifying shared templates.
