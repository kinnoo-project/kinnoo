from __future__ import annotations

import re
from pathlib import Path


EXPOSURE_PATTERNS: list[tuple[str, str]] = [
    (r"print\s*\(.*os\.environ", "print() with os.environ access"),
    (r"print\s*\(.*os\.getenv", "print() with os.getenv() access"),
    (r"log\w*\.\w+\(.*os\.environ", "logging with os.environ access"),
    (r"log\w*\.\w+\(.*os\.getenv", "logging with os.getenv() access"),
    (r"\.write\s*\(.*os\.environ", "file write with os.environ access"),
    (r"\.write\s*\(.*os\.getenv", "file write with os.getenv() access"),
]

SWEEP_FILE_EXTENSIONS = {".py", ".js", ".mjs", ".ts", ".json"}

CREDENTIAL_PATTERNS: list[tuple[str, str]] = [
    (r"AKIA[0-9A-Z]{16}", "credential-like pattern (AWS access key id)"),
    (r"ghp_[A-Za-z0-9]{36}", "credential-like pattern (GitHub personal access token)"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "credential-like pattern (GitHub fine-grained token)"),
    (r"sk-[A-Za-z0-9]{20,}", "credential-like pattern (API token prefix sk-)"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "credential-like pattern (Slack token)"),
    (
        r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        "credential-like pattern (hardcoded key/token assignment)",
    ),
]

RISKY_JS_PRIMITIVE_PATTERNS: list[tuple[str, str]] = [
    (r"\beval\s*\(", "risky js execution primitive (eval)"),
    (r"\bnew\s+Function\s*\(", "risky js execution primitive (Function constructor)"),
    (
        r"\b(?:child_process\.)?(?:exec|execSync|spawn|spawnSync|execFile|execFileSync)\s*\(",
        "risky js execution primitive (child process execution)",
    ),
]

JS_TS_SWEEP_EXTENSIONS = {".js", ".mjs", ".ts"}

OPENCLAW_CONFIG_DANGER_PATTERNS: list[tuple[str, str]] = [
    (
        r'"allow_?shell"\s*:\s*true',
        "dangerous openclaw config (allow_shell=true enables shell command execution)",
    ),
    (
        r'"disable_?sandbox"\s*:\s*true',
        "dangerous openclaw config (disable_sandbox=true removes runtime isolation)",
    ),
    (
        r'"allow_?unsafe_?eval"\s*:\s*true',
        "dangerous openclaw config (allow_unsafe_eval=true permits dynamic code execution)",
    ),
    (
        r'"auto_?approve(?:_actions)?"\s*:\s*true',
        "dangerous openclaw config (auto_approve=true bypasses approval gates)",
    ),
    (
        r'"network_access"\s*:\s*"unrestricted"',
        "dangerous openclaw config (network_access=unrestricted broadens outbound access)",
    ),
    (
        r'"tool_policy"\s*:\s*"allow_all"',
        "dangerous openclaw config (tool_policy=allow_all disables tool restrictions)",
    ),
]


def _looks_like_openclaw_config_candidate(source_file: Path, text_preview: str) -> bool:
    name_marker = "openclaw" in source_file.name.lower()
    body_marker = '"openclaw"' in text_preview.lower()
    return name_marker or body_marker

ASSET_FILENAME_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\.env($|\.)", re.IGNORECASE), "secret-like filename (.env)"),
    (re.compile(r"\.pem$", re.IGNORECASE), "secret-like filename (.pem)"),
    (re.compile(r"\.key$", re.IGNORECASE), "secret-like filename (.key)"),
    (re.compile(r"\.p12$", re.IGNORECASE), "secret-like filename (*.p12)"),
    (re.compile(r"\.pfx$", re.IGNORECASE), "secret-like filename (*.pfx)"),
    (re.compile(r"^id_rsa(\.pub)?$", re.IGNORECASE), "secret-like filename (id_rsa)"),
    (re.compile(r"credentials?", re.IGNORECASE), "secret-like filename (credential marker)"),
]

ASSET_TEXT_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "credential-like text pattern (AWS access key)",
    ),
    (
        re.compile(r"aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{16,}", re.IGNORECASE),
        "credential-like text pattern (AWS secret key assignment)",
    ),
    (
        re.compile(r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
        "credential-like text pattern (API key assignment)",
    ),
    (
        re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|PRIVATE) KEY-----"),
        "credential-like text pattern (private key block)",
    ),
]

DEFAULT_ASSET_TEXT_SCAN_MAX_BYTES = 128 * 1024


def sweep_env_var_exposure(agent_dir: Path, declared_env_vars: list[str]) -> list[str]:
    """Heuristically scan for potential env-var exposure patterns in Python source files.

    Returns warnings formatted as "<file>:<line>: <description>".
    """
    del declared_env_vars

    warnings: list[str] = []
    if not agent_dir.exists() or not agent_dir.is_dir():
        return warnings

    compiled_patterns = [
        (re.compile(pattern, re.IGNORECASE), description)
        for pattern, description in EXPOSURE_PATTERNS
    ]
    compiled_credential_patterns = [
        (re.compile(pattern, re.IGNORECASE), description)
        for pattern, description in CREDENTIAL_PATTERNS
    ]
    compiled_risky_js_patterns = [
        (re.compile(pattern), description)
        for pattern, description in RISKY_JS_PRIMITIVE_PATTERNS
    ]
    compiled_openclaw_danger_patterns = [
        (re.compile(pattern, re.IGNORECASE), description)
        for pattern, description in OPENCLAW_CONFIG_DANGER_PATTERNS
    ]

    for source_file in sorted(agent_dir.rglob("*")):
        if not source_file.is_file():
            continue
        if ".venv" in source_file.parts:
            continue
        if source_file.suffix.lower() not in SWEEP_FILE_EXTENSIONS:
            continue

        try:
            lines = source_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        text_preview = "\n".join(lines[:120])
        is_openclaw_config_candidate = (
            source_file.suffix.lower() == ".json"
            and _looks_like_openclaw_config_candidate(source_file, text_preview)
        )

        relative_path = source_file.relative_to(agent_dir)
        for line_number, line_text in enumerate(lines, start=1):
            for compiled_pattern, description in compiled_patterns:
                if compiled_pattern.search(line_text):
                    warnings.append(f"{relative_path}:{line_number}: {description}")
                    break
            for compiled_pattern, description in compiled_credential_patterns:
                if compiled_pattern.search(line_text):
                    warning_text = f"{relative_path}:{line_number}: {description}"
                    if warning_text not in warnings:
                        warnings.append(warning_text)
                    break

            # Restrict risky execution checks to JS/TS source files to avoid
            # cross-language false positives from unrelated syntax.
            if source_file.suffix.lower() in JS_TS_SWEEP_EXTENSIONS:
                for compiled_pattern, description in compiled_risky_js_patterns:
                    if compiled_pattern.search(line_text):
                        warning_text = f"{relative_path}:{line_number}: {description}"
                        if warning_text not in warnings:
                            warnings.append(warning_text)
                        break

            if is_openclaw_config_candidate:
                for compiled_pattern, description in compiled_openclaw_danger_patterns:
                    if compiled_pattern.search(line_text):
                        warning_text = f"{relative_path}:{line_number}: {description}"
                        if warning_text not in warnings:
                            warnings.append(warning_text)
                        break

    return warnings


def _looks_binary(content: bytes) -> bool:
    return b"\x00" in content


def sweep_asset_credential_risks(
    agent_dir: Path,
    asset_file_paths: list[Path],
    max_text_scan_bytes: int = DEFAULT_ASSET_TEXT_SCAN_MAX_BYTES,
) -> list[str]:
    """Heuristically scan bundled asset files for credential-like risks.

    Returns warning strings. Scan is warning-only and never blocking.
    """
    warnings: list[str] = []

    for asset_file in sorted(asset_file_paths):
        if not asset_file.exists() or not asset_file.is_file():
            continue

        try:
            relative_path = asset_file.relative_to(agent_dir).as_posix()
        except ValueError:
            # Defensive fallback; caller should already pass in-agent files.
            relative_path = asset_file.name

        basename = asset_file.name
        for pattern, description in ASSET_FILENAME_PATTERNS:
            if pattern.search(basename):
                warnings.append(f"{relative_path}: {description}")

        try:
            raw_content = asset_file.read_bytes()
        except OSError:
            continue

        if _looks_binary(raw_content):
            warnings.append(
                f"{relative_path}: skipped binary file for text credential scan"
            )
            continue

        text_window = raw_content[:max_text_scan_bytes]
        try:
            text_content = text_window.decode("utf-8")
        except UnicodeDecodeError:
            warnings.append(
                f"{relative_path}: skipped binary file for text credential scan"
            )
            continue

        for pattern, description in ASSET_TEXT_SECRET_PATTERNS:
            if pattern.search(text_content):
                warnings.append(f"{relative_path}: {description}")

    return warnings


def sweep_memory_snapshot_credential_risks(
    agent_dir: Path,
    snapshot_candidate_paths: list[Path],
    max_text_scan_bytes: int = DEFAULT_ASSET_TEXT_SCAN_MAX_BYTES,
) -> list[str]:
    """Scan state snapshot candidates for credential-like patterns.

    The scan is warning-only and reuses the same safe reporting contract used
    for asset credential warnings to avoid leaking raw secret values.
    """
    return sweep_asset_credential_risks(
        agent_dir=agent_dir,
        asset_file_paths=snapshot_candidate_paths,
        max_text_scan_bytes=max_text_scan_bytes,
    )
