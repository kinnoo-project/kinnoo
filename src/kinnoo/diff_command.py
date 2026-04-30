from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

try:
    from kinnoo.inspect_command import read_manifest_from_kno_archive
except ImportError:
    from .inspect_command import read_manifest_from_kno_archive


def _read_archive_files(archive_path: Path) -> dict[str, bytes] | None:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            archive_files: dict[str, bytes] = {}
            for member in archive_zip.infolist():
                if member.is_dir():
                    continue
                normalized_name = str(Path(member.filename).as_posix())
                archive_files[normalized_name] = archive_zip.read(member)
            return archive_files
    except zipfile.BadZipFile:
        print(f"Error: Archive '{archive_path}' is not a valid zip-based .kno file.", file=sys.stderr)
        return None
    except OSError as error:
        print(f"Error: Failed reading archive '{archive_path}': {error}", file=sys.stderr)
        return None


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            continue
        candidate = entry.strip()
        if candidate:
            items.append(candidate)
    return sorted(set(items))


def _manifest_change_lines(
    manifest_a: dict[str, object],
    manifest_b: dict[str, object],
) -> list[str]:
    lines: list[str] = []

    dependencies_a = _normalize_string_list(manifest_a.get("dependencies"))
    dependencies_b = _normalize_string_list(manifest_b.get("dependencies"))
    dependencies_added = [item for item in dependencies_b if item not in dependencies_a]
    dependencies_removed = [item for item in dependencies_a if item not in dependencies_b]
    if dependencies_added or dependencies_removed:
        lines.append(
            "dependencies: "
            f"added={dependencies_added} removed={dependencies_removed}"
        )

    env_vars_a = _normalize_string_list(manifest_a.get("env_vars"))
    env_vars_b = _normalize_string_list(manifest_b.get("env_vars"))
    env_vars_added = [item for item in env_vars_b if item not in env_vars_a]
    env_vars_removed = [item for item in env_vars_a if item not in env_vars_b]
    if env_vars_added or env_vars_removed:
        lines.append(
            "env_vars: "
            f"added={env_vars_added} removed={env_vars_removed}"
        )

    permissions_a = manifest_a.get("permissions")
    permissions_b = manifest_b.get("permissions")
    if permissions_a != permissions_b:
        lines.append(
            "permissions: "
            f"from={json.dumps(permissions_a, sort_keys=True)} "
            f"to={json.dumps(permissions_b, sort_keys=True)}"
        )

    return lines


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_change_sets(
    files_a: dict[str, bytes],
    files_b: dict[str, bytes],
) -> tuple[list[str], list[str], list[str]]:
    names_a = set(files_a.keys())
    names_b = set(files_b.keys())

    added = sorted(names_b - names_a)
    removed = sorted(names_a - names_b)

    modified: list[str] = []
    for common_name in sorted(names_a & names_b):
        if _sha256_bytes(files_a[common_name]) != _sha256_bytes(files_b[common_name]):
            modified.append(common_name)

    return added, removed, modified


def diff_archives(archive_a_path: str, archive_b_path: str, *, json_output: bool = False) -> int:
    archive_a = Path(archive_a_path)
    archive_b = Path(archive_b_path)

    if not archive_a.exists() or not archive_a.is_file():
        print(f"Error: Archive '{archive_a}' does not exist or is not a file.", file=sys.stderr)
        return 1
    if not archive_b.exists() or not archive_b.is_file():
        print(f"Error: Archive '{archive_b}' does not exist or is not a file.", file=sys.stderr)
        return 1

    manifest_a = read_manifest_from_kno_archive(archive_a)
    if manifest_a is None:
        return 1

    manifest_b = read_manifest_from_kno_archive(archive_b)
    if manifest_b is None:
        return 1

    files_a = _read_archive_files(archive_a)
    if files_a is None:
        return 1

    files_b = _read_archive_files(archive_b)
    if files_b is None:
        return 1

    manifest_lines = _manifest_change_lines(manifest_a, manifest_b)
    added_files, removed_files, modified_files = _file_change_sets(files_a, files_b)

    has_file_changes = bool(added_files or removed_files or modified_files)
    changes_detected = bool(manifest_lines or has_file_changes)

    if json_output:
        payload = {
            "schema_version": "1.0",
            "archive_a": str(archive_a),
            "archive_b": str(archive_b),
            "changes_detected": changes_detected,
            "manifest_changes": manifest_lines,
            "file_changes": {
                "added": added_files,
                "removed": removed_files,
                "modified": modified_files,
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"[kinnoo diff] Comparing '{archive_a.name}' -> '{archive_b.name}'")

        if manifest_lines:
            print("Manifest changes:")
            for line in manifest_lines:
                print(f"- {line}")

        if has_file_changes:
            print("File changes:")
            added_label = ", ".join(added_files) if added_files else "(none)"
            removed_label = ", ".join(removed_files) if removed_files else "(none)"
            modified_label = ", ".join(modified_files) if modified_files else "(none)"
            print(f"- added: {added_label}")
            print(f"- removed: {removed_label}")
            print(f"- modified: {modified_label}")

        if not changes_detected:
            print("[kinnoo diff] No differences detected.")

    if changes_detected:
        return 2
    return 0
