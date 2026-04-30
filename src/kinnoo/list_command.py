"""List command implementation for local-archive and remote-registry inventory."""

from __future__ import annotations

import os
import json
from pathlib import Path

from .auth_command import refresh_registry_auth_if_needed
from .config import load_registry_config
from .archive import LocalArchiveBackend
from .registry import RegistryService
from .remote_client import RemoteRegistryClient
from .size_format import format_size_human_readable


def list_agents(source: str = "local", json_output: bool = False) -> int:
    config = load_registry_config()
    effective_source = source
    if source == "auto":
        effective_source = "remote" if config.registry_url else "local"

    if effective_source == "remote":
        config, refresh_error = refresh_registry_auth_if_needed(config=config)
        if refresh_error:
            print(f"Error: {refresh_error}")
            return 1

        if not config.registry_url:
            print(
                "Error: Remote mode requires a registry URL. "
                "Run 'kinnoo login' or set KINNOO_REGISTRY_URL. "
                "Remote mode does not fall back to local mock storage.",
            )
            return 1

        if not config.registry_token or not config.tenant_slug:
            print(
                "Error: Remote registry authentication is missing. "
                "Run 'kinnoo login' or set KINNOO_REGISTRY_TOKEN and KINNOO_TENANT_SLUG.",
            )
            return 1

        service = RegistryService(
            backend=RemoteRegistryClient(
                base_url=config.registry_url,
                token=config.registry_token,
                tenant_slug=config.tenant_slug,
            )
        )

        summaries = service.list_latest_agents()

        if not summaries:
            if json_output:
                print(json.dumps({"source": "remote", "results": []}, sort_keys=True))
            else:
                print("No agents found in remote registry.")
            return 0

        json_results = [
            {
                "name": _summary_text(summary=summary, field="name", default="(unknown)"),
                "latest_version": _summary_text(summary=summary, field="latest_version", default="(unknown)"),
                "description": _summary_text(summary=summary, field="description", default="(no description)"),
                "archive_size": _format_archive_size(_summary_size_bytes(summary=summary)),
                "source": "remote",
            }
            for summary in summaries
        ]

        if json_output:
            print(json.dumps({"source": "remote", "results": json_results}, sort_keys=True))
            return 0

        print("Remote registry agents:")
        for summary in json_results:
            description = summary.get("description", "(no description)")
            archive_size = summary.get("archive_size", "unknown")
            name = summary.get("name", "(unknown)")
            latest_version = summary.get("latest_version", "(unknown)")
            print(
                f"- {name} | latest: {latest_version} | "
                f"description: {description} | size: {archive_size}"
            )

        return 0

    archive_root = os.environ.get("KINNOO_ARCHIVE_ROOT")
    backend_root = Path(archive_root).expanduser() if archive_root else None

    backend = LocalArchiveBackend(root=backend_root)
    summaries = backend.list_latest_agents()

    if not summaries:
        if json_output:
            print(json.dumps({"source": "local", "results": []}, sort_keys=True))
        else:
            print("No agents found in local archive.")
        return 0

    json_results = [
        {
            "name": _summary_text(summary=summary, field="name", default="(unknown)"),
            "latest_version": _summary_text(summary=summary, field="latest_version", default="(unknown)"),
            "description": _summary_text(summary=summary, field="description", default="(no description)"),
            "archive_size": _format_archive_size(_summary_size_bytes(summary=summary)),
            "source": "local",
        }
        for summary in summaries
    ]

    if json_output:
        print(json.dumps({"source": "local", "results": json_results}, sort_keys=True))
        return 0

    print("Local archive agents:")
    for summary in json_results:
        description = summary.get("description", "(no description)")
        archive_size = summary.get("archive_size", "unknown")
        name = summary.get("name", "(unknown)")
        latest_version = summary.get("latest_version", "(unknown)")
        print(
            f"- {name} | latest: {latest_version} | "
            f"description: {description} | size: {archive_size}"
        )

    return 0


def _format_archive_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown"
    return format_size_human_readable(size_bytes)


def _summary_text(*, summary: object, field: str, default: str) -> str:
    value = _summary_value(summary=summary, field=field)
    if value in (None, ""):
        return default
    return str(value)


def _summary_size_bytes(*, summary: object) -> int | None:
    value = _summary_value(summary=summary, field="archive_size_bytes")
    if isinstance(value, int):
        return value
    return None


def _summary_value(*, summary: object, field: str) -> object | None:
    if isinstance(summary, dict):
        return summary.get(field)
    return getattr(summary, field, None)
