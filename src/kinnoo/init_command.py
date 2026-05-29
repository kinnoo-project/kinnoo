
"""
Agent scaffolding logic for kinnoo init.
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from kinnoo.templates import (
    CHATGPT_GO_MAIN,
    CHATGPT_GO_README,
    CHATGPT_README,
    CHATGPT_REQUIREMENTS,
    CHATGPT_RUN_PY,
    CLAUDE_GO_MAIN,
    CLAUDE_GO_README,
    CLAUDE_README,
    CLAUDE_REQUIREMENTS,
    CLAUDE_RUN_PY,
    GEMINI_GO_MAIN,
    GEMINI_GO_README,
    GEMINI_README,
    GEMINI_REQUIREMENTS,
    GEMINI_RUN_PY,
    GO_README_TEMPLATE,
    GO_RUN_TEMPLATE,
    KINNOO_YAML_TEMPLATE,
    LANGGRAPH_README,
    LANGGRAPH_REQUIREMENTS,
    LANGGRAPH_RUN_PY,
    MCP_CLIENT_GO_MAIN,
    MCP_CLIENT_GO_README,
    MCP_CLIENT_README,
    MCP_CLIENT_REQUIREMENTS,
    MCP_CLIENT_RUN_PY,
    MCP_SERVER_GO_MAIN,
    MCP_SERVER_GO_README,
    MCP_SERVER_KINNOO_YAML_TEMPLATE,
    MCP_SERVER_README,
    MCP_SERVER_REQUIREMENTS,
    MCP_SERVER_RUN_PY,
    OPENAI_AGENTS_README,
    OPENAI_AGENTS_REQUIREMENTS,
    OPENAI_AGENTS_RUN_PY,
    OPENCLAW_AGENTS_MD_TEMPLATE,
    OPENCLAW_DEFAULT_SKILL_TEMPLATE,
    OPENCLAW_INDEX_MJS_TEMPLATE,
    OPENCLAW_JSON_TEMPLATE,
    OPENCLAW_KINNOO_YAML_TEMPLATE,
    OPENCLAW_PACKAGE_JSON_TEMPLATE,
    OPENCLAW_README_TEMPLATE,
    OPENCLAW_SOUL_MD_TEMPLATE,
    PYDANTIC_AI_README,
    PYDANTIC_AI_REQUIREMENTS,
    PYDANTIC_AI_RUN_PY,
    README_MD_TEMPLATE,
    REQUIREMENTS_TXT_TEMPLATE,
    RUN_PY_TEMPLATE,
)

try:
    from kinnoo import __version__ as KINNOO_VERSION
except ImportError:
    from . import __version__ as KINNOO_VERSION

SUPPORTED_FRAMEWORKS = [
    "gemini",
    "chatgpt",
    "claude-chat",
    "pydantic-ai",
    "langgraph",
    "openai-agents",
    "mcp-client",
    "mcp-server",
    "openclaw",
    "no-framework",
]

SUPPORTED_LANGUAGES = [
    "python",
    "js",
    "javascript",
    "ts",
    "typescript",
    "go",
]

_LANGUAGE_ALIASES = {
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "go": "go",
}

_FRAMEWORK_LANGUAGE_COMPATIBILITY = {
    "gemini": {"python", "javascript", "typescript", "go"},
    "chatgpt": {"python", "javascript", "typescript", "go"},
    "claude-chat": {"python", "javascript", "typescript", "go"},
    "pydantic-ai": {"python"},
    "langgraph": {"python", "javascript", "typescript"},
    "openai-agents": {"python"},
    "mcp-client": {"python", "javascript", "typescript", "go"},
    "mcp-server": {"python", "javascript", "typescript", "go"},
    "openclaw": {"javascript", "typescript"},
    "no-framework": {"python", "javascript", "typescript", "go"},
}

_JS_RUN_TEMPLATE = """const inputText = process.argv[2] || '';
console.log(`Hello from JS agent. Input: ${inputText}`);
"""

_TS_RUN_TEMPLATE = """const inputText = process.argv[2] ?? '';
console.log(`Hello from TS agent. Input: ${inputText}`);
"""

_NODE_PACKAGE_JSON_TEMPLATE = """{{
    "name": "{name}",
    "version": "0.1.0",
    "private": true,
    "type": "module",
    "scripts": {{
        "start": "node {entrypoint}"
    }}
}}
"""

_NODE_README_TEMPLATE = """# {name}

This is a Kinnoo agent scaffolded with `kinnoo init --language {language_flag}`.

- Edit `{entrypoint}` to implement your agent logic.
- See `kinnoo.yaml` for manifest fields.
"""

_GITIGNORE_PYTHON = """# --- Kinnoo & Agent Ops ---
.kinnoo/             # Local PID files and CLI state
.env                 # API keys
*.pem                # Private keys
.agent-repo-cache*

# --- Git ---
.git/

# --- Environment ---
__pycache__/
.venv/
env/
venv/
*.py[cod]
*$py.class
.pytest_cache/
*.DS_Store*

# --- Data & Distribution ---
dist/
build/
*.egg-info/
"""

_GITIGNORE_JAVASCRIPT = """# --- Kinnoo & Agent Ops ---
.kinnoo/
.env
*.pem
.agent-repo-cache*

# --- Environment ---
node_modules/
.npm
.pnpm-debug.log*
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.DS_Store*

# --- Build Artifacts ---
dist/
out/
.cache/
"""

_GITIGNORE_TYPESCRIPT = """# --- Kinnoo & Agent Ops ---
.kinnoo/
.env
*.pem

# --- Environment ---
node_modules/
.npm
dist/                # Compiled JS output
*.tsbuildinfo        # Incremental build state
.pnpm-debug.log*
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.DS_Store*
.cache/

# --- Testing & Coverage ---
coverage/
.vitest/

# --- Config & Lockfiles ---
# but ignore local dev overrides
.env.local
.env.development.local
"""

_GITIGNORE_GO = """# --- Kinnoo & Agent Ops ---
.kinnoo/
.env
*.pem

# --- Go Build Outputs ---
bin/
dist/
*.test
*.out
*.prof

# --- Environment ---
.DS_Store
"""

_GITIGNORE_OPENCLAW = """--- OpenClaw Core Privacy ---
memory/              # 🛡️ CRITICAL: Ignores all daily YYYY-MM-DD.md logs
.dreams/             # Experimental background consolidation logs
scratch/             # The agent's temporary workspace/download area

# --- Kinnoo & Security ---
.kinnoo/
.env

# --- Credentials & Config ---
.openclaw/           # Local gateway settings & auth tokens
.env
credentials.json
*.pem
*.DS_Store*
"""

_OPENCLAW_BOOTSTRAP_TEMPLATE = """# BOOTSTRAP

Document startup checks and first-run setup steps for this agent.
"""

_OPENCLAW_HEARTBEAT_TEMPLATE = """# HEARTBEAT

Track periodic health notes and runtime heartbeat expectations.
"""

_OPENCLAW_MEMORY_TEMPLATE = """# MEMORY

Capture high-level long-term context and references for this agent.
"""

_OPENCLAW_IDENTITY_TEMPLATE = """# IDENTITY

Define the agent persona, role, and non-negotiable behaviors.
"""

_OPENCLAW_USER_TEMPLATE = """# USER

Describe user preferences, interaction patterns, and constraints.
"""


def _folder_guide_table() -> str:
    return (
        "\n## Folder Guide\n\n"
        "| Folder | What goes here |\n"
        "| --- | --- |\n"
        "| tools/ | Tool wrappers and utility code the agent can call |\n"
        "| prompts/ | Prompt snippets and reusable instructions |\n"
        "| evals/ | Evaluation cases and scoring fixtures |\n"
        "| tests/ | Regression and smoke tests for this agent |\n"
        "| data/ | Local sample data and offline test fixtures |\n"
    )


def _standardize_readme(readme_text: str, *, entrypoint: str, include_folder_table: bool) -> str:
    lines: list[str] = [readme_text.rstrip(), ""]
    lines.append(f"- Edit `{entrypoint}` to implement your agent run logic.")
    lines.append("- `kinnoo.yaml` holds the agent manifest and runtime metadata contract.")

    if include_folder_table:
        lines.append(_folder_guide_table().rstrip())

    lines.append("")
    lines.append("---")
    lines.append(f"🍊 *This agent was scaffolded with Kinnoo CLI v{KINNOO_VERSION} using Schema 0.1.0.*")
    return "\n".join(lines).rstrip() + "\n"


def _build_openclaw_wrapper_manifest(name: str) -> str:
    """Build schema-compatible OpenClaw wrapper manifest for delegated workspaces."""
    return (
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: \"OpenClaw workspace managed via kinnoo wrapper\"\n"
        "author: \"TODO: Add author name\"\n"
        "entrypoint: index.mjs\n"
        "framework: openclaw\n"
        "runtime:\n"
        "  language: nodejs\n"
        "  version: \">=20\"\n"
        "  type: daemon\n"
        "  package_manager: npm\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )

KNOWN_FRAMEWORK_DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash-lite",
    "chatgpt": "gpt-5-nano",
    "claude-chat": "claude-sonnet-4-20250514",
    "pydantic-ai": "openai:gpt-4o-mini",
}

GO_MCP_SDK_MODULE = "github.com/modelcontextprotocol/go-sdk"
GO_MCP_SDK_VERSION = "v1.4.1"


def _go_install_instructions() -> str:
    """Return OS-specific Go installation instructions for first-time setup."""
    system = platform.system().lower()
    if system == "darwin":
        return (
            "Install Go on macOS:\n"
            "  1) brew install go\n"
            "  2) or download an installer from https://go.dev/dl/\n"
            "  3) verify with: go version"
        )
    if system == "linux":
        return (
            "Install Go on Linux:\n"
            "  1) Use your package manager (for example: apt install golang-go)\n"
            "  2) or install from https://go.dev/dl/\n"
            "  3) verify with: go version"
        )
    if system == "windows":
        return (
            "Install Go on Windows:\n"
            "  1) winget install GoLang.Go\n"
            "  2) or install from https://go.dev/dl/\n"
            "  3) open a new terminal and run: go version"
        )
    return (
        "Install Go from https://go.dev/dl/ and ensure `go` is available in PATH, "
        "then verify with: go version"
    )


def _require_go_toolchain_for_init() -> str:
    """Return the go executable path or raise an actionable setup error."""
    go_executable = shutil.which("go")
    if go_executable is not None:
        return go_executable
    raise RuntimeError(
        "Go toolchain is required to scaffold Go agents because Kinnoo runs `go mod init` "
        "during `kinnoo init --language go`.\n"
        f"{_go_install_instructions()}"
    )


def _initialize_go_module(agent_dir: Path, module_name: str, go_executable: str) -> None:
    """Initialize go.mod using the local Go toolchain."""
    result = subprocess.run(
        [go_executable, "mod", "init", module_name],
        cwd=agent_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return

    details = result.stderr.strip() or result.stdout.strip() or "unknown go mod init error"
    raise RuntimeError(
        "Failed to initialize Go module with `go mod init`.\n"
        f"Directory: {agent_dir}\n"
        f"Command: {go_executable} mod init {module_name}\n"
        f"Details: {details}"
    )


def _pin_go_module_dependency(agent_dir: Path, *, module: str, version: str, go_executable: str) -> None:
    """Pin a Go module dependency using the Go toolchain."""
    requirement = f"{module}@{version}"
    result = subprocess.run(
        [go_executable, "mod", "edit", f"-require={requirement}"],
        cwd=agent_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return

    details = result.stderr.strip() or result.stdout.strip() or "unknown go mod edit error"
    raise RuntimeError(
        "Failed to pin Go dependency with `go mod edit`.\n"
        f"Directory: {agent_dir}\n"
        f"Command: {go_executable} mod edit -require={requirement}\n"
        f"Details: {details}"
    )

def _normalize_language(language: Optional[str]) -> str | None:
    if language is None:
        return None
    return _LANGUAGE_ALIASES.get(language.lower())


def _build_node_manifest(name: str, *, entrypoint: str, language: str) -> str:
    return (
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: \"TODO: Add a short agent description\"\n"
        "author: \"TODO: Add author name\"\n"
        f"entrypoint: {entrypoint}\n"
        "runtime:\n"
        f"  language: {language}\n"
        "  version: \">=20\"\n"
        "  type: one-shot\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )


def _build_go_manifest(
    name: str,
    *,
    entrypoint: str = "main.go",
    runtime_type: str = "one-shot",
) -> str:
    return (
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: \"TODO: Add a short agent description\"\n"
        "author: \"TODO: Add author name\"\n"
        f"entrypoint: {entrypoint}\n"
        "runtime:\n"
        "  language: go\n"
        "  version: \">=1.22\"\n"
        f"  type: {runtime_type}\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )


def _select_menu_option(prompt: str, options: list[str]) -> str:
    print(prompt)
    for index, option in enumerate(options, start=1):
        print(f"  {index}. {option}")

    while True:
        raw_value = input("Select an option by number: ").strip()
        if not raw_value.isdigit():
            print("Invalid selection. Enter a number.")
            continue
        selected_index = int(raw_value)
        if 1 <= selected_index <= len(options):
            return options[selected_index - 1]
        print("Invalid selection. Enter a valid number from the list.")


def interactive_init_wizard(target_dir: Path) -> tuple[str, str, str]:
    """Prompt for framework/language selection and return scaffold parameters."""
    framework_options = SUPPORTED_FRAMEWORKS.copy()
    selected_framework = _select_menu_option("Select framework:", framework_options)

    language_options = sorted(_FRAMEWORK_LANGUAGE_COMPATIBILITY[selected_framework])
    if len(language_options) == 1:
        selected_language = language_options[0]
        print(f"Selected language: {selected_language}")
    else:
        selected_language = _select_menu_option("Select language:", language_options)

    base_name = f"{selected_framework}-agent" if selected_framework != "no-framework" else "agent"
    agent_name = base_name
    suffix = 1
    while (target_dir / agent_name).exists():
        suffix += 1
        agent_name = f"{base_name}-{suffix}"

    return selected_framework, selected_language, agent_name


def _extract_package_name(line: str) -> str:
    """Extract package name from a requirements.txt line (strip version specifiers)."""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("-"):
        return ""
    # Split on version specifiers
    for sep in (">=", "<=", "==", "!=", "~=", ">", "<", "["):
        if sep in line:
            return line.split(sep)[0].strip().lower()
    return line.lower()


def _merge_requirements(agent_dir: Path, new_requirements: str) -> None:
    """Write requirements.txt, merging with existing if present (task183)."""
    req_path = agent_dir / "requirements.txt"
    if not req_path.exists():
        req_path.write_text(new_requirements)
        return

    existing_content = req_path.read_text()
    existing_packages = set()
    for line in existing_content.splitlines():
        pkg = _extract_package_name(line)
        if pkg:
            existing_packages.add(pkg)

    new_lines = []
    for line in new_requirements.splitlines():
        pkg = _extract_package_name(line)
        if pkg and pkg not in existing_packages:
            new_lines.append(line)

    if new_lines:
        # Ensure existing content ends with newline before appending
        if existing_content and not existing_content.endswith("\n"):
            existing_content += "\n"
        req_path.write_text(existing_content + "\n".join(new_lines) + "\n")


def _merge_package_json(agent_dir: Path, name: str, entrypoint: str) -> None:
    """Write package.json, merging with existing if present (task183)."""
    pkg_path = agent_dir / "package.json"
    new_pkg = json.loads(_NODE_PACKAGE_JSON_TEMPLATE.format(name=name, entrypoint=entrypoint))

    if not pkg_path.exists():
        pkg_path.write_text(json.dumps(new_pkg, indent=2) + "\n")
        return

    try:
        existing_pkg = json.loads(pkg_path.read_text())
    except (json.JSONDecodeError, ValueError):
        # Malformed JSON — overwrite
        pkg_path.write_text(json.dumps(new_pkg, indent=2) + "\n")
        return

    # Merge dependencies: existing entries take precedence
    new_deps = new_pkg.get("dependencies", {})
    existing_deps = existing_pkg.get("dependencies", {})
    for dep, version in new_deps.items():
        if dep not in existing_deps:
            existing_deps[dep] = version
    existing_pkg["dependencies"] = existing_deps

    pkg_path.write_text(json.dumps(existing_pkg, indent=2) + "\n")


def init_agent(
    name: str,
    target_dir: Path,
    framework: Optional[str] = None,
    language: Optional[str] = None,
    minimal: bool = False,
):
    is_no_framework = framework == "no-framework"
    selected_framework = None if is_no_framework else framework

    # task178: Support "." to init in current directory, and allow existing dirs
    if name == ".":
        agent_dir = target_dir
        name = target_dir.name
    else:
        agent_dir = target_dir / name

    normalized_language = _normalize_language(language)
    if language is not None and normalized_language is None:
        raise ValueError(
            "Unsupported language. Supported languages: "
            + ", ".join(SUPPORTED_LANGUAGES)
            + "."
        )

    if framework is not None:
        allowed_languages = _FRAMEWORK_LANGUAGE_COMPATIBILITY.get(framework, {"python"})
        chosen_language = normalized_language or ("javascript" if selected_framework == "openclaw" else "python")
        if chosen_language not in allowed_languages:
            allowed_label = ", ".join(sorted(allowed_languages))
            raise ValueError(
                f"Incompatible --framework/--language combination: {framework} + {chosen_language}. "
                f"Allowed language(s) for {framework}: {allowed_label}."
            )

    effective_language = normalized_language or ("javascript" if selected_framework == "openclaw" else "python")
    go_executable: str | None = None
    if effective_language == "go":
        go_executable = _require_go_toolchain_for_init()

    entrypoint_name = {
        "python": "main.py",
        "javascript": "index.js",
        "typescript": "index.ts",
        "go": "main.go",
    }[effective_language]

    # task181: Entrypoint path includes src/ prefix
    entrypoint_path = f"src/{entrypoint_name}"

    # task178: Don't raise if directory already exists; create if needed
    agent_dir.mkdir(exist_ok=True)

    # task181: Create src/ subdirectory for entrypoint files
    (agent_dir / "src").mkdir(exist_ok=True)

    # OpenClaw uses a Node.js daemon manifest contract; MCP server uses a dedicated Python mcp-server manifest.
    if selected_framework == "openclaw":
        manifest_content = OPENCLAW_KINNOO_YAML_TEMPLATE.format(name=name)
        # Update entrypoint to src/ path
        manifest_content = manifest_content.replace("entrypoint: index.mjs", f"entrypoint: src/index.mjs")
    elif selected_framework == "mcp-server" and effective_language == "python":
        manifest_content = MCP_SERVER_KINNOO_YAML_TEMPLATE.format(name=name)
        manifest_content = manifest_content.replace("entrypoint: main.py", f"entrypoint: {entrypoint_path}")
    elif effective_language == "go":
        manifest_content = _build_go_manifest(
            name,
            entrypoint=entrypoint_path,
            runtime_type="mcp-server" if selected_framework == "mcp-server" else "one-shot",
        )
    elif effective_language in {"javascript", "typescript"}:
        manifest_content = _build_node_manifest(
            name,
            entrypoint=entrypoint_path,
            language=effective_language,
        )
    else:
        manifest_content = KINNOO_YAML_TEMPLATE.format(name=name)
        manifest_content = manifest_content.replace("entrypoint: main.py", f"entrypoint: {entrypoint_path}")

    if selected_framework is not None and not (
        selected_framework == "openclaw"
        or (selected_framework == "mcp-server" and effective_language == "python")
    ):
        manifest_content += f"framework: {selected_framework}\n"
        default_model = KNOWN_FRAMEWORK_DEFAULT_MODELS.get(selected_framework)
        if default_model is not None:
            manifest_content += f"model: {default_model}\n"

    framework_templates = {
        "gemini": (GEMINI_RUN_PY, GEMINI_REQUIREMENTS, GEMINI_README),
        "chatgpt": (CHATGPT_RUN_PY, CHATGPT_REQUIREMENTS, CHATGPT_README),
        "claude-chat": (CLAUDE_RUN_PY, CLAUDE_REQUIREMENTS, CLAUDE_README),
        "pydantic-ai": (PYDANTIC_AI_RUN_PY, PYDANTIC_AI_REQUIREMENTS, PYDANTIC_AI_README),
        "langgraph": (LANGGRAPH_RUN_PY, LANGGRAPH_REQUIREMENTS, LANGGRAPH_README),
        "openai-agents": (OPENAI_AGENTS_RUN_PY, OPENAI_AGENTS_REQUIREMENTS, OPENAI_AGENTS_README),
        "mcp-client": (MCP_CLIENT_RUN_PY, MCP_CLIENT_REQUIREMENTS, MCP_CLIENT_README),
        "mcp-server": (MCP_SERVER_RUN_PY, MCP_SERVER_REQUIREMENTS, MCP_SERVER_README),
    }
    go_framework_templates = {
        "gemini": (GEMINI_GO_MAIN, GEMINI_GO_README),
        "chatgpt": (CHATGPT_GO_MAIN, CHATGPT_GO_README),
        "claude-chat": (CLAUDE_GO_MAIN, CLAUDE_GO_README),
        "mcp-client": (MCP_CLIENT_GO_MAIN, MCP_CLIENT_GO_README),
        "mcp-server": (MCP_SERVER_GO_MAIN, MCP_SERVER_GO_README),
    }

    # Write files
    (agent_dir / "kinnoo.yaml").write_text(manifest_content)
    if selected_framework == "openclaw":
        (agent_dir / "AGENTS.md").write_text(OPENCLAW_AGENTS_MD_TEMPLATE)
        (agent_dir / "IDENTITY.md").write_text(_OPENCLAW_IDENTITY_TEMPLATE)
        (agent_dir / "SOUL.md").write_text(OPENCLAW_SOUL_MD_TEMPLATE)
        (agent_dir / "USER.md").write_text(_OPENCLAW_USER_TEMPLATE)
        readme_text = _standardize_readme(
            OPENCLAW_README_TEMPLATE.format(name=name),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)

        if not minimal:
            (agent_dir / "BOOTSTRAP.md").write_text(_OPENCLAW_BOOTSTRAP_TEMPLATE)
            (agent_dir / "HEARTBEAT.md").write_text(_OPENCLAW_HEARTBEAT_TEMPLATE)
            (agent_dir / "MEMORY.md").write_text(_OPENCLAW_MEMORY_TEMPLATE)
            (agent_dir / "skills").mkdir(exist_ok=True)
            (agent_dir / "memory").mkdir(exist_ok=True)
        return

    if selected_framework in framework_templates and effective_language != "go":
        run_template, requirements_template, readme_template = framework_templates[selected_framework]
        (agent_dir / "src" / entrypoint_name).write_text(run_template)
        _merge_requirements(agent_dir, requirements_template)
        readme_text = _standardize_readme(
            readme_template.format(name=name),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)
    elif selected_framework in go_framework_templates:
        run_template, readme_template = go_framework_templates[selected_framework]
        (agent_dir / "src" / entrypoint_name).write_text(run_template)
        readme_text = _standardize_readme(
            readme_template.format(name=name),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)
    elif effective_language == "javascript":
        (agent_dir / "src" / "index.js").write_text(_JS_RUN_TEMPLATE)
        _merge_package_json(agent_dir, name, entrypoint_path)
        readme_text = _standardize_readme(
            _NODE_README_TEMPLATE.format(
                name=name,
                language_flag="js",
                entrypoint=entrypoint_path,
            ),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)
    elif effective_language == "typescript":
        (agent_dir / "src" / "index.ts").write_text(_TS_RUN_TEMPLATE)
        _merge_package_json(agent_dir, name, entrypoint_path)
        readme_text = _standardize_readme(
            _NODE_README_TEMPLATE.format(
                name=name,
                language_flag="ts",
                entrypoint=entrypoint_path,
            ),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)
    elif effective_language == "go":
        (agent_dir / "src" / "main.go").write_text(GO_RUN_TEMPLATE)
        readme_text = _standardize_readme(
            GO_README_TEMPLATE.format(name=name),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)
    else:
        (agent_dir / "src" / "main.py").write_text(RUN_PY_TEMPLATE)
        _merge_requirements(agent_dir, REQUIREMENTS_TXT_TEMPLATE)
        readme_text = _standardize_readme(
            README_MD_TEMPLATE.format(name=name),
            entrypoint=entrypoint_path,
            include_folder_table=not minimal,
        )
        (agent_dir / "README.kinnoo.md").write_text(readme_text)

    if not minimal:
        # task182: Use exist_ok=True to not override existing directories
        for folder_name in ("tools", "prompts", "evals", "tests", "data"):
            (agent_dir / folder_name).mkdir(exist_ok=True)

    if effective_language == "go":
        assert go_executable is not None
        _initialize_go_module(agent_dir, name, go_executable)
        if selected_framework in {"mcp-client", "mcp-server"}:
            _pin_go_module_dependency(
                agent_dir,
                module=GO_MCP_SDK_MODULE,
                version=GO_MCP_SDK_VERSION,
                go_executable=go_executable,
            )

def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new Kinnoo agent directory with manifest and templates."
    )
    parser.add_argument("agent_name", nargs="?", help="Name of the agent directory to create.")
    parser.add_argument("--framework", type=str, default=None, help="Optional framework for agent template.")
    parser.add_argument("--language", type=str, default=None, help="Optional language (python/js/ts/go) for agent template.")
    args = parser.parse_args()

    # Print usage if agent_name is missing
    if not args.agent_name:
        print("Usage: kinnoo init <agent_name> [--framework <framework>]", file=sys.stderr)
        sys.exit(1)

    framework = args.framework
    if framework is not None:
        fw = framework.lower()
        if fw not in SUPPORTED_FRAMEWORKS:
            print(f"Unsupported framework. The supported frameworks are: {', '.join(SUPPORTED_FRAMEWORKS)}.", file=sys.stderr)
            print("Usage: kinnoo init <agent_name> [--framework <framework>]", file=sys.stderr)
            sys.exit(1)
        framework = fw

    language = args.language
    if language is not None:
        language = language.lower()
        if language not in SUPPORTED_LANGUAGES:
            print(
                f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}.",
                file=sys.stderr,
            )
            print(
                "Usage: kinnoo init <agent_name> [--framework <framework>] [--language <language>]",
                file=sys.stderr,
            )
            sys.exit(1)

    # Directory creation and template generation
    try:
        init_agent(args.agent_name, Path(os.getcwd()), framework=framework, language=language)
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
