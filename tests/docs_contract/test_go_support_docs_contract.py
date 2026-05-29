from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_doc(path: str) -> str:
    return (_repo_root() / path).read_text(encoding="utf-8")


def test_feature19_test83_cli_help_includes_go_language_and_framework_combos() -> None:
    repo_root = _repo_root()
    result = subprocess.run(
        [sys.executable, str(repo_root / "src" / "kinnoo" / "cli.py"), "init", "--help"],
        capture_output=True,
        text=True,
    )
    help_text = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0, help_text
    assert "--language" in help_text
    assert "python, javascript, typescript, go" in help_text
    assert (
        "Go is supported for gemini, chatgpt, claude-chat, mcp-client, mcp-server, and no-framework."
        in help_text
    )

    assert "kinnoo init gemini --language go" in help_text
    assert "kinnoo init chatgpt --language go" in help_text
    assert "kinnoo init claude-chat --language go" in help_text
    assert "kinnoo init mcp-server --language go" in help_text
    assert "kinnoo init mcp-client --language go" in help_text


def test_feature19_test83_docs_cover_go_source_binary_modes_and_preflight_status() -> None:
    cli_reference = _read_doc("docs/cli-reference.md")
    getting_started = _read_doc("docs/getting-started.md")
    yaml_spec = _read_doc("docs/kinnoo-yaml-spec.md")
    readme = _read_doc("README.md")
    combined_docs = "\n".join([cli_reference, getting_started, yaml_spec, readme])

    assert "--language {python,javascript,typescript,go}" in cli_reference
    assert "Go-compatible framework combinations" in cli_reference
    assert "Go source vs binary run behavior" in cli_reference

    assert "Go source mode" in combined_docs
    assert "Go binary mode" in combined_docs
    assert "entrypoint ends with `.go`" in combined_docs
    assert "precompiled executable" in combined_docs or "precompiled Go binaries" in combined_docs

    assert "- [PASS]" in combined_docs
    assert "- [WARN]" in combined_docs
    assert "- [FAIL]" in combined_docs
    assert "Ready to run" in combined_docs
    assert "Not ready to run" in combined_docs
    assert "Remediation summary:" in combined_docs
    assert "Preflight result: PASS" in combined_docs
    assert "Preflight result: FAIL" in combined_docs


def test_feature19_test83_docs_cover_go_preflight_remediation_guidance() -> None:
    cli_reference = _read_doc("docs/cli-reference.md")
    getting_started = _read_doc("docs/getting-started.md")
    yaml_spec = _read_doc("docs/kinnoo-yaml-spec.md")
    supported_agents = _read_doc("docs/supported-agents.md")
    readme = _read_doc("README.md")
    combined_docs = "\n".join([cli_reference, getting_started, yaml_spec, supported_agents, readme])

    assert "install Go or configure `runtime.path`" in combined_docs
    assert "GOOS" in combined_docs
    assert "GOARCH" in combined_docs
    assert "Mach-O/ELF/PE" in combined_docs
    assert "chmod +x" in combined_docs

    assert "wrong architecture/OS" in combined_docs
    assert "unsupported format" in combined_docs
    assert "non-executable" in combined_docs
    assert "github.com/modelcontextprotocol/go-sdk" in combined_docs
    assert "v1.4.1" in combined_docs
    assert "breaking changes" in combined_docs
