import os
import subprocess
import sys
from pathlib import Path

import pytest


def _create_agent(agent_dir: Path, *, inputs_required: bool | None = None, print_argv_json: bool = False) -> None:
    required_block = ""
    if inputs_required is not None:
        required_value = "true" if inputs_required else "false"
        required_block = f"\n    required: {required_value}"

    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: safety-agent
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
    type: string{required_block}
outputs:
  type: string
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("\n", encoding="utf-8")
    if print_argv_json:
        run_py = "import sys, json\nprint('ARGS_JSON:' + json.dumps(sys.argv[1:]))\n"
    else:
        run_py = "import sys\nprint('AGENT_EXECUTED:' + '|'.join(sys.argv[1:]))\n"
    (agent_dir / "run.py").write_text(run_py, encoding="utf-8")


def _run_with_tty(command: list[str], response: str) -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        pytest.skip("PTY-based prompt simulation is not supported on Windows")

    import pty

    master_fd, slave_fd = pty.openpty()
    try:
        process = subprocess.Popen(
            command,
            stdin=slave_fd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        os.close(slave_fd)

    try:
        os.write(master_fd, f"{response}\n".encode("utf-8"))
        stdout_text, stderr_text = process.communicate(timeout=120)
    finally:
        os.close(master_fd)

    return subprocess.CompletedProcess(
        args=command,
        returncode=process.returncode,
        stdout=stdout_text,
        stderr=stderr_text,
    )


def test_no_guard_flag_skips_check(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agent"
    _create_agent(agent_dir)

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "'; DROP TABLE users;--",
            "--no-guard",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "[kinnoo] Input safety warning:" not in result.stderr
    assert "AGENT_EXECUTED:" in result.stdout


def test_malicious_input_abort_on_reject(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agent"
    _create_agent(agent_dir)

    result = _run_with_tty(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "'; DROP TABLE users;--",
        ],
        response="n",
    )

    assert result.returncode != 0
    assert "[kinnoo] Input safety warning:" in result.stderr
    assert "AGENT_EXECUTED:" not in result.stdout
    assert "AGENT_EXECUTED:" not in result.stderr


def test_malicious_input_proceed_on_accept(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agent"
    _create_agent(agent_dir)

    result = _run_with_tty(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "'; DROP TABLE users;--",
        ],
        response="y",
    )

    assert result.returncode == 0, result.stderr
    assert "[kinnoo] Input safety warning:" in result.stderr
    assert "AGENT_EXECUTED:" in result.stdout


def test_non_interactive_auto_aborts(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agent"
    _create_agent(agent_dir)

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "'; DROP TABLE users;--",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "[kinnoo] Input safety warning:" in result.stderr
    assert "Non-interactive mode: aborting due to input safety warning." in result.stderr
    assert "AGENT_EXECUTED:" not in result.stdout


def test_pass_through_inputs_are_guard_checked(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agent"
    _create_agent(agent_dir, inputs_required=False)

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--",
            "-e",
            "safe",
            "-u",
            "http://169.254.169.254/latest/meta-data/",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "[kinnoo] Input safety warning:" in result.stderr
    assert "[SSRF]" in result.stderr
    assert "param: -u" in result.stderr
    assert "AGENT_EXECUTED:" not in result.stdout


def test_no_guard_bypasses_pass_through_checks(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agent"
    _create_agent(agent_dir, inputs_required=False)

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--no-guard",
            "--",
            "-e",
            "' OR 1=1--",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "[kinnoo] Input safety warning:" not in result.stderr
    assert "AGENT_EXECUTED:" in result.stdout
