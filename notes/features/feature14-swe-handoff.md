# Feature 95 — SWE Handoff: Getting Started & Registry Guides

## Context
Create two user-facing guides: a getting-started tutorial and a registry workflow guide.

## Files to Create
- `docs/getting-started.md` — Walk through: install kinnoo, init agent, pack, run
- `docs/registry-guide.md` — Walk through: login, publish, search, install from registry

## Getting Started Guide Structure
1. Prerequisites (Python 3.11+, pip)
2. Install kinnoo (`pip install kinnoo`)
3. Create your first agent (`kinnoo init my-agent --framework chatgpt`)
4. Configure the agent (edit kinnoo.yaml, add API key)
5. Run locally (`kinnoo run my-agent "hello"`)
6. Pack for distribution (`kinnoo pack my-agent`)
7. Next steps → link to registry guide

## Registry Guide Structure
1. Create an account (invite-only process)
2. Login (`kinnoo login`)
3. Publish (`kinnoo publish my-agent --remote`)
4. Search (`kinnoo search chatgpt --remote`)
5. Install (`kinnoo install my-agent --remote`)
6. Run installed agent (`kinnoo run my-agent "test"`)
7. Signing and verification (`kinnoo keygen`, `kinnoo pack --sign`, `kinnoo install --strict`)

## Implementation Notes
- Include copy-paste commands with expected output
- Focus on the invite-only beta workflow
- Cross-reference from README.md

## Dependencies
- None

## Acceptance Criteria Summary
1. docs/getting-started.md with complete walkthrough
2. docs/registry-guide.md with publish/install workflow
3. Both include terminal commands and expected output
