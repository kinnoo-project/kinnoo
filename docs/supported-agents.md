# Supported Agents

This document summarizes currently supported framework templates and core lifecycle capabilities.

## Scope

- Matrix reflects current CLI behavior.
- "Yes" means available in normal workflows.
- "Partial" means available with caveats documented below.

## Capability Matrix

| Framework | Init scaffold | Pack | Run | Publish | Install |
| --- | --- | --- | --- | --- | --- |
| generic | Yes | Yes | Yes | Yes | Yes |
| chatgpt | Yes | Yes | Yes | Yes | Yes |
| gemini | Yes | Yes | Yes | Yes | Yes |
| claude-chat | Yes | Yes | Yes | Yes | Yes |
| pydantic-ai | Yes | Yes | Yes | Yes | Yes |
| langgraph | Yes | Yes | Yes | Yes | Yes |
| openai-agents | Yes | Yes | Yes | Yes | Yes |
| mcp-client | Yes | Yes | Yes | Yes | Yes |
| mcp-server | Yes | Yes | Yes | Yes | Yes |
| openclaw | Yes | Yes | Partial | Yes | Yes |

## Notes

- Naming alignment for common labels:
	- ChatGPT -> `chatgpt`
	- OpenAI -> `openai-agents`
	- Gemini -> `gemini`
	- Claude -> `claude-chat`
	- Generic -> `generic`

- `openclaw` run/log flows use delegated wrapper behavior and may require external OpenClaw runtime tooling.
- Registry operations (`publish`, `install`, `list`, `search`) can run in local/mock mode or configured remote mode.
- Trust-sensitive operations are available through existing flags such as `--strict` and archive signing workflows.
