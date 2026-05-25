# Task 173 SWE Handoff - Go Init Scaffolding

## Task Linkage
- Task: task173
- Feature: feature19 (AC1-AC6)
- Primary test: test79

## What To Implement
- Add init support for --language go.
- Add Go one-shot default template with main.go entrypoint.
- Add Go templates for:
  - --framework gemini
  - --framework chatgpt
  - --framework claude-chat
  - --framework mcp-server
  - --framework mcp-client
- Ensure generated kinnoo.yaml manifests are valid for each combination.

## Files Expected
- src/kinnoo/cli.py
- src/kinnoo/init_command.py
- src/kinnoo/templates.py
- src/kinnoo/template_catalog.py
- tests/client_cli_init/

## Acceptance Mapping
- AC1: go default scaffold created with main.go + runtime.language go.
- AC2-AC4: provider chat templates generated with compile-ready placeholders.
- AC5-AC6: mcp server/client templates generated and valid.

## Implementation Notes
- Keep existing language/framework behavior backward compatible.
- Use deterministic template text for tests.
- Avoid requiring API keys at scaffold time.
- Generated Go code should compile after users fill placeholder env vars.

## Done Definition
- test79 automated test(s) added/updated and passing.
- task173 status moved to needs-review.
- Teaching notes added to notes/tasks/task173-notes.md.
