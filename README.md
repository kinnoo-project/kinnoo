# Kinnoo 🍊


![Status: Beta](https://img.shields.io/badge/status-beta-blue)
![Release](https://img.shields.io/badge/release-v0.10.0-yellow)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

Kinnoo is a unified platform that allows **AI agent developers** to create, package and share AI agents, which **agent end-users** can install and run on a local machine.
 
[Website](https://kinnoo.ai) · [Docs](https://github.com/kinnoo-project/kinnoo/tree/main/docs/README.md) · [Getting Started](https://github.com/kinnoo-project/kinnoo/blob/main/docs/getting-started.md)

## What Kinnoo Is

- Strong **lifecycle** harness: `init`, `test`, `pack`, `publish`, `fetch`, `install`, `inspect`, `run` - all within the same CLI.
- Strong **contract** harness: `kinnoo.yaml` provides a framework-agnostic manifest with validation and predictable runtime expectations.
- Strong **trust** harness: integrity verification, optional signing, strict trust gates, and inspection-first workflows before install/run.
- Strong **distribution** harness: registry auth, publish/search/list/install flows, and versioned artifact distribution for teams.
- Framework **portability**: build and ship agents across common agent frameworks with consistent packaging and operator UX.

## What Kinnoo Is Not

- Not a foundation model or model-hosting service.
- Not a replacement for framework-level design and orchestration (planner logic, tool routing, memory/retrieval strategy).
- Not a UI-only chatbot builder; Kinnoo focuses on CLI-runnable agent lifecycle workflows.
- Not a guarantee of agent quality by itself; it gives reproducibility and trust controls and provides a framework for running tests on your agents, but evaluation quality still depends on your tests and runtime design.

## Installation and Quick Start

To **install** the Kinnoo CLI:
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install kinnoo
```

To **create and publish** an agent to the Kinnoo registry:
```bash
kinnoo init chatgpt my-chat-agent
kinnoo pack my-chat-agent
export KINNOO_REGISTRY_URL=https://api.kinnoo.ai
kinnoo login
kinnoo publish my-chat-agent --pack --strict --remote
```

To **install and run** an agent from the registry:
```bash
kinnoo install kinnootest/test-chat-agent
kinnoo run test-chat-agent 'what is 2+2?'
```

See [Getting Started](https://github.com/kinnoo-project/kinnoo/blob/main/docs/getting-started.md) for more details.

## Supported Frameworks

Kinnoo currently supports initializing and running agents for these frameworks:

- vanilla python (generic)
- vanilla javascript / typescript (generic)
- chatgpt
- gemini
- claude-chat
- pydantic-ai
- langgraph
- openai-agents
- mcp-client
- openclaw

See [Supported Agents](https://github.com/kinnoo-project/kinnoo/blob/main/docs/supported-agents.md) for more details.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` for development and contribution workflow.

## License

MIT (`LICENSE`).
