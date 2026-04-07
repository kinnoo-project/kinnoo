# Kinnoo

![Status: Beta](https://img.shields.io/badge/status-beta-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)


Kinnoo is a CLI-first platform for packaging, sharing, and installing AI agents with explicit manifest and trust controls.

It is designed for AI agent developers who need reproducible archive workflows (`.kno`), local execution, and registry-based distribution.

## Why Kinnoo

- Agent manifest contract (`kinnoo.yaml`) with validation.
- Local scaffold, run, test, inspect, pack, and install workflows.
- Registry login/publish/search/install workflows.
- Integrity and signature-aware trust flags for install and publish paths.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install kinnoo
```

## Quick Start

```bash
kinnoo init --framework chatgpt my-agent
kinnoo run ./my-agent "hello"
kinnoo pack ./my-agent
kinnoo login
kinnoo publish ./my-agent --pack --remote
```


## License

Kinnoo is licensed under the [Apache License 2.0](LICENSE).

## Documentation

- `docs/getting-started.md`
- `docs/registry-guide.md`
- `docs/kinnoo-yaml-spec.md`
- `docs/cli-reference.md`
- `docs/security-model.md`
- `docs/supported-agents.md`

## Supported Frameworks

Kinnoo currently scaffolds and runs agent templates for these framework families:

- generic (no framework)
- chatgpt
- gemini
- claude-chat
- pydantic-ai
- langgraph
- openai-agents
- mcp-client
- mcp-server
- openclaw

See `docs/supported-agents.md` for capability matrix details.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` for development and contribution workflow.

## License

MIT (`LICENSE`).
