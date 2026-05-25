# Kinnoo 🍊


![Status: Beta](https://img.shields.io/badge/status-beta-blue)
![Release](https://img.shields.io/badge/release-v0.10.0-yellow)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/license-Apache%202.0-green)

Kinnoo is a unified platform that allows **AI agent developers** to create, package and share AI agents, which **agent end-users** can install and run on a local machine.
 
[Website](https://kinnoo.ai) · [Docs](docs/README.md) · [Getting Started](docs/getting-started.md)

## What Kinnoo Is

- Strong **lifecycle** harness: control the entire lifecycle of an AI agent (`init`, `test`, `pack`, `publish`, `fetch`, `install`, `inspect`, `run`, `uninstall`) with the Kinnoo CLI.
- Strong **contract** harness: `kinnoo.yaml` provides a framework-agnostic manifest designed to enforce consistent agent runtime behavior.
- Strong **trust** harness: agent archive and per-file code integrity verification, publisher identity verification, strict trust gates, and inspect-before-run functionality.
- Strong **distribution** harness: registry auth, publish/search/list/install flows, and versioned artifact distribution for teams.
- Framework **portability**: build and ship agents across common agent frameworks with consistent packaging and operator UX.

## What Kinnoo Is Not

- Not a foundation model or model-hosting service.
- Not a replacement for framework-level design and orchestration (planner logic, tool routing, memory/retrieval strategy).
- Not a UI-only chatbot or no-code agent builder; Kinnoo focuses on CLI-runnable agent lifecycle workflows.
- Not a guarantee of agent quality by itself; it gives reproducibility and trust controls and provides a framework for running tests on your agents, but evaluation quality still depends on your tests and runtime design.

## Quick Start

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

See [Getting Started](docs/getting-started.md) for more details.

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

See [Supported Agents](docs/supported-agents.md) for more details.

## Go Runtime Modes

Kinnoo supports Go scaffolding with these framework combinations:

- `kinnoo init gemini --language go <agent-name>`
- `kinnoo init chatgpt --language go <agent-name>`
- `kinnoo init claude-chat --language go <agent-name>`
- `kinnoo init mcp-client --language go <agent-name>`
- `kinnoo init mcp-server --language go <agent-name>`
- `kinnoo init no-framework --language go <agent-name>`

Go scaffolding uses the local Go toolchain to run `go mod init <agent-name>` during `kinnoo init`.

`kinnoo run` and `kinnoo run --preflight` support two Go execution modes:

- Go source mode: entrypoint ends with `.go` (typically `main.go`), and Kinnoo checks Go toolchain/runtime constraints.
- Go binary mode: entrypoint points to a precompiled executable (for example `bin/agent` or `dist/agent.exe`), and Kinnoo skips Go toolchain checks but runs binary compatibility checks.

Preflight output uses explicit status labels:

- `- [PASS] ...` for passing checks.
- `- [WARN] ...` for non-blocking issues (for example, optional Go module warnings).
- `- [FAIL] ...` for blocking checks.

Final preflight summary:

- success: `Ready to run` and `Preflight result: PASS`
- failure: `Not ready to run`, `Remediation summary:`, and `Preflight result: FAIL`

Common Go preflight remediation guidance:

- missing Go toolchain for source mode: install Go or configure `runtime.path`.
- wrong architecture/OS: rebuild with host `GOOS` and `GOARCH`.
- unsupported binary format: rebuild to a supported executable format (Mach-O/ELF/PE).
- non-executable binary: run `chmod +x <entrypoint>`.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` for development and contribution workflow.

## License

Apache 2.0 (`LICENSE`).
