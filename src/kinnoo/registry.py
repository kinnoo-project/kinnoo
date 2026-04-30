"""Registry abstraction layer for publish/resolve/list/search flows."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Literal, Optional

from .registry_backend import RegistryBackend
from .schema import NAME_PATTERN, SEMVER_PATTERN


@dataclass(frozen=True)
class RegistryRecord:
    """Canonical registry entry representation used across backends."""

    name: str
    version: str
    archive_path: Path
    metadata_path: Path | None = None
    publisher_public_key: str | None = None


@dataclass(frozen=True)
class RegistryAgentSummary:
    """Latest-version summary used by `kinnoo list` output."""

    name: str
    latest_version: str
    description: str
    archive_size_bytes: int | None = None


@dataclass(frozen=True)
class InstallTargetSpec:
    """Parsed install target classification for install command routing."""

    kind: Literal["archive-path", "registry-latest", "registry-exact", "invalid"]
    raw_target: str
    archive_path: Path | None = None
    tenant: str | None = None
    name: str | None = None
    version: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ClawHubMirrorRecord:
    """Canonical ClawHub mirror metadata entry used for registry sync/import."""

    tenant_slug: str
    agent_slug: str
    name: str
    version: str
    source_registry: str
    source_version: str
    source_url: str | None = None
    synced_at: str | None = None
    metadata: dict[str, Any] | None = None


class RegistryService:
    """Backend-agnostic service boundary used by command handlers."""

    def __init__(self, backend: RegistryBackend) -> None:
        self._backend = backend

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
    ) -> RegistryRecord:
        return self._backend.publish(
            name=name,
            version=version,
            archive_path=archive_path,
            manifest_metadata=manifest_metadata,
        )

    def resolve(
        self,
        *,
        name: str,
        version: Optional[str] = None,
        tenant: str | None = None,
    ) -> Optional[RegistryRecord]:
        try:
            return self._backend.resolve(name=name, version=version, tenant=tenant)
        except TypeError:
            return self._backend.resolve(name=name, version=version)

    def list_entries(self) -> list[RegistryRecord]:
        return self._backend.list_entries()

    def search(self, *, query: str) -> list[RegistryRecord]:
        return self._backend.search(query=query)

    def list_latest_agents(self) -> list[RegistryAgentSummary]:
        backend_lister = getattr(self._backend, "list_latest_agents", None)
        if callable(backend_lister):
            return backend_lister()

        summaries: dict[str, RegistryAgentSummary] = {}
        for record in self.list_entries():
            existing = summaries.get(record.name)
            if existing is None:
                summaries[record.name] = RegistryAgentSummary(
                    name=record.name,
                    latest_version=record.version,
                    description="",
                    archive_size_bytes=None,
                )
        return [summaries[name] for name in sorted(summaries)]

    def search_agents(self, *, query: str) -> list[RegistryAgentSummary]:
        backend_searcher = getattr(self._backend, "search_agents", None)
        if callable(backend_searcher):
            return backend_searcher(query=query)

        query_normalized = query.strip().lower()
        if not query_normalized:
            return self.list_latest_agents()

        return [
            summary
            for summary in self.list_latest_agents()
            if query_normalized in summary.name.lower()
            or query_normalized in summary.description.lower()
        ]

    def resolve_with_error(
        self,
        *,
        name: str,
        version: Optional[str] = None,
        tenant: str | None = None,
    ) -> tuple[Optional[RegistryRecord], Optional[str]]:
        backend_resolver = getattr(self._backend, "resolve_with_error", None)
        if callable(backend_resolver):
            try:
                return backend_resolver(name=name, version=version, tenant=tenant)
            except TypeError:
                return backend_resolver(name=name, version=version)

        record = self.resolve(name=name, version=version, tenant=tenant)
        if record is not None:
            return record, None

        if version:
            return None, f"Registry version '{name}=={version}' was not found."
        return None, f"Registry agent '{name}' was not found."

    def upsert_clawhub_mirror_record(
        self,
        *,
        agent_slug: str,
        source_version: str,
        source_url: str | None = None,
        synced_at: str | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ClawHubMirrorRecord:
        backend_upserter = getattr(self._backend, "upsert_clawhub_mirror_record", None)
        if not callable(backend_upserter):
            raise NotImplementedError("Registry backend does not support ClawHub mirror upserts.")

        record = backend_upserter(
            agent_slug=agent_slug,
            source_version=source_version,
            source_url=source_url,
            synced_at=synced_at,
            metadata=metadata,
        )
        if isinstance(record, ClawHubMirrorRecord):
            return record

        if isinstance(record, dict):
            return ClawHubMirrorRecord(
                tenant_slug=str(record.get("tenant_slug", "clawhub")),
                agent_slug=str(record.get("agent_slug", agent_slug)),
                name=str(record.get("name", _mirror_name_from_slug(agent_slug))),
                version=str(record.get("version", source_version)),
                source_registry=str(record.get("source_registry", "clawhub")),
                source_version=str(record.get("source_version", source_version)),
                source_url=(
                    str(record.get("source_url"))
                    if isinstance(record.get("source_url"), str) and str(record.get("source_url")).strip()
                    else None
                ),
                synced_at=(
                    str(record.get("synced_at"))
                    if isinstance(record.get("synced_at"), str) and str(record.get("synced_at")).strip()
                    else None
                ),
                metadata=record.get("metadata") if isinstance(record.get("metadata"), dict) else None,
            )

        raise RuntimeError("Unsupported ClawHub mirror record payload returned by backend.")

    def list_clawhub_mirror_records(self) -> list[ClawHubMirrorRecord]:
        backend_lister = getattr(self._backend, "list_clawhub_mirror_records", None)
        if not callable(backend_lister):
            return []

        records = backend_lister()
        normalized: list[ClawHubMirrorRecord] = []
        for raw_record in records:
            if isinstance(raw_record, ClawHubMirrorRecord):
                normalized.append(raw_record)
                continue
            if not isinstance(raw_record, dict):
                continue
            normalized.append(
                ClawHubMirrorRecord(
                    tenant_slug=str(raw_record.get("tenant_slug", "clawhub")),
                    agent_slug=str(raw_record.get("agent_slug", "")),
                    name=str(raw_record.get("name", "")),
                    version=str(raw_record.get("version", "")),
                    source_registry=str(raw_record.get("source_registry", "clawhub")),
                    source_version=str(raw_record.get("source_version", "")),
                    source_url=(
                        str(raw_record.get("source_url"))
                        if isinstance(raw_record.get("source_url"), str)
                        and str(raw_record.get("source_url")).strip()
                        else None
                    ),
                    synced_at=(
                        str(raw_record.get("synced_at"))
                        if isinstance(raw_record.get("synced_at"), str)
                        and str(raw_record.get("synced_at")).strip()
                        else None
                    ),
                    metadata=(
                        raw_record.get("metadata")
                        if isinstance(raw_record.get("metadata"), dict)
                        else None
                    ),
                )
            )

        return sorted(normalized, key=lambda item: (item.agent_slug, item.version))

    def get_clawhub_mirror_record(self, *, agent_slug: str) -> ClawHubMirrorRecord | None:
        backend_getter = getattr(self._backend, "get_clawhub_mirror_record", None)
        if not callable(backend_getter):
            return None

        payload = backend_getter(agent_slug=agent_slug)
        if payload is None:
            return None
        if isinstance(payload, ClawHubMirrorRecord):
            return payload
        if not isinstance(payload, dict):
            return None

        return ClawHubMirrorRecord(
            tenant_slug=str(payload.get("tenant_slug", "clawhub")),
            agent_slug=str(payload.get("agent_slug", agent_slug)),
            name=str(payload.get("name", _mirror_name_from_slug(agent_slug))),
            version=str(payload.get("version", payload.get("source_version", ""))),
            source_registry=str(payload.get("source_registry", "clawhub")),
            source_version=str(payload.get("source_version", payload.get("version", ""))),
            source_url=(
                str(payload.get("source_url"))
                if isinstance(payload.get("source_url"), str) and str(payload.get("source_url")).strip()
                else None
            ),
            synced_at=(
                str(payload.get("synced_at"))
                if isinstance(payload.get("synced_at"), str) and str(payload.get("synced_at")).strip()
                else None
            ),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
        )


def _mirror_name_from_slug(agent_slug: str) -> str:
    cleaned = agent_slug.strip().strip("/")
    if not cleaned:
        return "unknown"
    return cleaned.split("/")[-1]


def parse_install_target_spec(target: str) -> InstallTargetSpec:
    """Parse install target into file-path or registry selector forms.

    Supported selector forms:
    - ``<name>`` (latest)
    - ``<name>==<version>`` (exact)
    - ``<tenant>/<name>`` (latest)
    - ``<tenant>/<name>==<version>`` (exact)
    """

    candidate = target.strip()
    if not candidate:
        return InstallTargetSpec(
            kind="invalid",
            raw_target=target,
            error="Install target cannot be empty.",
        )

    looks_like_path = (
        candidate.startswith(".")
        or candidate.startswith("/")
        or candidate.startswith("~")
        or candidate.endswith(".kno")
        or Path(candidate).exists()
    )

    if looks_like_path:
        return InstallTargetSpec(
            kind="archive-path",
            raw_target=target,
            archive_path=Path(candidate).expanduser(),
        )

    separator_count = candidate.count("==")
    if separator_count > 1:
        return InstallTargetSpec(
            kind="invalid",
            raw_target=target,
            error=(
                "Invalid registry selector format. Use '<name>' or "
                "'<name>==<version>'."
            ),
        )

    if separator_count == 1:
        name_part, version_part = candidate.split("==", 1)
        name = name_part.strip()
        version = version_part.strip()

        if not name or not version:
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=(
                    "Invalid registry selector format. Use '<name>==<version>' "
                    "with both name and version present."
                ),
            )

        tenant: str | None = None
        selector_name = name
        if "/" in name:
            tenant_part, raw_name = name.split("/", 1)
            tenant_part = tenant_part.strip()
            raw_name = raw_name.strip()
            if not tenant_part or not raw_name:
                return InstallTargetSpec(
                    kind="invalid",
                    raw_target=target,
                    error=(
                        "Invalid registry selector format. Use '<name>==<version>' or "
                        "'<tenant>/<name>==<version>'."
                    ),
                )
            if not re.fullmatch(r"^[a-z][a-z0-9-]*$", tenant_part):
                return InstallTargetSpec(
                    kind="invalid",
                    raw_target=target,
                    error=f"Invalid registry tenant slug '{tenant_part}'.",
                )
            tenant = tenant_part
            selector_name = raw_name

        if not re.fullmatch(NAME_PATTERN, selector_name):
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=f"Invalid registry agent name '{selector_name}'.",
            )

        if not re.fullmatch(SEMVER_PATTERN, version):
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=f"Invalid registry version '{version}'. Expected semver.",
            )

        return InstallTargetSpec(
            kind="registry-exact",
            raw_target=target,
            tenant=tenant,
            name=selector_name,
            version=version,
        )

    tenant: str | None = None
    selector_name = candidate
    if "/" in candidate:
        tenant_part, raw_name = candidate.split("/", 1)
        tenant_part = tenant_part.strip()
        raw_name = raw_name.strip()
        if not tenant_part or not raw_name:
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=(
                    f"Invalid install target '{candidate}'. Use a .kno file path, "
                    "'<name>', '<name>==<version>', '<tenant>/<name>', or '<tenant>/<name>==<version>'."
                ),
            )
        if not re.fullmatch(r"^[a-z][a-z0-9-]*$", tenant_part):
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=f"Invalid registry tenant slug '{tenant_part}'.",
            )
        tenant = tenant_part
        selector_name = raw_name

    if not re.fullmatch(NAME_PATTERN, selector_name):
        return InstallTargetSpec(
            kind="invalid",
            raw_target=target,
            error=(
                f"Invalid install target '{candidate}'. Use a .kno file path, "
                "'<name>', '<name>==<version>', '<tenant>/<name>', or '<tenant>/<name>==<version>'."
            ),
        )

    return InstallTargetSpec(
        kind="registry-latest",
        raw_target=target,
        tenant=tenant,
        name=selector_name,
    )
