import subprocess
import sys
import tempfile
import shutil
import os
from pathlib import Path
import zipfile
import pytest

def make_kno_archive(tmp_path, agent_name="testagent"):
    """Helper to create a minimal .kno archive for testing extraction."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    # Write a fully valid kinnoo.yaml manifest
    manifest = (
        "name: test-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    (agent_dir / "kinnoo.yaml").write_text(manifest)
    (agent_dir / "run.py").write_text("print('hello')\n")
    archive_path = tmp_path / f"{agent_name}.kno"
    with zipfile.ZipFile(archive_path, "w") as z:
        for file in agent_dir.iterdir():
            z.write(file, arcname=file.name)
    return archive_path, agent_dir

def test_install_extracts_archive(tmp_path):
    # Arrange: create .kno archive
    archive_path, agent_dir = make_kno_archive(tmp_path)
    # Remove the original agent_dir to simulate fresh install
    shutil.rmtree(agent_dir)
    assert not agent_dir.exists()
    # Act: run kinnoo install <archive>
    cli_path = os.path.abspath("src/kinnoo/cli.py")
    result = subprocess.run([
        sys.executable, cli_path, "install", str(archive_path), "--yes"
    ], capture_output=True, text=True)
    # Assert: agent_dir is created and files extracted
    assert result.returncode == 0
    assert agent_dir.exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "run.py").exists()
    assert f"Extracted '{archive_path.name}' to '{agent_dir}'" in result.stdout


def test_feature22_install_extracts_assets_with_relative_paths(tmp_path):
    source_agent_dir = tmp_path / "asset-agent"
    source_agent_dir.mkdir()

    (source_agent_dir / "assets" / "nested").mkdir(parents=True)
    (source_agent_dir / "assets" / "nested" / "note.txt").write_text(
        "asset payload\n",
        encoding="utf-8",
    )
    (source_agent_dir / "data").mkdir(parents=True)
    (source_agent_dir / "data" / "config.json").write_text(
        '{"ok": true}\n',
        encoding="utf-8",
    )

    manifest = (
        "name: asset-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
        "assets:\n"
        "  paths:\n"
        "    - assets\n"
        "    - data/config.json\n"
    )
    (source_agent_dir / "kinnoo.yaml").write_text(manifest, encoding="utf-8")
    (source_agent_dir / "run.py").write_text("print('asset-agent-ok')\n", encoding="utf-8")
    (source_agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    cli_path = os.path.abspath("src/kinnoo/cli.py")
    pack_env = os.environ.copy()
    pack_env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")

    pack_result = subprocess.run(
        [sys.executable, cli_path, "pack", str(source_agent_dir)],
        capture_output=True,
        text=True,
        env=pack_env,
    )
    assert pack_result.returncode == 0, pack_result.stderr

    archive_path = tmp_path / "archive-root" / "asset-agent" / "1.0.0" / "asset-agent.kno"
    assert archive_path.exists()

    install_result = subprocess.run(
        [
            sys.executable,
            cli_path,
            "install",
            str(archive_path),
            "--yes",
            "--allow-unverified-publisher",
        ],
        capture_output=True,
        text=True,
        env=pack_env,
    )
    assert install_result.returncode == 0, install_result.stderr

    installed_dir = archive_path.with_suffix("")
    assert installed_dir.exists()
    assert (installed_dir / "assets" / "nested" / "note.txt").exists()
    assert (installed_dir / "data" / "config.json").exists()

    run_result = subprocess.run(
        [sys.executable, str(installed_dir / "run.py")],
        capture_output=True,
        text=True,
    )
    assert run_result.returncode == 0
    assert "asset-agent-ok" in run_result.stdout
