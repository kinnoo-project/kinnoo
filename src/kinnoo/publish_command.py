"""Publish command implementation for archive-source registry publish flows."""

from __future__ import annotations

import re
import os
import shutil
import json
from pathlib import Path
from typing import Any
from urllib import request as urllib_request
from urllib import error as urllib_error
import yaml

from .auth_command import refresh_registry_auth_if_needed
from .archive import LocalArchiveBackend
from .checksum import checksum_sidecar_path_for_archive
from .config import RegistryConfig, load_publish_behavior_config, load_registry_config
from .inspect_command import read_manifest_from_kno_archive
from .registry import RegistryRecord, RegistryService
from .registry_backends import MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient
from .schema import NAME_PATTERN
from .validator import validate_manifest_data
from .signing import verify_detached_signature_artifacts


def _http_user_agent() -> str:
    configured = (os.environ.get("KINNOO_HTTP_USER_AGENT") or "").strip()
    if configured:
        return configured
    return "curl/8.7.1"


def _publish_validated_archive(
    *,
    archive: Path,
    expected_name: str | None,
    expected_version: str | None,
    backend: Any,
    backend_label: str,
    strict_mode: bool = False,
    json_output: bool = False,
) -> int:
    def _emit_json(payload: dict[str, object]) -> None:
        print(json.dumps(payload, sort_keys=True))

    source_sidecar_path = checksum_sidecar_path_for_archive(archive)
    manifest_data = read_manifest_from_kno_archive(archive)
    if manifest_data is None:
        if json_output:
            _emit_json(
                {
                    "agent_name": expected_name,
                    "agent_version": expected_version,
                    "registry": backend_label,
                    "source_archive_path": str(archive),
                    "publish_result": "rejected",
                    "error_code": "MANIFEST_READ_FAILED",
                    "error_message": "Failed to read manifest metadata from resolved local archive source.",
                }
            )
            return 1
        print("Error: Failed to read manifest metadata from resolved local archive source.")
        return 1

    is_valid, validation_errors = validate_manifest_data(manifest_data)
    if not is_valid:
        if json_output:
            _emit_json(
                {
                    "agent_name": expected_name,
                    "agent_version": expected_version,
                    "registry": backend_label,
                    "source_archive_path": str(archive),
                    "publish_result": "rejected",
                    "error_code": "MANIFEST_INVALID",
                    "error_message": "Manifest validation failed for resolved local archive source.",
                }
            )
            return 1
        print("Error: Manifest validation failed for resolved local archive source.")
        for error in validation_errors:
            print(f"- {error}")
        return 1

    name = str(manifest_data.get("name", "")).strip()
    version = str(manifest_data.get("version", "")).strip()

    signature_path = Path(f"{archive}.sig")
    signature_metadata_path = Path(f"{archive}.sig.json")

    if strict_mode:
        if not signature_path.exists() or not signature_metadata_path.exists():
            if json_output:
                _emit_json(
                    {
                        "agent_name": name,
                        "agent_version": version,
                        "registry": backend_label,
                        "source_archive_path": str(archive),
                        "publish_result": "rejected",
                        "error_code": "STRICT_SIGNATURE_REQUIRED",
                        "error_message": "Strict publish requires valid signature metadata; unsigned artifacts are not allowed.",
                    }
                )
                return 1
            print(
                "Error: Strict publish requires valid signature metadata; unsigned artifacts are not allowed."
            )
            print("Error: Re-pack with --sign before using publish --strict.")
            return 1
        try:
            verify_detached_signature_artifacts(
                archive_path=archive,
                signature_path=signature_path,
                metadata_path=signature_metadata_path,
            )
        except ValueError as error:
            if json_output:
                _emit_json(
                    {
                        "agent_name": name,
                        "agent_version": version,
                        "registry": backend_label,
                        "source_archive_path": str(archive),
                        "publish_result": "rejected",
                        "error_code": "STRICT_SIGNATURE_VERIFICATION_FAILED",
                        "error_message": f"Strict publish signature verification failed: {error}",
                    }
                )
                return 1
            print(f"Error: Strict publish signature verification failed: {error}")
            print("Error: Re-sign archive with a valid Ed25519 key and retry publish --strict.")
            return 1

    if expected_name is not None and name != expected_name:
        if json_output:
            _emit_json(
                {
                    "agent_name": expected_name,
                    "agent_version": expected_version,
                    "registry": backend_label,
                    "source_archive_path": str(archive),
                    "publish_result": "rejected",
                    "error_code": "ARCHIVE_NAME_MISMATCH",
                    "error_message": (
                        "Archive metadata mismatch for resolved source. "
                        f"Requested '{expected_name}' but archive manifest name is '{name}'."
                    ),
                }
            )
            return 1
        print(
            "Error: Archive metadata mismatch for resolved source. "
            f"Requested '{expected_name}' but archive manifest name is '{name}'."
        )
        return 1

    if expected_version is not None and version != expected_version:
        if json_output:
            _emit_json(
                {
                    "agent_name": expected_name,
                    "agent_version": expected_version,
                    "registry": backend_label,
                    "source_archive_path": str(archive),
                    "publish_result": "rejected",
                    "error_code": "ARCHIVE_VERSION_MISMATCH",
                    "error_message": (
                        "Archive metadata mismatch for resolved source. "
                        f"Expected {expected_name}=={expected_version} but got {name}=={version}."
                    ),
                }
            )
            return 1
        print(
            "Error: Archive metadata mismatch for resolved source. "
            f"Expected {expected_name}=={expected_version} but got {name}=={version}."
        )
        return 1

    service = RegistryService(backend=backend)

    target_archive_path: Path | None = None
    tagged_exists_before_publish = False
    existing_untagged_dirs_before: set[str] = set()
    if isinstance(backend, MockFilesystemRegistryBackend):
        target_archive_path = backend.registry_version_path(name=name, version=version) / f"{name}.kno"
        tagged_exists_before_publish = target_archive_path.exists()
        existing_untagged_dirs_before = {
            path.name
            for path in (backend.root / name).iterdir()
            if path.is_dir() and path.name.startswith("untagged-")
        } if (backend.root / name).exists() else set()

    metadata_payload = {
        "name": name,
        "version": version,
        "description": manifest_data.get("description"),
        "author": manifest_data.get("author"),
        "license": manifest_data.get("license"),
    }

    try:
        published_record = service.publish(
            name=name,
            version=version,
            archive_path=archive,
            manifest_metadata=metadata_payload,
        )
    except FileExistsError as error:
        if json_output:
            _emit_json(
                {
                    "agent_name": name,
                    "agent_version": version,
                    "registry": backend_label,
                    "source_archive_path": str(archive),
                    "publish_result": "rejected",
                    "error_code": "VERSION_EXISTS",
                    "error_message": str(error),
                }
            )
            return 1
        print(f"Error: {error}")
        return 1
    except OSError as error:
        if json_output:
            _emit_json(
                {
                    "agent_name": name,
                    "agent_version": version,
                    "registry": backend_label,
                    "source_archive_path": str(archive),
                    "publish_result": "rejected",
                    "error_code": "PUBLISH_IO_ERROR",
                    "error_message": f"Failed to publish archive: {error}",
                }
            )
            return 1
        print(f"Error: Failed to publish archive: {error}")
        return 1

    if not json_output:
        print(f"Published {name}=={version} ({backend_label})")
        print(f"Source archive: {archive}")
    if isinstance(published_record, RegistryRecord):
        if not json_output:
            print(f"Target registry path: {published_record.archive_path}")

        target_sidecar_path = checksum_sidecar_path_for_archive(published_record.archive_path)
        if source_sidecar_path.exists() and source_sidecar_path.is_file():
            try:
                shutil.copy2(source_sidecar_path, target_sidecar_path)
            except OSError as error:
                if json_output:
                    _emit_json(
                        {
                            "agent_name": name,
                            "agent_version": version,
                            "registry": backend_label,
                            "source_archive_path": str(archive),
                            "publish_result": "rejected",
                            "error_code": "CHECKSUM_COPY_FAILED",
                            "error_message": f"Failed to publish checksum sidecar: {error}",
                        }
                    )
                    return 1
                print(f"Error: Failed to publish checksum sidecar: {error}")
                return 1
            if not json_output:
                print(f"Published checksum sidecar: {target_sidecar_path}")
        else:
            if not json_output:
                print("Published checksum sidecar: (none found at source)")
    elif isinstance(published_record, dict):
        remote_record_hint = published_record.get("archive_path") or published_record.get("id") or "(remote accepted)"
        if not json_output:
            print(f"Remote publish result: {remote_record_hint}")
    else:
        if not json_output:
            print("Published checksum sidecar: (backend-managed)")

    if tagged_exists_before_publish and isinstance(backend, MockFilesystemRegistryBackend):
        untagged_root = backend.root / name
        new_untagged_dirs = []
        if untagged_root.exists():
            new_untagged_dirs = sorted(
                [
                    path
                    for path in untagged_root.iterdir()
                    if path.is_dir()
                    and path.name.startswith("untagged-")
                    and path.name not in existing_untagged_dirs_before
                ],
                key=lambda path: int(path.name.split("untagged-", 1)[1])
                if path.name.split("untagged-", 1)[1].isdigit()
                else 0,
            )

        if new_untagged_dirs:
            rollover_archive = new_untagged_dirs[-1] / f"{name}.kno"
            if not json_output:
                print(f"Rollover archived previous tagged artifact to: {rollover_archive}")

    if json_output:
        _emit_json(
            {
                "agent_name": name,
                "agent_version": version,
                "registry": backend_label,
                "source_archive_path": str(archive),
                "publish_result": "accepted",
                "error_code": None,
                "error_message": None,
            }
        )

    return 0


def _remote_config_error(config: RegistryConfig) -> str | None:
    missing: list[str] = []
    if not config.registry_url:
        missing.append("registry_url or KINNOO_REGISTRY_URL")
    if not config.registry_token:
        missing.append("registry_token or KINNOO_REGISTRY_TOKEN")
    if not config.tenant_slug:
        missing.append("tenant_slug or KINNOO_TENANT_SLUG")
    if not missing:
        return None
    return "Remote registry configuration incomplete. Missing: " + ", ".join(missing)


def _resolve_publish_backend(*, use_local: bool, use_remote: bool) -> tuple[Any | None, str, str | None]:
    if use_local and use_remote:
        return None, "", "--local and --remote cannot be used together."

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None
    config = load_registry_config()
    config, refresh_error = refresh_registry_auth_if_needed(config=config)
    if refresh_error:
        return None, "", refresh_error
    publish_behavior = load_publish_behavior_config()

    tenant_slug = (config.tenant_slug or "").strip()
    if backend_root is not None and tenant_slug:
        # Keep local/mock publish layout aligned with tenant-scoped prefix conventions.
        backend_root = backend_root / "tenants" / tenant_slug

    if use_local:
        return MockFilesystemRegistryBackend(root=backend_root), "local", None

    remote_requested = (
        use_remote
        or bool(config.registry_url)
        or publish_behavior.publish_to_authenticated_registry
    )
    if remote_requested:
        resolved_token = config.registry_token
        resolved_tenant = config.tenant_slug
        has_persisted_auth_state = bool(
            isinstance(resolved_token, str)
            and resolved_token.strip()
            and isinstance(resolved_tenant, str)
            and resolved_tenant.strip()
        )

        if (
            publish_behavior.publish_to_authenticated_registry
            and not use_local
            and not has_persisted_auth_state
        ):
            token_result = _issue_registry_token_with_admin_credentials(config=config)
            if isinstance(token_result, str):
                return None, "", token_result
            resolved_token, resolved_tenant = token_result

        resolved_config = RegistryConfig(
            registry_url=config.registry_url,
            registry_token=resolved_token,
            tenant_slug=resolved_tenant,
        )

        config_error = _remote_config_error(resolved_config)
        if config_error is not None:
            return None, "", config_error
        return (
            RemoteRegistryClient(
                base_url=str(resolved_config.registry_url),
                token=str(resolved_config.registry_token),
                tenant_slug=str(resolved_config.tenant_slug),
            ),
            "remote",
            None,
        )

    return MockFilesystemRegistryBackend(root=backend_root), "local", None


def _issue_registry_token_with_admin_credentials(
    *,
    config: RegistryConfig,
) -> tuple[str, str] | str:
    """Issue a remote registry token using admin credentials from environment.

    Returns:
        - ``(token, tenant_slug)`` on success
        - error message string on failure
    """

    if not config.registry_url:
        return (
            "publish_to_authenticated_registry is enabled, but registry URL is missing. "
            "Set KINNOO_REGISTRY_URL or registry_url in ~/.kinnoo/config.yaml."
        )

    username = (os.environ.get("REGISTRY_ADMIN_EMAIL") or "").strip()
    password = os.environ.get("REGISTRY_ADMIN_PASSWORD") or ""
    tenant_slug = (config.tenant_slug or "global").strip() or "global"

    if not username:
        return (
            "publish_to_authenticated_registry is enabled, but REGISTRY_ADMIN_EMAIL is missing."
        )
    if not password:
        return (
            "publish_to_authenticated_registry is enabled, but REGISTRY_ADMIN_PASSWORD is missing."
        )

    request_body = json.dumps(
        {
            "username": username,
            "password": password,
            "tenant_slug": tenant_slug,
        }
    ).encode("utf-8")

    token_url = f"{str(config.registry_url).rstrip('/')}/api/auth/token"
    request = urllib_request.Request(
        url=token_url,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=15.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as error:
        response_body = ""
        try:
            response_body = error.read().decode("utf-8", errors="replace").strip()
        except Exception:
            response_body = ""

        if error.code == 401:
            return "Admin credential authentication failed (401). Check REGISTRY_ADMIN_EMAIL/REGISTRY_ADMIN_PASSWORD."
        if response_body:
            return (
                f"Failed to obtain admin auth token from registry (HTTP {error.code}). "
                f"Response: {response_body}"
            )
        return f"Failed to obtain admin auth token from registry (HTTP {error.code})."
    except urllib_error.URLError as error:
        reason = _format_url_error_reason(error)
        return (
            "Failed to reach registry auth endpoint. Verify KINNOO_REGISTRY_URL and server availability. "
            f"Reason: {reason}"
        )
    except json.JSONDecodeError:
        return "Registry auth endpoint returned invalid JSON while requesting publish token."

    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token.strip():
        return "Registry auth response did not include access_token."

    return token.strip(), tenant_slug


def _format_url_error_reason(error: urllib_error.URLError) -> str:
    reason = getattr(error, "reason", None)
    if isinstance(reason, BaseException):
        return str(reason) or reason.__class__.__name__
    if reason is None:
        return "unknown network error"
    return str(reason)


def _manifest_name_from_agent_dir(agent_dir: Path) -> str | None:
    manifest_path = agent_dir / "kinnoo.yaml"
    if not manifest_path.exists() or not manifest_path.is_file():
        return None

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(manifest, dict):
        return None

    name = manifest.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    return name.strip()


def _ensure_manifest_visibility_private(agent_dir: Path) -> tuple[bool, str | None]:
    manifest_path = agent_dir / "kinnoo.yaml"
    if not manifest_path.exists() or not manifest_path.is_file():
        return False, "Error: --private requires a kinnoo.yaml file in the target agent directory."

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception as error:
        return False, f"Error: Failed to read kinnoo.yaml for --private: {error}"

    if not isinstance(manifest, dict):
        return False, "Error: kinnoo.yaml must parse to a mapping/object for --private."

    current_visibility = manifest.get("visibility")
    if isinstance(current_visibility, str) and current_visibility.strip().lower() == "private":
        return False, None

    manifest["visibility"] = "private"
    try:
        manifest_path.write_text(
            yaml.safe_dump(manifest, sort_keys=False),
            encoding="utf-8",
        )
    except Exception as error:
        return False, f"Error: Failed to update kinnoo.yaml visibility for --private: {error}"

    return True, None


def publish_agent(
    target: str | None = None,
    agent_name: str | None = None,
    use_local: bool = False,
    use_remote: bool = False,
    pack: bool = False,
    make_private: bool = False,
    bump: str | None = None,
    strict_mode: bool = False,
    json_output: bool = False,
) -> int:
    """Publish latest archived artifact for agent name to selected registry backend.

    For feature13 task83, publish source resolution is name-based from the local
    archive backend rather than direct archive path input.
    """
    if target is not None and agent_name is not None:
        print("Error: Provide either 'target' or legacy 'agent_name', not both.")
        return 1

    # Backward compatibility: preserve historical keyword call sites that pass agent_name.
    resolved_target = target if target is not None else agent_name
    if resolved_target is None:
        print("Error: Missing publish target.")
        return 1

    backend, backend_label, backend_error = _resolve_publish_backend(
        use_local=use_local,
        use_remote=use_remote,
    )
    if backend_error is not None:
        print(f"Error: {backend_error}")
        return 1
    if backend is None:
        print("Error: Failed to initialize registry backend.")
        return 1

    if bump is not None and not pack:
        print("Error: --bump can only be used together with --pack.")
        return 1

    if make_private and not pack:
        print("Error: --private can only be used together with --pack.")
        return 1

    normalized_name = resolved_target.strip()

    if pack:
        agent_dir = Path(normalized_name).expanduser()
        if not agent_dir.exists() or not agent_dir.is_dir():
            print(
                "Error: With --pack, <target> must be a file path to an agent directory.",
            )
            return 1

        if make_private:
            updated_visibility, visibility_error = _ensure_manifest_visibility_private(agent_dir)
            if visibility_error is not None:
                print(visibility_error)
                return 1
            if updated_visibility:
                print(f"[kinnoo publish] Updated visibility to private in {agent_dir / 'kinnoo.yaml'}")
            else:
                print("[kinnoo publish] Manifest visibility already private")

        try:
            from kinnoo.pack_command import pack_agent
        except ImportError:
            from .pack_command import pack_agent

        pack_exit = pack_agent(agent_dir=str(agent_dir), bump=bump)
        if pack_exit != 0:
            return pack_exit

        packed_name = _manifest_name_from_agent_dir(agent_dir)
        if packed_name is None:
            print(
                "Error: Could not resolve manifest name from agent directory after --pack flow.",
            )
            return 1

        normalized_name = packed_name

    legacy_archive_candidate = Path(normalized_name).expanduser()
    if (
        legacy_archive_candidate.exists()
        and legacy_archive_candidate.is_file()
        and legacy_archive_candidate.suffix.lower() == ".kno"
    ):
        return _publish_validated_archive(
            archive=legacy_archive_candidate,
            expected_name=None,
            expected_version=None,
            backend=backend,
            backend_label=backend_label,
            strict_mode=strict_mode,
            json_output=json_output,
        )

    if not normalized_name:
        print("Error: Agent name cannot be empty.")
        return 1
    if not re.fullmatch(NAME_PATTERN, normalized_name):
        print(f"Error: Invalid agent name '{normalized_name}'.")
        return 1

    archive_root = Path.home() / ".kinnoo" / "archive"
    archive_backend = LocalArchiveBackend(root=Path(os.environ.get("KINNOO_ARCHIVE_ROOT", archive_root)))
    source_record = archive_backend.resolve_latest(name=normalized_name)
    if source_record is None:
        agent_archive_dir = archive_backend.root / normalized_name
        if not agent_archive_dir.exists() or not agent_archive_dir.is_dir():
            print(
                f"Error: Local archive source for agent '{normalized_name}' was not found at {agent_archive_dir}."
            )
            return 1

        available_versions = sorted(path.name for path in agent_archive_dir.iterdir() if path.is_dir())
        if available_versions:
            print(
                f"Error: Local archive source for agent '{normalized_name}' has no publishable .kno artifacts."
            )
        else:
            print(f"Error: Local archive source for agent '{normalized_name}' has no versions.")
        return 1

    archive = source_record.archive_path
    if not archive.exists() or not archive.is_file():
        print(f"Error: Resolved source archive is missing or invalid: {archive}")
        return 1

    return _publish_validated_archive(
        archive=archive,
        expected_name=source_record.name,
        expected_version=source_record.version,
        backend=backend,
        backend_label=backend_label,
        strict_mode=strict_mode,
        json_output=json_output,
    )
