"""Shared checksum helpers for archive integrity workflows."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_CHECKSUM_LINE_PATTERN = re.compile(r"^([0-9a-f]{64})  (.+)$")


class ChecksumParseError(ValueError):
    """Raised when a checksum sidecar has invalid format."""


def checksum_sidecar_path_for_archive(archive_path: Path) -> Path:
    """Return the canonical sidecar path for an archive file."""
    return archive_path.with_name(f"{archive_path.name}.sha256")


def compute_file_sha256(file_path: Path) -> str:
    """Compute lowercase hex SHA256 digest for a file's bytes."""
    digest = hashlib.sha256()
    with file_path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_checksum_sidecar_line(checksum_value: str, archive_filename: str) -> str:
    """Format sidecar content line using stable '<sha256>  <filename>' format."""
    return f"{checksum_value}  {archive_filename}\n"


def parse_checksum_sidecar_text(sidecar_text: str) -> tuple[str, str]:
    """Parse sidecar text and return (expected_checksum, archive_filename)."""
    stripped = sidecar_text.strip()
    match = _CHECKSUM_LINE_PATTERN.fullmatch(stripped)
    if match is None:
        raise ChecksumParseError(
            "Invalid checksum sidecar format. Expected '<sha256>  <archive-filename>'."
        )

    expected_checksum, archive_filename = match.groups()
    return expected_checksum, archive_filename


def read_checksum_sidecar(sidecar_path: Path) -> tuple[str, str]:
    """Read and parse checksum sidecar file."""
    sidecar_text = sidecar_path.read_text(encoding="utf-8")
    return parse_checksum_sidecar_text(sidecar_text)


def verify_archive_checksum(archive_path: Path, expected_checksum: str) -> tuple[bool, str]:
    """Return (is_match, actual_checksum) for archive bytes against expected checksum."""
    actual_checksum = compute_file_sha256(archive_path)
    return actual_checksum == expected_checksum, actual_checksum


def write_checksum_sidecar_for_archive(archive_path: Path) -> Path:
    """Write checksum sidecar adjacent to archive and return sidecar path."""
    checksum_value = compute_file_sha256(archive_path)
    sidecar_path = checksum_sidecar_path_for_archive(archive_path)
    sidecar_path.write_text(
        format_checksum_sidecar_line(checksum_value, archive_path.name),
        encoding="utf-8",
    )
    return sidecar_path
