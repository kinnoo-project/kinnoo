from __future__ import annotations
# ---------------------------------------------------------------------------
# Manifest normalization: inject defaults for missing fields
# ---------------------------------------------------------------------------
def normalize_manifest_defaults(manifest: dict) -> dict:
    """Inject defaults for dependencies, inputs, outputs, and assets fields."""
    m = dict(manifest)  # shallow copy
    if "dependencies" not in m:
        m["dependencies"] = []
    if "inputs" not in m:
        m["inputs"] = {"type": "string"}
    elif "type" not in m["inputs"]:
        m["inputs"]["type"] = "string"
    if "outputs" not in m:
        m["outputs"] = {"type": "string"}
    elif "type" not in m["outputs"]:
        m["outputs"]["type"] = "string"

    if "assets" in m and isinstance(m["assets"], dict):
        m["assets"] = dict(m["assets"])  # avoid mutating original nested object
        if "paths" not in m["assets"]:
            m["assets"]["paths"] = []
        if "bundle" not in m["assets"]:
            m["assets"]["bundle"] = True
        if "max_bundle_size_mb" not in m["assets"]:
            m["assets"]["max_bundle_size_mb"] = 100

    return m

# ---------------------------------------------------------------------------
# Normalize 'type' field in inputs/outputs to always be a list
# ---------------------------------------------------------------------------
def normalize_type_field(io_dict: dict) -> None:
    """Normalize the 'type' field in an IO dict to always be a list."""
    t = io_dict.get('type')
    if isinstance(t, str):
        io_dict['type'] = [t]
    elif isinstance(t, list):
        io_dict['type'] = t
    # else: leave as-is (should not happen if defaults are injected)


def normalize_env_vars(env_vars: object) -> list[str]:
    """Normalize env_vars to a deterministic list of unique non-empty names.

    This helper is runtime-oriented and intentionally defensive. Validator-level
    type checks still own strict schema enforcement.
    """
    if not isinstance(env_vars, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for value in env_vars:
        if not isinstance(value, str):
            continue
        name = value.strip()
        if not name or name in seen:
            continue
        normalized.append(name)
        seen.add(name)
    return normalized
"""Schema constants for kinnoo.yaml manifest validation.

Required fields and their expected Python types.  Nested fields use dot
notation (e.g., ``runtime.language``).
"""

# Fields that MUST be present in every kinnoo.yaml manifest.
# Dot-separated paths represent nested dicts (e.g. "runtime.language"
# means manifest["runtime"]["language"]).
REQUIRED_FIELDS: list[str] = [
    "name",
    "version",
    "runtime.language",
    "runtime.version",
    "runtime.type",
    "dependencies",
    "inputs.type",
    "outputs.type",
]

# Expected Python type for each required field.
# Values are the actual type objects used in isinstance() checks.
FIELD_TYPES: dict[str, type] = {
    "name": str,
    "version": str,
    "runtime.language": str,
    "runtime.version": str,
    "runtime.type": str,
    "dependencies": list,
    "inputs.type": list,
    "outputs.type": list,
}

# Supported runtime types in this version of kinnoo.
SUPPORTED_RUNTIME_TYPES: list[str] = ["one-shot", "mcp-server", "daemon"]

# Supported runtime languages in this version of kinnoo.
SUPPORTED_RUNTIME_LANGUAGES: list[str] = ["python", "nodejs", "javascript", "typescript", "go"]

# Supported top-level manifest `type` values.
SUPPORTED_MANIFEST_TYPES: list[str] = ["agent", "openclaw-skill"]

# Supported manifest I/O contract type values.
# Keep both 'text' and 'string' for backward compatibility with existing
# manifests and default normalization behavior.
SUPPORTED_INPUT_TYPES: list[str] = ["text", "string", "file", "json"]
SUPPORTED_OUTPUT_TYPES: list[str] = ["text", "string", "file", "json"]

# Supported Node.js package managers for runtime.language == nodejs.
SUPPORTED_NODE_PACKAGE_MANAGERS: list[str] = ["npm", "pnpm"]

# Feature23 readiness probe method values for mcp-server runtime workflows.
SUPPORTED_READINESS_METHODS: list[str] = ["tcp", "stdout"]

# Feature24 service declaration types for optional manifest services entries.
SUPPORTED_SERVICE_TYPES: list[str] = [
    "mcp-server",
    "vector-db",
    "database",
    "api",
    "local-process",
    # Backward-compatible aliases accepted by validator.
    "postgres",
    "redis",
    "http-api",
    "process",
]

# Backward-compatibility aliases mapped to canonical feature24 taxonomy.
SERVICE_TYPE_ALIASES: dict[str, str] = {
    "postgres": "database",
    "redis": "database",
    "http-api": "api",
    "process": "local-process",
}

# Feature24 health-check method values for service declarations.
SUPPORTED_HEALTH_CHECK_METHODS: list[str] = ["tcp", "http", "process"]

# Feature26 manifest permissions keys for runtime.type == mcp-server.
MCP_SERVER_PERMISSION_KEYS: list[str] = [
    "read_only",
    "allow_write",
    "allow_create",
    "allowed_paths",
]

MCP_SERVER_PERMISSION_BOOL_FIELDS: list[str] = [
    "read_only",
    "allow_write",
    "allow_create",
]

# Feature39 manifest permissions keys for explicit sandbox policy declarations.
PERMISSIONS_KEYS: list[str] = [
    "network",
    "filesystem_scope",
    "shell",
    "browser",
    "env_access",
]

PERMISSIONS_BOOL_FIELDS: list[str] = [
    "network",
    "shell",
    "browser",
]

SUPPORTED_FILESYSTEM_SCOPES: list[str] = [
    "none",
    "read-only",
    "workspace-write",
    "full",
]

# Feature25 default timeout values for runtime service health checks.
DEFAULT_HTTP_HEALTH_CHECK_TIMEOUT_SECONDS: float = 5.0
DEFAULT_TCP_HEALTH_CHECK_TIMEOUT_SECONDS: float = 3.0

# Optional V2 manifest metadata fields (feature9).
# These are intentionally optional and should not be included in REQUIRED_FIELDS.
OPTIONAL_FIELDS: list[str] = [
    "type",
    "description",
    "author",
    "license",
    "entrypoint",
    "entrypoints",
    "env_vars",
    "provenance",
    "provenance.source_registry",
    "provenance.source_slug",
    "provenance.source_url",
    "provenance.source_version",
    "runtime.path",
    "runtime.run_command",
    "runtime.package_manager",
    "inputs.required",
    "model",
    "assets",
    "assets.paths",
    "assets.bundle",
    "assets.max_bundle_size_mb",
    "services",
    "permissions",
    "tests_file",
    "tests_version",
    "tests",
]

# Expected types for optional V2 fields when present.
# Enforced in a later validation phase to keep feature rollout scoped by task.
OPTIONAL_FIELD_TYPES: dict[str, object] = {
    "type": str,
    "description": str,
    "author": str,
    "license": str,
    "entrypoint": str,
    "entrypoints": list,
    "env_vars": list,
    "provenance": dict,
    "provenance.source_registry": str,
    "provenance.source_slug": str,
    "provenance.source_url": str,
    "provenance.source_version": str,
    "runtime.path": str,
    "runtime.run_command": str,
    "runtime.package_manager": str,
    "inputs.required": bool,
    "model": str,
    "assets": dict,
    "assets.paths": list,
    "assets.bundle": bool,
    "assets.max_bundle_size_mb": (int, float),
    "services": list,
    "permissions": dict,
    "tests_file": str,
    "tests_version": (int, str),
    "tests": list,
}

# Regex for a valid semver string: MAJOR.MINOR.PATCH with optional pre-release
# and build metadata (https://semver.org).
SEMVER_PATTERN: str = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# Valid package name: lowercase alphanumeric, starting with a letter or digit,
# hyphens and underscores allowed between characters.
NAME_PATTERN: str = r"^[a-z0-9][a-z0-9-_]*$"

# Feature72 lockfile schema version.
LOCKFILE_SCHEMA_VERSION: int = 1
