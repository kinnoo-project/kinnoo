from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .runtime_language import is_nodejs_compatible_runtime

RUNTIME_MONITOR_EVENTS_RELATIVE_PATH = Path(".kinnoo") / "runtime-monitor-events.jsonl"
_NETWORK_EVENTS_FILENAME = "runtime-monitor-network.jsonl"
_MONITOR_SCHEMA_VERSION = "1.0"


@dataclass
class RuntimeMonitorEvent:
    category: str
    event_type: str
    details: dict[str, object]


@dataclass(frozen=True)
class ViolationEnforcementDecision:
    action: str
    reason_code: str
    hard_violation: bool


@dataclass(frozen=True)
class RuntimeResourceControls:
    max_seconds: float | None
    max_cpu_seconds: int | None
    max_memory_mb: int | None


@dataclass(frozen=True)
class RuntimeMonitorPolicySummary:
    network_allowed: bool
    filesystem_scope: str
    shell_allowed: bool
    browser_allowed: bool
    telemetry_limited: bool
    telemetry_reason_code: str | None
    telemetry_limited_capabilities: tuple[str, ...]


def normalize_runtime_resource_controls(
    *,
    max_seconds: float | None,
    max_cpu_seconds: int | None,
    max_memory_mb: int | None,
) -> RuntimeResourceControls:
    if max_seconds is not None and max_seconds <= 0:
        raise ValueError("max-seconds must be greater than 0")
    if max_cpu_seconds is not None and max_cpu_seconds <= 0:
        raise ValueError("max-cpu-seconds must be greater than 0")
    if max_memory_mb is not None and max_memory_mb <= 0:
        raise ValueError("max-memory-mb must be greater than 0")

    return RuntimeResourceControls(
        max_seconds=max_seconds,
        max_cpu_seconds=max_cpu_seconds,
        max_memory_mb=max_memory_mb,
    )


def posix_resource_limits_supported() -> bool:
    if os.name != "posix":
        return False
    try:
        import resource  # type: ignore
    except Exception:
        return False
    return hasattr(resource, "setrlimit")


def predict_dry_run_actions(
    *,
    entrypoint_path: Path,
    runtime_language: str,
    pass_through_args: list[str],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = [
        {
            "category": "process",
            "action": "process_spawn",
            "detail": f"would execute {runtime_language} entrypoint '{entrypoint_path.name}'",
        }
    ]

    script_text = ""
    try:
        script_text = entrypoint_path.read_text(encoding="utf-8")
    except Exception:
        script_text = ""

    network_markers = (
        "socket.create_connection",
        "requests.",
        "httpx.",
        "urllib.request",
    )
    filesystem_markers = (
        "write_text(",
        "write_bytes(",
        "open(",
        "Path(",
        "mkdir(",
    )

    pass_through_blob = " ".join(pass_through_args)
    if any(marker in script_text for marker in network_markers) or any(
        token in pass_through_blob for token in ("--url", "-u", "http://", "https://", "--network")
    ):
        actions.append(
            {
                "category": "network",
                "action": "network_access_attempt",
                "detail": "network access intent detected from entrypoint or pass-through arguments",
            }
        )

    if any(marker in script_text for marker in filesystem_markers) or any(
        token in pass_through_blob for token in ("--output", "-o", "--write", "--fs-write")
    ):
        actions.append(
            {
                "category": "filesystem",
                "action": "filesystem_write",
                "detail": "filesystem write intent detected from entrypoint or pass-through arguments",
            }
        )

    return actions


def resolve_monitor_policy_summary(
    *,
    manifest: dict[str, object],
    runtime_language: str,
    force_telemetry_limited: bool = False,
) -> RuntimeMonitorPolicySummary:
    permissions_raw = manifest.get("permissions")
    permissions = permissions_raw if isinstance(permissions_raw, dict) else {}

    network_allowed = bool(permissions.get("network") is True)
    filesystem_scope_raw = permissions.get("filesystem_scope")
    filesystem_scope = (
        filesystem_scope_raw.strip().lower()
        if isinstance(filesystem_scope_raw, str) and filesystem_scope_raw.strip()
        else "none"
    )
    shell_allowed = bool(permissions.get("shell") is True)
    browser_allowed = bool(permissions.get("browser") is True)

    limited_capabilities: list[str] = []
    if is_nodejs_compatible_runtime(runtime_language):
        limited_capabilities.extend(["network", "filesystem"])
    if force_telemetry_limited:
        for capability in ("network", "filesystem"):
            if capability not in limited_capabilities:
                limited_capabilities.append(capability)

    telemetry_limited = len(limited_capabilities) > 0
    reason_code = "telemetry_limited_backend" if telemetry_limited else None

    return RuntimeMonitorPolicySummary(
        network_allowed=network_allowed,
        filesystem_scope=filesystem_scope,
        shell_allowed=shell_allowed,
        browser_allowed=browser_allowed,
        telemetry_limited=telemetry_limited,
        telemetry_reason_code=reason_code,
        telemetry_limited_capabilities=tuple(limited_capabilities),
    )


def resolve_violation_enforcement(
    *,
    capability: str,
    configured_mode: str,
) -> ViolationEnforcementDecision:
    """Resolve deterministic enforcement behavior for a policy violation.

    Soft policy violations can be warning-only when configured, while critical
    capabilities always trigger hard terminate kill-switch behavior.
    """
    normalized_mode = configured_mode.strip().lower()
    if normalized_mode not in {"warn", "terminate"}:
        normalized_mode = "terminate"

    # Shell execution is treated as a critical violation regardless of mode.
    if capability == "shell":
        return ViolationEnforcementDecision(
            action="kill_switch_terminate",
            reason_code="hard_shell_execution_violation",
            hard_violation=True,
        )

    if normalized_mode == "warn":
        return ViolationEnforcementDecision(
            action="warn_continue",
            reason_code="soft_policy_warning",
            hard_violation=False,
        )

    return ViolationEnforcementDecision(
        action="kill_switch_terminate",
        reason_code="policy_terminate_mode",
        hard_violation=True,
    )


class RuntimeMonitor:
    """Best-effort runtime telemetry monitor for run execution paths.

    This baseline monitor intentionally captures a deterministic subset of events:
    process spawn, network access attempts (Python runtime), and filesystem writes.
    """

    def __init__(
        self,
        *,
        agent_dir: Path,
        runtime_language: str,
        forbidden_values: Iterable[str] | None = None,
    ) -> None:
        self._agent_dir = agent_dir.resolve()
        self._runtime_language = runtime_language
        self._forbidden_values = [value for value in (forbidden_values or []) if value]
        self._run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._events: list[RuntimeMonitorEvent] = []
        self._sequence = 0

        self._before_snapshot: dict[str, tuple[int, int]] = {}
        self._monitor_dir = self._agent_dir / ".kinnoo"
        self._network_events_path = self._monitor_dir / _NETWORK_EVENTS_FILENAME

        self._sitecustomize_dir: Path | None = None

    def prepare_environment(
        self,
        *,
        process_args: list[str],
        cwd: Path,
        env: dict[str, str],
    ) -> dict[str, str]:
        self._before_snapshot = self._snapshot_filesystem(cwd)
        self._record_event(
            category="process",
            event_type="process_spawn",
            details={
                "executable": Path(process_args[0]).name if process_args else "unknown",
                "args_count": max(len(process_args) - 1, 0),
                "cwd": str(cwd.resolve()),
            },
        )

        prepared_env = dict(env)
        if self._runtime_language == "python":
            self._monitor_dir.mkdir(parents=True, exist_ok=True)
            if self._network_events_path.exists():
                self._network_events_path.unlink()

            self._sitecustomize_dir = Path(tempfile.mkdtemp(prefix="kinnoo-runtime-monitor-"))
            sitecustomize_path = self._sitecustomize_dir / "sitecustomize.py"
            sitecustomize_path.write_text(_build_sitecustomize_source(), encoding="utf-8")

            existing_pythonpath = prepared_env.get("PYTHONPATH", "")
            if existing_pythonpath:
                prepared_env["PYTHONPATH"] = f"{self._sitecustomize_dir}{os.pathsep}{existing_pythonpath}"
            else:
                prepared_env["PYTHONPATH"] = str(self._sitecustomize_dir)
            prepared_env["KINNOO_RUNTIME_MONITOR_NETWORK_LOG"] = str(self._network_events_path)

        return prepared_env

    def finalize(self, *, exit_code: int) -> None:
        self._collect_network_events()
        self._collect_filesystem_events()
        self._write_events(exit_code=exit_code)
        self._cleanup()

    def _cleanup(self) -> None:
        if self._sitecustomize_dir is not None:
            shutil.rmtree(self._sitecustomize_dir, ignore_errors=True)
            self._sitecustomize_dir = None

    def _snapshot_filesystem(self, root: Path) -> dict[str, tuple[int, int]]:
        snapshot: dict[str, tuple[int, int]] = {}
        root = root.resolve()
        for current_root, dir_names, file_names in os.walk(root):
            rel_root = Path(current_root).resolve().relative_to(root)
            if rel_root.parts and rel_root.parts[0] in {".venv", ".git", "__pycache__", ".kinnoo"}:
                dir_names[:] = []
                continue

            for file_name in file_names:
                full_path = Path(current_root) / file_name
                if full_path.name.endswith((".pyc", ".pyo")):
                    continue
                try:
                    stat_result = full_path.stat()
                except OSError:
                    continue
                relative = str(full_path.resolve().relative_to(root))
                snapshot[relative] = (int(stat_result.st_mtime_ns), int(stat_result.st_size))
        return snapshot

    def _collect_filesystem_events(self) -> None:
        after_snapshot = self._snapshot_filesystem(self._agent_dir)
        changed_paths: list[tuple[str, str]] = []

        for relative_path, metadata in after_snapshot.items():
            before_metadata = self._before_snapshot.get(relative_path)
            if before_metadata is None:
                changed_paths.append((relative_path, "created"))
                continue
            if before_metadata != metadata:
                changed_paths.append((relative_path, "modified"))

        for relative_path, change_kind in sorted(changed_paths)[:64]:
            self._record_event(
                category="filesystem",
                event_type="filesystem_write",
                details={
                    "path": relative_path,
                    "change": change_kind,
                },
            )

    def _collect_network_events(self) -> None:
        if not self._network_events_path.exists():
            return

        try:
            lines = self._network_events_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            host = str(payload.get("host", "unknown"))
            port_value = payload.get("port", 0)
            try:
                port = int(port_value)
            except (TypeError, ValueError):
                port = 0

            self._record_event(
                category="network",
                event_type="network_access_attempt",
                details={
                    "host": host,
                    "port": port,
                    "operation": str(payload.get("operation", "connect")),
                },
            )

    def _record_event(self, *, category: str, event_type: str, details: dict[str, object]) -> None:
        self._events.append(RuntimeMonitorEvent(category=category, event_type=event_type, details=details))

    def _write_events(self, *, exit_code: int) -> None:
        if not self._events:
            return

        target_path = self._agent_dir / RUNTIME_MONITOR_EVENTS_RELATIVE_PATH
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            return

        try:
            with target_path.open("a", encoding="utf-8") as output_file:
                for event in self._events:
                    self._sequence += 1
                    payload = {
                        "schema_version": _MONITOR_SCHEMA_VERSION,
                        "run_id": self._run_id,
                        "sequence": self._sequence,
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "runtime_language": self._runtime_language,
                        "category": event.category,
                        "event_type": event.event_type,
                        "exit_code": int(exit_code),
                        "details": event.details,
                    }
                    serialized = json.dumps(payload, sort_keys=True)
                    for forbidden in self._forbidden_values:
                        serialized = serialized.replace(forbidden, "[REDACTED]")
                    output_file.write(f"{serialized}\n")
        except OSError:
            return


def _build_sitecustomize_source() -> str:
    return (
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import socket\n"
        "\n"
        "_KINNOO_MONITOR_PATH = os.environ.get('KINNOO_RUNTIME_MONITOR_NETWORK_LOG')\n"
        "\n"
        "def _emit(payload):\n"
        "    if not _KINNOO_MONITOR_PATH:\n"
        "        return\n"
        "    try:\n"
        "        target = Path(_KINNOO_MONITOR_PATH)\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        with target.open('a', encoding='utf-8') as output_file:\n"
        "            output_file.write(json.dumps(payload, sort_keys=True) + '\\n')\n"
        "    except Exception:\n"
        "        return\n"
        "\n"
        "_orig_create_connection = socket.create_connection\n"
        "\n"
        "def _create_connection_with_monitor(address, *args, **kwargs):\n"
        "    host = 'unknown'\n"
        "    port = 0\n"
        "    if isinstance(address, tuple) and len(address) >= 2:\n"
        "        host = str(address[0])\n"
        "        try:\n"
        "            port = int(address[1])\n"
        "        except Exception:\n"
        "            port = 0\n"
        "    _emit({'operation': 'create_connection', 'host': host, 'port': port})\n"
        "    return _orig_create_connection(address, *args, **kwargs)\n"
        "\n"
        "socket.create_connection = _create_connection_with_monitor\n"
    )
