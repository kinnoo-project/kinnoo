from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

from .archive import LocalArchiveBackend
from .auth_command import refresh_registry_auth_if_needed
from .config import load_registry_config
from .install_command import (
    _download_remote_archive_payload,
    _resolve_remote_latest_version,
    _safe_extract_zip,
    _verify_embedded_integrity_and_signature,
)
from .inspect_command import read_manifest_from_kno_archive
from .registry import RegistryService, parse_install_target_spec
from .registry_backends import MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient


def fetch_agent(
    target: str,
    *,
    use_local: bool = False,
    use_remote: bool = False,
    strict_mode: bool = False,
    json_output: bool = False,
) -> int:
    target_spec = parse_install_target_spec(target)
    if target_spec.kind not in {"registry-latest", "registry-exact"}:
        print("Error: fetch target must be <name> or <name>==<version>.", file=sys.stderr)
        return 1

    if use_local and use_remote:
        print("Error: --local and --remote cannot be used together.", file=sys.stderr)
        return 1

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None

    backend = None
    backend_label = "local"
    if use_local:
        backend = MockFilesystemRegistryBackend(root=backend_root)
    elif use_remote:
        config = load_registry_config()
        config, refresh_error = refresh_registry_auth_if_needed(config=config)
        if refresh_error:
            print(f"Error: {refresh_error}", file=sys.stderr)
            return 1
        if not config.registry_url or not config.registry_token or not config.tenant_slug:
            print(
                "Error: Remote registry configuration incomplete. "
                "Set registry_url/registry_token/tenant_slug in ~/.kinnoo/config.yaml "
                "or KINNOO_REGISTRY_URL/KINNOO_REGISTRY_TOKEN/KINNOO_TENANT_SLUG.",
                file=sys.stderr,
            )
            return 1
        backend = RemoteRegistryClient(
            base_url=config.registry_url,
            token=config.registry_token,
            tenant_slug=config.tenant_slug,
        )
        backend_label = "remote"
    else:
        config = load_registry_config()
        config, refresh_error = refresh_registry_auth_if_needed(config=config)
        if refresh_error:
            print(f"Error: {refresh_error}", file=sys.stderr)
            return 1
        if config.registry_url and config.registry_token and config.tenant_slug:
            backend = RemoteRegistryClient(
                base_url=config.registry_url,
                token=config.registry_token,
                tenant_slug=config.tenant_slug,
            )
            backend_label = "remote"
        else:
            backend = MockFilesystemRegistryBackend(root=backend_root)

    service = RegistryService(backend=backend)

    requested_version = target_spec.version if target_spec.kind == "registry-exact" else None
    selector_name = str(target_spec.name)
    selector_tenant = getattr(target_spec, "tenant", None)
    selector_with_tenant = f"{selector_tenant}/{selector_name}" if selector_tenant else selector_name
    resolved_archive_path: Path | None = None
    is_remote_temp_archive = False

    if backend_label == "remote":
        resolved_version = requested_version
        if resolved_version is None:
            resolved_version = _resolve_remote_latest_version(backend=backend, agent_name=selector_with_tenant)
            if resolved_version is None:
                print("Error: Failed to resolve latest remote version.", file=sys.stderr)
                return 1

        try:
            payload = backend.resolve(
                name=selector_name,
                version=resolved_version,
                tenant=selector_tenant,
            )
        except Exception as error:
            print(f"Error: Failed to resolve remote registry target: {error}", file=sys.stderr)
            return 1

        download_url = None
        if isinstance(payload, dict):
            raw_download_url = payload.get("download_url")
            if isinstance(raw_download_url, str) and raw_download_url.strip():
                download_url = raw_download_url.strip()

        if not download_url:
            print("Error: Remote resolve response missing download_url.", file=sys.stderr)
            return 1

        try:
            archive_bytes = _download_remote_archive_payload(backend=backend, download_url=download_url)
        except Exception as error:
            print(f"Error: Failed to download remote archive: {error}", file=sys.stderr)
            return 1

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".kno") as temp_archive:
                temp_archive.write(archive_bytes)
                resolved_archive_path = Path(temp_archive.name)
                is_remote_temp_archive = True
        except OSError as error:
            print(f"Error: Failed to stage downloaded archive: {error}", file=sys.stderr)
            return 1
    else:
        resolved_record, resolve_error = service.resolve_with_error(
            name=selector_name,
            version=requested_version,
            tenant=selector_tenant,
        )
        if resolved_record is None:
            print(f"Error: {resolve_error or 'Registry resolution failed.'}", file=sys.stderr)
            return 1
        resolved_archive_path = resolved_record.archive_path

    assert resolved_archive_path is not None

    try:
        temp_extract_root = Path(tempfile.mkdtemp(prefix="kinnoo-fetch-"))
        try:
            with zipfile.ZipFile(resolved_archive_path, "r") as archive:
                _safe_extract_zip(archive, temp_extract_root)
        except (OSError, zipfile.BadZipFile) as error:
            shutil.rmtree(temp_extract_root, ignore_errors=True)
            print(f"Error: Invalid archive payload: {error}", file=sys.stderr)
            return 1
        except ValueError as error:
            shutil.rmtree(temp_extract_root, ignore_errors=True)
            print(f"Error: Invalid archive payload: {error}", file=sys.stderr)
            return 1

        verified, verify_message = _verify_embedded_integrity_and_signature(
            extracted_dir=temp_extract_root,
            archive_path=resolved_archive_path,
            strict_mode=strict_mode,
            expected_publisher_public_key=None,
        )
        shutil.rmtree(temp_extract_root, ignore_errors=True)
        if not verified:
            print(verify_message, file=sys.stderr)
            return 1

        manifest = read_manifest_from_kno_archive(resolved_archive_path)
        if not isinstance(manifest, dict):
            print("Error: Failed to parse archive manifest.", file=sys.stderr)
            return 1

        agent_name = str(manifest.get("name", "")).strip()
        agent_version = str(manifest.get("version", "")).strip()
        if not agent_name or not agent_version:
            print("Error: Archive manifest missing name/version.", file=sys.stderr)
            return 1

        archive_root_default = Path.home() / ".kinnoo" / "archive"
        archive_backend = LocalArchiveBackend(
            root=Path(os.environ.get("KINNOO_ARCHIVE_ROOT", archive_root_default)).expanduser()
        )
        stored = archive_backend.store(
            name=agent_name,
            version=agent_version,
            source_archive=resolved_archive_path,
            overwrite=True,
        )

        if json_output:
            print(
                json.dumps(
                    {
                        "name": stored.name,
                        "version": stored.version,
                        "archive_path": str(stored.archive_path),
                        "source": backend_label,
                        "strict": strict_mode,
                        "verified": True,
                    },
                    sort_keys=True,
                )
            )
        else:
            print(
                f"[kinnoo fetch] Fetched {stored.name}=={stored.version} to '{stored.archive_path}' ({backend_label})."
            )

        return 0
    finally:
        if is_remote_temp_archive and resolved_archive_path is not None and resolved_archive_path.exists():
            resolved_archive_path.unlink(missing_ok=True)
