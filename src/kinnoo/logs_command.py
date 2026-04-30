"""OpenClaw logs passthrough wrapper for kinnoo logs command."""

from __future__ import annotations

import subprocess
import sys

try:
    from kinnoo.openclaw_preflight import run_openclaw_preflight_for_command
except ImportError:
    from .openclaw_preflight import run_openclaw_preflight_for_command


def logs_openclaw(*, follow: bool = False, json_output: bool = False) -> int:
    """Delegate to `openclaw logs` with deterministic passthrough flags."""
    preflight_result = run_openclaw_preflight_for_command("logs")
    if not preflight_result.ok:
        print(
            "Error: OpenClaw logs preflight failed "
            f"(category={preflight_result.category}). {preflight_result.message}",
            file=sys.stderr,
        )
        return 1

    command = ["openclaw", "logs"]
    if follow:
        command.append("--follow")
    if json_output:
        command.append("--json")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        print(
            f"Error: OpenClaw logs invocation failed (category=openclaw_logs_invocation_failed): {error}",
            file=sys.stderr,
        )
        return 1

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        print(
            "Error: OpenClaw logs delegation failed "
            "(category=openclaw_logs_runtime_nonzero_exit). "
            "Review OpenClaw logs output and retry.",
            file=sys.stderr,
        )

    return int(result.returncode)
