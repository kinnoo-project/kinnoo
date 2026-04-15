# Getting Started

This guide walks through installing Kinnoo, creating an agent, running it locally, and packaging it.

Kinnoo acts as a lifecycle and trust harness around your agent code: you define a standard manifest, run locally with consistent command surfaces, package reproducible artifacts into an agent archive, and then publish that archive to the remote registry. Other developers and end-users can then search for your agent archive, unpack / install, and run your agent - using the same command-line interface.

## Prerequisites

- Python 3.11+
- `pip`

## 1) Install Kinnoo

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install kinnoo
```

## 2) Create Your First Agent

```bash
kinnoo init chatgpt my-agent
```

This creates a scaffolded project in `./my-agent`.

Expected output (example):

```text
Initialized agent: my-agent
```

## 3) Configure Manifest and Runtime Inputs

Open `my-agent/kinnoo.yaml` and verify key fields:

- `name`
- `version`
- `entrypoint`
- `runtime`

If your framework requires provider credentials, export them in your shell before running.

## 4) Run Locally

```bash
kinnoo run ./my-agent "hello"
```

Expected output (example):

```text
[kinnoo] running agent my-agent
...agent response...
```

For readiness checks without full execution:

```bash
kinnoo run ./my-agent --preflight
```

## 5) Package for Distribution

```bash
kinnoo pack ./my-agent
```

Expected output (example):

```text
[kinnoo pack] Packaging agent directory...
[kinnoo pack] Archive written: .../my-agent-<version>.kno
```

Optional signed package:

```bash
kinnoo keygen
kinnoo pack ./my-agent --sign ./kinnoo-ed25519-private.pem
```

Strict publish flow (recommended for shared registries):

```bash
kinnoo publish ./my-agent --pack --strict --remote
```

## 6) Next Step: Registry Workflows

Continue with `docs/registry-guide.md` for login, publish, search, and install workflows.
