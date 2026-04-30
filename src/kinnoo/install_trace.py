from __future__ import annotations

import json
import sys
from pathlib import Path

INSTALL_TRACE_RELATIVE_PATH = Path(".kinnoo") / "install-trace.json"
VIOLATION_EVENTS_RELATIVE_PATH = Path(".kinnoo") / "violation-events.jsonl"
UNINSTALL_TRACE_RELATIVE_PATH = Path(".kinnoo") / "uninstall-trace.jsonl"


def write_install_trace(target_dir: Path, payload: dict[str, object]) -> Path | None:
    """Persist deterministic install trace JSON under extracted target directory."""
    trace_path = target_dir / INSTALL_TRACE_RELATIVE_PATH
    try:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        trace_path.write_text(f"{serialized}\n", encoding="utf-8")
    except Exception as error:  # pragma: no cover - defensive I/O guard
        print(f"Warning: Failed to write install trace '{trace_path}': {error}", file=sys.stderr)
        return None

    return trace_path


def write_violation_event(target_dir: Path, payload: dict[str, object]) -> Path | None:
    """Append a structured violation event JSON line under target directory."""
    trace_path = target_dir / VIOLATION_EVENTS_RELATIVE_PATH
    try:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, sort_keys=True)
        with trace_path.open("a", encoding="utf-8") as trace_file:
            trace_file.write(f"{serialized}\n")
    except Exception as error:  # pragma: no cover - defensive I/O guard
        print(f"Warning: Failed to write violation event '{trace_path}': {error}", file=sys.stderr)
        return None

    return trace_path


def write_uninstall_trace(install_root: Path, payload: dict[str, object]) -> Path | None:
    """Append a structured uninstall event under the install root metadata directory."""
    trace_path = install_root / UNINSTALL_TRACE_RELATIVE_PATH
    try:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, sort_keys=True)
        with trace_path.open("a", encoding="utf-8") as trace_file:
            trace_file.write(f"{serialized}\n")
    except Exception as error:  # pragma: no cover - defensive I/O guard
        print(f"Warning: Failed to write uninstall trace '{trace_path}': {error}", file=sys.stderr)
        return None

    return trace_path
