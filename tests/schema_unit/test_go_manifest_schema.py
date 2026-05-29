from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Allow importing from src/kinnoo without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from kinnoo.validator import validate_manifest_data  # noqa: E402
from kinnoo.init_command import _build_go_manifest  # noqa: E402

_BASE_GO_MANIFEST: dict = {
    "name": "go-agent",
    "version": "0.1.0",
    "entrypoint": "main.go",
    "runtime": {
        "language": "go",
        "version": ">=1.22",
        "type": "one-shot",
    },
    "dependencies": [],
    "inputs": {"type": "text"},
    "outputs": {"type": "text"},
}


def test_feature19_go_source_entrypoint_is_valid() -> None:
    """test80: Go source manifests should validate with main.go entrypoint."""
    data = dict(_BASE_GO_MANIFEST)
    data["runtime"] = dict(data["runtime"])

    is_valid, errors = validate_manifest_data(data)

    assert is_valid is True, f"Expected Go source manifest to validate; errors: {errors}"
    assert errors == []


def test_feature19_go_binary_entrypoint_is_valid() -> None:
    """test80: Go binary entrypoint declarations should validate."""
    data = dict(_BASE_GO_MANIFEST)
    data["runtime"] = dict(data["runtime"])
    data["entrypoint"] = "bin/go-agent"

    is_valid, errors = validate_manifest_data(data)

    assert is_valid is True, f"Expected Go binary manifest to validate; errors: {errors}"
    assert errors == []


def test_feature19_unsupported_runtime_language_is_rejected() -> None:
    """test80: Unsupported runtime.language values should return actionable errors."""
    data = dict(_BASE_GO_MANIFEST)
    data["runtime"] = dict(data["runtime"])
    data["runtime"]["language"] = "ruby"

    is_valid, errors = validate_manifest_data(data)

    assert is_valid is False, "Expected unsupported runtime.language value to fail validation"
    assert any("runtime.language" in message for message in errors), (
        f"Expected runtime.language guidance in errors; got: {errors}"
    )


def test_feature19_go_rejects_non_go_script_entrypoint() -> None:
    """test80: Go runtime should reject entrypoint paths that target other runtimes."""
    data = dict(_BASE_GO_MANIFEST)
    data["runtime"] = dict(data["runtime"])
    data["entrypoint"] = "main.py"

    is_valid, errors = validate_manifest_data(data)

    assert is_valid is False, "Expected non-Go script entrypoint to fail for Go runtime"
    assert any("entrypoint" in message and "not a Go source or executable path" in message for message in errors), (
        f"Expected Go entrypoint guidance in errors; got: {errors}"
    )


def test_feature19_go_rejects_non_go_script_in_entrypoints_contract() -> None:
    """test80: Multi-entrypoint declarations also enforce Go entrypoint contract."""
    data = dict(_BASE_GO_MANIFEST)
    data["runtime"] = dict(data["runtime"])
    data.pop("entrypoint", None)
    data["entrypoints"] = ["main.go", "fallback.py"]

    is_valid, errors = validate_manifest_data(data)

    assert is_valid is False, "Expected invalid entrypoints[] item to fail for Go runtime"
    assert any("entrypoints[1]" in message and "not a Go source or executable path" in message for message in errors), (
        f"Expected indexed Go entrypoint guidance in errors; got: {errors}"
    )


def test_feature19_go_manifest_generator_defaults_entrypoint_to_main_go() -> None:
    """test80: Generated Go manifests default to entrypoint main.go."""
    generated_manifest = yaml.safe_load(_build_go_manifest("go-default-agent"))

    assert generated_manifest["entrypoint"] == "main.go"
    assert generated_manifest["runtime"]["language"] == "go"

    is_valid, errors = validate_manifest_data(generated_manifest)

    assert is_valid is True, f"Expected generated default Go manifest to validate; errors: {errors}"
    assert errors == []
