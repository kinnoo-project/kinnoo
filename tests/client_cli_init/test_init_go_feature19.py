from __future__ import annotations

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
        "readme_markers": ["go run main.go", "--language go"],
    },
    {
        "id": "test79-ac2-gemini-go",
        "framework": "gemini",
        "runtime_type": "one-shot",
        "expected_framework": "gemini",
        "expected_model": "gemini-2.5-flash-lite",
        "main_markers": ["[gemini-go template]", "GOOGLE_API_KEY", "gemini-2.5-flash-lite"],
        "readme_markers": ["GOOGLE_API_KEY", "Hello Gemini from Go"],
    },
    {
        "id": "test79-ac3-chatgpt-go",
        "framework": "chatgpt",
        "runtime_type": "one-shot",
        "expected_framework": "chatgpt",
        "expected_model": "gpt-5-nano",
        "main_markers": ["[chatgpt-go template]", "OPENAI_API_KEY", "gpt-5-nano"],
        "readme_markers": ["OPENAI_API_KEY", "Hello ChatGPT from Go"],
    },
    {
        "id": "test79-ac4-claude-go",
        "framework": "claude-chat",
        "runtime_type": "one-shot",
        "expected_framework": "claude-chat",
        "expected_model": "claude-sonnet-4-20250514",
        "main_markers": ["[claude-chat-go template]", "ANTHROPIC_API_KEY", "claude-sonnet-4-20250514"],
        "readme_markers": ["ANTHROPIC_API_KEY", "Hello Claude from Go"],
    },
    {
        "id": "test79-ac5-mcp-server-go",
        "framework": "mcp-server",
        "runtime_type": "mcp-server",
        "expected_framework": "mcp-server",
        "expected_model": None,
        "main_markers": ["kinnoo-mcp-server-template-go", "tools/list", "initialize"],
        "readme_markers": ["go run main.go", "Quick Handshake Smoke Test"],
    },
    {
        "id": "test79-ac6-mcp-client-go",
        "framework": "mcp-client",
        "runtime_type": "one-shot",
        "expected_framework": "mcp-client",
        "expected_model": None,
        "main_markers": ["[mcp-client-go template]", "MCP_SERVER_CMD", "initialize"],
        "readme_markers": ["MCP_SERVER_CMD", "MCP_SERVER_ARGS", "go run main.go"],
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

    result = run_kinnoo_cli(args, cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    agent_dir = tmp_path / agent_name
    manifest_path = agent_dir / "kinnoo.yaml"
    main_path = agent_dir / "main.go"
    readme_path = agent_dir / "README.md"
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

    main_text = main_path.read_text(encoding="utf-8")
    for marker in case["main_markers"]:
        assert str(marker) in main_text

    readme_text = readme_path.read_text(encoding="utf-8")
    for marker in case["readme_markers"]:
        assert str(marker) in readme_text

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["entrypoint"] == "main.go"
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
