# Supported Agents

Kinnoo supports multiple framework templates so you can keep your preferred agent stack and still get one consistent lifecycle (`init`, `run`, `pack`, `publish`, `install`).

Use this page to pick the right scaffold quickly and understand where behavior differs.

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

## Choosing a Framework Template

- Want full control or custom runtime logic? Start with `generic`.
- Building with OpenAI APIs? Use `chatgpt` or `openai-agents` depending on your architecture.
- Building with Anthropic or Gemini providers? Use `claude-chat` or `gemini`.
- Building graph-based orchestrations? Use `langgraph`.
- Building MCP ecosystem integrations? Use `mcp-client` or `mcp-server`.

## Naming Reference

- ChatGPT -> `chatgpt`
- OpenAI Agents -> `openai-agents`
- Gemini -> `gemini`
- Claude -> `claude-chat`
- Generic -> `generic`

## Caveats and Notes

- `openclaw` run/log behavior is partial and can depend on external OpenClaw runtime tooling.
- Registry workflows (`publish`, `install`, `list`, `search`) work with local or remote backends.
- For trust-sensitive flows, use signing plus strict flags (for example `pack --sign`, `publish --strict`, `install --strict`).
