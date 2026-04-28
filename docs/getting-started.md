# Getting Started

Kinnoo gives a developer building AI agents a reliable way to package, publish and share your agents for others to install and run them. As an AI agent developer, Kinnoo also gives you a feature-rich CLI for consistently managing the agent lifecycle from local development to a stable, tested, secure package that can be run in production.

Setting up Kinnoo is easy! This hands-on guide provides step-by-step instructions that will guide you through installing the Kinnoo CLI, initializing an agent, running it locally, then packaging and publishing it to your agent registry. Instructions for fetching or installing an agent from the registry are also provided below.

## Prerequisites

- Python 3.11+
- `pip`

## 1) Install Kinnoo CLI

Start with a clean virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install kinnoo
```

## 2) Set Up Your Kinnoo Environment

For interfacing with the hosted Kinnoo agent registry, the only required environment variable is the registry endpoint:

```bash
export KINNOO_REGISTRY_URL=https://api.kinnoo.ai
```

## 3) Log into Kinnoo / Create an account with Kinnoo

To create an account or login, you can navigate to the website (```https://kinnoo.ai```) and follow the steps for signing up (or logging in) with your e-mail, Google, or GitHub account. Alternatively, once the Kinnoo CLI is installed and setup, you can open a terminal and type:

```bash
kinnoo login
```

and follow the instructions for creating an account or logging in. Creating an account will automatically create your own agent repository within the agent registry. 

Once you are logged in and ```KINNOO_REGISTRY_URL``` is set, you can use Kinnoo CLI commands (e.g., ```kinnoo list```, ```kinnoo search```, ```kinnoo fetch```, ```kinnoo install```, etc) to interact with the agent registry. Typing ```--help``` or ```-h``` with any CLI command will display help text with detailed command usage and examples.

## 4) Initialize Your First Agent

After installing the Kinnoo CLI, we recommend initializing an agent with the CLI, to get a sense of the typical folder structure of an agent's codebase and to get a feel for how other Kinnoo CLI commands are used with an agent.

```kinnoo init -h``` will show you the current languages and agent frameworks supported. For now, let's start with a simple ChatGPT chat agent. At a command prompt, type:

```bash
kinnoo init chatgpt my-chat-agent
```

This creates a new directory `./my-chat-agent` and initializes a scaffold file and folder structure in that directory. Importantly, this directory creates a template `kinnoo.yaml`, which is a manifest file used to describe that agent's metadata - author, description, framework, services, etc. You can find full documentation on the `kinnoo.yaml` agent manifest [here](https://github.com/kinnoo-project/kinnoo/blob/main/docs/kinnoo-yaml-spec.md).

For the ChatGPT agent, you will need an ```OPENAI_API_KEY``` in your environment. If you don't have one, navigate to ```https://platform.openai.com```, create an account, then create an API key.

## 5) Run Locally

Once your agent is initialized, you can run it locally by typing:

```bash
kinnoo run ./my-chat-agent "what is 2+2?"
```

If this is your first time running the agent, Kinnoo will first install any libraries or packages that are required for the agent to run. A successful run of the ChatGPT agent described above should output something like

```bash
In base-10, 2 + 2 = 4. If you want, I can show how it looks in other bases.
```

If you only want a quick run pre-flight readiness check (for example, if you want to check if your runtime environment is setup properly):

```bash
kinnoo run --preflight ./my-chat-agent
```

## 6) Package and Publish Your Agent

Typically, you will want to document and run some test cases to verify that your agent behaves as expected (more on testing your agent <LINK>here</LINK>). Once you have finished your local development and testing, and your agent is ready to publish to the registry, simply type
 

```bash
kinnoo pack ./my-chat-agent
```

followed by

```bash
kinnoo publish ./my-chat-agent
```

You should see an output message stating that your agent has been accepted into the remote registry.

There are lots of options for adding security, privacy, identity, package verification, versioning, publishing to an on-premise (local) registry, etc... These options are all covered in the [CLI reference](https://github.com/kinnoo-project/kinnoo/blob/main/docs/cli-reference.md).


## 7) Install from Registry

Once your agent is in the remote registry and your agent has public visibility (default), then others can install your published agent from the remote registry by typing

```bash
kinnoo install my-chat-agent
```

If instead an end-user wants to just fetch the packaged agent archive and not fully install the agent (e.g., the end-user wants to do some additional security checks on the agent before unpacking and installing it), the end-user can type

```bash
kinnoo fetch my-chat-agent
```

This covers the complete lifecycle path of a agent using the Kinnoo CLI. The complete CLI reference can be found [here](https://github.com/kinnoo-project/kinnoo/blob/main/docs/cli-reference.md). We hope that Kinnoo makes the agent developer and runtime experience simpler, more secure, and more robust. As you start using Kinnoo to develop, publish, and run agents, we would love your feedback!


## Quick Troubleshooting

### Installation and setup

- **`kinnoo: command not found`**: activate your venv (`source .venv/bin/activate`) and reinstall (`pip install kinnoo`).
- **Login/auth discovery failure**: confirm `KINNOO_REGISTRY_URL` is exactly `https://api.kinnoo.ai`.

### Agent initialization

- **Directory already exists**: choose a new agent name or remove the existing folder.
- **Unsupported framework**: check supported templates in `docs/supported-agents.md`.

### Local run

- **Manifest validation errors**: run `kinnoo inspect ./my-chat-agent` and fix required `kinnoo.yaml` fields.
- **Provider auth errors**: set the framework-specific API key expected by your agent template.

### Packaging

- **Pack fails on missing files/invalid manifest**: rerun `kinnoo inspect ./my-chat-agent` and verify `entrypoint`/`entrypoints` paths.
- **Pack warns about overwriting an existing agent archive**: bump the agent version before packaging, e.g. `kinnoo pack --bump patch my-chat-agent`.

### Publishing

- **Unauthorized/forbidden**: run `kinnoo login` again, then retry publish.
- **Version conflict**: bump version in `kinnoo.yaml` or package + publish with `kinnoo publish --pack --bump patch my-chat-agent`.

## Next Steps

- Registry workflows and team sharing: `docs/registry-guide.md`
- Manifest field reference: `docs/kinnoo-yaml-spec.md`
- Trust and verification model: `docs/security-model.md`
