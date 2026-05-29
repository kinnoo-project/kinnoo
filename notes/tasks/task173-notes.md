# Task 173 Notes

## Summary
- Added `kinnoo init` Go language scaffolding support for feature19 AC1-AC6.
- Implemented Go template matrix for:
	- default one-shot (`--language go`)
	- provider chat frameworks (`gemini`, `chatgpt`, `claude-chat`)
	- MCP frameworks (`mcp-server`, `mcp-client`)
- Updated init plumbing so each Go scaffold generates:
	- `main.go`
	- `go.mod`
	- coherent `kinnoo.yaml` with `runtime.language: go`
- Added a focused table-driven pytest file for test79 coverage across all six AC scenarios.
- Follow-up refactor: Go scaffolding now initializes modules with the local Go toolchain (`go mod init`) instead of writing `go.mod` from a static template.
- Added fail-fast UX when Go is missing, including OS-specific install instructions.

## Teaching Notes
- Template-matrix design scales best when split into two concerns:
	- runtime shape (`kinnoo.yaml`, entrypoint, runtime type)
	- framework payload (`main.go` content + framework README)
- For agent scaffolding, "compile-ready placeholders" are safer than SDK-bound code when credentials and SDK versions are unknown at scaffold time.
- In AI-agent projects, this is analogous to separating orchestration contract from provider adapter logic: keep the execution contract stable while providers remain swappable.
- Parameterized tests are a strong fit for acceptance-criteria matrices because each AC scenario is an explicit row with stable, contract-level assertions.

## Test Results
- `python3 -m pytest tests --testmon tests/client_cli_init/test_init_go_feature19.py -k "feature19_test79_go_init_matrix" -q`
	- Result: `6 passed, 432 deselected`
- `python3 -m pytest tests --testmon -k "feature19_test79_go_init_matrix or go_init_requires_go_toolchain" -q`
	- Result: `7 passed, 454 deselected`
- `python3 scripts/validate_project_manifests.py`
	- Result: `Validation passed: manifests are consistent`
