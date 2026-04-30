from __future__ import annotations

import json
import sys
from typing import Iterable


def redact_secret_values(text: str, secret_values: Iterable[str]) -> str:
    redacted = text
    for secret_value in secret_values:
        if not secret_value:
            continue
        redacted = redacted.replace(secret_value, "[REDACTED]")
    return redacted


def format_violation_event_line(
    payload: dict[str, object],
    secret_values: Iterable[str] | None = None,
) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    if secret_values is None:
        return serialized
    return redact_secret_values(serialized, secret_values)


def emit_violation_event_diagnostic(
    payload: dict[str, object],
    secret_values: Iterable[str] | None = None,
) -> None:
    rendered = format_violation_event_line(payload, secret_values=secret_values)
    print(f"[kinnoo security] violation event: {rendered}", file=sys.stderr)


def emit_sync_event_diagnostic(payload: dict[str, object]) -> None:
    rendered = json.dumps(payload, sort_keys=True)
    print(f"[kinnoo sync] diagnostic: {rendered}", file=sys.stderr)
