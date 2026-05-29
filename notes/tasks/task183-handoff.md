# Task 183 SWE Handoff - Intelligently Merge Dependencies

## Task Linkage
- Task: task183
- Feature: feature20 (AC6)
- Primary test: test89

## What To Implement
- Before writing requirements.txt: check if it already exists. If so, read existing lines, determine which kinnoo-required packages are missing, and append only those.
- Before writing package.json: check if it already exists. If so, parse existing JSON, merge new dependencies into the `dependencies` field without overwriting existing entries, and write back.
- For Go: the existing `go mod init` + `go mod edit -require` flow already handles incremental deps correctly, so no change needed for Go.

## Files Expected
- src/kinnoo/init_command.py
- tests/client_cli_init/test_init_feature20.py

## Acceptance Mapping
- AC6: Dependencies appended to existing files, not overwritten.

## Design Notes
- For requirements.txt: parse line-by-line, extract package names (strip version specifiers), and only append new lines for packages not already present.
- For package.json: use `json.loads()` / `json.dumps()` with the existing content. Merge `dependencies` dict — existing entries take precedence (don't downgrade versions).
- Handle edge cases: empty files, malformed files (fallback to overwrite with warning).
