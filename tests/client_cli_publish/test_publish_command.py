from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
SRC_ROOT = Path(__file__).resolve().parents[2] / "src"


def _cli_env(*, archive_root: Path, registry_root: Path) -> dict[str, str]:
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath_parts = [str(SRC_ROOT)]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)

    isolated_home = archive_root.parent / "isolated-home"
    isolated_home.mkdir(parents=True, exist_ok=True)

    return {
        **os.environ,
        "HOME": str(isolated_home),
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "PYTHONPATH": os.pathsep.join(pythonpath_parts),
    }


def _write_agent_dir(agent_root: Path, *, name: str, version: str) -> Path:
    agent_dir = agent_root / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
                "framework: generic",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    return agent_dir


def _write_node_agent_dir(agent_root: Path, *, name: str, version: str) -> Path:
    agent_dir = agent_root / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
                "framework: generic",
                "entrypoint: run.js",
                "runtime:",
                "  language: javascript",
                "  version: \">=20\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "run.js").write_text("console.log('hello')\n", encoding="utf-8")
    (agent_dir / "package.json").write_text(
        '{"name":"js-pack-publish-agent","version":"1.0.0"}\n',
        encoding="utf-8",
    )
    return agent_dir


def test_publish_with_pack_packs_then_publishes(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    agent_dir = _write_agent_dir(work_root, name="pack-publish-agent", version="1.0.0")

    env = _cli_env(archive_root=archive_root, registry_root=registry_root)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", str(agent_dir), "--pack", "--local"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "[kinnoo pack] Packaging agent directory" in output
    assert "Published pack-publish-agent==1.0.0" in output

    published_archives = [
        candidate
        for candidate in registry_root.rglob("pack-publish-agent.kno")
        if "1.0.0" in candidate.as_posix()
    ]
    assert published_archives


def test_publish_with_pack_and_bump_publishes_bumped_version(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    agent_dir = _write_agent_dir(work_root, name="bump-publish-agent", version="1.2.3")

    env = _cli_env(archive_root=archive_root, registry_root=registry_root)

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "publish",
            str(agent_dir),
            "--pack",
            "--bump",
            "minor",
            "--local",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Published bump-publish-agent==1.3.0" in output

    published_archives = [
        candidate
        for candidate in registry_root.rglob("bump-publish-agent.kno")
        if "1.3.0" in candidate.as_posix()
    ]
    assert published_archives
    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "version: 1.3.0" in manifest_text


def test_publish_with_pack_node_runtime_without_requirements_succeeds(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    agent_dir = _write_node_agent_dir(work_root, name="js-pack-publish-agent", version="1.0.0")

    env = _cli_env(archive_root=archive_root, registry_root=registry_root)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", str(agent_dir), "--pack", "--local"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "Published js-pack-publish-agent==1.0.0" in output

    published_archives = [
        candidate
        for candidate in registry_root.rglob("js-pack-publish-agent.kno")
        if "1.0.0" in candidate.as_posix()
    ]
    assert published_archives


def test_publish_pack_bump_guardrail_errors(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    agent_dir = _write_agent_dir(work_root, name="guardrail-agent", version="2.0.0")

    env = _cli_env(archive_root=archive_root, registry_root=registry_root)

    bump_without_pack = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "guardrail-agent", "--bump", "minor"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    bump_without_pack_output = f"{bump_without_pack.stdout}\n{bump_without_pack.stderr}"
    assert bump_without_pack.returncode != 0
    assert "--bump can only be used together with --pack" in bump_without_pack_output

    private_without_pack = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "guardrail-agent", "--private"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    private_without_pack_output = f"{private_without_pack.stdout}\n{private_without_pack.stderr}"
    assert private_without_pack.returncode != 0
    assert "--private can only be used together with --pack" in private_without_pack_output

    missing_archive_no_pack = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "missing-agent", "--local"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    missing_archive_output = f"{missing_archive_no_pack.stdout}\n{missing_archive_no_pack.stderr}"
    assert missing_archive_no_pack.returncode != 0
    assert "Local archive source for agent 'missing-agent' was not found" in missing_archive_output

    invalid_bump_value = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "publish",
            str(agent_dir),
            "--pack",
            "--bump",
            "invalid-part",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    invalid_bump_output = f"{invalid_bump_value.stdout}\n{invalid_bump_value.stderr}"
    assert invalid_bump_value.returncode != 0
    assert "invalid choice" in invalid_bump_output


def test_publish_with_pack_public_sets_manifest_visibility(tmp_path: Path) -> None:
    # [agent] test deprecated: task488 replaces publish --public with publish --private.
    import pytest
    pytest.skip("[agent] test deprecated: replaced by test_publish_with_pack_private_sets_manifest_visibility")


def test_publish_with_pack_private_sets_manifest_visibility(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    agent_dir = _write_agent_dir(work_root, name="private-publish-agent", version="1.0.0")

    env = _cli_env(archive_root=archive_root, registry_root=registry_root)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", str(agent_dir), "--pack", "--private", "--local"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Updated visibility to private" in output

    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "visibility: private" in manifest_text
