"""Filesystem MCP fixture with runtime permission enforcement helpers.

The runtime wrapper in this fixture is intentionally lightweight and test-focused.
Task155 uses these helpers to enforce deny-by-default write/create behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FilesystemPermissionError(RuntimeError):
    """Raised when a filesystem operation violates manifest permissions."""


class MCPToolCallError(RuntimeError):
    """Raised when a tool call request is malformed or unsupported."""


@dataclass(frozen=True)
class FilesystemPermissions:
    """Normalized permissions payload for filesystem MCP runtime checks."""

    read_only: bool = True
    allow_write: bool = False
    allow_create: bool = False
    allowed_paths: tuple[str, ...] = ()


def permissions_from_manifest(manifest: dict[str, Any]) -> FilesystemPermissions:
    """Normalize permissions from a manifest with safe defaults.

    Defaults are deny-by-default for write/create to reduce accidental mutation
    risk for filesystem-backed MCP tool calls.
    """
    raw = manifest.get("permissions")
    if not isinstance(raw, dict):
        return FilesystemPermissions()

    read_only = raw.get("read_only", True)
    allow_write = raw.get("allow_write", False)
    allow_create = raw.get("allow_create", False)
    raw_allowed_paths = raw.get("allowed_paths", [])

    normalized_paths: list[str] = []
    if isinstance(raw_allowed_paths, list):
        for value in raw_allowed_paths:
            if isinstance(value, str) and value.strip():
                normalized_paths.append(value)

    return FilesystemPermissions(
        read_only=bool(read_only),
        allow_write=bool(allow_write),
        allow_create=bool(allow_create),
        allowed_paths=tuple(normalized_paths),
    )


class FilesystemPermissionGate:
    """Permission gate for filesystem MCP write/create operations."""

    def __init__(self, permissions: FilesystemPermissions, root_dir: str | Path) -> None:
        self._permissions = permissions
        self._root_dir = Path(root_dir).resolve()

    def assert_allowed(self, action: str, target_path: str | Path) -> Path:
        """Validate operation permission and return normalized resolved target path."""
        normalized_action = action.strip().lower()
        resolved_target = Path(target_path).resolve()

        if normalized_action not in {"write", "create"}:
            raise FilesystemPermissionError(
                f"Unsupported filesystem action '{action}'. Allowed actions are 'write' and 'create'."
            )

        if self._permissions.read_only:
            raise FilesystemPermissionError(
                "Filesystem MCP server is in read-only mode; write/create operations are blocked. "
                "Set permissions.read_only to false and enable allow_write/allow_create to opt in."
            )

        if normalized_action == "write" and not self._permissions.allow_write:
            raise FilesystemPermissionError(
                "Write operation rejected: permissions.allow_write is false. "
                "Set allow_write to true to permit file modifications."
            )

        if normalized_action == "create" and not self._permissions.allow_create:
            raise FilesystemPermissionError(
                "Create operation rejected: permissions.allow_create is false. "
                "Set allow_create to true to permit new file creation."
            )

        self._assert_allowed_path(resolved_target)
        return resolved_target

    def _assert_allowed_path(self, resolved_target: Path) -> None:
        if not self._permissions.allowed_paths:
            return

        for allowed in self._permissions.allowed_paths:
            resolved_allowed = (self._root_dir / allowed).resolve()
            if resolved_target == resolved_allowed or resolved_allowed in resolved_target.parents:
                return

        allowed_display = ", ".join(self._permissions.allowed_paths)
        raise FilesystemPermissionError(
            "Path access rejected by permissions.allowed_paths sandbox. "
            f"Target '{resolved_target}' must be under one of: {allowed_display}."
        )


def handle_mcp_tool_call(request: dict[str, Any], gate: FilesystemPermissionGate) -> dict[str, Any]:
    """Handle a simplified MCP tools/call request through runtime permission checks.

    This keeps an end-to-end request path in the fixture so tests can verify that
    permission enforcement occurs during handler processing, not only in helper calls.
    """
    method = request.get("method")
    params = request.get("params")
    if method != "tools/call" or not isinstance(params, dict):
        raise MCPToolCallError("Expected tools/call request with params object.")

    tool_name = params.get("name")
    arguments = params.get("arguments")
    if not isinstance(tool_name, str) or not isinstance(arguments, dict):
        raise MCPToolCallError("tools/call params must include string name and arguments object.")

    action = ""
    if tool_name.endswith(".write"):
        action = "write"
    elif tool_name.endswith(".create"):
        action = "create"
    else:
        raise MCPToolCallError(f"Unsupported filesystem tool '{tool_name}'.")

    target_path = arguments.get("path")
    if not isinstance(target_path, str) or not target_path.strip():
        raise MCPToolCallError("Tool arguments must include non-empty 'path' string.")

    resolved = gate.assert_allowed(action, target_path)
    return {
        "ok": True,
        "tool": tool_name,
        "action": action,
        "resolved_path": str(resolved),
    }


def main() -> int:
    # Placeholder runtime output keeps fixture entrypoint deterministic for pack tests.
    print("filesystem mcp server fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
