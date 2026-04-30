# --- Framework-specific templates ---

GEMINI_RUN_PY = '''import sys
import asyncio
from google import genai
import os

async def main(input_text):
  api_key = os.getenv("GOOGLE_API_KEY")
  if not api_key:
    print("Missing GOOGLE_API_KEY environment variable.")
    sys.exit(1)
  client = genai.Client(api_key=api_key)
  response = await asyncio.to_thread(
    client.models.generate_content,
    model="gemini-2.5-flash-lite",
    contents=input_text
  )
  print(response.text)

if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

GEMINI_REQUIREMENTS = "google-genai\n"

GEMINI_README = '''# {name}

This agent uses Google Gemini (Flash Lite) via the `google-genai` library.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export GOOGLE_API_KEY=your-key-here`

## Run Example
```
python main.py "Hello Gemini!"
```
'''

CHATGPT_RUN_PY = '''import sys
import asyncio
import openai
import os

async def main(input_text):
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    print("Missing OPENAI_API_KEY environment variable.")
    sys.exit(1)
  client = openai.AsyncOpenAI(api_key=api_key)
  response = await client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": input_text}]
  )
  print(response.choices[0].message.content)

if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

CHATGPT_REQUIREMENTS = "openai\n"

CHATGPT_README = '''# {name}

This agent uses OpenAI ChatGPT via the `openai` library.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Run Example
```
python main.py "Hello ChatGPT!"
```
'''

CLAUDE_RUN_PY = '''import sys
import asyncio
import anthropic
import os

async def main(input_text):
  api_key = os.getenv("ANTHROPIC_API_KEY")
  if not api_key:
    print("Missing ANTHROPIC_API_KEY environment variable.")
    sys.exit(1)
  client = anthropic.AsyncAnthropic(api_key=api_key)
  response = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": input_text}]
  )
  print(response.content[0].text)

if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

CLAUDE_REQUIREMENTS = "anthropic\n"

CLAUDE_README = '''# {name}

This agent uses Anthropic Claude via the `anthropic` library.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export ANTHROPIC_API_KEY=your-key-here`

## Run Example
```
python main.py "Hello Claude!"
```
'''

PYDANTIC_AI_RUN_PY = '''import os
import sys
import asyncio


async def _run_framework_mode(input_text):
  # Framework-native path: use pydantic-ai Agent when dependencies/env are available.
  from pydantic_ai import Agent

  agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt="You are a concise assistant.",
  )
  result = await agent.run(input_text)
  print(result.output)


async def _run_test_safe_mode(input_text):
  # Deterministic CI-safe path for environments without external API access.
  print(f"[pydantic-ai template] test-safe response: {input_text}")


async def main(input_text):
  test_safe_mode = os.getenv("KINNOO_TEST_SAFE_MODE", "").lower() in {"1", "true", "yes"}
  if test_safe_mode:
    await _run_test_safe_mode(input_text)
    return

  try:
    await _run_framework_mode(input_text)
  except Exception:
    # Fall back to deterministic output when framework dependencies or credentials are unavailable.
    await _run_test_safe_mode(input_text)


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

PYDANTIC_AI_REQUIREMENTS = "pydantic-ai>=0.0,<0.1\n"

PYDANTIC_AI_README = '''# {name}

This agent scaffold targets the `pydantic-ai` framework.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Runtime Paths
- Production framework path: uses `pydantic_ai.Agent` with an OpenAI model.
- Deterministic test-safe path: set `KINNOO_TEST_SAFE_MODE=1` to run without external API calls.

## Model Configuration
- Update model/provider settings in `main.py` for your target backend.

## Run Example
```
python main.py "Hello PydanticAI!"
```

## Test-Safe Example
```
KINNOO_TEST_SAFE_MODE=1 python main.py "Hello PydanticAI!"
```
'''

LANGGRAPH_RUN_PY = '''import os
import sys
import asyncio
from typing import TypedDict


class GraphState(TypedDict):
  user_input: str
  response: str


def _build_graph():
  # Framework-native graph path: state schema + node + edges.
  from langgraph.graph import END, START, StateGraph

  graph_builder = StateGraph(GraphState)

  def respond_node(state: GraphState) -> GraphState:
    return {
      "user_input": state["user_input"],
      "response": f"[langgraph template] graph response: {state['user_input']}",
    }

  graph_builder.add_node("respond", respond_node)
  graph_builder.add_edge(START, "respond")
  graph_builder.add_edge("respond", END)
  return graph_builder.compile()


async def _run_framework_mode(input_text):
  graph = _build_graph()
  result = await asyncio.to_thread(graph.invoke, {"user_input": input_text, "response": ""})
  print(result["response"])


async def _run_test_safe_mode(input_text):
  # Deterministic CI-safe path for environments without external API access.
  print(f"[langgraph template] test-safe response: {input_text}")


async def main(input_text):
  test_safe_mode = os.getenv("KINNOO_TEST_SAFE_MODE", "").lower() in {"1", "true", "yes"}
  if test_safe_mode:
    await _run_test_safe_mode(input_text)
    return

  try:
    await _run_framework_mode(input_text)
  except Exception:
    # Fall back to deterministic output when framework dependencies are unavailable.
    await _run_test_safe_mode(input_text)


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

LANGGRAPH_REQUIREMENTS = "langgraph>=0.2,<0.3\n"

LANGGRAPH_README = '''# {name}

This agent scaffold targets the `langgraph` framework.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Runtime Paths
- Production framework path: uses `StateGraph`, explicit START/END edges, and graph invocation.
- Deterministic test-safe path: set `KINNOO_TEST_SAFE_MODE=1` to run without external API calls.

## Graph Configuration
- Define state schema and graph nodes/edges in `main.py`.

## Run Example
```
python main.py "Hello LangGraph!"
```

## Test-Safe Example
```
KINNOO_TEST_SAFE_MODE=1 python main.py "Hello LangGraph!"
```
'''

OPENAI_AGENTS_RUN_PY = '''import os
import sys
import asyncio


def _build_agent():
  # Framework-native path: define an OpenAI Agent with instructions.
  from agents import Agent

  return Agent(
    name="KinnooAssistant",
    instructions="You are a concise assistant.",
  )


async def _run_framework_mode(input_text):
  from agents import Runner

  agent = _build_agent()
  result = await Runner.run(agent, input_text)
  final_output = getattr(result, "final_output", None)
  print(final_output if final_output is not None else str(result))


async def _run_test_safe_mode(input_text):
  # Deterministic CI-safe path for environments without external API access.
  print(f"[openai-agents template] test-safe response: {input_text}")


async def main(input_text):
  test_safe_mode = os.getenv("KINNOO_TEST_SAFE_MODE", "").lower() in {"1", "true", "yes"}
  if test_safe_mode:
    await _run_test_safe_mode(input_text)
    return

  try:
    await _run_framework_mode(input_text)
  except Exception:
    # Fall back to deterministic output when framework dependencies are unavailable.
    await _run_test_safe_mode(input_text)


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

OPENAI_AGENTS_REQUIREMENTS = "openai-agents>=0.1,<0.2\n"

OPENAI_AGENTS_README = '''# {name}

This agent scaffold targets the `openai-agents` SDK.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set your API key: `export OPENAI_API_KEY=your-key-here`

## Runtime Paths
- Production framework path: uses `Agent` construction and `Runner.run(...)` workflow.
- Deterministic test-safe path: set `KINNOO_TEST_SAFE_MODE=1` to run without external API calls.

## Agent Configuration
- Define agent roles, handoffs, and guardrails in `main.py`.

## Run Example
```
python main.py "Hello OpenAI Agents!"
```

## Test-Safe Example
```
KINNOO_TEST_SAFE_MODE=1 python main.py "Hello OpenAI Agents!"
```
'''

MCP_CLIENT_RUN_PY = '''import asyncio
import os
import shlex
import sys
from typing import Any, Dict, List, Optional

try:
  from dotenv import load_dotenv
except ImportError:
  def load_dotenv(*_args, **_kwargs):
    return False

try:
  from mcp import ClientSession, StdioServerParameters
  from mcp.client.stdio import stdio_client
except ImportError:
  ClientSession = None
  StdioServerParameters = None
  stdio_client = None


def _parse_server_command(raw_command: str) -> tuple[str, list[str]]:
  parts = shlex.split(raw_command)
  if not parts:
    raise ValueError("[kinnoo] MCP_SERVER_CMD is empty after parsing")
  return parts[0], parts[1:]


def _parse_server_env(raw_env: str) -> Optional[Dict[str, str]]:
  if not raw_env:
    return None

  import json

  try:
    decoded = json.loads(raw_env)
  except json.JSONDecodeError as exc:
    raise ValueError(f"[kinnoo] MCP_SERVER_ENV must be valid JSON: {exc}") from exc

  if not isinstance(decoded, dict):
    raise ValueError("[kinnoo] MCP_SERVER_ENV must decode to a JSON object")

  return {str(key): str(value) for key, value in decoded.items()}


class BaseMCPAgent:
  def __init__(self):
    self.session: Optional[ClientSession] = None
    self._client_context = None

  async def connect_to_server(
    self,
    command: str,
    args: List[str],
    env: Optional[Dict[str, str]] = None,
  ) -> None:
    if ClientSession is None:
      raise RuntimeError("[kinnoo] Missing mcp package. pip install mcp")

    server_params = StdioServerParameters(
      command=command,
      args=args,
      env={**os.environ, **(env or {})},
    )

    self._client_context = stdio_client(server_params)
    read_stream, write_stream = await self._client_context.__aenter__()

    self.session = ClientSession(read_stream, write_stream)
    await self.session.__aenter__()
    await self.session.initialize()

  async def disconnect(self) -> None:
    if self.session is not None:
      await self.session.__aexit__(None, None, None)
      self.session = None
    if self._client_context is not None:
      await self._client_context.__aexit__(None, None, None)
      self._client_context = None

  async def get_tools(self):
    """Retrieve available tools from the connected server."""
    if not self.session:
      raise RuntimeError("Agent not connected to a server.")
    return await self.session.list_tools()

  async def execute_tool(self, name: str, params: Dict[str, Any]):
    """Call a specific tool provided by the connected server."""
    if not self.session:
      raise RuntimeError("[kinnoo] Agent not connected to an MCP server.")
    return await self.session.call_tool(name, params)

  async def agent_logic_loop(self, input_text: str):
    """Placeholder for agent logic (LLM integration, tool execution, etc.)"""
    print(f"[kinnoo] Agent logic started with input: {input_text}")
    # Example: tools = await self.get_tools()
    pass


async def main(input_text: str) -> None:
  load_dotenv()

  server_cmd_raw = os.getenv("MCP_SERVER_CMD", "").strip()
  if not server_cmd_raw:
    print("[kinnoo] Set MCP_SERVER_CMD in your .env or your shell environment to connect to an MCP server.")
    return

  server_env_raw = os.getenv("MCP_SERVER_ENV", "").strip()
  try:
    command, args = _parse_server_command(server_cmd_raw)
    env = _parse_server_env(server_env_raw)
  except ValueError as exc:
    print(f"[kinnoo] Configuration Error: {exc}")
    return

  agent = BaseMCPAgent()
  try:
    await agent.connect_to_server(command, args, env)
    await agent.agent_logic_loop(input_text)
  except Exception as exc:
    print(f"[kinnoo] Runtime Error: {exc}")
  finally:
    await agent.disconnect()


if __name__ == '__main__':
  input_text = sys.argv[1] if len(sys.argv) > 1 else ''
  asyncio.run(main(input_text))
'''

MCP_CLIENT_REQUIREMENTS = "mcp\npython-dotenv\n"

MCP_CLIENT_README = '''# {name}

This scaffold demonstrates a Kinnoo-compatible MCP client template.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Package/install an MCP server agent archive (for example a filesystem MCP server)

## Suggested End-to-End Workflow
1. Package MCP server:
   - `python src/kinnoo/cli.py pack <mcp-server-dir>`
2. Install MCP server package:
   - `python src/kinnoo/cli.py install <mcp-server>.kno`
3. Start your MCP server in stdio mode and export its launch command:
  - `export MCP_SERVER_CMD="python path/to/mcp_server.py"`
4. (Optional) Provide extra server env vars as JSON:
  - `export MCP_SERVER_ENV='{{"API_KEY":"demo"}}'`
5. Run this client template:
  - `python main.py "list available files"`

## Optional Environment Variables
- `MCP_SERVER_CMD` command to launch an MCP stdio server process
- `MCP_SERVER_ENV` JSON object merged into the MCP server process environment

## Contract Notes
- Input is read from `sys.argv[1]`
- Output is printed to stdout
'''

MCP_SERVER_RUN_PY = '''import json
import sys


def _ok_response(request_id, result):
  return {
    "jsonrpc": "2.0",
    "id": request_id,
    "result": result,
  }


def _error_response(request_id, code, message):
  return {
    "jsonrpc": "2.0",
    "id": request_id,
    "error": {
      "code": code,
      "message": message,
    },
  }


def _handle_request(request):
  request_id = request.get("id")
  method = request.get("method")
  params = request.get("params") or {}

  if method == "initialize":
    return _ok_response(
      request_id,
      {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
          "name": "kinnoo-mcp-server-template",
          "version": "0.1.0",
        },
        "capabilities": {
          "tools": {
            "listChanged": False,
          }
        },
      },
    )

  if method == "tools/list":
    return _ok_response(
      request_id,
      {
        "tools": [
          {
            "name": "echo",
            "description": "Echo back input text.",
            "inputSchema": {
              "type": "object",
              "properties": {
                "text": {
                  "type": "string"
                }
              },
              "required": ["text"],
            },
          }
        ]
      },
    )

  if method == "tools/call":
    if params.get("name") != "echo":
      return _error_response(request_id, -32601, "Unknown tool")

    arguments = params.get("arguments") or {}
    text = arguments.get("text", "")
    return _ok_response(
      request_id,
      {
        "content": [
          {
            "type": "text",
            "text": f"echo: {text}",
          }
        ]
      },
    )

  return _error_response(request_id, -32601, "Method not found")


def main():
  # Minimal newline-delimited JSON-RPC server loop over stdio.
  for raw in sys.stdin:
    raw = raw.strip()
    if not raw:
      continue

    try:
      request = json.loads(raw)
      response = _handle_request(request)
    except Exception as exc:
      response = _error_response(None, -32700, f"Parse error: {exc}")

    sys.stdout.write(json.dumps(response) + "\\n")
    sys.stdout.flush()


if __name__ == "__main__":
  main()
'''

MCP_SERVER_REQUIREMENTS = ""

MCP_SERVER_README = '''# {name}

This scaffold demonstrates a minimal MCP server implemented over stdio.

## Setup
- Install dependencies: `pip install -r requirements.txt`

## Run Server
```
python main.py
```

## Quick Handshake Smoke Test
```
printf '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{}}}}\n' | python main.py
```

## Tool Call Smoke Test
```
printf '{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{{"name":"echo","arguments":{{"text":"hello"}}}}}}\n' | python main.py
```
'''

OPENCLAW_PACKAGE_JSON_TEMPLATE = '''{{
  "name": "{name}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {{
    "start": "node index.mjs"
  }}
}}
'''

OPENCLAW_JSON_TEMPLATE = '''{{
  "name": "{name}",
  "description": "OpenClaw scaffold generated by kinnoo",
  "entrypoint": "index.mjs",
  "skills_dir": "skills",
  "memory_dir": "memory"
}}
'''

OPENCLAW_INDEX_MJS_TEMPLATE = '''const inputText = process.argv[2] ?? "";

const requiredEnvVars = ["OPENCLAW_API_KEY", "KINNOO_TEST_SAFE_MODE"];
const missingEnvVars = requiredEnvVars.filter((name) => !process.env[name]);

if (missingEnvVars.length > 0) {
  console.error(`[openclaw scaffold] missing env vars: ${missingEnvVars.join(",")}`);
  process.exit(1);
}

const mode = process.env.KINNOO_TEST_SAFE_MODE === "1" ? "test-safe" : "live";
console.log(`[openclaw scaffold] daemon ready mode=${mode} input=${inputText}`);

const heartbeat = setInterval(() => {
  // Keep the scaffold alive in daemon mode; lifecycle is controlled by kinnoo stop.
}, 60_000);

const shutdown = () => {
  clearInterval(heartbeat);
  console.log("[openclaw scaffold] daemon stopping");
  process.exit(0);
};

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
'''

OPENCLAW_DEFAULT_SKILL_TEMPLATE = '''# Default Skill

This is the default OpenClaw skill scaffold. Replace with project-specific guidance.
'''

OPENCLAW_AGENTS_MD_TEMPLATE = '''# AGENTS

Describe available agents, responsibilities, and handoff expectations.
'''

OPENCLAW_SOUL_MD_TEMPLATE = '''# SOUL

Document the agent's identity, principles, and behavior constraints.
'''

OPENCLAW_README_TEMPLATE = '''# {name}

This is a standalone OpenClaw-style scaffold generated by `kinnoo init --framework openclaw`.

## Prerequisites
- Node.js 20+ (matches `runtime.version` in `kinnoo.yaml`)

## Setup
- Install dependencies from the project root: `npm install`

## Required Environment Variables
- `OPENCLAW_API_KEY`
- `KINNOO_TEST_SAFE_MODE` (`1` for deterministic test-safe mode)

## Run with Kinnoo
```
python src/kinnoo/cli.py run . "hello from openclaw"
```

## Run directly with Node.js
```
node index.mjs "hello from openclaw"
```

## Stop Daemon
```
python src/kinnoo/cli.py stop .
```
'''
"""
Templates for kinnoo agent scaffolding files.
"""

# [agent] Keep this minimal manifest example synchronized with required manifest
# fields whenever schema/template changes affect minimum valid kinnoo.yaml shape.
INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE = """name: my-agent
version: 0.1.0
entrypoint: main.py
runtime:
  language: python
  version: "3.10"
  type: one-shot
dependencies: []
inputs:
  type: string
outputs:
  type: string
"""

INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES = (
    "Recommended generation steps:",
    "pip install uv",
    "uv export --format requirements-txt > requirements.txt",
)

KINNOO_YAML_TEMPLATE = """name: {name}
version: 0.1.0
description: "TODO: Add a short agent description"
author: "TODO: Add author name"
entrypoint: main.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
"""

MCP_SERVER_KINNOO_YAML_TEMPLATE = """name: {name}
version: 0.1.0
description: "TODO: Add a short MCP server description"
author: "TODO: Add author name"
entrypoint: main.py
framework: mcp-server
runtime:
  language: python
  version: ">=3.10"
  type: mcp-server
channels:
  - stdio
dependencies: []
inputs:
  type: text
outputs:
  type: text
"""

OPENCLAW_KINNOO_YAML_TEMPLATE = """name: {name}
version: 0.1.0
description: "TODO: Add a short OpenClaw agent description"
author: "TODO: Add author name"
entrypoint: index.mjs
framework: openclaw
runtime:
  language: nodejs
  version: ">=20"
  type: daemon
  package_manager: npm
channels:
  - stdio
skills:
  - skills/default
state_dirs:
  - memory
env_vars:
  - OPENCLAW_API_KEY
  - KINNOO_TEST_SAFE_MODE
dependencies: []
inputs:
  type: text
outputs:
  type: text
"""

RUN_PY_TEMPLATE = """import sys
import asyncio

async def main(input_text):
    print(f'Hello, world! Input: {input_text}')

if __name__ == '__main__':
    input_text = sys.argv[1] if len(sys.argv) > 1 else ''
    asyncio.run(main(input_text))
"""

REQUIREMENTS_TXT_TEMPLATE = ""  # Empty for MVP

README_MD_TEMPLATE = """# {name}

This is a Kinnoo agent scaffolded with `kinnoo init`.

- Edit `main.py` to implement your agent logic.
- See `kinnoo.yaml` for manifest fields.
"""
