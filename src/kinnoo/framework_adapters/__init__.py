from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AdapterResult:
    framework: str
    detected: bool
    coverage_score: float
    inferred_overrides: dict[str, Any]
    confidence_overrides: dict[str, dict[str, Any]]
    warnings: list[str]
    unresolved_guidance: list[str]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def merge_adapter_into_report(
    *,
    base_report: dict[str, Any],
    adapter_result: AdapterResult,
) -> dict[str, Any]:
    merged = dict(base_report)
    inferred = dict(base_report.get("inferred", {}))
    confidence = dict(base_report.get("confidence", {}))
    warnings = list(base_report.get("warnings", []))

    inferred = _deep_merge(inferred, adapter_result.inferred_overrides)
    confidence.update(adapter_result.confidence_overrides)

    for warning in adapter_result.warnings:
        if warning not in warnings:
            warnings.append(warning)

    merged["inferred"] = inferred
    merged["confidence"] = confidence
    merged["warnings"] = warnings
    merged["adapter"] = {
        "framework": adapter_result.framework,
        "coverage_score": adapter_result.coverage_score,
        "detected": adapter_result.detected,
        "unresolved_guidance": list(adapter_result.unresolved_guidance),
    }
    return merged


def detect_node_package_manager(project_dir: Path) -> str:
    if (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_dir / "yarn.lock").exists():
        return "yarn"
    return "npm"


def read_text_files(project_dir: Path, suffixes: set[str]) -> list[str]:
    contents: list[str] = []
    ignored_segments = {".git", "node_modules", ".venv", "dist", "build", "coverage"}

    for path in sorted(project_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        try:
            relative_parts = path.relative_to(project_dir).parts
        except ValueError:
            continue
        if any(part in ignored_segments for part in relative_parts):
            continue
        try:
            contents.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue

    return contents
