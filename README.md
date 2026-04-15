# Kinnoo

![Status: Beta](https://img.shields.io/badge/status-beta-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

Kinnoo is a CLI-first platform for packaging, sharing, and installing AI agents with explicit manifest and trust controls.

Kinnoo is the lifecycle, security, and distribution harness for AI agents: define a standard manifest, package reproducible artifacts, enforce trust checks, and distribute through a registry so agents can be installed and run consistently across environments.

It is designed for AI agent developers building CLI-runnable agents who need one reliable control plane across local development and registry distribution. Kinnoo provides a standard manifest contract (`kinnoo.yaml`), reproducible archive workflows (`.kno`), trust gates for publish/install, and consistent install/run paths for end users.

## What Kinnoo Is

- Strong lifecycle harness: scaffold, run, test, inspect, pack, fetch, publish, install, and uninstall with one CLI.
- Strong contract harness: `kinnoo.yaml` provides a framework-agnostic manifest with validation and predictable runtime expectations.
- Strong trust harness: integrity verification, optional signing, strict trust gates, and inspection-first workflows before install/run.
- Strong distribution harness: registry auth, publish/search/list/install flows, and versioned artifact distribution for teams.
- Framework portability: build and ship agents across common framework families with consistent packaging and operator UX.

## What Kinnoo Is Not

- Not a foundation model or model-hosting service.
- Not a replacement for framework-level orchestration (planner logic, tool routing, memory/retrieval strategy).
- Not a UI-only chatbot builder; Kinnoo focuses on CLI-runnable agent lifecycle workflows.
- Not a guarantee of agent quality by itself; it gives reproducibility and trust controls and provides a framework for running tests on your agents, but evaluation quality still depends on your tests and runtime design.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install kinnoo
```

## Quick Start

```bash
kinnoo init chatgpt my-agent
kinnoo run ./my-agent "hello"
kinnoo pack ./my-agent
kinnoo login
kinnoo publish ./my-agent --pack --strict --remote
```

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
