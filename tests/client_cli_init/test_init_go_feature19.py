from __future__ import annotations

import os
import platform
from pathlib import Path

import pytest
import yaml

from kinnoo.validator import validate
from tests.helpers import run_cli as run_kinnoo_cli

_GO_INIT_MATRIX_CASES = [
    {
        "id": "test79-ac1-default-go",
        "framework": None,
        "runtime_type": "one-shot",
        "expected_framework": None,
        "expected_model": None,
        "main_markers": ["Hello from Go agent."],
        "go_mod_markers": [],
        "readme_markers": ["go run main.go", "--language go"],
    },
    {
        "id": "test79-ac2-gemini-go",
        "framework": "gemini",
        "runtime_type": "one-shot",
        "expected_framework": "gemini",
        "expected_model": "gemini-2.5-flash-lite",
        "main_markers": ["[gemini-go template]", "GOOGLE_API_KEY", "gemini-2.5-flash-lite"],
        "go_mod_markers": [],
        "readme_markers": ["GOOGLE_API_KEY", "Hello Gemini from Go"],
    },
    {
        "id": "test79-ac3-chatgpt-go",
        "framework": "chatgpt",
        "runtime_type": "one-shot",
        "expected_framework": "chatgpt",
        "expected_model": "gpt-5-nano",
        "main_markers": ["[chatgpt-go template]", "OPENAI_API_KEY", "gpt-5-nano"],
        "go_mod_markers": [],
        "readme_markers": ["OPENAI_API_KEY", "Hello ChatGPT from Go"],
    },
    {
        "id": "test79-ac4-claude-go",
        "framework": "claude-chat",
        "runtime_type": "one-shot",
        "expected_framework": "claude-chat",
        "expected_model": "claude-sonnet-4-20250514",
        "main_markers": ["[claude-chat-go template]", "ANTHROPIC_API_KEY", "claude-sonnet-4-20250514"],
        "go_mod_markers": [],
        "readme_markers": ["ANTHROPIC_API_KEY", "Hello Claude from Go"],
    },
    {
        "id": "test79-ac5-mcp-server-go",
        "framework": "mcp-server",
        "runtime_type": "mcp-server",
        "expected_framework": "mcp-server",
        "expected_model": None,
        "main_markers": [
            "github.com/modelcontextprotocol/go-sdk/mcp",
            "mcp.NewServer",
            "mcp.AddTool",
            "kinnoo-mcp-server-template-go",
        ],
        "go_mod_markers": ["github.com/modelcontextprotocol/go-sdk v1.4.1"],
        "readme_markers": ["official MCP Go SDK", "v1.4.1", "breaking changes"],
    },
    {
        "id": "test79-ac6-mcp-client-go",
        "framework": "mcp-client",
        "runtime_type": "one-shot",
        "expected_framework": "mcp-client",
        "expected_model": None,
        "main_markers": [
            "github.com/modelcontextprotocol/go-sdk/mcp",
            "mcp.NewClient",
            "mcp.CommandTransport",
            "session.CallTool",
        ],
        "go_mod_markers": ["github.com/modelcontextprotocol/go-sdk v1.4.1"],
        "readme_markers": ["official MCP Go SDK", "v1.4.1", "MCP_SERVER_CMD"],
    },
]

_NON_GO_ENTRYPOINT_FILES = [
    "main.py",
    "run.py",
    "run.js",
    "run.ts",
    "index.js",
    "index.ts",
]


def _build_fake_go_env(tmp_path: Path) -> dict[str, str]:
    fake_bin = tmp_path / "fake-go-bin"
    fake_bin.mkdir(exist_ok=True)
    fake_go = fake_bin / "go"
    fake_go.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"mod\" ] && [ \"$2\" = \"init\" ]; then\n"
        "  module_name=$3\n"
        "  printf 'module %s\\n\\ngo 1.22\\n' \"$module_name\" > go.mod\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"mod\" ] && [ \"$2\" = \"edit\" ]; then\n"
        "  requirement=${3#-require=}\n"
        "  requirement=$(printf '%s' \"$requirement\" | tr '@' ' ')\n"
        "  if [ ! -f go.mod ]; then\n"
        "    echo 'go.mod not initialized' >&2\n"
        "    exit 1\n"
        "  fi\n"
        "  printf '\\nrequire %s\\n' \"$requirement\" >> go.mod\n"
        "  exit 0\n"
        "fi\n"
        "echo 'unsupported fake go command' >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake_go.chmod(0o755)

    env = os.environ.copy()
    existing_path = env.get("PATH", "")
    env["PATH"] = f"{fake_bin}{os.pathsep}{existing_path}" if existing_path else str(fake_bin)
    return env


@pytest.mark.regression_integration
@pytest.mark.client_cli_init
@pytest.mark.client_cli
@pytest.mark.integration
@pytest.mark.parametrize("case", _GO_INIT_MATRIX_CASES, ids=[case["id"] for case in _GO_INIT_MATRIX_CASES])
def test_feature19_test79_go_init_matrix(case: dict[str, object], tmp_path: Path) -> None:
    framework = case["framework"]
    case_id = str(case["id"])
    agent_name = f"feature19-{case_id}"

    args: list[str] = ["init"]
    if framework is not None:
        args.append(str(framework))
    args.extend(["--language", "go", agent_name])

    result = run_kinnoo_cli(args, cwd=tmp_path, env=_build_fake_go_env(tmp_path))
    assert result.returncode == 0, result.stderr

    agent_dir = tmp_path / agent_name
    manifest_path = agent_dir / "kinnoo.yaml"
    main_path = agent_dir / "src" / "main.go"
    readme_path = agent_dir / "README.kinnoo.md"
    go_mod_path = agent_dir / "go.mod"

    assert manifest_path.exists()
    assert main_path.exists()
    assert readme_path.exists()
    assert go_mod_path.exists()
    assert not (agent_dir / "requirements.txt").exists()
    assert not (agent_dir / "package.json").exists()
    for file_name in _NON_GO_ENTRYPOINT_FILES:
        assert not (agent_dir / file_name).exists()

    go_mod_text = go_mod_path.read_text(encoding="utf-8")
    assert f"module {agent_name}" in go_mod_text
    for marker in case["go_mod_markers"]:
        assert str(marker) in go_mod_text

    main_text = main_path.read_text(encoding="utf-8")
    for marker in case["main_markers"]:
        assert str(marker) in main_text

    readme_text = readme_path.read_text(encoding="utf-8")
    for marker in case["readme_markers"]:
        assert str(marker) in readme_text

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["entrypoint"] == "src/main.go"
    assert manifest["runtime"]["language"] == "go"
    assert manifest["runtime"]["type"] == case["runtime_type"]

    expected_framework = case["expected_framework"]
    if expected_framework is None:
        assert "framework" not in manifest
    else:
        assert manifest.get("framework") == expected_framework

    expected_model = case["expected_model"]
    if expected_model is None:
        assert "model" not in manifest
    else:
        assert manifest.get("model") == expected_model

    is_valid, errors = validate(str(manifest_path))
    assert is_valid is True, errors
    assert errors == []


@pytest.mark.regression_integration
@pytest.mark.client_cli_init
@pytest.mark.client_cli
@pytest.mark.integration
def test_go_init_requires_go_toolchain_with_os_specific_install_hint(tmp_path: Path) -> None:
    agent_name = "feature19-go-missing-toolchain"
    env = os.environ.copy()
    env["PATH"] = ""

    result = run_kinnoo_cli(["init", "--language", "go", agent_name], cwd=tmp_path, env=env)
    assert result.returncode != 0

    output = f"{result.stdout}\n{result.stderr}"
    assert "Go toolchain is required to scaffold Go agents" in output
    assert "kinnoo init --language go" in output

    host_os = platform.system().lower()
    if host_os == "darwin":
        assert "brew install go" in output
    elif host_os == "linux":
        assert "apt install golang-go" in output
    elif host_os == "windows":
        assert "winget install GoLang.Go" in output
    else:
        assert "https://go.dev/dl/" in output

    assert not (tmp_path / agent_name).exists()
