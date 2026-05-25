import os
import subprocess
import sys
from pathlib import Path

import pytest


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"

pytestmark = [
    pytest.mark.regression_integration,
    pytest.mark.client_cli_run,
    pytest.mark.client_cli,
    pytest.mark.integration,
]


def _write_go_agent_fixture(
    agent_dir: Path,
    *,
    include_entrypoint: bool = True,
    include_go_mod: bool = True,
    dependencies: list[str] | None = None,
    runtime_path: str | None = None,
) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)

    if dependencies:
        dependency_lines = "\n".join(f"  - {dependency}" for dependency in dependencies)
        dependencies_block = f"dependencies:\n{dependency_lines}"
    else:
        dependencies_block = "dependencies: []"

    manifest_lines = [
        "name: go-source-agent",
        "version: 1.0.0",
        "entrypoint: main.go",
        "runtime:",
        "  language: go",
        "  version: \">=1.22\"",
        "  type: one-shot",
    ]
    if runtime_path is not None:
        manifest_lines.append(f"  path: \"{runtime_path}\"")
    manifest_lines.extend(
        [
            dependencies_block,
            "inputs:",
            "  type: text",
            "outputs:",
            "  type: text",
        ]
    )

    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )

    if include_entrypoint:
        (agent_dir / "main.go").write_text(
            "package main\n\n"
            "import \"fmt\"\n\n"
            "func main() {\n"
            "    fmt.Println(\"fixture-main\")\n"
            "}\n",
            encoding="utf-8",
        )

    if include_go_mod:
        (agent_dir / "go.mod").write_text(
            "module example.com/go-source-agent\n\n"
            "go 1.22\n",
            encoding="utf-8",
        )


def _write_fake_go_toolchain(fake_bin: Path) -> Path:
    fake_bin.mkdir(parents=True, exist_ok=True)
    go_script = fake_bin / "go"
    go_script.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "if [ \"${1:-}\" = \"version\" ]; then\n"
        "  echo \"go version go1.22.5 darwin/arm64\"\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"run\" ]; then\n"
        "  entrypoint=\"${2:-}\"\n"
        "  payload=\"${3:-}\"\n"
        "  echo \"go-run-stdout:${entrypoint}:${payload}\"\n"
        "  echo \"go-run-stderr:${payload}\" >&2\n"
        "  if [ \"${payload}\" = \"fail\" ]; then\n"
        "    exit 7\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "echo \"unexpected fake-go invocation: $*\" >&2\n"
        "exit 64\n",
        encoding="utf-8",
    )
    go_script.chmod(0o755)
    return go_script


def _env_with_path(path_dir: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PATH": f"{path_dir}{os.pathsep}{os.environ.get('PATH', '')}",
    }


def test_go_source_run_executes_with_go_run_and_propagates_streams_and_exit_code(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-run-agent"
    _write_go_agent_fixture(agent_dir, include_entrypoint=True, include_go_mod=True)

    fake_bin = tmp_path / "fake-bin"
    _write_fake_go_toolchain(fake_bin)
    env = _env_with_path(fake_bin)

    success_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "hello"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert success_result.returncode == 0
    assert "go-run-stdout:" in success_result.stdout
    assert "main.go:hello" in success_result.stdout
    assert "go-run-stderr:hello" in success_result.stderr

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "fail"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert fail_result.returncode == 7
    assert "go-run-stdout:" in fail_result.stdout
    assert "main.go:fail" in fail_result.stdout
    assert "go-run-stderr:fail" in fail_result.stderr


def test_go_source_preflight_passes_with_toolchain_and_module_warning(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-preflight-pass-agent"
    _write_go_agent_fixture(agent_dir, include_entrypoint=True, include_go_mod=False)

    fake_bin = tmp_path / "fake-bin"
    _write_fake_go_toolchain(fake_bin)
    env = _env_with_path(fake_bin)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "[PASS] runtime version check passed: current Go 1.22.5 satisfies runtime.version '>=1.22'" in output
    assert "[PASS] entrypoint check passed" in output
    assert "[PASS] dependency readiness check passed" in output
    assert "[WARN] module readiness warning: go.mod not found" in output
    assert "Preflight result: PASS" in output


def test_go_source_preflight_fails_when_entrypoint_missing(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-preflight-missing-entrypoint-agent"
    _write_go_agent_fixture(agent_dir, include_entrypoint=False, include_go_mod=True)

    fake_bin = tmp_path / "fake-bin"
    _write_fake_go_toolchain(fake_bin)
    env = _env_with_path(fake_bin)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "[FAIL] manifest validates against kinnoo schema" in output
    assert "Declared entrypoint path not found: 'main.go'." in output
    assert "Preflight result: FAIL" in output


def test_go_source_preflight_fails_when_go_toolchain_missing(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-preflight-missing-toolchain-agent"
    _write_go_agent_fixture(agent_dir, include_entrypoint=True, include_go_mod=True)

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(empty_bin)},
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "[FAIL] runtime version check failed: Go toolchain not found on PATH" in output
    assert "Preflight result: FAIL" in output


def test_go_source_run_uses_runtime_path_when_go_not_on_path(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fake-bin"
    go_executable = _write_fake_go_toolchain(fake_bin)

    agent_dir = tmp_path / "go-run-runtime-path-agent"
    _write_go_agent_fixture(
        agent_dir,
        include_entrypoint=True,
        include_go_mod=True,
        runtime_path=str(go_executable),
    )

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "runtime-path"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(empty_bin)},
    )

    assert result.returncode == 0
    assert "go-run-stdout:" in result.stdout
    assert "main.go:runtime-path" in result.stdout
    assert "go-run-stderr:runtime-path" in result.stderr


def test_go_source_preflight_fails_when_go_mod_missing_with_declared_dependencies(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-preflight-missing-go-mod-with-deps-agent"
    _write_go_agent_fixture(
        agent_dir,
        include_entrypoint=True,
        include_go_mod=False,
        dependencies=["github.com/google/uuid"],
    )

    fake_bin = tmp_path / "fake-bin"
    _write_fake_go_toolchain(fake_bin)
    env = _env_with_path(fake_bin)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "[FAIL] dependency readiness check failed: go.mod not found" in output
    assert "while dependencies are declared [github.com/google/uuid]" in output
    assert "Action: add go.mod with `go mod init <module>` and keep dependencies in sync" in output
    assert "Preflight result: FAIL" in output
