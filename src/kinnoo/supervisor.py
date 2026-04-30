from __future__ import annotations

import json
import os
import socket
import signal
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


DEFAULT_READINESS_TIMEOUT_SECONDS = 5.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.05


@dataclass
class ReadinessConfig:
    mode: str
    port: int | None = None
    marker: str | None = None
    timeout_seconds: float = DEFAULT_READINESS_TIMEOUT_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS


@dataclass
class StreamState:
    stdout_lines: deque[str]
    stderr_lines: deque[str]
    stdout_thread: threading.Thread | None
    stderr_thread: threading.Thread | None


@dataclass
class ShutdownReport:
    exit_code: int
    sigterm_sent: bool
    sigkill_sent: bool


@dataclass
class DaemonStopReport:
    pid: int
    terminated: bool
    already_stopped: bool
    sigterm_sent: bool
    sigkill_sent: bool


def daemon_runtime_dir(agent_dir: Path) -> Path:
    """Return the deterministic runtime metadata directory for daemon control plane files."""
    return agent_dir / ".kinnoo"


def daemon_state_path(agent_dir: Path) -> Path:
    """Return the daemon state metadata path for a given agent directory."""
    return daemon_runtime_dir(agent_dir) / "daemon-state.json"


def daemon_log_path(agent_dir: Path) -> Path:
    """Return the daemon log path for a given agent directory."""
    return daemon_runtime_dir(agent_dir) / "daemon.log"


def clear_daemon_state(agent_dir: Path) -> None:
    """Remove persisted daemon state when lifecycle control reaches a terminal stop state."""
    state_file = daemon_state_path(agent_dir)
    try:
        state_file.unlink()
    except FileNotFoundError:
        return


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but current user cannot signal it.
        return True
    return True


def daemon_pid_is_running(pid: int) -> bool:
    """Return whether a daemon PID currently exists from the local process table."""
    return _pid_is_running(pid)


def stop_daemon_pid(
    pid: int,
    timeout_seconds: float = 3.0,
    poll_interval_seconds: float = 0.05,
) -> DaemonStopReport:
    """Stop a daemon process with SIGTERM first, then SIGKILL as a deterministic fallback."""
    if pid <= 0:
        return DaemonStopReport(
            pid=pid,
            terminated=False,
            already_stopped=False,
            sigterm_sent=False,
            sigkill_sent=False,
        )

    if not _pid_is_running(pid):
        return DaemonStopReport(
            pid=pid,
            terminated=True,
            already_stopped=True,
            sigterm_sent=False,
            sigkill_sent=False,
        )

    try:
        os.kill(pid, signal.SIGTERM)
        sigterm_sent = True
    except ProcessLookupError:
        return DaemonStopReport(
            pid=pid,
            terminated=True,
            already_stopped=True,
            sigterm_sent=False,
            sigkill_sent=False,
        )

    timeout_seconds = max(0.0, timeout_seconds)
    poll_interval_seconds = max(0.01, poll_interval_seconds)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() <= deadline:
        if not _pid_is_running(pid):
            return DaemonStopReport(
                pid=pid,
                terminated=True,
                already_stopped=False,
                sigterm_sent=sigterm_sent,
                sigkill_sent=False,
            )
        time.sleep(poll_interval_seconds)

    try:
        os.kill(pid, signal.SIGKILL)
        sigkill_sent = True
    except ProcessLookupError:
        return DaemonStopReport(
            pid=pid,
            terminated=True,
            already_stopped=False,
            sigterm_sent=sigterm_sent,
            sigkill_sent=False,
        )

    # After SIGKILL we evaluate one final time to ensure deterministic reporting.
    terminated = not _pid_is_running(pid)
    return DaemonStopReport(
        pid=pid,
        terminated=terminated,
        already_stopped=False,
        sigterm_sent=sigterm_sent,
        sigkill_sent=sigkill_sent,
    )


def write_daemon_state(agent_dir: Path, state: dict[str, object]) -> Path:
    """Persist daemon state metadata atomically for downstream lifecycle commands."""
    runtime_dir = daemon_runtime_dir(agent_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    state_file = daemon_state_path(agent_dir)
    temp_file = state_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    temp_file.replace(state_file)
    return state_file


def build_daemon_state_payload(
    *,
    agent_dir: Path,
    runtime_language: str,
    runtime_type: str,
    entrypoint: str,
    process_id: int,
    process_args: list[str],
    log_path: Path,
) -> dict[str, object]:
    """Build deterministic daemon state metadata content."""
    return {
        "agent_dir": str(agent_dir),
        "entrypoint": entrypoint,
        "runtime_language": runtime_language,
        "runtime_type": runtime_type,
        "pid": int(process_id),
        "command": process_args,
        "log_path": str(log_path),
        "started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "state_version": 1,
    }


def infer_readiness_config(runtime_section: dict) -> ReadinessConfig:
    """Infer readiness behavior from runtime settings.

    Priority:
    1. Explicit readiness_probe settings.
    2. Fallback to TCP when runtime.port is configured.
    3. Otherwise immediate-ready mode.
    """
    readiness_probe = runtime_section.get("readiness_probe")
    if isinstance(readiness_probe, dict):
        method = readiness_probe.get("method")
        if method == "tcp":
            port = readiness_probe.get("port")
            if isinstance(port, int) and port > 0:
                return ReadinessConfig(mode="tcp", port=port)
        if method == "stdout":
            marker = readiness_probe.get("marker")
            if isinstance(marker, str) and marker.strip():
                return ReadinessConfig(mode="stdout", marker=marker)

    runtime_port = runtime_section.get("port")
    if isinstance(runtime_port, int) and runtime_port > 0:
        return ReadinessConfig(mode="tcp", port=runtime_port)

    return ReadinessConfig(mode="immediate")


def start_server(
    command: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _stream_pipe(
    pipe,
    sink: deque[str],
    callback: Callable[[str], None] | None,
) -> None:
    if pipe is None:
        return
    for line in iter(pipe.readline, ""):
        sink.append(line)
        if callback is not None:
            callback(line)
    pipe.close()


def stream_output(
    process: subprocess.Popen[str],
    stdout_callback: Callable[[str], None] | None = None,
    stderr_callback: Callable[[str], None] | None = None,
) -> StreamState:
    stdout_lines: deque[str] = deque(maxlen=1024)
    stderr_lines: deque[str] = deque(maxlen=1024)

    stdout_thread: threading.Thread | None = None
    stderr_thread: threading.Thread | None = None

    if process.stdout is not None:
        stdout_thread = threading.Thread(
            target=_stream_pipe,
            args=(process.stdout, stdout_lines, stdout_callback),
            daemon=True,
        )
        stdout_thread.start()

    if process.stderr is not None:
        stderr_thread = threading.Thread(
            target=_stream_pipe,
            args=(process.stderr, stderr_lines, stderr_callback),
            daemon=True,
        )
        stderr_thread.start()

    return StreamState(
        stdout_lines=stdout_lines,
        stderr_lines=stderr_lines,
        stdout_thread=stdout_thread,
        stderr_thread=stderr_thread,
    )


def _is_tcp_ready(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_until_ready(
    process: subprocess.Popen[str],
    readiness: ReadinessConfig,
    stream_state: StreamState | None = None,
) -> bool:
    if readiness.mode == "immediate":
        return True

    start_time = time.monotonic()
    timeout_seconds = max(0.0, readiness.timeout_seconds)
    poll_interval = max(0.01, readiness.poll_interval_seconds)

    while (time.monotonic() - start_time) <= timeout_seconds:
        if process.poll() is not None:
            return False

        if readiness.mode == "tcp":
            if isinstance(readiness.port, int) and readiness.port > 0 and _is_tcp_ready(readiness.port):
                return True

        elif readiness.mode == "stdout":
            if stream_state is None:
                return False
            marker = readiness.marker or ""
            if marker and any(marker in line for line in stream_state.stdout_lines):
                return True

        time.sleep(poll_interval)

    return False


def shutdown_server_with_report(
    process: subprocess.Popen[str],
    timeout_seconds: float = 3.0,
) -> ShutdownReport:
    """Attempt SIGTERM first, then escalate to SIGKILL when required."""
    if process.poll() is not None:
        return ShutdownReport(
            exit_code=int(process.returncode or 0),
            sigterm_sent=False,
            sigkill_sent=False,
        )

    process.send_signal(signal.SIGTERM)
    try:
        exit_code = process.wait(timeout=max(0.1, timeout_seconds))
        return ShutdownReport(
            exit_code=int(exit_code),
            sigterm_sent=True,
            sigkill_sent=False,
        )
    except subprocess.TimeoutExpired:
        process.send_signal(signal.SIGKILL)
        return ShutdownReport(
            exit_code=int(process.wait()),
            sigterm_sent=True,
            sigkill_sent=True,
        )


def shutdown_server(process: subprocess.Popen[str], timeout_seconds: float = 3.0) -> int:
    """Backward-compatible shutdown API returning only process exit code."""
    return shutdown_server_with_report(process, timeout_seconds=timeout_seconds).exit_code