import subprocess
import sys
import tempfile
import shutil
import os
from pathlib import Path
import zipfile
import pytest

def make_invalid_kno_archive(tmp_path, agent_name="badagent"):
    """Helper to create a .kno archive with an invalid kinnoo.yaml."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    # Write an invalid kinnoo.yaml (missing entrypoint)
    (agent_dir / "kinnoo.yaml").write_text("name: badagent\n")
    (agent_dir / "run.py").write_text("print('hello')\n")
    archive_path = tmp_path / f"{agent_name}.kno"
    with zipfile.ZipFile(archive_path, "w") as z:
        for file in agent_dir.iterdir():
            z.write(file, arcname=file.name)
    return archive_path, agent_dir

def test_install_aborts_on_invalid_manifest(tmp_path):
    # Arrange: create .kno archive with invalid manifest
    archive_path, agent_dir = make_invalid_kno_archive(tmp_path)
    shutil.rmtree(agent_dir)
    assert not agent_dir.exists()
    cli_path = os.path.abspath("src/kinnoo/cli.py")
    # Act: run kinnoo install <archive>
    result = subprocess.run([
        sys.executable, cli_path, "install", str(archive_path), "--yes"
    ], capture_output=True, text=True)
    # Assert: install aborts, prints validation error, and does not leave agent_dir
    assert result.returncode != 0
    assert "Manifest validation failed" in result.stderr
    assert "entrypoint" in result.stderr  # Should mention missing entrypoint
    assert not agent_dir.exists()  # Directory should be cleaned up
