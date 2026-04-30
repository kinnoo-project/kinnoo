from __future__ import annotations

import shutil
import subprocess
import sys
import venv
import zipfile
import re
import os
import json
import tempfile
import hashlib
import base64
import platform
from datetime import datetime, timezone
from urllib import request as urllib_request
from urllib.parse import urlparse
from pathlib import Path
import yaml

NODE_LIFECYCLE_SCRIPT_NAMES = {
    "preinstall",
    "install",
    "postinstall",
    "prepublish",
    "preprepare",
    "prepare",
    "postprepare",
}

try:
    from kinnoo.checksum import (
        ChecksumParseError,
        checksum_sidecar_path_for_archive,
        read_checksum_sidecar,
        verify_archive_checksum,
    )
    from kinnoo.registry import RegistryService, parse_install_target_spec
    from kinnoo.registry_backends import MockFilesystemRegistryBackend
    from kinnoo.auth_command import refresh_registry_auth_if_needed
    from kinnoo.config import load_registry_config, resolve_lockfile_path
    from kinnoo.remote_client import RemoteRegistryClient
    from kinnoo.health_check import (
        check_node_package_manager_availability,
        check_node_runtime_constraint,
        check_openclaw_cli_constraint,
    )
    from kinnoo.schema import SUPPORTED_NODE_PACKAGE_MANAGERS, normalize_env_vars, LOCKFILE_SCHEMA_VERSION
    from kinnoo.inspect_command import read_manifest_from_kno_archive
    from kinnoo.validator import validate
    from kinnoo.install_trace import write_install_trace
    from kinnoo.logging_utils import emit_violation_event_diagnostic
    from kinnoo.signing import verify_detached_signature_artifacts
    from kinnoo.signing import (
        load_ed25519_public_key_from_pem,
        public_key_fingerprint,
        verify_signature,
    )
    from kinnoo.integrity import verify_integrity_manifest
    from kinnoo.openclaw_preflight import run_openclaw_preflight_for_command
    from kinnoo.runtime_language import is_nodejs_compatible_runtime
except ImportError:
    from .checksum import (
        ChecksumParseError,
        checksum_sidecar_path_for_archive,
        read_checksum_sidecar,
        verify_archive_checksum,
    )
    from .registry import RegistryService, parse_install_target_spec
    from .registry_backends import MockFilesystemRegistryBackend
    from .auth_command import refresh_registry_auth_if_needed
    from .config import load_registry_config, resolve_lockfile_path
    from .remote_client import RemoteRegistryClient
    from .health_check import (
        check_node_package_manager_availability,
        check_node_runtime_constraint,
        check_openclaw_cli_constraint,
    )
    from .schema import SUPPORTED_NODE_PACKAGE_MANAGERS, normalize_env_vars, LOCKFILE_SCHEMA_VERSION
    from .inspect_command import read_manifest_from_kno_archive
    from .validator import validate
    from .install_trace import write_install_trace
    from .logging_utils import emit_violation_event_diagnostic
    from .signing import verify_detached_signature_artifacts
    from .signing import load_ed25519_public_key_from_pem, public_key_fingerprint, verify_signature
    from .integrity import verify_integrity_manifest
    from .openclaw_preflight import run_openclaw_preflight_for_command
    from .runtime_language import is_nodejs_compatible_runtime


def _read_requirements(requirements_path: Path) -> list[str]:
    requirements: list[str] = []
    if not requirements_path.exists():
        return requirements
    for raw_line in requirements_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def _read_requirements_from_archive(archive_path: Path) -> list[str]:
    requirements: list[str] = []
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            requirements_members = [
                member_name
                for member_name in archive_zip.namelist()
                if Path(member_name).name == "requirements.txt"
            ]
            if not requirements_members:
                return requirements

            with archive_zip.open(requirements_members[0]) as requirements_file:
                requirements_text = requirements_file.read().decode("utf-8")
    except Exception:
        return requirements

    for raw_line in requirements_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def _requirement_name(requirement_line: str) -> str:
    base = re.split(r"[<>=!~\[\s]", requirement_line, maxsplit=1)[0]
    return base.strip().lower().replace("_", "-")


def _requirement_display_name(requirement_line: str) -> str:
    base = re.split(r"[<>=!~\[\s]", requirement_line, maxsplit=1)[0]
    return base.strip()


def _safe_extract_zip(archive_zip: zipfile.ZipFile, target_dir: Path) -> None:
    """Extract zip entries only if all members stay within target_dir."""
    target_root = target_dir.resolve()
    for member in archive_zip.infolist():
        member_name = member.filename
        # Block absolute paths and drive-letter style paths before extraction.
        if member_name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", member_name):
            raise ValueError(f"Archive member uses absolute path: {member_name}")
        resolved_member_path = (target_root / member_name).resolve()
        try:
            resolved_member_path.relative_to(target_root)
        except ValueError as error:
            raise ValueError(f"Archive member escapes target directory: {member_name}") from error

    archive_zip.extractall(target_dir)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _load_signature_fingerprint(archive_path: Path) -> str | None:
    metadata_path = Path(f"{archive_path}.sig.json")
    if not metadata_path.exists() or not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    fingerprint = metadata.get("public_key_fingerprint_sha256")
    if isinstance(fingerprint, str) and fingerprint.strip():
        return fingerprint.strip()
    return None


def _load_sidecar_public_key_pem(archive_path: Path) -> str | None:
    metadata_path = Path(f"{archive_path}.sig.json")
    if not metadata_path.exists() or not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict):
        return None
    public_key_pem = metadata.get("public_key_pem")
    if isinstance(public_key_pem, str) and public_key_pem.strip():
        return public_key_pem.strip()
    return None


def _archive_has_embedded_signature_metadata(archive_path: Path) -> bool:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            if "META-INF/signature.json" not in archive_zip.namelist():
                return False
            payload = archive_zip.read("META-INF/signature.json").decode("utf-8")
    except Exception:
        return False

    try:
        parsed = json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        return False
    if not isinstance(parsed, dict):
        return False

    signature_value = parsed.get("signature")
    return isinstance(signature_value, str) and bool(signature_value.strip())


def _verify_embedded_integrity_and_signature(
    *,
    extracted_dir: Path,
    archive_path: Path,
    strict_mode: bool,
    expected_publisher_public_key: str | None,
    emit_signature_success_message: bool = True,
) -> tuple[bool, str]:
    integrity_path = extracted_dir / "META-INF" / "integrity.json"
    signature_path = extracted_dir / "META-INF" / "signature.json"

    if not integrity_path.exists() or not integrity_path.is_file():
        if strict_mode:
            return False, "Error: Strict mode requires META-INF/integrity.json in the archive."
        return True, "Warning: META-INF/integrity.json not found; continuing for backward compatibility."

    try:
        manifest = json.loads(integrity_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return False, f"Error: Failed to parse META-INF/integrity.json: {error}"

    mismatches = verify_integrity_manifest(extracted_dir, manifest)
    if mismatches:
        mismatch_details = "\n".join(f"  - {item}" for item in mismatches)
        return (
            False,
            "Verification FAILED: integrity mismatch detected.\n" + mismatch_details,
        )

    file_count = len(manifest.get("files", {})) if isinstance(manifest, dict) else 0
    success_message = f"[kinnoo install] Verified {file_count} files, all passed."

    if not strict_mode:
        return True, success_message

    if not signature_path.exists() or not signature_path.is_file():
        return False, "Error: Strict mode requires META-INF/signature.json but it was not found."

    try:
        signature_doc = json.loads(signature_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return False, f"Error: Failed to parse META-INF/signature.json: {error}"

    if not isinstance(signature_doc, dict):
        return False, "Error: META-INF/signature.json must contain a JSON object."

    signature_base64 = signature_doc.get("signature")
    if not isinstance(signature_base64, str) or not signature_base64.strip():
        return False, "Error: META-INF/signature.json is missing required 'signature' field."

    try:
        signature_bytes = base64.b64decode(signature_base64.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        return False, f"Error: META-INF/signature.json has invalid base64 signature: {error}"

    public_key_pem = expected_publisher_public_key
    if public_key_pem is None:
        embedded_public_key = signature_doc.get("public_key_pem")
        if isinstance(embedded_public_key, str) and embedded_public_key.strip():
            public_key_pem = embedded_public_key.strip()
    if public_key_pem is None:
        public_key_pem = _load_sidecar_public_key_pem(archive_path)
    if public_key_pem is None:
        return False, "Error: Strict mode could not resolve public key for signature verification."

    try:
        signing_public_key = load_ed25519_public_key_from_pem(public_key_pem)
    except ValueError as error:
        return False, f"Error: Invalid embedded signing public key: {error}"

    actual_fingerprint = public_key_fingerprint(signing_public_key)
    expected_fingerprint = signature_doc.get("public_key_fingerprint")
    if isinstance(expected_fingerprint, str) and expected_fingerprint.strip():
        if expected_fingerprint.strip() != actual_fingerprint:
            return False, "Error: signature fingerprint does not match signing public key."

    integrity_payload = integrity_path.read_bytes()
    if not verify_signature(signing_public_key, integrity_payload, signature_bytes):
        return False, "Error: signature verification failed for META-INF/integrity.json."

    if emit_signature_success_message:
        return True, success_message + "\n[kinnoo install] Embedded signature verified."
    return True, success_message


def _preinstall_verify_embedded_signature(
    *,
    archive_path: Path,
    expected_publisher_public_key: str | None,
) -> tuple[bool, str | None]:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            names = set(archive_zip.namelist())
            integrity_member = "META-INF/integrity.json"
            signature_member = "META-INF/signature.json"

            if integrity_member not in names:
                return False, "Error: Strict mode requires META-INF/integrity.json in the archive."
            if signature_member not in names:
                return False, "Error: Strict mode requires META-INF/signature.json but it was not found."

            integrity_payload = archive_zip.read(integrity_member)
            try:
                manifest = json.loads(integrity_payload.decode("utf-8"))
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
                return False, f"Error: Failed to parse META-INF/integrity.json: {error}"

            if not isinstance(manifest, dict):
                return False, "Error: META-INF/integrity.json must contain a JSON object."

            files_map = manifest.get("files", {})
            if not isinstance(files_map, dict):
                return False, "Error: META-INF/integrity.json is missing required 'files' mapping."

            mismatches: list[str] = []
            for relative_path, expected_entry in files_map.items():
                if not isinstance(relative_path, str) or not relative_path:
                    mismatches.append("integrity manifest contains an invalid file path entry")
                    continue
                if not isinstance(expected_entry, dict):
                    mismatches.append(f"{relative_path}: integrity entry must be an object")
                    continue
                expected_sha256 = expected_entry.get("sha256")
                if not isinstance(expected_sha256, str) or not expected_sha256.strip():
                    mismatches.append(f"{relative_path}: missing sha256 in integrity entry")
                    continue
                if relative_path not in names:
                    mismatches.append(f"{relative_path}: listed in integrity.json but missing from archive")
                    continue

                payload = archive_zip.read(relative_path)
                actual_sha256 = hashlib.sha256(payload).hexdigest()
                if actual_sha256 != expected_sha256:
                    mismatches.append(
                        f"{relative_path}: checksum mismatch (expected {expected_sha256}, got {actual_sha256})"
                    )

            if mismatches:
                mismatch_details = "\n".join(f"  - {item}" for item in mismatches)
                return False, "Verification FAILED: integrity mismatch detected.\n" + mismatch_details

            try:
                signature_doc = json.loads(archive_zip.read(signature_member).decode("utf-8"))
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
                return False, f"Error: Failed to parse META-INF/signature.json: {error}"

            if not isinstance(signature_doc, dict):
                return False, "Error: META-INF/signature.json must contain a JSON object."

            signature_base64 = signature_doc.get("signature")
            if not isinstance(signature_base64, str) or not signature_base64.strip():
                return False, "Error: META-INF/signature.json is missing required 'signature' field."

            try:
                signature_bytes = base64.b64decode(signature_base64.encode("ascii"))
            except (ValueError, UnicodeEncodeError) as error:
                return False, f"Error: META-INF/signature.json has invalid base64 signature: {error}"

            public_key_pem = expected_publisher_public_key
            if public_key_pem is None:
                embedded_public_key = signature_doc.get("public_key_pem")
                if isinstance(embedded_public_key, str) and embedded_public_key.strip():
                    public_key_pem = embedded_public_key.strip()
            if public_key_pem is None:
                public_key_pem = _load_sidecar_public_key_pem(archive_path)
            if public_key_pem is None:
                return False, "Error: Strict mode could not resolve public key for signature verification."

            try:
                signing_public_key = load_ed25519_public_key_from_pem(public_key_pem)
            except ValueError as error:
                return False, f"Error: Invalid embedded signing public key: {error}"

            actual_fingerprint = public_key_fingerprint(signing_public_key)
            expected_fingerprint = signature_doc.get("public_key_fingerprint")
            if isinstance(expected_fingerprint, str) and expected_fingerprint.strip():
                if expected_fingerprint.strip() != actual_fingerprint:
                    return False, "Error: signature fingerprint does not match signing public key."

            if not verify_signature(signing_public_key, integrity_payload, signature_bytes):
                return False, "Error: signature verification failed for META-INF/integrity.json."
    except zipfile.BadZipFile:
        return False, f"Error: Archive '{archive_path}' is not a valid .kno (zip) archive."
    except OSError as error:
        return False, f"Error: Failed to inspect archive for strict signature verification: {error}"

    return True, "[kinnoo install] Embedded signature verified."


def _update_lockfile_after_install(
    *,
    target_dir: Path,
    agent_name: str,
    agent_version: str,
    archive_path: Path,
    install_source: str,
) -> int:
    lockfile_path = resolve_lockfile_path(start_dir=target_dir)
    lockfile_path.parent.mkdir(parents=True, exist_ok=True)

    existing_doc: dict[str, object] = {}
    if lockfile_path.exists() and lockfile_path.is_file():
        try:
            loaded = yaml.safe_load(lockfile_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing_doc = dict(loaded)
        except (OSError, yaml.YAMLError):
            existing_doc = {}

    agents = existing_doc.get("agents")
    if not isinstance(agents, dict):
        agents = {}

    fingerprint = _load_signature_fingerprint(archive_path)
    agent_entry: dict[str, object] = {
        "version": agent_version,
        "source": install_source,
        "archive_sha256": _sha256_file(archive_path),
        "installed_at": _utc_now_iso(),
    }
    if fingerprint is not None:
        agent_entry["signature_fingerprint"] = fingerprint

    agents[agent_name] = agent_entry

    ordered_agents: dict[str, object] = {}
    for key in sorted(agents.keys()):
        ordered_agents[str(key)] = agents[key]

    lockfile_doc: dict[str, object] = {
        "lock_version": LOCKFILE_SCHEMA_VERSION,
        "locked_at": _utc_now_iso(),
        "platform": {
            "python": platform.python_version(),
            "os": f"{platform.system().lower()}-{platform.machine().lower()}",
        },
        "agents": ordered_agents,
    }

    try:
        lockfile_path.write_text(
            yaml.safe_dump(lockfile_doc, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as error:
        print(f"Error: Failed to write lockfile '{lockfile_path}': {error}", file=sys.stderr)
        return 1

    print(f"[kinnoo install] Updated lockfile: {lockfile_path}")
    return 0


def _finalize_install_success(
    *,
    frozen_mode: bool,
    target_dir: Path,
    agent_name: str,
    agent_version: str,
    archive_path: Path,
    install_source: str,
) -> int:
    if frozen_mode:
        print("[kinnoo install] Frozen mode active; lockfile left unchanged.")
        return 0

    return _update_lockfile_after_install(
        target_dir=target_dir,
        agent_name=agent_name,
        agent_version=agent_version,
        archive_path=archive_path,
        install_source=install_source,
    )


def _resolve_install_lockfile_path(
    *,
    archive_path: Path,
    target_dir_arg: str | None,
) -> Path:
    if target_dir_arg:
        try:
            start_dir = Path(target_dir_arg).expanduser().resolve()
        except OSError:
            start_dir = Path.cwd()
    else:
        start_dir = archive_path.with_suffix("")
    return resolve_lockfile_path(start_dir=start_dir)


def _enforce_frozen_install_lock(
    *,
    archive_path: Path,
    target_dir_arg: str | None,
    agent_name: str,
    agent_version: str,
) -> int:
    lockfile_path = _resolve_install_lockfile_path(
        archive_path=archive_path,
        target_dir_arg=target_dir_arg,
    )

    if not lockfile_path.exists() or not lockfile_path.is_file():
        print(
            f"Error: Frozen install requires lockfile at '{lockfile_path}'.",
            file=sys.stderr,
        )
        print(
            "Error: Re-run install without --frozen to regenerate lockfile, then retry --frozen.",
            file=sys.stderr,
        )
        return 1

    try:
        lockfile_doc = yaml.safe_load(lockfile_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        print(f"Error: Failed to read frozen lockfile '{lockfile_path}': {error}", file=sys.stderr)
        return 1

    if not isinstance(lockfile_doc, dict):
        print(
            f"Error: Frozen install lockfile '{lockfile_path}' is not a valid mapping.",
            file=sys.stderr,
        )
        return 1

    agents = lockfile_doc.get("agents")
    if not isinstance(agents, dict):
        print(
            f"Error: Frozen install lockfile '{lockfile_path}' is missing an 'agents' mapping.",
            file=sys.stderr,
        )
        return 1

    agent_entry = agents.get(agent_name)
    if not isinstance(agent_entry, dict):
        print(
            f"Error: Frozen lockfile entry not found for agent '{agent_name}'.",
            file=sys.stderr,
        )
        print(
            "Error: Re-run install without --frozen to regenerate lockfile, then retry --frozen.",
            file=sys.stderr,
        )
        return 1

    locked_version = agent_entry.get("version")
    if not isinstance(locked_version, str) or not locked_version.strip():
        print(
            f"Error: Frozen lockfile entry for '{agent_name}' is missing a valid version.",
            file=sys.stderr,
        )
        return 1

    normalized_locked_version = locked_version.strip()
    if normalized_locked_version != agent_version:
        print(
            "Error: Frozen lock mismatch for agent "
            f"'{agent_name}': lockfile version is '{normalized_locked_version}' "
            f"but archive version is '{agent_version}'.",
            file=sys.stderr,
        )
        print(
            "Error: Re-run install without --frozen to regenerate lockfile, then retry --frozen.",
            file=sys.stderr,
        )
        return 1

    locked_checksum = agent_entry.get("archive_sha256")
    if not isinstance(locked_checksum, str) or not locked_checksum.strip():
        print(
            f"Error: Frozen lockfile entry for '{agent_name}' is missing archive_sha256.",
            file=sys.stderr,
        )
        return 1

    resolved_locked_checksum = locked_checksum.strip().lower()
    actual_checksum = _sha256_file(archive_path)
    if resolved_locked_checksum != actual_checksum:
        print(
            "Error: Frozen lock mismatch for agent "
            f"'{agent_name}': lockfile checksum is '{resolved_locked_checksum}' "
            f"but archive checksum is '{actual_checksum}'.",
            file=sys.stderr,
        )
        print(
            "Error: Re-run install without --frozen to regenerate lockfile, then retry --frozen.",
            file=sys.stderr,
        )
        return 1

    print(f"[kinnoo install] Frozen lockfile check passed for '{agent_name}'.")
    return 0


def _wheel_distribution_name(wheel_filename: str) -> str:
    return wheel_filename.split("-", 1)[0].lower().replace("_", "-")


def _is_offline_mode_enabled() -> bool:
    # [agent] Offline mode is intentionally controlled by env vars so tests can
    # enforce deterministic no-network behavior without relying on host firewall state.
    offline_values = {"1", "true", "yes", "on"}
    kinnoo_offline = os.environ.get("KINNOO_OFFLINE", "").strip().lower()
    pip_no_index = os.environ.get("PIP_NO_INDEX", "").strip().lower()
    return kinnoo_offline in offline_values or pip_no_index in offline_values


def _detect_node_package_manager_from_lockfile(target_dir: Path) -> str:
    if (target_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (target_dir / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _resolve_node_package_manager(runtime: dict[str, object], target_dir: Path) -> tuple[str | None, str | None]:
    package_manager_value = runtime.get("package_manager")
    if package_manager_value is None:
        return _detect_node_package_manager_from_lockfile(target_dir), None

    if not isinstance(package_manager_value, str) or not package_manager_value.strip():
        return None, "runtime.package_manager must be a non-empty string when provided for nodejs runtime"

    normalized = package_manager_value.strip().lower()
    if normalized not in SUPPORTED_NODE_PACKAGE_MANAGERS:
        supported = ", ".join(SUPPORTED_NODE_PACKAGE_MANAGERS)
        return None, (
            f"runtime.package_manager '{package_manager_value}' is not supported. "
            f"Supported values: {supported}"
        )

    return normalized, None


def _parse_node_audit_severity_counts(raw_output: str) -> dict[str, int]:
    """Parse npm audit JSON output into deterministic severity counters."""
    counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}

    try:
        payload = json.loads(raw_output)
    except (TypeError, ValueError, json.JSONDecodeError):
        return counts

    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    vulnerabilities_meta = metadata.get("vulnerabilities") if isinstance(metadata, dict) else None
    if isinstance(vulnerabilities_meta, dict):
        for severity in counts:
            value = vulnerabilities_meta.get(severity)
            if isinstance(value, int) and value >= 0:
                counts[severity] = value
        return counts

    vulnerabilities = payload.get("vulnerabilities") if isinstance(payload, dict) else None
    if isinstance(vulnerabilities, dict):
        for entry in vulnerabilities.values():
            if not isinstance(entry, dict):
                continue
            severity = entry.get("severity")
            if isinstance(severity, str):
                normalized = severity.strip().lower()
                if normalized in counts:
                    counts[normalized] += 1

    return counts


def _run_node_audit_summary(target_dir: Path, package_manager: str) -> dict[str, int]:
    """Run node dependency audit and print deterministic severity summary."""
    audit_command = [package_manager, "audit", "--json"]
    audit_result = subprocess.run(
        audit_command,
        capture_output=True,
        text=True,
        cwd=target_dir,
    )

    # npm audit commonly returns non-zero when vulnerabilities are present.
    audit_output = audit_result.stdout or audit_result.stderr or ""
    severity_counts = _parse_node_audit_severity_counts(audit_output)

    summary = (
        "[kinnoo install] Node audit severity summary: "
        f"critical={severity_counts['critical']} "
        f"high={severity_counts['high']} "
        f"moderate={severity_counts['moderate']} "
        f"low={severity_counts['low']}"
    )
    print(summary)

    if not audit_output.strip():
        print(
            "Warning: Node audit command produced no parseable output; severity summary defaults to zero counts.",
            file=sys.stderr,
        )

    return severity_counts


def _detect_node_lifecycle_scripts(package_json_path: Path) -> list[str]:
    """Return deterministic lifecycle script names declared in package.json."""
    try:
        package_payload = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return []

    scripts = package_payload.get("scripts") if isinstance(package_payload, dict) else None
    if not isinstance(scripts, dict):
        return []

    declared: list[str] = []
    for script_name, script_command in scripts.items():
        if not isinstance(script_name, str) or not isinstance(script_command, str):
            continue
        normalized_name = script_name.strip()
        if not normalized_name or not script_command.strip():
            continue
        if normalized_name in NODE_LIFECYCLE_SCRIPT_NAMES:
            declared.append(normalized_name)

    return sorted(set(declared))


def _write_node_install_trace(
    target_dir: Path,
    *,
    package_manager: str,
    lifecycle_scripts: list[str],
    allow_vulnerable: bool,
    ignore_scripts: bool,
    severity_counts: dict[str, int],
    outcome: str,
    decision_reason: str,
) -> None:
    """Write machine-readable Node install trace with audit and policy decisions."""
    trace_payload: dict[str, object] = {
        "schema_version": "1.0",
        "runtime_language": "nodejs",
        "package_manager": package_manager,
        "lifecycle_scripts": {
            "detected": bool(lifecycle_scripts),
            "names": list(lifecycle_scripts),
            "policy": "ignored" if ignore_scripts else "allowed",
        },
        "audit": {
            "severity_counts": {
                "critical": int(severity_counts.get("critical", 0)),
                "high": int(severity_counts.get("high", 0)),
                "moderate": int(severity_counts.get("moderate", 0)),
                "low": int(severity_counts.get("low", 0)),
            }
        },
        "decision": {
            "outcome": outcome,
            "reason": decision_reason,
            "allow_vulnerable": allow_vulnerable,
            "ignore_scripts": ignore_scripts,
        },
    }

    trace_path = write_install_trace(target_dir=target_dir, payload=trace_payload)
    if trace_path is not None:
        print(f"[kinnoo install] Wrote install trace: '{trace_path}'")


def _install_node_dependencies(
    target_dir: Path,
    runtime: dict[str, object],
    *,
    allow_vulnerable: bool,
    ignore_scripts: bool,
) -> int:
    runtime_version = runtime.get("version")
    runtime_constraint = str(runtime_version) if runtime_version is not None else ""
    runtime_ok, runtime_message = check_node_runtime_constraint(runtime_constraint)
    if not runtime_ok:
        print(f"Error: {runtime_message}", file=sys.stderr)
        print(
            "Error: Install a compatible Node.js runtime and retry installation.",
            file=sys.stderr,
        )
        return 1

    package_manager, resolution_error = _resolve_node_package_manager(runtime, target_dir)
    if package_manager is None:
        print(f"Error: {resolution_error}", file=sys.stderr)
        return 1

    package_manager_ok, package_manager_message = check_node_package_manager_availability(package_manager)
    if not package_manager_ok:
        print(f"Error: {package_manager_message}", file=sys.stderr)
        print(
            "Error: Install the configured package manager and ensure it is available on PATH.",
            file=sys.stderr,
        )
        return 1

    package_json_path = target_dir / "package.json"
    if not package_json_path.exists():
        print(
            "Error: Node.js runtime install requires package.json in the extracted agent directory.",
            file=sys.stderr,
        )
        return 1

    lifecycle_scripts = _detect_node_lifecycle_scripts(package_json_path)
    if lifecycle_scripts:
        lifecycle_label = ", ".join(lifecycle_scripts)
        print(
            "Warning: Detected Node lifecycle scripts in package.json: "
            f"{lifecycle_label}.",
            file=sys.stderr,
        )
        if ignore_scripts:
            print(
                "[kinnoo install] Lifecycle scripts policy: ignored (--ignore-scripts enabled)."
            )
        else:
            print(
                "Warning: Lifecycle scripts are allowed and may execute during dependency installation.",
                file=sys.stderr,
            )
    elif ignore_scripts:
        print("[kinnoo install] Lifecycle scripts policy: ignored (--ignore-scripts enabled).")
    else:
        print("[kinnoo install] Lifecycle scripts policy: allowed.")

    install_command = [package_manager, "install"]
    if ignore_scripts:
        install_command.append("--ignore-scripts")
    install_result = subprocess.run(
        install_command,
        capture_output=True,
        text=True,
        cwd=target_dir,
    )
    if install_result.returncode != 0:
        command_label = " ".join(install_command)
        print(
            f"Error: Node dependency installation failed while running '{command_label}'. "
            "Verify your package manager setup and package.json dependencies.",
            file=sys.stderr,
        )
        if install_result.stderr:
            print(install_result.stderr, file=sys.stderr)
        return install_result.returncode

    print(f"[kinnoo install] Node dependencies installed successfully via {package_manager}.")
    severity_counts = _run_node_audit_summary(target_dir=target_dir, package_manager=package_manager)

    critical_count = severity_counts.get("critical", 0)
    if critical_count > 0 and not allow_vulnerable:
        _write_node_install_trace(
            target_dir=target_dir,
            package_manager=package_manager,
            lifecycle_scripts=lifecycle_scripts,
            allow_vulnerable=allow_vulnerable,
            ignore_scripts=ignore_scripts,
            severity_counts=severity_counts,
            outcome="blocked",
            decision_reason="critical_vulnerabilities_blocked",
        )
        print(
            "Error: Critical vulnerabilities were detected in Node dependency audit results. "
            "Install blocked by default. Re-run with --allow-vulnerable to proceed at your own risk.",
            file=sys.stderr,
        )
        return 1

    decision_reason = "no_critical_vulnerabilities"
    if critical_count > 0 and allow_vulnerable:
        decision_reason = "critical_vulnerabilities_overridden"
        print(
            "Warning: Continuing install despite critical vulnerabilities because --allow-vulnerable was set.",
            file=sys.stderr,
        )

    _write_node_install_trace(
        target_dir=target_dir,
        package_manager=package_manager,
        lifecycle_scripts=lifecycle_scripts,
        allow_vulnerable=allow_vulnerable,
        ignore_scripts=ignore_scripts,
        severity_counts=severity_counts,
        outcome="allowed",
        decision_reason=decision_reason,
    )

    return 0


DEFAULT_OPENCLAW_MINIMUM_VERSION = "0.1.0"


def _resolve_remote_latest_version(*, backend: RemoteRegistryClient, agent_name: str) -> str | None:
    """Resolve explicit latest version from remote registry list metadata."""
    tenant_slug: str | None = None
    normalized_agent_name = agent_name
    if "/" in agent_name:
        tenant_part, raw_name = agent_name.split("/", 1)
        if tenant_part.strip() and raw_name.strip():
            tenant_slug = tenant_part.strip()
            normalized_agent_name = raw_name.strip()

    list_agents_fn = getattr(backend, "list_agents", None)
    if callable(list_agents_fn):
        summaries = list_agents_fn(tenant=tenant_slug)
    else:
        summaries = backend.list_latest_agents()
    for summary in summaries:
        if isinstance(summary, dict):
            candidate_name = summary.get("name") or summary.get("agent_slug")
            latest_version = summary.get("latest_version")
        else:
            candidate_name = getattr(summary, "name", None)
            latest_version = getattr(summary, "latest_version", None)

        if candidate_name == normalized_agent_name and isinstance(latest_version, str) and latest_version.strip():
            return latest_version.strip()

    return None


def _download_remote_archive_payload(*, backend: RemoteRegistryClient, download_url: str) -> bytes:
    """Download archive bytes from remote resolve payload URL."""
    parsed = urlparse(download_url)
    backend_base = urlparse(getattr(backend, "_base_url", ""))

    # Presigned URLs commonly use http/https; local test backends may emit file URLs.
    if parsed.scheme in {"http", "https", "file"}:
        # If URL points back to the registry host, fetch with bearer auth.
        if (
            parsed.scheme in {"http", "https"}
            and backend_base.scheme in {"http", "https"}
            and parsed.netloc == backend_base.netloc
        ):
            path_with_query = parsed.path + (f"?{parsed.query}" if parsed.query else "")
            return backend.request_bytes(path=path_with_query)
        with urllib_request.urlopen(download_url, timeout=30) as response:
            return response.read()

    # Some servers return relative API download paths instead of fully-qualified URLs.
    if not parsed.scheme and download_url.startswith("/api/"):
        return backend.request_bytes(path=download_url)

    # Some legacy servers return root-relative paths; attempt authenticated fetch first.
    if not parsed.scheme and download_url.startswith("/"):
        try:
            return backend.request_bytes(path=download_url)
        except Exception as error:
            raise RuntimeError(
                "Remote registry returned a root-relative path that could not be downloaded. "
                "Server should return a presigned http(s) URL or an /api/... download path. "
                f"Details: {error}"
            ) from error

    if not parsed.scheme:
        normalized_path = "/" + download_url.lstrip("/")
        return backend.request_bytes(path=normalized_path)

    raise RuntimeError(f"Unsupported remote download URL scheme '{parsed.scheme}'.")


def _write_openclaw_install_trace(
    target_dir: Path,
    *,
    agent_name: str,
    minimum_version: str,
    delegated_command: list[str],
    outcome: str,
    category: str,
    decision_reason: str,
    delegated_exit_code: int | None,
) -> None:
    trace_payload: dict[str, object] = {
        "schema_version": "1.0",
        "runtime_language": "nodejs",
        "delegated_install": {
            "backend": "openclaw-cli",
            "agent": agent_name,
            "workspace": str(target_dir),
            "minimum_version": minimum_version,
            "command": delegated_command,
        },
        "decision": {
            "outcome": outcome,
            "category": category,
            "reason": decision_reason,
            "delegated_exit_code": delegated_exit_code,
        },
    }
    trace_path = write_install_trace(target_dir=target_dir, payload=trace_payload)
    if trace_path is not None:
        print(f"[kinnoo install] Wrote install trace: '{trace_path}'")


def _install_openclaw_skill_dependencies(
    target_dir: Path,
    *,
    agent_name: str,
    minimum_openclaw_version: str,
) -> int:
    precheck_ok, precheck_category, precheck_message = check_openclaw_cli_constraint(
        minimum_openclaw_version
    )
    print(f"[kinnoo install][openclaw] [{precheck_category}] {precheck_message}")
    delegated_command = [
        "openclaw",
        "agents",
        "add",
        agent_name,
        "--workspace",
        str(target_dir),
    ]
    if not precheck_ok:
        _write_openclaw_install_trace(
            target_dir=target_dir,
            agent_name=agent_name,
            minimum_version=minimum_openclaw_version,
            delegated_command=delegated_command,
            outcome="blocked",
            category=precheck_category,
            decision_reason=f"openclaw_cli_precheck_failed:{precheck_category}",
            delegated_exit_code=None,
        )
        print(
            f"Error: OpenClaw delegated install prechecks failed (category={precheck_category}). "
            "Install/upgrade OpenClaw CLI and retry.",
            file=sys.stderr,
        )
        return 1

    print(
        "[kinnoo install][openclaw] Delegating workspace registration to OpenClaw CLI: "
        f"{' '.join(delegated_command)}"
    )
    delegated_result = subprocess.run(
        delegated_command,
        capture_output=True,
        text=True,
        cwd=target_dir,
    )

    if delegated_result.returncode != 0:
        delegated_category = "openclaw_cli_delegated_nonzero_exit"
        _write_openclaw_install_trace(
            target_dir=target_dir,
            agent_name=agent_name,
            minimum_version=minimum_openclaw_version,
            delegated_command=delegated_command,
            outcome="failed",
            category=delegated_category,
            decision_reason=f"openclaw_cli_delegated_install_failed:{delegated_category}",
            delegated_exit_code=int(delegated_result.returncode),
        )
        print(
            "Error: OpenClaw delegated install failed "
            f"(category={delegated_category}). "
            "Review OpenClaw CLI output and retry.",
            file=sys.stderr,
        )
        if delegated_result.stderr:
            print(delegated_result.stderr, file=sys.stderr)
        return delegated_result.returncode

    _write_openclaw_install_trace(
        target_dir=target_dir,
        agent_name=agent_name,
        minimum_version=minimum_openclaw_version,
        delegated_command=delegated_command,
        outcome="allowed",
        category="openclaw_cli_delegated_success",
        decision_reason="openclaw_cli_delegated_install_succeeded",
        delegated_exit_code=0,
    )
    print("[kinnoo install][openclaw] Workspace registration completed successfully.")
    return 0


def _iter_state_dir_paths(manifest_data: dict[str, object]) -> list[str]:
    """Return normalized state directory roots from manifest state_dirs entries."""
    declared_state_dirs = manifest_data.get("state_dirs")
    if not isinstance(declared_state_dirs, list):
        return []

    normalized_paths: list[str] = []
    for entry in declared_state_dirs:
        if isinstance(entry, str):
            candidate = entry.strip()
            if candidate:
                normalized_paths.append(candidate)
            continue

        if isinstance(entry, dict):
            path_value = entry.get("path")
            if isinstance(path_value, str):
                candidate = path_value.strip()
                if candidate:
                    normalized_paths.append(candidate)

    return normalized_paths


def _permission_bool_label(value: object) -> str:
    if value is True:
        return "allowed"
    if value is False:
        return "denied"
    return "unspecified"


def _build_permissions_summary_lines(manifest_data: dict[str, object]) -> list[str]:
    """Build deterministic human-readable permissions summary lines."""
    permissions = manifest_data.get("permissions")
    if not isinstance(permissions, dict):
        return []

    lines: list[str] = []
    lines.append(f"  - Network: {_permission_bool_label(permissions.get('network'))}")

    filesystem_scope = permissions.get("filesystem_scope")
    if isinstance(filesystem_scope, str) and filesystem_scope.strip():
        lines.append(f"  - Filesystem Scope: {filesystem_scope.strip()}")
    else:
        lines.append("  - Filesystem Scope: unspecified")

    lines.append(f"  - Shell: {_permission_bool_label(permissions.get('shell'))}")
    lines.append(f"  - Browser: {_permission_bool_label(permissions.get('browser'))}")

    env_access = permissions.get("env_access")
    if isinstance(env_access, list):
        env_names: list[str] = []
        for item in env_access:
            if not isinstance(item, str):
                continue
            name = item.strip()
            if not name:
                continue
            env_names.append(name)
        if env_names:
            lines.append(f"  - Env Access: {', '.join(env_names)}")
        else:
            lines.append("  - Env Access: (none)")
    else:
        lines.append("  - Env Access: (none)")

    return lines


def _restore_state_snapshots(
    target_dir: Path,
    manifest_data: dict[str, object],
    overwrite_state: bool,
) -> int:
    """Restore packed state snapshots into runtime state directories.

    Snapshot source layout:
    - state_snapshots/<declared-state-dir>/...
    """
    snapshot_root = target_dir / "state_snapshots"
    if not snapshot_root.exists() or not snapshot_root.is_dir():
        return 0

    restored_count = 0
    skipped_count = 0
    for state_dir_path in _iter_state_dir_paths(manifest_data):
        source_state_dir = snapshot_root / state_dir_path
        if not source_state_dir.exists() or not source_state_dir.is_dir():
            continue

        destination_state_dir = target_dir / state_dir_path
        if destination_state_dir.exists() and not overwrite_state:
            print(
                "Warning: Existing state directory detected; preserving current state and skipping restore for "
                f"'{state_dir_path}'. Re-run install with --state-overwrite to replace it.",
                file=sys.stderr,
            )
            skipped_count += 1
            continue

        if destination_state_dir.exists() and overwrite_state:
            if destination_state_dir.is_dir():
                shutil.rmtree(destination_state_dir)
            else:
                destination_state_dir.unlink()

        for source_file in sorted(source_state_dir.rglob("*")):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source_state_dir)
            destination_file = destination_state_dir / relative
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination_file)

        restored_count += 1

    if restored_count > 0:
        print(f"[kinnoo install] Restored state snapshots for {restored_count} state directory(ies).")
    if skipped_count > 0:
        print(
            f"[kinnoo install] Skipped restore for {skipped_count} state directory(ies) due to existing state.",
            file=sys.stderr,
        )

    return 0


def install_agent(
    archive_path: str,
    target_dir_arg: str | None = None,
    force: bool = False,
    assume_yes: bool = False,
    overwrite_state: bool = False,
    allow_vulnerable: bool = False,
    ignore_scripts: bool = False,
    accept_permissions: bool = False,
    allow_unverified_publisher: bool = False,
    strict_mode: bool = False,
    skip_verify: bool = False,
    frozen_mode: bool = False,
    expected_publisher_public_key: str | None = None,
    use_local: bool = False,
    use_remote: bool = False,
    minimum_openclaw_version: str = DEFAULT_OPENCLAW_MINIMUM_VERSION,
    openclaw_skill_identifier: str | None = None,
    install_source: str = "archive-file",
) -> int:
    if openclaw_skill_identifier is not None:
        return _install_openclaw_skill_for_existing_agent(
            agent_name=archive_path,
            skill_identifier=openclaw_skill_identifier,
            minimum_openclaw_version=minimum_openclaw_version,
        )

    target_spec = parse_install_target_spec(archive_path)
    if target_spec.kind == "invalid":
        print(f"Error: {target_spec.error}", file=sys.stderr)
        return 1

    if target_spec.kind in {"registry-latest", "registry-exact"}:
        selector_name = str(target_spec.name)
        selector_tenant = getattr(target_spec, "tenant", None)
        selector_with_tenant = f"{selector_tenant}/{selector_name}" if selector_tenant else selector_name
        selector = selector_with_tenant
        version: str | None = None
        if target_spec.kind == "registry-exact":
            version = target_spec.version
            selector = f"{selector_with_tenant}=={target_spec.version}"

        if use_local and use_remote:
            print("Error: --local and --remote cannot be used together.", file=sys.stderr)
            return 1

        registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
        backend_root = Path(registry_root).expanduser() if registry_root else None

        backend = None
        backend_label = "local"
        resolved_install_source = "registry-local"
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
            resolved_install_source = "registry-remote"
        else:
            config = load_registry_config()
            config, refresh_error = refresh_registry_auth_if_needed(config=config)
            if refresh_error:
                print(f"Error: {refresh_error}", file=sys.stderr)
                return 1
            if config.registry_url:
                if not config.registry_token or not config.tenant_slug:
                    print(
                        "Error: Remote registry URL is configured but token/tenant settings are missing. "
                        "Set KINNOO_REGISTRY_TOKEN and KINNOO_TENANT_SLUG (or config file equivalents).",
                        file=sys.stderr,
                    )
                    return 1
                backend = RemoteRegistryClient(
                    base_url=config.registry_url,
                    token=config.registry_token,
                    tenant_slug=config.tenant_slug,
                )
                backend_label = "remote"
                resolved_install_source = "registry-remote"
            else:
                backend = MockFilesystemRegistryBackend(root=backend_root)
                resolved_install_source = "registry-local"

        service = RegistryService(backend=backend)

        resolved_archive_path: Path | None = None
        expected_publisher_key: str | None = None
        expected_archive_checksum: str | None = None

        if backend_label == "remote":
            resolved_version = version
            if resolved_version is None:
                try:
                    resolved_version = _resolve_remote_latest_version(
                        backend=backend,
                        agent_name=selector_with_tenant,
                    )
                except Exception as error:
                    print(f"Error: Failed to resolve latest remote version: {error}", file=sys.stderr)
                    return 1

                if resolved_version is None:
                    print(
                        "Error: Failed to resolve remote latest version from registry listing. "
                        "Try installing with an explicit version (for example: agent==1.2.3).",
                        file=sys.stderr,
                    )
                    return 1

            try:
                resolved_payload = backend.resolve(
                    name=selector_name,
                    version=resolved_version,
                    tenant=selector_tenant,
                )
            except Exception as error:
                print(f"Error: Failed to resolve remote registry target: {error}", file=sys.stderr)
                return 1

            download_url = None
            if isinstance(resolved_payload, dict):
                raw_download_url = resolved_payload.get("download_url")
                if isinstance(raw_download_url, str) and raw_download_url.strip():
                    download_url = raw_download_url.strip()
                raw_checksum = resolved_payload.get("checksum_sha256")
                if isinstance(raw_checksum, str) and raw_checksum.strip():
                    expected_archive_checksum = raw_checksum.strip()

            if not download_url:
                print(
                    "Error: Remote resolve response did not include a usable download_url.",
                    file=sys.stderr,
                )
                return 1

            try:
                payload = _download_remote_archive_payload(
                    backend=backend,
                    download_url=download_url,
                )
            except Exception as error:
                print(f"Error: Failed to download archive from remote registry: {error}", file=sys.stderr)
                return 1

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".kno") as temp_archive:
                    temp_archive.write(payload)
                    resolved_archive_path = Path(temp_archive.name)
            except OSError as error:
                print(f"Error: Failed to stage downloaded archive: {error}", file=sys.stderr)
                return 1
        else:
            resolved_record, resolve_error = service.resolve_with_error(
                name=selector_name,
                version=version,
                tenant=selector_tenant,
            )
            if resolved_record is None:
                print(f"Error: {resolve_error or 'Registry resolution failed.'}", file=sys.stderr)
                return 1
            resolved_archive_path = resolved_record.archive_path
            expected_publisher_key = resolved_record.publisher_public_key

        resolved_target_dir_arg = target_dir_arg
        if resolved_target_dir_arg is None:
            if version is None:
                resolved_target_dir_arg = str(Path.cwd() / str(target_spec.name))
            else:
                resolved_target_dir_arg = str(Path.cwd() / f"{target_spec.name}-{version}")

        if resolved_archive_path is None:
            print("Error: Registry resolution failed.", file=sys.stderr)
            return 1

        print(
            f"[kinnoo install] Resolved registry selector '{selector}' to '{resolved_archive_path}' ({backend_label})"
        )

        try:
            return _install_from_archive_path(
                archive_path=str(resolved_archive_path),
                target_dir_arg=resolved_target_dir_arg,
                force=force,
                assume_yes=assume_yes,
                overwrite_state=overwrite_state,
                allow_vulnerable=allow_vulnerable,
                ignore_scripts=ignore_scripts,
                accept_permissions=accept_permissions,
                allow_unverified_publisher=allow_unverified_publisher,
                strict_mode=strict_mode,
                skip_verify=skip_verify,
                frozen_mode=frozen_mode,
                expected_publisher_public_key=expected_publisher_key,
                expected_archive_checksum=expected_archive_checksum,
                minimum_openclaw_version=minimum_openclaw_version,
                install_source=resolved_install_source,
            )
        finally:
            if backend_label == "remote" and resolved_archive_path.exists():
                resolved_archive_path.unlink(missing_ok=True)

    archive = target_spec.archive_path or Path(archive_path)
    return _install_from_archive_path(
        archive_path=str(archive),
        target_dir_arg=target_dir_arg,
        force=force,
        assume_yes=assume_yes,
        overwrite_state=overwrite_state,
        allow_vulnerable=allow_vulnerable,
        ignore_scripts=ignore_scripts,
        accept_permissions=accept_permissions,
        allow_unverified_publisher=allow_unverified_publisher,
        strict_mode=strict_mode,
        skip_verify=skip_verify,
        frozen_mode=frozen_mode,
        expected_publisher_public_key=expected_publisher_public_key,
        minimum_openclaw_version=minimum_openclaw_version,
        install_source=install_source,
    )


def _resolve_openclaw_agent_workspace(agent_name: str) -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            ["openclaw", "agents", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return None, f"failed to execute openclaw agents list: {error}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return None, detail or "openclaw agents list returned non-zero exit code"

    try:
        payload = json.loads(result.stdout.strip() or "[]")
    except json.JSONDecodeError:
        return None, "openclaw agents list output was not valid JSON"

    if not isinstance(payload, list):
        return None, "openclaw agents list output was not a JSON list"

    for item in payload:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or item_id != agent_name:
            continue
        workspace_value = item.get("workspace")
        if isinstance(workspace_value, str) and workspace_value.strip():
            return workspace_value.strip(), None
        fallback_workspace = str(Path.home() / ".openclaw" / f"workspace-{agent_name}")
        return fallback_workspace, None

    return None, "agent not found"


def _normalize_openclaw_skill_identifier(raw_identifier: str) -> tuple[str | None, str | None]:
    candidate = raw_identifier.strip()
    if not candidate:
        return None, "skill identifier is empty"

    parsed = urlparse(candidate)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host not in {"clawhub.ai", "app.clawhub.ai"}:
            return None, "unsupported skill URL host"

        segments = [segment for segment in parsed.path.split("/") if segment]
        if len(segments) >= 3 and segments[0] in {"skills", "skill"}:
            owner, slug = segments[1], segments[2]
        elif len(segments) >= 2:
            owner, slug = segments[0], segments[1]
        else:
            return None, "skill URL must contain owner/slug path"

        normalized = f"{owner.strip()}/{slug.strip()}"
        if "/" not in normalized or normalized.startswith("/") or normalized.endswith("/"):
            return None, "skill URL did not resolve to a valid owner/slug"
        return normalized, None

    if "/" not in candidate:
        return None, "skill identifier must be owner/slug or a supported URL"

    owner, slug = candidate.split("/", 1)
    owner = owner.strip()
    slug = slug.strip()
    if not owner or not slug:
        return None, "skill identifier must include non-empty owner and slug"
    return f"{owner}/{slug}", None


def _classify_openclaw_skill_install_outcome(*, returncode: int, stdout: str, stderr: str) -> tuple[str, bool]:
    combined = f"{stdout}\n{stderr}".lower()
    if "already installed" in combined or "already-installed" in combined:
        return "already-installed", True
    if "not found" in combined or "not-found" in combined:
        return "not-found", False
    if returncode == 0:
        return "success", True
    return "failed", False


def _install_openclaw_skill_for_existing_agent(
    *,
    agent_name: str,
    skill_identifier: str,
    minimum_openclaw_version: str,
) -> int:
    normalized_agent = agent_name.strip()
    if not normalized_agent:
        print("Error: agent name is required for --openclaw-skill installs.", file=sys.stderr)
        return 1

    normalized_skill, normalize_error = _normalize_openclaw_skill_identifier(skill_identifier)
    if normalized_skill is None:
        print(
            "Error: invalid --openclaw-skill identifier. "
            f"{normalize_error}. Use owner/slug or a supported ClawHub URL.",
            file=sys.stderr,
        )
        return 1

    preflight_result = run_openclaw_preflight_for_command(
        "openclaw-skill-install",
        minimum_version=minimum_openclaw_version,
    )
    if not preflight_result.ok:
        print(
            "Error: OpenClaw skill install preflight failed "
            f"(category={preflight_result.category}). {preflight_result.message}",
            file=sys.stderr,
        )
        return 1

    workspace_path, resolve_error = _resolve_openclaw_agent_workspace(normalized_agent)
    if workspace_path is None:
        print(
            f"Error: OpenClaw agent '{normalized_agent}' was not found. "
            "Create/register the agent first and retry.",
            file=sys.stderr,
        )
        if resolve_error and resolve_error != "agent not found":
            print(f"Error: OpenClaw agent resolution failed: {resolve_error}", file=sys.stderr)
        return 1

    command = [
        "openclaw",
        "skills",
        "install",
        normalized_skill,
        "--workspace",
        workspace_path,
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    outcome, success = _classify_openclaw_skill_install_outcome(
        returncode=int(result.returncode),
        stdout=result.stdout or "",
        stderr=result.stderr or "",
    )
    if outcome == "success":
        print(
            f"[kinnoo install][openclaw-skill] outcome=success agent={normalized_agent} skill={normalized_skill}"
        )
        return 0
    if outcome == "already-installed":
        print(
            f"[kinnoo install][openclaw-skill] outcome=already-installed agent={normalized_agent} skill={normalized_skill}"
        )
        return 0
    if outcome == "not-found":
        print(
            f"Error: OpenClaw skill install outcome=not-found (category=openclaw_skill_not_found) "
            f"agent={normalized_agent} skill={normalized_skill}",
            file=sys.stderr,
        )
        return 1

    if result.returncode != 0:
        print(
            "Error: OpenClaw skill install delegation failed "
            "(category=openclaw_skill_install_nonzero_exit).",
            file=sys.stderr,
        )

    return 0 if success else int(result.returncode)


def _install_from_archive_path(
    archive_path: str,
    target_dir_arg: str | None = None,
    force: bool = False,
    assume_yes: bool = False,
    overwrite_state: bool = False,
    allow_vulnerable: bool = False,
    ignore_scripts: bool = False,
    accept_permissions: bool = False,
    allow_unverified_publisher: bool = False,
    strict_mode: bool = False,
    skip_verify: bool = False,
    frozen_mode: bool = False,
    expected_publisher_public_key: str | None = None,
    expected_archive_checksum: str | None = None,
    minimum_openclaw_version: str = DEFAULT_OPENCLAW_MINIMUM_VERSION,
    install_source: str = "archive-file",
) -> int:
    archive = Path(archive_path)
    if not archive.exists() or not archive.is_file():
        print(f"Error: Archive '{archive}' does not exist or is not a file.", file=sys.stderr)
        return 1
    if not str(archive).endswith(".kno"):
        print(f"Error: Archive '{archive}' is not a .kno file.", file=sys.stderr)
        return 1

    if strict_mode and allow_unverified_publisher:
        print(
            "Error: --allow-unverified-publisher cannot be used with --strict.",
            file=sys.stderr,
        )
        return 1

    checksum_path = checksum_sidecar_path_for_archive(archive)
    signature_path = Path(f"{archive}.sig")
    signature_metadata_path = Path(f"{archive}.sig.json")

    if skip_verify:
        print("[kinnoo install] Verification skipped (--skip-verify).")
    else:
        checksum_verified = False
        if checksum_path.exists():
            try:
                expected_checksum, expected_archive_filename = read_checksum_sidecar(checksum_path)
            except (OSError, ChecksumParseError) as error:
                print(f"Error: Failed to read checksum sidecar: {error}", file=sys.stderr)
                return 1

            if expected_archive_filename != archive.name:
                print(
                    "Error: Checksum sidecar filename does not match archive filename.",
                    file=sys.stderr,
                )
                return 1

            # [agent] Integrity verification must occur before extraction/write side effects.
            checksum_matches, _ = verify_archive_checksum(archive, expected_checksum)
            if not checksum_matches:
                print(
                    "Archive integrity check failed — the file may be corrupted or tampered with",
                    file=sys.stderr,
                )
                return 1

            print("[kinnoo install] Archive checksum verified.")
            checksum_verified = True
        elif isinstance(expected_archive_checksum, str) and expected_archive_checksum.strip():
            checksum_matches, _ = verify_archive_checksum(archive, expected_archive_checksum.strip())
            if not checksum_matches:
                print(
                    "Archive integrity check failed — the file may be corrupted or tampered with",
                    file=sys.stderr,
                )
                return 1
            print("[kinnoo install] Archive checksum verified.")
            checksum_verified = True

        source_is_unverified = not checksum_verified
        if strict_mode and source_is_unverified:
            print(
                "Error: Strict mode requires archive integrity verification; checksum sidecar is missing.",
                file=sys.stderr,
            )
            return 1

        if source_is_unverified:
            print("No checksum file found — archive integrity not verified", file=sys.stderr)
            warning_message = "This agent is from an unverified source."
            print(warning_message, file=sys.stderr)
            if not assume_yes:
                try:
                    unverified_confirmation = input(
                        "This agent is from an unverified source. Continue? (y/n): "
                    ).strip().lower()
                except EOFError:
                    print("Install aborted by user.", file=sys.stderr)
                    return 1
                if unverified_confirmation not in {"y", "yes"}:
                    print("Install aborted by user.", file=sys.stderr)
                    return 1

        has_signature_artifacts = signature_path.exists() or signature_metadata_path.exists()
        has_embedded_signature_metadata = _archive_has_embedded_signature_metadata(archive)

        has_detached_signature_pair = signature_path.exists() and signature_metadata_path.exists()
        preinstall_embedded_signature_verified = False

        if strict_mode and not has_detached_signature_pair:
            print(
                "[kinnoo install] Detached signature artifacts not found; falling back to embedded META-INF/signature.json verification."
            )
            embedded_ok, embedded_message = _preinstall_verify_embedded_signature(
                archive_path=archive,
                expected_publisher_public_key=expected_publisher_public_key,
            )
            if not embedded_ok:
                if embedded_message:
                    print(embedded_message, file=sys.stderr)
                return 1
            if embedded_message:
                print(embedded_message)
            preinstall_embedded_signature_verified = True

        if has_signature_artifacts:
            if not signature_path.exists() or not signature_metadata_path.exists():
                print(
                    "Error: Signed archive is missing required signature artifacts (.sig and .sig.json).",
                    file=sys.stderr,
                )
                print(
                    "Error: Re-pack with --sign and retry install.",
                    file=sys.stderr,
                )
                return 1

            try:
                verify_detached_signature_artifacts(
                    archive_path=archive,
                    signature_path=signature_path,
                    metadata_path=signature_metadata_path,
                    expected_public_key_pem=expected_publisher_public_key,
                )
            except ValueError as error:
                print(
                    f"Error: Signature verification failed: {error}",
                    file=sys.stderr,
                )
                if strict_mode:
                    print(
                        "Error: Strict mode requires valid signature metadata; unsigned artifacts are not allowed.",
                        file=sys.stderr,
                    )
                print(
                    "Error: Archive authenticity could not be verified. Re-download from a trusted publisher or re-pack with a valid signing key.",
                    file=sys.stderr,
                )
                return 1

            print("[kinnoo install] Archive signature verified.")
        elif checksum_verified and not strict_mode:
            signature_metadata_present = has_embedded_signature_metadata
            if expected_publisher_public_key is not None and not signature_metadata_present:
                print(
                    "Error: Registry publisher key association exists but archive signature metadata is missing.",
                    file=sys.stderr,
                )
                print(
                    "Error: Re-publish a signed archive with matching publisher signature metadata.",
                    file=sys.stderr,
                )
                return 1
            if signature_metadata_present:
                print(
                    "Warning: Signature metadata found, but signature verification is skipped in non-strict mode. Use --strict to verify publisher authenticity.",
                    file=sys.stderr,
                )
                if assume_yes:
                    if not allow_unverified_publisher:
                        print(
                            "Error: Non-interactive install requires --allow-unverified-publisher when signature verification is skipped.",
                            file=sys.stderr,
                        )
                        return 1
                    print(
                        "[kinnoo install] Signature verification override acknowledged via --allow-unverified-publisher."
                    )
                else:
                    try:
                        print("[kinnoo install] Continue without signature verification? [y/N]: ", end="", flush=True)
                        publisher_confirmation = input().strip().lower()
                    except EOFError:
                        print("Install aborted: signature verification not approved.", file=sys.stderr)
                        return 1

                    if publisher_confirmation not in {"y", "yes"}:
                        print("Install aborted: signature verification not approved.", file=sys.stderr)
                        return 1
            else:
                print(
                    "Warning: UNVERIFIED PUBLISHER - no signature metadata found for this archive.",
                    file=sys.stderr,
                )
                if assume_yes:
                    if not allow_unverified_publisher:
                        print(
                            "Error: Non-interactive install requires --allow-unverified-publisher when signature metadata is absent.",
                            file=sys.stderr,
                        )
                        return 1
                    print(
                        "[kinnoo install] Unverified publisher override acknowledged via --allow-unverified-publisher."
                    )
                else:
                    try:
                        publisher_confirmation = input(
                            "UNVERIFIED PUBLISHER: no signature metadata found. Continue? [y/N]: "
                        ).strip().lower()
                    except EOFError:
                        print("Install aborted: unverified publisher not approved.", file=sys.stderr)
                        return 1

                    if publisher_confirmation not in {"y", "yes"}:
                        print("Install aborted: unverified publisher not approved.", file=sys.stderr)
                        return 1

    manifest_data = read_manifest_from_kno_archive(archive)
    if manifest_data is None:
        return 1

    runtime_type = "unknown"
    runtime = manifest_data.get("runtime")
    if isinstance(runtime, dict):
        runtime_type_value = runtime.get("type")
        if isinstance(runtime_type_value, str) and runtime_type_value.strip():
            runtime_type = runtime_type_value

    agent_name = str(manifest_data.get("name", "unknown"))
    agent_version = str(manifest_data.get("version", "unknown"))
    manifest_framework = ""
    manifest_framework_value = manifest_data.get("framework")
    if isinstance(manifest_framework_value, str) and manifest_framework_value.strip():
        manifest_framework = manifest_framework_value.strip().lower()
    manifest_type = "agent"
    manifest_type_value = manifest_data.get("type")
    if isinstance(manifest_type_value, str) and manifest_type_value.strip():
        manifest_type = manifest_type_value.strip().lower()
    is_openclaw_agent = manifest_framework == "openclaw" or manifest_type == "openclaw-skill"

    if frozen_mode:
        frozen_validation_exit_code = _enforce_frozen_install_lock(
            archive_path=archive,
            target_dir_arg=target_dir_arg,
            agent_name=agent_name,
            agent_version=agent_version,
        )
        if frozen_validation_exit_code != 0:
            return frozen_validation_exit_code

    env_var_names = normalize_env_vars(manifest_data.get("env_vars"))
    requirement_lines = _read_requirements_from_archive(archive)
    dependency_names = [_requirement_display_name(line) for line in requirement_lines]

    print("[kinnoo install] Install summary:")
    print(f"- Agent: {agent_name}")
    print(f"- Version: {agent_version}")
    print(f"- Runtime Type: {runtime_type}")
    if dependency_names:
        print("- Dependencies:")
        for dependency_name in dependency_names:
            print(f"  - {dependency_name}")
    else:
        print("- Dependencies: (none)")
    if env_var_names:
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        print("- Env Vars:")
        for env_var_name in env_var_names:
            print(f"  - {env_var_name}")
    else:
        print("- Env Vars: (none)")

    permission_summary_lines = _build_permissions_summary_lines(manifest_data)
    if permission_summary_lines:
        print("- Permissions:")
        for permission_line in permission_summary_lines:
            print(permission_line)
    else:
        print("- Permissions: (none declared)")

    if permission_summary_lines:
        if accept_permissions:
            print(
                "[kinnoo install] Permissions consent acknowledged via --accept-permissions override."
            )
        elif assume_yes:
            emit_violation_event_diagnostic(
                {
                    "event_type": "permission_violation",
                    "boundary": "install",
                    "classification": "permissions_consent_required",
                    "capability": "permissions",
                    "attempted_action": "non_interactive_install_without_accept_permissions",
                    "message": "permissions consent override required for non-interactive install",
                    "remediation": "Re-run with --accept-permissions to acknowledge requested capabilities.",
                }
            )
            print(
                "Error: Manifest declares permissions. Re-run with --accept-permissions to acknowledge requested capabilities in non-interactive mode.",
                file=sys.stderr,
            )
            return 1
        else:
            try:
                permission_confirmation = input(
                    "This agent declares explicit permissions. Allow requested permissions? [y/N]: "
                ).strip().lower()
            except EOFError:
                emit_violation_event_diagnostic(
                    {
                        "event_type": "permission_violation",
                        "boundary": "install",
                        "classification": "permissions_consent_denied",
                        "capability": "permissions",
                        "attempted_action": "interactive_permissions_consent",
                        "message": "permissions consent not granted",
                        "remediation": "Re-run install and answer 'y' when prompted for permissions consent.",
                    }
                )
                print("Install aborted: permissions consent not granted.", file=sys.stderr)
                return 1

            if permission_confirmation not in {"y", "yes"}:
                emit_violation_event_diagnostic(
                    {
                        "event_type": "permission_violation",
                        "boundary": "install",
                        "classification": "permissions_consent_denied",
                        "capability": "permissions",
                        "attempted_action": "interactive_permissions_consent",
                        "message": "permissions consent not granted",
                        "remediation": "Re-run install and answer 'y' when prompted for permissions consent.",
                    }
                )
                print("Install aborted: permissions consent not granted.", file=sys.stderr)
                return 1

    if not assume_yes:
        try:
            confirmation = input("Continue with install? [y/N]: ").strip().lower()
        except EOFError:
            print("Install aborted by user.", file=sys.stderr)
            return 1
        if confirmation not in {"y", "yes"}:
            print("Install aborted by user.", file=sys.stderr)
            return 1

    if manifest_type == "openclaw-skill":
        preflight_result = run_openclaw_preflight_for_command("install")
        if not preflight_result.ok:
            print(f"Error: {preflight_result.message}", file=sys.stderr)
            return 1

    if target_dir_arg:
        target_dir = Path(target_dir_arg).resolve()
    elif is_openclaw_agent:
        target_dir = Path.home() / ".openclaw" / f"workspace-{agent_name}"
    else:
        target_dir = archive.with_suffix("")

    if not str(target_dir) or str(target_dir) in ["/", "", "."]:
        print(f"Error: Invalid target directory '{target_dir}'.", file=sys.stderr)
        return 1

    if target_dir.exists() and not force:
        if is_openclaw_agent:
            print(
                f"Error: OpenClaw workspace already exists at '{target_dir}'.",
                file=sys.stderr,
            )
            print(
                "Error: Re-run with --force to replace the workspace or remove it manually before retrying.",
                file=sys.stderr,
            )
            return 1
        print(f"Error: Target directory '{target_dir}' already exists. Aborting to prevent overwrite.", file=sys.stderr)
        return 1
    if target_dir.exists() and force:
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            print(f"Error: Failed to remove existing directory '{target_dir}': {error}", file=sys.stderr)
            return 1

    try:
        with zipfile.ZipFile(archive, "r") as archive_zip:
            _safe_extract_zip(archive_zip, target_dir)
    except zipfile.BadZipFile:
        print(f"Error: Archive '{archive}' is not a valid .kno (zip) archive.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Error: Refusing to extract unsafe archive entries: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error: Failed to extract archive: {error}", file=sys.stderr)
        return 1

    print(f"[kinnoo install] Extracted '{archive.name}' to '{target_dir}'")

    kinnoo_yaml_path = target_dir / "kinnoo.yaml"
    if not kinnoo_yaml_path.exists():
        print(f"Error: kinnoo.yaml not found in extracted directory '{target_dir}'. Aborting install.", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    if not skip_verify:
        embedded_ok, embedded_message = _verify_embedded_integrity_and_signature(
            extracted_dir=target_dir,
            archive_path=archive,
            strict_mode=strict_mode,
            expected_publisher_public_key=expected_publisher_public_key,
            emit_signature_success_message=not preinstall_embedded_signature_verified,
        )
        if embedded_message:
            target_stream = sys.stdout if embedded_ok else sys.stderr
            print(embedded_message, file=target_stream)
        if not embedded_ok:
            shutil.rmtree(target_dir, ignore_errors=True)
            return 1

    try:
        is_valid, errors = validate(str(kinnoo_yaml_path))
    except Exception as error:
        print(f"Error: Failed to validate kinnoo.yaml: {error}", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    if not is_valid:
        print("Manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    print("[kinnoo install] Manifest validated successfully.")

    restore_exit_code = _restore_state_snapshots(
        target_dir=target_dir,
        manifest_data=manifest_data,
        overwrite_state=overwrite_state,
    )
    if restore_exit_code != 0:
        shutil.rmtree(target_dir, ignore_errors=True)
        return restore_exit_code

    if manifest_type == "openclaw-skill":
        openclaw_exit_code = _install_openclaw_skill_dependencies(
            target_dir=target_dir,
            agent_name=agent_name,
            minimum_openclaw_version=minimum_openclaw_version,
        )
        if openclaw_exit_code != 0:
            return openclaw_exit_code
        return _finalize_install_success(
            frozen_mode=frozen_mode,
            target_dir=target_dir,
            agent_name=agent_name,
            agent_version=agent_version,
            archive_path=archive,
            install_source=install_source,
        )

    runtime_language = "python"
    if isinstance(runtime, dict):
        runtime_language_value = runtime.get("language")
        if isinstance(runtime_language_value, str) and runtime_language_value.strip():
            runtime_language = runtime_language_value.strip().lower()

    if is_nodejs_compatible_runtime(runtime_language):
        node_exit_code = _install_node_dependencies(
            target_dir=target_dir,
            runtime=runtime if isinstance(runtime, dict) else {},
            allow_vulnerable=allow_vulnerable,
            ignore_scripts=ignore_scripts,
        )
        if node_exit_code != 0:
            return node_exit_code
        return _finalize_install_success(
            frozen_mode=frozen_mode,
            target_dir=target_dir,
            agent_name=agent_name,
            agent_version=agent_version,
            archive_path=archive,
            install_source=install_source,
        )

    wheels_dir = target_dir / "wheels"
    venv_dir = target_dir / ".venv"

    if not venv_dir.exists():
        try:
            venv.create(venv_dir, with_pip=True)
        except Exception as error:
            print(f"Error: Failed to create venv in '{venv_dir}': {error}", file=sys.stderr)
            shutil.rmtree(target_dir, ignore_errors=True)
            return 1

    pip_exe = venv_dir / "bin" / "pip"
    if not pip_exe.exists():
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    if not pip_exe.exists():
        print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    wheel_files: list[Path] = []
    if wheels_dir.exists() and wheels_dir.is_dir():
        wheel_files = list(wheels_dir.glob("*.whl"))

    requirements_path = target_dir / "requirements.txt"
    requirements = _read_requirements(requirements_path)
    if not requirements:
        if wheel_files:
            for wheel in wheel_files:
                print(f"[kinnoo install] Installing wheel: {wheel.name}")
                wheel_install = subprocess.run(
                    [str(pip_exe), "install", str(wheel)],
                    capture_output=True,
                    text=True,
                )
                if wheel_install.returncode != 0:
                    print(f"Error: pip install failed for {wheel.name}", file=sys.stderr)
                    if wheel_install.stderr:
                        print(wheel_install.stderr, file=sys.stderr)
                    shutil.rmtree(target_dir, ignore_errors=True)
                    return wheel_install.returncode
            print("[kinnoo install] All wheels installed successfully.")
        else:
            print("[kinnoo install] No dependencies listed in requirements.txt. Skipping dependency install.")
        return _finalize_install_success(
            frozen_mode=frozen_mode,
            target_dir=target_dir,
            agent_name=agent_name,
            agent_version=agent_version,
            archive_path=archive,
            install_source=install_source,
        )

    offline_mode_enabled = _is_offline_mode_enabled()

    expected_distributions = {_requirement_name(item) for item in requirements}
    available_distributions = {_wheel_distribution_name(wheel.name) for wheel in wheel_files}
    missing_distributions = sorted(expected_distributions - available_distributions)

    needs_pypi_fallback = bool(missing_distributions)
    if missing_distributions:
        print(
            "Warning: Missing packaged wheels for dependencies: "
            f"{', '.join(missing_distributions)}. Falling back to PyPI; internet access is required.",
            file=sys.stderr,
        )

    local_install_attempted = False
    if wheel_files:
        local_install_attempted = True
        local_install = subprocess.run(
            [
                str(pip_exe),
                "install",
                "--no-index",
                "--find-links",
                str(wheels_dir),
                "-r",
                str(requirements_path),
            ],
            capture_output=True,
            text=True,
        )
        if local_install.returncode != 0:
            needs_pypi_fallback = True
            print(
                "Warning: Local wheel-only installation failed. Falling back to PyPI; internet access is required.",
                file=sys.stderr,
            )
    else:
        needs_pypi_fallback = True
        print(
            "Warning: No bundled wheels were found. Falling back to PyPI; internet access is required.",
            file=sys.stderr,
        )

    if needs_pypi_fallback and offline_mode_enabled:
        if missing_distributions:
            print(
                "Error: Offline install requested, but packaged wheels are missing for: "
                f"{', '.join(missing_distributions)}. "
                "Rebuild the archive with complete wheels or disable offline mode.",
                file=sys.stderr,
            )
        else:
            print(
                "Error: Offline install requested, and bundled wheel-only installation failed. "
                "Rebuild the archive with complete compatible wheels or disable offline mode.",
                file=sys.stderr,
            )
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    if needs_pypi_fallback:
        fallback_install = subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_path)],
            capture_output=True,
            text=True,
        )
        if fallback_install.returncode != 0:
            print(
                "Error: PyPI fallback installation failed.",
                file=sys.stderr,
            )
            if fallback_install.stderr:
                print(fallback_install.stderr, file=sys.stderr)
            shutil.rmtree(target_dir, ignore_errors=True)
            return fallback_install.returncode
        print("[kinnoo install] Dependencies installed via PyPI fallback.")
    elif local_install_attempted:
        print("[kinnoo install] Dependencies installed successfully from bundled wheels.")
        print("[kinnoo install] Offline-ready install path used (no network fallback required).")

    return _finalize_install_success(
        frozen_mode=frozen_mode,
        target_dir=target_dir,
        agent_name=agent_name,
        agent_version=agent_version,
        archive_path=archive,
        install_source=install_source,
    )
