"""Registry backend contracts used by local and remote registry clients."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class RegistryBackend(Protocol):
    """Backend contract for registry operations.

    The protocol includes existing local operations plus tenant-aware hooks
    needed for the remote registry rollout.
    """

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
        tenant: str | None = None,
    ) -> Any:
        """Publish an archive under a name/version and return stored record."""

    def resolve(
        self,
        *,
        name: str,
        version: Optional[str] = None,
        tenant: str | None = None,
    ) -> Any:
        """Resolve a specific version or latest available version for a name."""

    def list_entries(self) -> list[Any]:
        """List all published records in deterministic order."""

    def search(self, *, query: str, tenant: str | None = None) -> list[Any]:
        """Search for records matching a query in deterministic order."""

    def list_latest_agents(self) -> list[Any]:
        """List latest-version summary rows per agent in deterministic order."""

    def search_agents(self, *, query: str) -> list[Any]:
        """Search latest-version agent summaries by query in deterministic order."""

    def list_agents(self, *, tenant: str | None = None) -> list[Any]:
        """List agent summaries, optionally scoped by tenant."""
