from __future__ import annotations

import os
import json
import sys
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

try:
    from kinnoo.checksum import ChecksumParseError, read_checksum_sidecar
    from kinnoo.code_sweep import sweep_env_var_exposure
    from kinnoo.schema import REQUIRED_FIELDS, OPTIONAL_FIELDS, normalize_manifest_defaults, normalize_type_field
    from kinnoo.size_format import format_size_human_readable
    from kinnoo.templates import (
        INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE,
        INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES,
    )
    from kinnoo.validator import validate_manifest_data
    from kinnoo.registry_backends import MockFilesystemRegistryBackend
    from kinnoo.registry import RegistryService
except ImportError:
    from .checksum import ChecksumParseError, read_checksum_sidecar
    from .code_sweep import sweep_env_var_exposure
    from .schema import REQUIRED_FIELDS, OPTIONAL_FIELDS, normalize_manifest_defaults, normalize_type_field
    from .size_format import format_size_human_readable
    from .templates import (
        INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE,
        INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES,
    )
    from .validator import validate_manifest_data
    from .registry_backends import MockFilesystemRegistryBackend
    from .registry import RegistryService


def _print_missing_manifest_guidance() -> None:
    print("Error: Missing required file 'kinnoo.yaml' in target directory.")
    print("Create a kinnoo.yaml file before running `kinnoo inspect`.")
    print("Minimal example:")
    print(INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE, end="")


def _print_missing_requirements_guidance() -> None:
    print("Error: Missing required file 'requirements.txt' in target directory.")
    print("Create requirements.txt before running `kinnoo inspect`.")
    for guidance_line in INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES:
        print(guidance_line)


def read_manifest_from_kno_archive(archive_path: Path) -> dict[str, object] | None:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            manifest_members = [
                member_name
                for member_name in archive_zip.namelist()
                if Path(member_name).name == "kinnoo.yaml"
            ]

            if not manifest_members:
                print(
                    "Error: kinnoo.yaml not found inside archive. Ensure the .kno contains a manifest file.",
                    file=sys.stderr,
                )
                return None

            manifest_member = manifest_members[0]
            with archive_zip.open(manifest_member) as manifest_file:
                manifest_bytes = manifest_file.read()
    except zipfile.BadZipFile:
        print(
            f"Error: Archive '{archive_path}' is not a valid zip-based .kno file.",
            file=sys.stderr,
        )
        return None
    except OSError as error:
        print(f"Error: Failed reading archive '{archive_path}': {error}", file=sys.stderr)
        return None

    try:
        manifest_text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        print(f"Error: Unable to decode kinnoo.yaml from archive: {error}", file=sys.stderr)
        return None

    try:
        manifest_data = yaml.safe_load(manifest_text)
    except yaml.YAMLError as error:
        print(f"Error: Failed to parse kinnoo.yaml from archive: {error}", file=sys.stderr)
        return None

    if not isinstance(manifest_data, dict):
        print("Error: kinnoo.yaml inside archive must parse to a mapping/object.", file=sys.stderr)
        return None

    return manifest_data


def _load_manifest_from_directory(manifest_path: Path) -> dict[str, Any] | None:
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Error: Unable to read '{manifest_path}': {error}", file=sys.stderr)
        return None

    try:
        manifest_data = yaml.safe_load(manifest_text)
    except yaml.YAMLError as error:
        print(f"Error: Failed to parse '{manifest_path.name}': {error}", file=sys.stderr)
        return None

    if not isinstance(manifest_data, dict):
        print(
            f"Error: '{manifest_path.name}' must parse to a mapping/object.",
            file=sys.stderr,
        )
        return None

    return manifest_data


def _normalize_manifest_for_display(manifest_data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_manifest_defaults(dict(manifest_data))
    if "inputs" in normalized and isinstance(normalized["inputs"], dict):
        normalize_type_field(normalized["inputs"])
    if "outputs" in normalized and isinstance(normalized["outputs"], dict):
        normalize_type_field(normalized["outputs"])
    return normalized


def _print_manifest_validation_errors(errors: list[str]) -> None:
    print("Error: Manifest validation failed.", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


def _env_var_names_for_display(manifest_data: dict[str, Any]) -> list[str]:
    env_vars = manifest_data.get("env_vars")
    if not isinstance(env_vars, list):
        return []

    names: list[str] = []
    for env_var in env_vars:
        if isinstance(env_var, str) and env_var.strip():
            names.append(env_var)

    return names


def _archive_checksum_for_display(archive_path: Path) -> str | None:
    sidecar_path = archive_path.with_name(f"{archive_path.name}.sha256")
    if not sidecar_path.exists():
        return None

    try:
        expected_checksum, referenced_filename = read_checksum_sidecar(sidecar_path)
    except (OSError, ChecksumParseError):
        return None

    if referenced_filename != archive_path.name:
        return None

    return expected_checksum


def _path_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _declared_asset_paths(manifest_data: dict[str, Any]) -> list[str]:
    assets = manifest_data.get("assets")
    if not isinstance(assets, dict):
        return []

    paths = assets.get("paths", [])
    if not isinstance(paths, list):
        return []

    normalized: list[str] = []
    for item in paths:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _asset_file_sizes_for_directory(
    manifest_data: dict[str, Any],
    directory_path: Path,
) -> dict[str, int]:
    file_sizes: dict[str, int] = {}
    for declared_path in _declared_asset_paths(manifest_data):
        candidate = (directory_path / declared_path).resolve(strict=False)
        if not _path_within_root(candidate, directory_path):
            continue

        if candidate.is_file():
            rel = candidate.relative_to(directory_path).as_posix()
            file_sizes[rel] = candidate.stat().st_size
            continue

        if candidate.is_dir():
            for child in sorted(candidate.rglob("*")):
                if not child.is_file():
                    continue
                rel = child.relative_to(directory_path).as_posix()
                file_sizes[rel] = child.stat().st_size

    return file_sizes


def _asset_file_sizes_for_archive(
    manifest_data: dict[str, Any],
    archive_path: Path,
) -> dict[str, int]:
    file_sizes: dict[str, int] = {}
    declared_paths = [path.strip("/") for path in _declared_asset_paths(manifest_data)]
    if not declared_paths:
        return file_sizes

    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            for member in archive_zip.infolist():
                member_name = member.filename.strip("/")
                if not member_name or member.is_dir():
                    continue

                for declared in declared_paths:
                    if not declared:
                        continue
                    if member_name == declared or member_name.startswith(f"{declared}/"):
                        file_sizes[member_name] = member.file_size
                        break
    except (OSError, zipfile.BadZipFile):
        return {}

    return file_sizes


def _print_asset_metadata(
    manifest_data: dict[str, Any],
    asset_file_sizes: dict[str, int],
) -> None:
    declared_paths = _declared_asset_paths(manifest_data)
    if not declared_paths:
        return

    print("- Asset Paths:")
    for declared_path in declared_paths:
        print(f"  - {declared_path}")

    total_size = sum(asset_file_sizes.values())
    print(f"- Assets Size: {format_size_human_readable(total_size)}")

    if asset_file_sizes:
        print("- Asset Files:")
        for rel_path, size_bytes in sorted(asset_file_sizes.items()):
            print(f"  - {rel_path} ({format_size_human_readable(size_bytes)})")


def _print_services_metadata(manifest_data: dict[str, Any]) -> None:
    """Render optional services declarations in a stable, human-readable shape."""
    services = manifest_data.get("services")
    if not isinstance(services, list) or not services:
        return

    print("- Services:")
    for index, service in enumerate(services):
        if not isinstance(service, dict):
            print(f"  - service[{index}]: (invalid service entry)")
            continue

        name = service.get("name")
        service_type = service.get("type")
        safe_name = name if isinstance(name, str) and name.strip() else f"service[{index}]"
        safe_type = service_type if isinstance(service_type, str) and service_type.strip() else "(missing)"
        print(f"  - {safe_name} ({safe_type})")

        health_check = service.get("health_check")
        if not isinstance(health_check, dict):
            continue

        method = health_check.get("method")
        if isinstance(method, str) and method.strip():
            print(f"    - health_check.method: {method}")

        # Print method-specific fields only when present to preserve readability.
        if "port" in health_check:
            print(f"    - health_check.port: {health_check['port']}")
        if "url" in health_check:
            print(f"    - health_check.url: {health_check['url']}")
        if "process_name" in health_check:
            print(f"    - health_check.process_name: {health_check['process_name']}")


KNOWN_MANIFEST_METADATA_FIELDS: list[str] = list(dict.fromkeys([*REQUIRED_FIELDS, *OPTIONAL_FIELDS]))
KNOWN_MANIFEST_METADATA_FIELD_SET: set[str] = set(KNOWN_MANIFEST_METADATA_FIELDS)


def _flatten_manifest_fields(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            continue
        dotted_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten_manifest_fields(value, dotted_key))
        else:
            flattened[dotted_key] = value
    return flattened


def _render_raw_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value

    rendered = yaml.safe_dump(
        value,
        sort_keys=False,
        default_flow_style=True,
    ).strip()
    return rendered if rendered else "null"


def _manifest_path_exists(payload: dict[str, Any], dotted_path: str) -> bool:
    current: Any = payload
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return False
        current = current[segment]
    return True


def _manifest_get_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for segment in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
    return current


def _manifest_set_path(payload: dict[str, Any], dotted_path: str, value: Any) -> None:
    segments = dotted_path.split(".")
    current: dict[str, Any] = payload
    for segment in segments[:-1]:
        child = current.get(segment)
        if not isinstance(child, dict):
            child = {}
            current[segment] = child
        current = child
    current[segments[-1]] = value


def _parse_update_value(raw_value: str) -> Any:
    try:
        parsed = yaml.safe_load(raw_value)
    except yaml.YAMLError:
        return raw_value

    if parsed is None and raw_value.strip().lower() not in {"null", "~"}:
        return raw_value
    return parsed


def _print_raw_metadata(
    target_label: str,
    manifest_data: dict[str, Any],
    *,
    full: bool,
) -> None:
    normalized = _normalize_manifest_for_display(manifest_data)

    print(f"Inspect target type: {target_label}")
    print("Manifest metadata (raw):")

    flattened = _flatten_manifest_fields(normalized)
    if full:
        for field in KNOWN_MANIFEST_METADATA_FIELDS:
            if field in flattened:
                print(f"{field}: {_render_raw_value(flattened[field])}")
            else:
                print(f"{field}: N/A")
        return

    for field in sorted(flattened.keys()):
        print(f"{field}: {_render_raw_value(flattened[field])}")


def _print_full_metadata_fields(normalized: dict[str, Any]) -> None:
    print("- All Metadata Fields:")
    for field in KNOWN_MANIFEST_METADATA_FIELDS:
        if _manifest_path_exists(normalized, field):
            value = _manifest_get_path(normalized, field)
            print(f"  - {field}: {_render_raw_value(value)}")
        else:
            print(f"  - {field}: N/A")


def _declared_types_for_display(manifest_data: dict[str, Any], section_name: str) -> list[str]:
    section = manifest_data.get(section_name)
    if not isinstance(section, dict):
        return []

    declared_type = section.get("type")
    if isinstance(declared_type, str):
        value = declared_type.strip().lower()
        return [value] if value else []

    if not isinstance(declared_type, list):
        return []

    normalized: list[str] = []
    for item in declared_type:
        if not isinstance(item, str):
            continue
        value = item.strip().lower()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _print_inspect_output(
    target_label: str,
    manifest_data: dict[str, Any],
    archive_checksum: str | None = None,
    archive_size_human: str | None = None,
    asset_file_sizes: dict[str, int] | None = None,
    *,
    full: bool = False,
    raw: bool = False,
) -> None:
    if raw:
        _print_raw_metadata(target_label, manifest_data, full=full)
        return

    normalized = _normalize_manifest_for_display(manifest_data)

    print(f"Inspect target type: {target_label}")
    print("Manifest metadata:")
    print(f"- Name: {normalized['name']}")
    print(f"- Version: {normalized['version']}")
    print(f"- Runtime Type: {normalized['runtime']['type']}")

    input_types = _declared_types_for_display(normalized, "inputs")
    output_types = _declared_types_for_display(normalized, "outputs")
    input_label = ", ".join(input_types) if input_types else "(none)"
    output_label = ", ".join(output_types) if output_types else "(none)"
    print(f"- Input Types: {input_label}")
    print(f"- Output Types: {output_label}")

    json_contract_notes: list[str] = []
    if "json" in input_types:
        json_contract_notes.append("use --json-input/--json-file for structured input payloads")
    if normalized["runtime"]["type"] != "mcp-server" and "json" in output_types:
        json_contract_notes.append("stdout must be valid JSON when outputs.type includes json")
    if json_contract_notes:
        print(f"- JSON Contract: {'; '.join(json_contract_notes)}")

    if archive_size_human is not None:
        print(f"- Archive Size: {archive_size_human}")
    if archive_checksum is not None:
        print(f"- Checksum (SHA256): {archive_checksum}")

    dependencies = normalized.get("dependencies", [])
    if dependencies:
        print("- Dependencies:")
        for dependency in dependencies:
            print(f"  - {dependency}")
    else:
        print("- Dependencies: (none)")

    optional_scalar_fields = (
        ("description", "Description"),
        ("author", "Author"),
        ("license", "License"),
    )
    for field_name, label in optional_scalar_fields:
        value = normalized.get(field_name)
        if isinstance(value, str) and value.strip():
            print(f"- {label}: {value}")

    if "env_vars" in normalized:
        env_var_names = _env_var_names_for_display(normalized)
        if env_var_names:
            # [agent] SECURITY INVARIANT: only env var NAMES, never values
            print("- Env Vars:")
            for env_var_name in env_var_names:
                print(f"  - {env_var_name}")
        else:
            print("- Env Vars: (none)")

    provenance = normalized.get("provenance")
    if isinstance(provenance, dict):
        print("- Provenance:")
        source_registry = provenance.get("source_registry")
        source_version = provenance.get("source_version")
        source_slug = provenance.get("source_slug")
        source_url = provenance.get("source_url")
        if isinstance(source_registry, str) and source_registry.strip():
            print(f"  - source_registry: {source_registry}")
        if isinstance(source_version, str) and source_version.strip():
            print(f"  - source_version: {source_version}")
        if isinstance(source_slug, str) and source_slug.strip():
            print(f"  - source_slug: {source_slug}")
        if isinstance(source_url, str) and source_url.strip():
            print(f"  - source_url: {source_url}")

    _print_services_metadata(normalized)

    _print_asset_metadata(normalized, asset_file_sizes or {})

    if full:
        _print_full_metadata_fields(normalized)


def _build_inspect_json_payload(
    target_label: str,
    manifest_data: dict[str, Any],
    archive_checksum: str | None = None,
    archive_size_human: str | None = None,
    asset_file_sizes: dict[str, int] | None = None,
    *,
    full: bool = False,
    raw: bool = False,
) -> dict[str, Any]:
    normalized = _normalize_manifest_for_display(manifest_data)
    payload: dict[str, Any] = {
        "target_type": target_label,
        "full": full,
        "raw": raw,
    }

    if raw:
        flattened = _flatten_manifest_fields(normalized)
        if full:
            payload["manifest_raw"] = {
                field: (_render_raw_value(flattened[field]) if field in flattened else "N/A")
                for field in KNOWN_MANIFEST_METADATA_FIELDS
            }
        else:
            payload["manifest_raw"] = {
                field: _render_raw_value(value) for field, value in sorted(flattened.items())
            }
        return payload

    input_types = _declared_types_for_display(normalized, "inputs")
    output_types = _declared_types_for_display(normalized, "outputs")
    json_contract_notes: list[str] = []
    if "json" in input_types:
        json_contract_notes.append("use --json-input/--json-file for structured input payloads")
    if normalized["runtime"]["type"] != "mcp-server" and "json" in output_types:
        json_contract_notes.append("stdout must be valid JSON when outputs.type includes json")

    payload["manifest"] = normalized
    payload["input_types"] = input_types
    payload["output_types"] = output_types
    payload["json_contract_notes"] = json_contract_notes
    payload["archive_size"] = archive_size_human
    payload["archive_checksum_sha256"] = archive_checksum
    payload["asset_file_sizes"] = asset_file_sizes or {}

    if full:
        payload["all_metadata_fields"] = {
            field: (
                _render_raw_value(_manifest_get_path(normalized, field))
                if _manifest_path_exists(normalized, field)
                else "N/A"
            )
            for field in KNOWN_MANIFEST_METADATA_FIELDS
        }

    return payload


def _inspect_archive_target(archive_path: Path, *, full: bool, raw: bool, json_output: bool = False) -> int:
    manifest_data = read_manifest_from_kno_archive(archive_path)
    if manifest_data is None:
        return 1

    is_valid, errors = validate_manifest_data(manifest_data)
    if not is_valid:
        _print_manifest_validation_errors(errors)
        return 1

    archive_size_human = format_size_human_readable(archive_path.stat().st_size)
    archive_checksum = _archive_checksum_for_display(archive_path)
    asset_file_sizes = _asset_file_sizes_for_archive(manifest_data, archive_path)
    if json_output:
        payload = _build_inspect_json_payload(
            "archive (.kno)",
            manifest_data,
            archive_checksum=archive_checksum,
            archive_size_human=archive_size_human,
            asset_file_sizes=asset_file_sizes,
            full=full,
            raw=raw,
        )
        print(json.dumps(payload, sort_keys=True))
    else:
        _print_inspect_output(
            "archive (.kno)",
            manifest_data,
            archive_checksum=archive_checksum,
            archive_size_human=archive_size_human,
            asset_file_sizes=asset_file_sizes,
            full=full,
            raw=raw,
        )

    return 0


def _inspect_directory_target(directory_path: Path, *, full: bool, raw: bool, json_output: bool = False) -> int:
    manifest_path = directory_path / "kinnoo.yaml"
    requirements_path = directory_path / "requirements.txt"

    if not manifest_path.exists():
        _print_missing_manifest_guidance()
        return 1

    if not requirements_path.exists():
        _print_missing_requirements_guidance()
        return 1

    manifest_data = _load_manifest_from_directory(manifest_path)
    if manifest_data is None:
        return 1

    is_valid, errors = validate_manifest_data(manifest_data, manifest_root=directory_path)
    if not is_valid:
        _print_manifest_validation_errors(errors)
        return 1

    asset_file_sizes = _asset_file_sizes_for_directory(manifest_data, directory_path)
    if json_output:
        payload = _build_inspect_json_payload(
            "directory",
            manifest_data,
            asset_file_sizes=asset_file_sizes,
            full=full,
            raw=raw,
        )
    else:
        _print_inspect_output(
            "directory",
            manifest_data,
            asset_file_sizes=asset_file_sizes,
            full=full,
            raw=raw,
        )

    import_report = _load_import_report(directory_path)
    if import_report is not None and not json_output:
        _print_import_report_hints(import_report)
    if json_output:
        payload["import_report"] = import_report

    if raw and not json_output:
        return 0

    declared_env_vars = _env_var_names_for_display(_normalize_manifest_for_display(manifest_data))
    sweep_warnings = sweep_env_var_exposure(directory_path, declared_env_vars)
    if json_output:
        payload["security_sweep_warnings"] = sweep_warnings
        payload["security_sweep_heuristic"] = True
        print(json.dumps(payload, sort_keys=True))
    elif sweep_warnings:
        print("Security sweep:")
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        for warning in sweep_warnings:
            print(f"- {warning}")
    else:
        print("Security sweep: no env var exposure patterns detected (heuristic)")
    if not json_output:
        print("(heuristic scan — may produce false positives; not a substitute for code review)")

    return 0


def _load_import_report(directory_path: Path) -> dict[str, Any] | None:
    report_path = directory_path / "kinnoo-import-report.json"
    if not report_path.exists() or not report_path.is_file():
        return None

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _print_import_report_hints(import_report: dict[str, Any]) -> None:
    requirements = import_report.get("requirements")
    unresolved = import_report.get("unresolved")

    if isinstance(requirements, dict):
        print("- Imported Requirement Hints:")
        for section in ("env", "config", "bin"):
            values = requirements.get(section)
            if isinstance(values, list) and values:
                rendered = ", ".join(str(item) for item in values)
                print(f"  - {section}: {rendered}")
            else:
                print(f"  - {section}: (none)")

    if isinstance(unresolved, list) and unresolved:
        print("- Unresolved Guidance:")
        for item in unresolved:
            if isinstance(item, str) and item.strip():
                print(f"  - {item}")


def inspect_target(target_arg: str, *, full: bool = False, raw: bool = False, json_output: bool = False) -> int:
    normalized_target = target_arg.strip()
    if normalized_target.lower().startswith("clawhub:") or normalized_target.lower().startswith("clawhub/"):
        mirror_slug = normalized_target.split(":", 1)[1] if ":" in normalized_target else normalized_target
        return _inspect_clawhub_mirror_target(mirror_slug, full=full, raw=raw, json_output=json_output)

    target = Path(target_arg)
    if not target.exists():
        print(f"Error: Inspect target '{target}' does not exist.", file=sys.stderr)
        return 1

    if target.is_dir():
        return _inspect_directory_target(target, full=full, raw=raw, json_output=json_output)

    if target.is_file():
        if target.suffix.lower() == ".kno":
            return _inspect_archive_target(target, full=full, raw=raw, json_output=json_output)

        print(
            f"Error: Unsupported inspect target file '{target}'. Expected an agent directory or .kno archive.",
            file=sys.stderr,
        )
        return 1

    print(f"Error: Inspect target '{target}' is neither a directory nor a regular file.", file=sys.stderr)
    return 1


def _inspect_clawhub_mirror_target(slug: str, *, full: bool, raw: bool, json_output: bool = False) -> int:
    normalized_slug = slug.strip().strip("/")
    if not normalized_slug:
        print("Error: ClawHub inspect target slug cannot be empty.", file=sys.stderr)
        return 1

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None
    service = RegistryService(backend=MockFilesystemRegistryBackend(root=backend_root))

    matches = [
        record
        for record in service.list_clawhub_mirror_records()
        if record.agent_slug == normalized_slug
    ]
    if not matches:
        print(
            f"Error: ClawHub mirror record '{normalized_slug}' not found in local mirror index.",
            file=sys.stderr,
        )
        return 1

    selected = sorted(matches, key=lambda item: item.source_version, reverse=True)[0]

    if json_output:
        payload = {
            "target_type": "clawhub mirror",
            "full": full,
            "raw": raw,
            "tenant_slug": selected.tenant_slug,
            "agent_slug": selected.agent_slug,
            "name": selected.name,
            "version": selected.version,
            "source_registry": selected.source_registry,
            "source_version": selected.source_version,
            "source_url": selected.source_url,
            "synced_at": selected.synced_at,
        }
        print(json.dumps(payload, sort_keys=True))
        return 0

    if raw:
        print("Inspect target type: clawhub mirror")
        print(f"tenant_slug: {selected.tenant_slug}")
        print(f"agent_slug: {selected.agent_slug}")
        print(f"name: {selected.name}")
        print(f"version: {selected.version}")
        print(f"source_registry: {selected.source_registry}")
        print(f"source_version: {selected.source_version}")
        print(f"source_url: {selected.source_url or 'N/A'}")
        print(f"synced_at: {selected.synced_at or 'N/A'}")
        return 0

    print("Inspect target type: clawhub mirror")
    print(f"- Name: {selected.name}")
    print(f"- Version: {selected.version}")
    print("- Source: ClawHub (mirrored)")
    print(f"- Source Slug: {selected.agent_slug}")
    print(f"- Source Registry: {selected.source_registry}")
    if selected.source_url:
        print(f"- Source URL: {selected.source_url}")
    print(f"- Last Synced At: {selected.synced_at or 'N/A'}")
    if full:
        print(f"- Tenant Slug: {selected.tenant_slug}")

    return 0


def inspect_update_target(
    target_arg: str,
    metadata_key: str,
    new_value_raw: str,
    *,
    skip_warnings: bool = False,
    json_output: bool = False,
) -> int:
    target = Path(target_arg)
    if not target.exists():
        print(f"Error: Inspect target '{target}' does not exist.", file=sys.stderr)
        return 1
    if target.is_file():
        print("Error: --update only supports agent directories, not archive files.", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"Error: Inspect target '{target}' is not a directory.", file=sys.stderr)
        return 1

    manifest_path = target / "kinnoo.yaml"
    if not manifest_path.exists():
        _print_missing_manifest_guidance()
        return 1

    manifest_data = _load_manifest_from_directory(manifest_path)
    if manifest_data is None:
        return 1

    metadata_key = metadata_key.strip()
    if not metadata_key or any(not segment for segment in metadata_key.split(".")):
        print("Error: metadata key must be a valid dotted path (for example runtime.language).", file=sys.stderr)
        return 1

    if (
        metadata_key not in KNOWN_MANIFEST_METADATA_FIELD_SET
        and not _manifest_path_exists(manifest_data, metadata_key)
    ):
        print(
            f"Error: Unsupported metadata key '{metadata_key}'. Use a known manifest field.",
            file=sys.stderr,
        )
        return 1

    old_value = _manifest_get_path(manifest_data, metadata_key)
    parsed_new_value = _parse_update_value(new_value_raw)

    if not skip_warnings:
        old_value_label = _render_raw_value(old_value) if old_value is not None else "N/A"
        new_value_label = _render_raw_value(parsed_new_value)
        prompt = (
            f"Changing {metadata_key} from {old_value_label} to {new_value_label}. Proceed? (y/N): "
        )
        try:
            response = input(prompt)
        except EOFError:
            response = ""
        if response.strip().lower() not in {"y", "yes"}:
            if json_output:
                payload = {
                    "updated": False,
                    "aborted": True,
                    "target": str(target),
                    "key": metadata_key,
                    "old_value": _render_raw_value(old_value) if old_value is not None else "N/A",
                    "new_value": _render_raw_value(parsed_new_value),
                    "error": "Update aborted.",
                }
                print(json.dumps(payload, sort_keys=True))
            else:
                print("Update aborted.")
            return 1

    updated_manifest = deepcopy(manifest_data)
    _manifest_set_path(updated_manifest, metadata_key, parsed_new_value)

    is_valid, errors = validate_manifest_data(updated_manifest, manifest_root=target)
    if not is_valid:
        _print_manifest_validation_errors(errors)
        print("No changes were written.", file=sys.stderr)
        return 1

    try:
        manifest_path.write_text(
            yaml.safe_dump(updated_manifest, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as error:
        print(f"Error: Failed writing '{manifest_path}': {error}", file=sys.stderr)
        return 1

    if json_output:
        payload = {
            "updated": True,
            "aborted": False,
            "target": str(target),
            "key": metadata_key,
            "old_value": _render_raw_value(old_value) if old_value is not None else "N/A",
            "new_value": _render_raw_value(parsed_new_value),
            "error": None,
        }
        print(json.dumps(payload, sort_keys=True))
    else:
        print("Manifest metadata updated.")
        print(f"- key: {metadata_key}")
        print(f"- old value: {_render_raw_value(old_value) if old_value is not None else 'N/A'}")
        print(f"- new value: {_render_raw_value(parsed_new_value)}")
    return 0
