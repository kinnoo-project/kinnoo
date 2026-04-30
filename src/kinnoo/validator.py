"""kinnoo manifest validator.

Public API
----------
validate(manifest_path: str) -> tuple[bool, list[str]]
    Parse *manifest_path* as a kinnoo.yaml file and return a 2-tuple:

    * ``is_valid`` (bool) – True when the manifest passes all checks.
    * ``errors`` (list[str]) – Human-readable error messages; empty when
      is_valid is True.

Usage::

    is_valid, errors = validate("path/to/kinnoo.yaml")
    if not is_valid:
        for msg in errors:
            print(msg)
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    FIELD_TYPES,
    MCP_SERVER_PERMISSION_BOOL_FIELDS,
    MCP_SERVER_PERMISSION_KEYS,
    NAME_PATTERN,
    OPTIONAL_FIELD_TYPES,
    PERMISSIONS_BOOL_FIELDS,
    PERMISSIONS_KEYS,
    REQUIRED_FIELDS,
    SERVICE_TYPE_ALIASES,
    SEMVER_PATTERN,
    SUPPORTED_FILESYSTEM_SCOPES,
    SUPPORTED_HEALTH_CHECK_METHODS,
    SUPPORTED_INPUT_TYPES,
    SUPPORTED_NODE_PACKAGE_MANAGERS,
    SUPPORTED_MANIFEST_TYPES,
    SUPPORTED_OUTPUT_TYPES,
    SUPPORTED_RUNTIME_LANGUAGES,
    SUPPORTED_RUNTIME_TYPES,
    SUPPORTED_SERVICE_TYPES,
)

from .schema import normalize_manifest_defaults, normalize_type_field
from .test_command import validate_kinnoo_tests_document

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_types(manifest: dict) -> dict:
    """Normalize 'type' fields in inputs/outputs to always be lists."""
    m = dict(manifest)
    if 'inputs' in m and isinstance(m['inputs'], dict):
        normalize_type_field(m['inputs'])
    if 'outputs' in m and isinstance(m['outputs'], dict):
        normalize_type_field(m['outputs'])
    return m

def _get_nested(data: dict[str, Any], dotted_key: str) -> tuple[bool, Any]:
    """Retrieve a value from a nested dict using a dot-separated key path.

    Returns:
        (found, value) — found is False when any segment is missing.
    """
    parts = dotted_key.split(".")
    node: Any = data
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _collect_services_shape_errors(data: dict[str, Any]) -> list[str]:
    """Validate optional services structure and nested value types.

    Task146 scope is schema-shape support only. Required-field checks, enum
    validation, and duplicate-name validation are implemented in task147.
    """
    errors: list[str] = []
    found, services = _get_nested(data, "services")
    if not found:
        return errors

    if not isinstance(services, list):
        return errors

    seen_service_names: set[str] = set()
    duplicate_service_names: set[str] = set()

    for index, service in enumerate(services):
        if not isinstance(service, dict):
            actual = type(service).__name__
            errors.append(
                f"Field 'services[{index}]' must be of type dict, got {actual}."
            )
            continue

        if "name" not in service:
            errors.append(f"Missing required field: 'services[{index}].name'")
        if "type" not in service:
            errors.append(f"Missing required field: 'services[{index}].type'")

        service_name = service.get("name")
        if service_name is not None and not isinstance(service_name, str):
            actual = type(service_name).__name__
            errors.append(
                f"Field 'services[{index}].name' must be of type str, got {actual}."
            )
        elif isinstance(service_name, str):
            if service_name in seen_service_names:
                duplicate_service_names.add(service_name)
            else:
                seen_service_names.add(service_name)

        service_type = service.get("type")
        if service_type is not None and not isinstance(service_type, str):
            actual = type(service_type).__name__
            errors.append(
                f"Field 'services[{index}].type' must be of type str, got {actual}."
            )
        elif isinstance(service_type, str) and service_type not in SUPPORTED_SERVICE_TYPES:
            supported = ", ".join(f"'{value}'" for value in SUPPORTED_SERVICE_TYPES)
            errors.append(
                f"Field 'services[{index}].type' has unsupported value: '{service_type}'. "
                f"Allowed values: {supported}."
            )
        elif isinstance(service_type, str):
            # Canonicalization keeps semantic equivalence explicit for alias values.
            service_type = SERVICE_TYPE_ALIASES.get(service_type, service_type)

        health_check = service.get("health_check")
        if health_check is None:
            continue

        if not isinstance(health_check, dict):
            actual = type(health_check).__name__
            errors.append(
                f"Field 'services[{index}].health_check' must be of type dict, got {actual}."
            )
            continue

        if "method" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.method' when health_check is declared."
            )
            continue

        method = health_check.get("method")
        if method is not None and not isinstance(method, str):
            actual = type(method).__name__
            errors.append(
                f"Field 'services[{index}].health_check.method' must be of type str, got {actual}."
            )
        elif isinstance(method, str) and method not in SUPPORTED_HEALTH_CHECK_METHODS:
            supported = ", ".join(
                f"'{value}'" for value in SUPPORTED_HEALTH_CHECK_METHODS
            )
            errors.append(
                f"Field 'services[{index}].health_check.method' has unsupported value: '{method}'. "
                f"Allowed values: {supported}."
            )

        url = health_check.get("url")
        if url is not None and not isinstance(url, str):
            actual = type(url).__name__
            errors.append(
                f"Field 'services[{index}].health_check.url' must be of type str, got {actual}."
            )

        process_name = health_check.get("process_name")
        if process_name is not None and not isinstance(process_name, str):
            actual = type(process_name).__name__
            errors.append(
                f"Field 'services[{index}].health_check.process_name' must be of type str, got {actual}."
            )

        port = health_check.get("port")
        if port is not None and (isinstance(port, bool) or not isinstance(port, int)):
            actual = type(port).__name__
            errors.append(
                f"Field 'services[{index}].health_check.port' must be of type int, got {actual}."
            )

        if method == "tcp" and "port" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.port' when method is 'tcp'."
            )
        if method == "http" and "url" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.url' when method is 'http'."
            )
        if method == "process" and "process_name" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.process_name' when method is 'process'."
            )

    # Emit deterministic duplicate errors by sorting names.
    for duplicate_name in sorted(duplicate_service_names):
        errors.append(f"Duplicate service name not allowed: '{duplicate_name}'.")

    return errors


def _collect_mcp_server_permissions_errors(data: dict[str, Any]) -> list[str]:
    """Validate optional permissions payload for legacy and feature39 contracts."""
    errors: list[str] = []

    runtime_found, runtime_type = _get_nested(data, "runtime.type")
    if not runtime_found:
        return errors

    permissions_found, permissions = _get_nested(data, "permissions")
    if not permissions_found:
        return errors

    # Feature26 backward compatibility: non-mcp-server manifests historically
    # ignored non-dict permissions payloads.
    if runtime_type != "mcp-server" and not isinstance(permissions, dict):
        return errors

    if not isinstance(permissions, dict):
        actual = type(permissions).__name__
        errors.append(
            f"Field 'permissions' must be of type dict, got {actual}."
        )
        return errors

    feature39_keys = set(PERMISSIONS_KEYS)
    has_feature39_keys = any(key in feature39_keys for key in permissions)

    # Feature39 explicit permissions contract.
    if has_feature39_keys or runtime_type != "mcp-server":
        allowed_keys = feature39_keys
        allowed_keys_display = ", ".join(f"'{key}'" for key in PERMISSIONS_KEYS)

        for key in sorted(permissions.keys()):
            if key not in allowed_keys:
                errors.append(
                    f"Field 'permissions' contains unsupported key: '{key}'. "
                    f"Allowed keys: {allowed_keys_display}."
                )

        for field_name in PERMISSIONS_BOOL_FIELDS:
            if field_name not in permissions:
                continue
            value = permissions[field_name]
            if not isinstance(value, bool):
                actual = type(value).__name__
                errors.append(
                    f"Field 'permissions.{field_name}' must be of type bool, got {actual}."
                )

        if "filesystem_scope" in permissions:
            filesystem_scope = permissions["filesystem_scope"]
            if not isinstance(filesystem_scope, str):
                actual = type(filesystem_scope).__name__
                errors.append(
                    f"Field 'permissions.filesystem_scope' must be of type str, got {actual}."
                )
            elif filesystem_scope not in SUPPORTED_FILESYSTEM_SCOPES:
                supported_scopes = ", ".join(
                    f"'{scope}'" for scope in SUPPORTED_FILESYSTEM_SCOPES
                )
                errors.append(
                    "Field 'permissions.filesystem_scope' has unsupported value: "
                    f"'{filesystem_scope}'. Supported values: {supported_scopes}."
                )

        if "env_access" in permissions:
            env_access = permissions["env_access"]
            if not isinstance(env_access, list):
                actual = type(env_access).__name__
                errors.append(
                    f"Field 'permissions.env_access' must be of type list, got {actual}."
                )
            else:
                for index, env_var_name in enumerate(env_access):
                    if not isinstance(env_var_name, str):
                        actual = type(env_var_name).__name__
                        errors.append(
                            f"Field 'permissions.env_access[{index}]' must be of type str, got {actual}."
                        )
                        continue
                    if env_var_name.strip() == "":
                        errors.append(
                            f"Field 'permissions.env_access[{index}]' must be a non-empty string."
                        )

        return errors

    # Feature26 legacy mcp-server permissions schema contract.
    allowed_keys = set(MCP_SERVER_PERMISSION_KEYS)
    allowed_keys_display = ", ".join(f"'{key}'" for key in MCP_SERVER_PERMISSION_KEYS)

    for key in sorted(permissions.keys()):
        if key not in allowed_keys:
            errors.append(
                f"Field 'permissions' contains unsupported key: '{key}'. "
                f"Allowed keys: {allowed_keys_display}."
            )

    for field_name in MCP_SERVER_PERMISSION_BOOL_FIELDS:
        if field_name not in permissions:
            continue
        value = permissions[field_name]
        if not isinstance(value, bool):
            actual = type(value).__name__
            errors.append(
                f"Field 'permissions.{field_name}' must be of type bool, got {actual}."
            )

    if "allowed_paths" in permissions:
        allowed_paths = permissions["allowed_paths"]
        if not isinstance(allowed_paths, list):
            actual = type(allowed_paths).__name__
            errors.append(
                f"Field 'permissions.allowed_paths' must be of type list, got {actual}."
            )
        else:
            for index, value in enumerate(allowed_paths):
                if not isinstance(value, str):
                    actual = type(value).__name__
                    errors.append(
                        f"Field 'permissions.allowed_paths[{index}]' must be of type str, got {actual}."
                    )

    return errors


def _collect_io_type_errors(data: dict[str, Any]) -> list[str]:
    """Validate manifest input/output contract type values."""
    errors: list[str] = []

    io_field_specs: tuple[tuple[str, list[str]], ...] = (
        ("inputs.type", SUPPORTED_INPUT_TYPES),
        ("outputs.type", SUPPORTED_OUTPUT_TYPES),
    )

    for field_name, allowed_values in io_field_specs:
        found, value = _get_nested(data, field_name)
        if not found or not isinstance(value, list):
            continue

        for index, declared_type in enumerate(value):
            if not isinstance(declared_type, str):
                actual = type(declared_type).__name__
                errors.append(
                    f"Field '{field_name}[{index}]' must be of type str, got {actual}."
                )
                continue

            if declared_type not in allowed_values:
                allowed = ", ".join(f"'{item}'" for item in allowed_values)
                errors.append(
                    f"Field '{field_name}' has unsupported value: '{declared_type}'. "
                    f"Supported values: {allowed}."
                )

    return errors


def resolve_entrypoint_selection(
    manifest_data: dict[str, Any],
    *,
    requested_entrypoint: str | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Resolve effective entrypoint selection for legacy and multi-entrypoint manifests.

    Returns:
        (selection, errors) where selection contains:
            - contract_mode: "entrypoint" | "entrypoints"
            - declared_entrypoints: list[str]
            - selected_entrypoint: str
            - selection_source: "default" | "flag"
    """
    errors: list[str] = []

    entrypoint_value = manifest_data.get("entrypoint")
    entrypoints_value = manifest_data.get("entrypoints")

    has_entrypoint = "entrypoint" in manifest_data
    has_entrypoints = "entrypoints" in manifest_data

    if has_entrypoint and has_entrypoints:
        errors.append("Fields 'entrypoint' and 'entrypoints' are mutually exclusive.")
        return None, errors

    declared_entrypoints: list[str] = []
    contract_mode = "entrypoint"

    if has_entrypoint:
        if not isinstance(entrypoint_value, str):
            actual = type(entrypoint_value).__name__
            errors.append(
                f"Field 'entrypoint' must be of type str, got {actual}."
            )
        elif entrypoint_value.strip() == "":
            errors.append("Field 'entrypoint' must be a non-empty string.")
        else:
            declared_entrypoints = [entrypoint_value.strip()]
            contract_mode = "entrypoint"
    elif has_entrypoints:
        contract_mode = "entrypoints"
        if not isinstance(entrypoints_value, list):
            actual = type(entrypoints_value).__name__
            errors.append(
                f"Field 'entrypoints' must be of type list, got {actual}."
            )
        else:
            if len(entrypoints_value) == 0:
                errors.append("Field 'entrypoints' must be a non-empty list.")
            for index, raw_item in enumerate(entrypoints_value):
                if not isinstance(raw_item, str):
                    actual = type(raw_item).__name__
                    errors.append(
                        f"Field 'entrypoints[{index}]' must be of type str, got {actual}."
                    )
                    continue
                item = raw_item.strip()
                if item == "":
                    errors.append(
                        f"Field 'entrypoints[{index}]' must be a non-empty string."
                    )
                    continue
                declared_entrypoints.append(item)
    else:
        errors.append("Missing required field: 'entrypoint' (or provide 'entrypoints').")
        return None, errors

    if errors:
        return None, errors

    selected_entrypoint = declared_entrypoints[0]
    selection_source = "default"
    if requested_entrypoint is not None:
        normalized_requested = requested_entrypoint.strip()
        if normalized_requested == "":
            errors.append("Flag '--entrypoint' requires a non-empty value.")
            return None, errors

        if contract_mode == "entrypoint":
            if normalized_requested != declared_entrypoints[0]:
                errors.append(
                    "Flag '--entrypoint' does not match manifest 'entrypoint'. "
                    f"Expected '{declared_entrypoints[0]}', got '{normalized_requested}'."
                )
                return None, errors
        else:
            if normalized_requested not in declared_entrypoints:
                allowed = ", ".join(f"'{value}'" for value in declared_entrypoints)
                errors.append(
                    "Flag '--entrypoint' is not declared in manifest 'entrypoints'. "
                    f"Allowed values: {allowed}."
                )
                return None, errors

        selected_entrypoint = normalized_requested
        selection_source = "flag"

    return {
        "contract_mode": contract_mode,
        "declared_entrypoints": declared_entrypoints,
        "selected_entrypoint": selected_entrypoint,
        "selection_source": selection_source,
    }, errors


def collect_entrypoint_path_errors(
    manifest_data: dict[str, Any],
    *,
    manifest_root: Path,
) -> list[str]:
    """Validate that declared entrypoint paths exist under the manifest root directory."""
    selection, selection_errors = resolve_entrypoint_selection(manifest_data)
    if selection is None:
        return list(selection_errors)

    errors: list[str] = []
    for entrypoint_value in selection["declared_entrypoints"]:
        entrypoint_path = (manifest_root / entrypoint_value).resolve(strict=False)
        if not entrypoint_path.exists() or not entrypoint_path.is_file():
            errors.append(
                f"Declared entrypoint path not found: '{entrypoint_value}'."
            )
    return errors


def _is_safe_relative_manifest_path(path_value: str) -> bool:
    """Return True when a manifest path is relative and traversal-safe."""
    candidate = PurePosixPath(path_value)
    return not candidate.is_absolute() and ".." not in candidate.parts


def _is_safe_relative_pattern(pattern_value: str) -> bool:
    """Return True when an exclude pattern is relative and traversal-safe.

    Exclude values may contain glob syntax, so this helper validates only the
    safety properties we rely on for snapshot policy handling.
    """
    normalized = pattern_value.strip()
    if normalized == "":
        return False
    if normalized.startswith("/"):
        return False

    candidate = PurePosixPath(normalized)
    return ".." not in candidate.parts


def _collect_disallowed_metadata_field_errors(data: dict[str, Any]) -> list[str]:
    """Reject metadata fields intentionally deferred from Phase 6 schema."""
    errors: list[str] = []

    for field_name in ("channels", "skills", "state_dirs"):
        found, _ = _get_nested(data, field_name)
        if found:
            errors.append(
                f"Field '{field_name}' is not supported in this schema version. Remove it from kinnoo.yaml."
            )

    return errors


def _collect_openclaw_skill_contract_errors(data: dict[str, Any]) -> list[str]:
    """Validate openclaw-skill type semantics and provenance contract."""
    errors: list[str] = []

    type_found, manifest_type = _get_nested(data, "type")
    if type_found and isinstance(manifest_type, str):
        if manifest_type not in SUPPORTED_MANIFEST_TYPES:
            supported = ", ".join(f"'{value}'" for value in SUPPORTED_MANIFEST_TYPES)
            errors.append(
                f"Field 'type' has unsupported value: '{manifest_type}'. Supported values: {supported}."
            )

    if not (type_found and manifest_type == "openclaw-skill"):
        # provenance object is still validated if present, even for non-openclaw-skill manifests.
        pass
    else:
        framework_found, framework_value = _get_nested(data, "framework")
        if framework_found and isinstance(framework_value, str) and framework_value != "openclaw":
            errors.append(
                "Field 'framework' must be 'openclaw' when type is 'openclaw-skill'."
            )

        runtime_language_found, runtime_language_value = _get_nested(data, "runtime.language")
        if runtime_language_found and runtime_language_value != "nodejs":
            errors.append(
                "Field 'runtime.language' must be 'nodejs' when type is 'openclaw-skill'."
            )

        runtime_type_found, runtime_type_value = _get_nested(data, "runtime.type")
        if runtime_type_found and runtime_type_value != "daemon":
            errors.append(
                "Field 'runtime.type' must be 'daemon' when type is 'openclaw-skill'."
            )

    provenance_found, provenance_value = _get_nested(data, "provenance")
    if not provenance_found:
        return errors

    if not isinstance(provenance_value, dict):
        return errors

    source_registry = provenance_value.get("source_registry")
    source_version = provenance_value.get("source_version")
    source_slug = provenance_value.get("source_slug")
    source_url = provenance_value.get("source_url")

    if not isinstance(source_registry, str) or not source_registry.strip():
        errors.append(
            "Field 'provenance.source_registry' is required when provenance is declared and must be a non-empty string."
        )

    if not isinstance(source_version, str) or not source_version.strip():
        errors.append(
            "Field 'provenance.source_version' is required when provenance is declared and must be a non-empty string."
        )

    has_source_slug = isinstance(source_slug, str) and source_slug.strip() != ""
    has_source_url = isinstance(source_url, str) and source_url.strip() != ""
    if not has_source_slug and not has_source_url:
        errors.append(
            "Field 'provenance' must include at least one of 'source_slug' or 'source_url'."
        )

    return errors


def _collect_openclaw_framework_errors(data: dict[str, Any]) -> list[str]:
    """Validate framework-specific rules for manifests declaring framework=openclaw."""
    errors: list[str] = []

    framework_found, framework_value = _get_nested(data, "framework")
    if not framework_found or not isinstance(framework_value, str):
        return errors
    if framework_value != "openclaw":
        return errors

    runtime_language_found, runtime_language_value = _get_nested(data, "runtime.language")
    if runtime_language_found and runtime_language_value != "nodejs":
        errors.append(
            "Field 'runtime.language' must be 'nodejs' when framework is 'openclaw'."
        )

    runtime_type_found, runtime_type_value = _get_nested(data, "runtime.type")
    if runtime_type_found and runtime_type_value != "daemon":
        errors.append(
            "Field 'runtime.type' must be 'daemon' when framework is 'openclaw'."
        )

    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _collect_validation_errors(
    data: dict[str, Any],
    *,
    manifest_root: Path | None = None,
) -> list[str]:
    """Collect schema/type/semantic validation errors for a manifest mapping."""
    errors: list[str] = []

    # Inject defaults for dependencies, inputs, outputs if missing
    data = normalize_manifest_defaults(data)
    # Normalize type fields in inputs/outputs to always be lists
    data = _normalize_types(data)

    entrypoint_selection, entrypoint_selection_errors = resolve_entrypoint_selection(data)
    errors.extend(entrypoint_selection_errors)

    # ------------------------------------------------------------------
    # 2. Required fields — presence check
    # ------------------------------------------------------------------
    for field in REQUIRED_FIELDS:
        found, _ = _get_nested(data, field)
        if not found:
            errors.append(f"Missing required field: '{field}'")

    # ------------------------------------------------------------------
    # 3. Type checks (only where the field is present)
    # ------------------------------------------------------------------
    for field, expected_type in FIELD_TYPES.items():
        found, value = _get_nested(data, field)
        if not found:
            continue  # already reported as missing above
        if not isinstance(value, expected_type):
            actual = type(value).__name__
            expected = expected_type.__name__
            errors.append(
                f"Field '{field}' must be of type {expected}, "
                f"got {actual}."
            )

    # ------------------------------------------------------------------
    # 4. Semantic validations (only when the field is present + correct type)
    # ------------------------------------------------------------------
    if manifest_root is not None and entrypoint_selection is not None:
        errors.extend(
            collect_entrypoint_path_errors(
                data,
                manifest_root=manifest_root,
            )
        )

    # 4a. version — must be valid semver
    version_found, version_value = _get_nested(data, "version")
    if version_found and isinstance(version_value, str):
        if not re.fullmatch(SEMVER_PATTERN, version_value):
            errors.append(
                f"Field 'version' has an invalid semver value: '{version_value}'. "
                "Expected format: MAJOR.MINOR.PATCH (e.g., '1.2.3')."
            )

    # 4b. name — must match package name pattern
    name_found, name_value = _get_nested(data, "name")
    if name_found and isinstance(name_value, str):
        if not re.fullmatch(NAME_PATTERN, name_value):
            errors.append(
                f"Field 'name' has an invalid value: '{name_value}'. "
                "Only lowercase alphanumeric characters, hyphens, and underscores are allowed, "
                "and it must start with a letter or digit."
            )

    # 4c. runtime.type — must be "one-shot"
    rt_found, rt_value = _get_nested(data, "runtime.type")
    if rt_found and isinstance(rt_value, str):
        if rt_value not in SUPPORTED_RUNTIME_TYPES:
            supported = ", ".join(f"'{v}'" for v in SUPPORTED_RUNTIME_TYPES)
            errors.append(
                f"Field 'runtime.type' has unsupported value: '{rt_value}'. "
                f"Only {supported} is supported in this version of kinnoo."
            )

    # 4d. runtime.language — must be a supported runtime language
    runtime_language_found, runtime_language_value = _get_nested(data, "runtime.language")
    if runtime_language_found and isinstance(runtime_language_value, str):
        if runtime_language_value not in SUPPORTED_RUNTIME_LANGUAGES:
            supported = ", ".join(f"'{value}'" for value in SUPPORTED_RUNTIME_LANGUAGES)
            errors.append(
                f"Field 'runtime.language' has unsupported value: '{runtime_language_value}'. "
                f"Supported values: {supported}."
            )

    runtime_package_manager_found, runtime_package_manager_value = _get_nested(
        data, "runtime.package_manager"
    )
    if runtime_package_manager_found and isinstance(runtime_package_manager_value, str):
        if runtime_package_manager_value not in SUPPORTED_NODE_PACKAGE_MANAGERS:
            supported = ", ".join(
                f"'{value}'" for value in SUPPORTED_NODE_PACKAGE_MANAGERS
            )
            errors.append(
                f"Field 'runtime.package_manager' has unsupported value: '{runtime_package_manager_value}'. "
                f"Supported values: {supported}."
            )

    # 4e. Optional V2 fields (feature9).
    # Validate optional metadata when present while preserving V1 compatibility.
    for optional_field, expected_type in OPTIONAL_FIELD_TYPES.items():
        if optional_field in {"entrypoint", "entrypoints"}:
            continue

        found, value = _get_nested(data, optional_field)
        if not found:
            continue

        # Feature26 backward compatibility: for non-mcp-server manifests,
        # legacy permissions payloads were ignored even when malformed.
        if optional_field == "permissions":
            runtime_found, runtime_type = _get_nested(data, "runtime.type")
            if runtime_found and runtime_type != "mcp-server" and not isinstance(value, dict):
                continue

        if not isinstance(value, expected_type):
            actual = type(value).__name__
            if isinstance(expected_type, tuple):
                expected = " or ".join(t.__name__ for t in expected_type)
            else:
                expected = expected_type.__name__
            errors.append(
                f"Field '{optional_field}' must be of type {expected}, "
                f"got {actual}."
            )
            continue

        if optional_field == "env_vars":
            for index, env_var in enumerate(value):
                if not isinstance(env_var, str):
                    actual = type(env_var).__name__
                    errors.append(
                        f"Field 'env_vars[{index}]' must be of type str, got {actual}."
                    )
                    continue
                if env_var.strip() == "":
                    errors.append(
                        f"Field 'env_vars[{index}]' must be a non-empty string."
                    )

        if optional_field == "model" and value.strip() == "":
            errors.append("Field 'model' must be a non-empty string.")

        if optional_field == "runtime.path" and value.strip() == "":
            errors.append("Field 'runtime.path' must be a non-empty string.")

        if optional_field == "assets.max_bundle_size_mb" and isinstance(value, bool):
            errors.append("Field 'assets.max_bundle_size_mb' must be of type int or float, got bool.")

        if optional_field == "assets.paths":
            for index, asset_path in enumerate(value):
                if not isinstance(asset_path, str):
                    actual = type(asset_path).__name__
                    errors.append(
                        f"Field 'assets.paths[{index}]' must be of type str, got {actual}."
                    )
                    continue
                if asset_path.strip() == "":
                    errors.append(
                        f"Field 'assets.paths[{index}]' must be a non-empty string."
                    )

    errors.extend(_collect_services_shape_errors(data))
    errors.extend(_collect_mcp_server_permissions_errors(data))
    errors.extend(_collect_io_type_errors(data))
    errors.extend(_collect_disallowed_metadata_field_errors(data))
    errors.extend(_collect_openclaw_skill_contract_errors(data))
    errors.extend(_collect_openclaw_framework_errors(data))

    tests_file_found, tests_file_value = _get_nested(data, "tests_file")
    if tests_file_found and isinstance(tests_file_value, str):
        if tests_file_value.strip() == "":
            errors.append("Field 'tests_file' must be a non-empty string.")

    tests_found, tests_value = _get_nested(data, "tests")
    if tests_found:
        tests_doc = {
            "version": data.get("tests_version", 1),
            "tests": tests_value,
        }
        errors.extend(validate_kinnoo_tests_document(tests_doc, prefix="kinnoo.yaml"))

    return errors


def validate_manifest_data(
    manifest_data: dict[str, Any],
    *,
    manifest_root: Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate an in-memory kinnoo manifest mapping.

    Parameters
    ----------
    manifest_data:
        Parsed manifest object expected to be a YAML top-level mapping.

    Returns
    -------
    tuple[bool, list[str]]
        ``(is_valid, errors)`` where *errors* is empty when valid.
    """
    if not isinstance(manifest_data, dict):
        return False, ["Manifest must be a YAML mapping (dict) at the top level."]

    errors = _collect_validation_errors(manifest_data, manifest_root=manifest_root)
    return len(errors) == 0, errors


def validate(manifest_path: str) -> tuple[bool, list[str]]:
    """Validate a kinnoo.yaml manifest file.

    Parameters
    ----------
    manifest_path:
        Filesystem path to the manifest file (``kinnoo.yaml``).

    Returns
    -------
    tuple[bool, list[str]]
        ``(is_valid, errors)`` where *errors* is an empty list when
        *is_valid* is ``True``.
    """
    path = Path(manifest_path)

    # ------------------------------------------------------------------
    # 1. File existence and YAML parse
    # ------------------------------------------------------------------
    if not path.exists():
        return False, [f"Manifest file not found: {manifest_path}"]

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return False, [f"YAML parse error: {exc}"]

    if not isinstance(data, dict):
        return False, ["Manifest must be a YAML mapping (dict) at the top level."]

    errors = _collect_validation_errors(data, manifest_root=path.parent)
    return len(errors) == 0, errors
