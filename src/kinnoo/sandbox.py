from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .runtime_language import is_nodejs_compatible_runtime


@dataclass(frozen=True)
class SandboxDecision:
    allowed: bool
    code: str
    message: str
    remediation: str
    capability: str | None = None
    action: str | None = None


def _permission_bool(value: object) -> bool:
    return isinstance(value, bool) and value


def _filesystem_scope_allows_write(scope: object) -> bool:
    if not isinstance(scope, str):
        return False
    normalized = scope.strip().lower()
    return normalized in {"workspace-write", "full"}


def _iter_attempted_capabilities(pass_through_args: list[str]) -> list[tuple[str, str]]:
    """Infer capability attempts from pass-through flags in a deterministic way.

    This baseline backend is intentionally conservative and cross-platform. It
    does not instrument OS syscalls; instead it interprets explicit CLI intent
    hints so policy behavior is deterministic in tests and automation.
    """
    attempted: list[tuple[str, str]] = []

    capability_markers: tuple[tuple[set[str], str, str], ...] = (
        ({"--network", "--url", "-u"}, "network", "network_access"),
        ({"--shell", "--exec", "--command", "-c"}, "shell", "shell_execution"),
        ({"--fs-write", "--write", "--output", "-o"}, "filesystem", "filesystem_write"),
    )

    for token in pass_through_args:
        normalized = token.strip()
        if not normalized:
            continue

        if normalized.startswith("http://") or normalized.startswith("https://"):
            attempted.append(("network", "network_access"))
            continue

        for markers, capability, action in capability_markers:
            if normalized in markers:
                attempted.append((capability, action))
                break

    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entry in attempted:
        if entry in seen:
            continue
        seen.add(entry)
        deduped.append(entry)

    return deduped


def evaluate_sandbox_permissions(
    *,
    manifest: dict[str, Any],
    runtime_type: str,
    runtime_language: str,
    pass_through_args: list[str],
) -> SandboxDecision:
    if runtime_language != "python" and not is_nodejs_compatible_runtime(runtime_language):
        return SandboxDecision(
            allowed=False,
            code="backend_unsupported_runtime_language",
            message=(
                "sandbox mode supports runtime.language='python' and node-compatible runtimes "
                "('nodejs', 'javascript', 'typescript') only in this version"
            ),
            remediation=(
                "Use runtime.language='python', 'nodejs', 'javascript', or 'typescript', "
                    "or run without --enforce-policy"
            ),
        )

    if runtime_type != "one-shot":
        return SandboxDecision(
            allowed=False,
            code="backend_unsupported_runtime",
            message=(
                "sandbox mode supports runtime.type='one-shot' only in this version"
            ),
            remediation=(
                    "Use runtime.type='one-shot' for policy enforcement or run without --enforce-policy"
            ),
        )

    permissions = manifest.get("permissions")
    if not isinstance(permissions, dict):
        return SandboxDecision(
            allowed=False,
            code="missing_permissions_policy",
            message="sandbox mode requires manifest permissions declaration",
            remediation=(
                    "Declare a permissions section in kinnoo.yaml or run without --enforce-policy"
            ),
        )

    attempted_capabilities = _iter_attempted_capabilities(pass_through_args)
    for capability, action in attempted_capabilities:
        if capability == "network" and not _permission_bool(permissions.get("network")):
            return SandboxDecision(
                allowed=False,
                code="policy_violation",
                message=(
                    "sandbox violation: capability=network action=network_access"
                ),
                remediation=(
                        "Set permissions.network=true or remove network actions before running with --enforce-policy"
                ),
                capability="network",
                action="network_access",
            )

        if capability == "shell" and not _permission_bool(permissions.get("shell")):
            return SandboxDecision(
                allowed=False,
                code="policy_violation",
                message=(
                    "sandbox violation: capability=shell action=shell_execution"
                ),
                remediation=(
                        "Set permissions.shell=true or remove shell actions before running with --enforce-policy"
                ),
                capability="shell",
                action="shell_execution",
            )

        if capability == "filesystem" and not _filesystem_scope_allows_write(
            permissions.get("filesystem_scope")
        ):
            return SandboxDecision(
                allowed=False,
                code="policy_violation",
                message=(
                    "sandbox violation: capability=filesystem action=filesystem_write"
                ),
                remediation=(
                    "Set permissions.filesystem_scope to 'workspace-write' or 'full', "
                        "or remove write actions before running with --enforce-policy"
                ),
                capability="filesystem",
                action="filesystem_write",
            )

    return SandboxDecision(
        allowed=True,
        code="allowed",
        message="sandbox policy check passed",
        remediation="none",
    )
