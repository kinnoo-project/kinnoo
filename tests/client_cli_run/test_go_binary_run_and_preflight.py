import os
import platform
import shutil
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


def _write_go_binary_agent_fixture(agent_dir: Path, *, entrypoint: str) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: go-binary-agent",
                "version: 1.0.0",
                f"entrypoint: {entrypoint}",
                "runtime:",
                "  language: go",
                "  version: \">=1.22\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "  required: false",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _host_go_platform() -> tuple[str, str]:
    if sys.platform.startswith("linux"):
        goos = "linux"
    elif sys.platform == "darwin":
        goos = "darwin"
    elif sys.platform.startswith("win"):
        goos = "windows"
    else:
        goos = sys.platform

    machine = platform.machine().strip().lower()
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
        "armv8": "arm64",
        "armv7": "arm",
        "armv7l": "arm",
        "armv6": "arm",
        "armv6l": "arm",
        "i386": "386",
        "i686": "386",
        "x86": "386",
    }
    return goos, arch_map.get(machine, machine)


def _resolve_echo_binary() -> Path:
    candidates = [
        Path("/bin/echo"),
        Path("/usr/bin/echo"),
    ]
    discovered = shutil.which("echo")
    if discovered:
        candidates.append(Path(discovered))

    for candidate in candidates:
        if candidate.exists() and candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    pytest.skip("No executable echo binary found on host for compatibility fixture")


def _copy_executable_binary(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)
    destination.chmod(0o755)


def _write_incompatible_binary_header(binary_path: Path) -> None:
    host_os, host_arch = _host_go_platform()

    if host_os == "darwin":
        mismatched_arch = "amd64" if host_arch != "amd64" else "arm64"
        cputype = 0x01000007 if mismatched_arch == "amd64" else 0x0100000C
        header = b"\xFE\xED\xFA\xCF" + cputype.to_bytes(4, "big") + (b"\x00" * 24)
    elif host_os == "linux":
        mismatched_arch = "amd64" if host_arch != "amd64" else "arm64"
        machine = 0x3E if mismatched_arch == "amd64" else 0xB7
        header_bytes = bytearray(64)
        header_bytes[0:4] = b"\x7FELF"
        header_bytes[4] = 2
        header_bytes[5] = 1
        header_bytes[6] = 1
        header_bytes[18:20] = machine.to_bytes(2, "little")
        header = bytes(header_bytes)
    else:
        pytest.skip("Host platform not supported by binary compatibility fixture")

    binary_path.write_bytes(header)
    binary_path.chmod(0o755)


def test_go_binary_run_executes_compatible_artifact_without_go_toolchain(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-binary-run-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="agent-bin")

    target_binary = agent_dir / "agent-bin"
    _copy_executable_binary(Path(sys.executable), target_binary)

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--", "-V"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(empty_bin)},
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Python" in output


def test_go_binary_preflight_passes_for_compatible_artifact_without_go_toolchain(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-binary-preflight-pass-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="agent-bin")

    target_binary = agent_dir / "agent-bin"
    _copy_executable_binary(Path(sys.executable), target_binary)

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(empty_bin)},
    )

    host_os, host_arch = _host_go_platform()
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "[PASS] runtime version check passed: Go toolchain check skipped for precompiled binary entrypoint" in output
    assert "[PASS] dependency readiness check passed: precompiled binary entrypoint does not require go.mod" in output
    assert "[PASS] binary compatibility check passed" in output
    assert f"host {host_os}/{host_arch}" in output
    assert "Preflight result: PASS" in output


def test_go_binary_preflight_fails_for_architecture_mismatch(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-binary-arch-mismatch-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="wrong-arch-bin")

    binary_path = agent_dir / "wrong-arch-bin"
    _write_incompatible_binary_header(binary_path)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    host_os, host_arch = _host_go_platform()
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "[FAIL] binary compatibility check failed" in output
    assert "detected target architecture" in output
    assert "incompatible with host" in output
    assert f"GOOS={host_os}" in output
    assert f"GOARCH={host_arch}" in output
    assert "Preflight result: FAIL" in output


def test_go_binary_preflight_fails_for_unsupported_format(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-binary-unsupported-format-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="not-a-binary")

    bad_entrypoint = agent_dir / "not-a-binary"
    bad_entrypoint.write_text("this is not a binary header\n", encoding="utf-8")
    bad_entrypoint.chmod(0o755)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "[FAIL] binary compatibility check failed" in output
    assert "unsupported executable format" in output
    assert "Mach-O, ELF, or PE" in output
    assert "Preflight result: FAIL" in output
    assert "- binary compatibility: rebuild for host GOOS/GOARCH" in output


def test_go_binary_preflight_fails_when_entrypoint_not_executable(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Executable permission bit semantics differ on Windows")

    agent_dir = tmp_path / "go-binary-non-executable-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="non-executable-bin")

    target_binary = agent_dir / "non-executable-bin"
    target_binary.write_text("placeholder\n", encoding="utf-8")
    target_binary.chmod(0o644)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "[FAIL] binary compatibility check failed" in output
    assert "entrypoint is not executable" in output
    assert "chmod +x" in output
    assert "Preflight result: FAIL" in output


def test_go_binary_preflight_reports_missing_entrypoint_file(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-binary-missing-entrypoint-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="missing-bin")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "[FAIL] manifest validates against kinnoo schema" in output
    assert "Declared entrypoint path not found: 'missing-bin'." in output


def test_go_binary_run_fails_fast_for_unsupported_format(tmp_path: Path) -> None:
    agent_dir = tmp_path / "go-binary-run-unsupported-format-agent"
    _write_go_binary_agent_fixture(agent_dir, entrypoint="bad-bin")

    bad_entrypoint = agent_dir / "bad-bin"
    bad_entrypoint.write_text("not a valid executable\n", encoding="utf-8")
    bad_entrypoint.chmod(0o755)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "hello"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Error: binary compatibility check failed" in output
    assert "unsupported executable format" in output
