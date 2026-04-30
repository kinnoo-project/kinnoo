"""Integrity manifest helpers for .kno archive packaging and verification.

Manifest schema example:
{
    "version": 1,
    "files": {
        "run.py": {
            "sha256": "<hex sha256>",
            "size": 123
        },
        "kinnoo.yaml": {
            "sha256": "<hex sha256>",
            "size": 456
        }
    }
}

The ``files`` map stores POSIX-style relative paths and excludes ``META-INF/``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _is_meta_inf_path(path: Path) -> bool:
    parts = path.parts
    return len(parts) > 0 and parts[0] == "META-INF"


def compute_integrity_manifest(directory: Path) -> dict:
    """Compute a deterministic integrity manifest for files inside ``directory``."""

    root = Path(directory)
    files: dict[str, dict[str, object]] = {}

    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(root)
        if _is_meta_inf_path(relative_path):
            continue
        relative_key = relative_path.as_posix()
        files[relative_key] = {
            "sha256": _sha256_file(candidate),
            "size": candidate.stat().st_size,
        }

    return {
        "version": 1,
        "files": files,
    }


def verify_integrity_manifest(directory: Path, manifest: dict) -> list[str]:
    """Verify files under ``directory`` against a manifest and return mismatches."""

    root = Path(directory)
    mismatches: list[str] = []

    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, dict):
        return ["integrity manifest is missing a valid 'files' object"]

    expected_paths = {str(path) for path in manifest_files.keys()}

    for relative_key in sorted(expected_paths):
        record = manifest_files.get(relative_key)
        if not isinstance(record, dict):
            mismatches.append(f"{relative_key}: invalid record structure")
            continue

        expected_hash = record.get("sha256")
        expected_size = record.get("size")
        if not isinstance(expected_hash, str):
            mismatches.append(f"{relative_key}: missing sha256")
            continue
        if not isinstance(expected_size, int):
            mismatches.append(f"{relative_key}: missing size")
            continue

        absolute_path = root / Path(relative_key)
        if not absolute_path.exists() or not absolute_path.is_file():
            mismatches.append(f"{relative_key}: file missing")
            continue

        actual_size = absolute_path.stat().st_size
        if actual_size != expected_size:
            mismatches.append(
                f"{relative_key}: size mismatch (expected {expected_size}, got {actual_size})"
            )
            continue

        actual_hash = _sha256_file(absolute_path)
        if actual_hash != expected_hash:
            mismatches.append(
                f"{relative_key}: hash mismatch (expected {expected_hash}, got {actual_hash})"
            )

    actual_paths: set[str] = set()
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(root)
        if _is_meta_inf_path(relative_path):
            continue
        actual_paths.add(relative_path.as_posix())

    for extra in sorted(actual_paths - expected_paths):
        mismatches.append(f"{extra}: file present but not listed in manifest")

    return mismatches
