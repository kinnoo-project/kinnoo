"""kinnoo — agent packaging toolkit."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .archive import ArchiveBackend, ArchiveRecord, LocalArchiveBackend
from .config import RegistryConfig, load_registry_config
from .registry import RegistryBackend, RegistryRecord, RegistryService
from .registry_backends import LocalFilesystemRegistryBackend, LocalRegistryBackend, MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient
from .validator import validate


def _read_repo_pyproject_version() -> str | None:
	pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
	if not pyproject_path.exists():
		return None

	try:
		import tomllib

		with pyproject_path.open("rb") as file_handle:
			project_data = tomllib.load(file_handle)
		version_value = project_data.get("project", {}).get("version")
		if isinstance(version_value, str) and version_value.strip():
			return version_value.strip()
	except Exception:
		return None

	return None


def _resolve_version() -> str:
	# Prefer repo-local version during source execution so CLI help follows pyproject edits.
	repo_version = _read_repo_pyproject_version()
	if repo_version is not None:
		return repo_version

	try:
		return version("kinnoo")
	except PackageNotFoundError:
		return "0.0.0"


__version__ = _resolve_version()

__all__ = [
	"validate",
	"__version__",
	"RegistryBackend",
	"RegistryRecord",
	"RegistryService",
	"ArchiveBackend",
	"ArchiveRecord",
	"LocalArchiveBackend",
	"RegistryConfig",
	"load_registry_config",
	"LocalRegistryBackend",
	"LocalFilesystemRegistryBackend",
	"MockFilesystemRegistryBackend",
	"RemoteRegistryClient",
]
