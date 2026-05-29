# Test 79 Test-Agent Handoff - Go Init Matrix

## Covers
- feature19 AC1, AC2, AC3, AC4, AC5, AC6

## Contract To Validate
- kinnoo init supports --language go with:
  - no framework
  - gemini/chatgpt/claude-chat
  - mcp-server/mcp-client
- Each generated scaffold includes expected Go files and valid kinnoo.yaml.

## Test Design Guidance
- Prefer table-driven parametrized tests for the matrix.
- Assert stable contracts only:
  - runtime.language == go
  - entrypoint == main.go for source templates
  - framework-specific file markers and placeholders
- Avoid brittle full-file snapshot comparisons.

## Execution Guidance
- Run focused regression tests for task173 only.
- Use python3 -m pytest tests --testmon with a selector that targets the new test file.
- Keep assertions deterministic and platform-neutral.
