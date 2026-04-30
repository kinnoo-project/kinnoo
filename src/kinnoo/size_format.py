"""Shared archive size formatting helpers for user-facing output."""

from __future__ import annotations


def format_size_human_readable(size_bytes: int) -> str:
    """Return deterministic human-readable size using binary units."""
    if size_bytes < 0:
        raise ValueError("size_bytes must be >= 0")

    if size_bytes < 1024:
        return f"{size_bytes} B"

    units = (("KB", 1024), ("MB", 1024**2), ("GB", 1024**3))
    for unit, divisor in reversed(units):
        if size_bytes >= divisor:
            return f"{size_bytes / divisor:.1f} {unit}"

    return f"{size_bytes} B"


def size_in_megabytes(size_bytes: int) -> float:
    """Convert bytes to MB using binary (MiB) base for threshold checks."""
    if size_bytes < 0:
        raise ValueError("size_bytes must be >= 0")
    return size_bytes / (1024 * 1024)
