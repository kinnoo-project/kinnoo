import subprocess
import sys
import tempfile
import shutil
import os
from pathlib import Path
import zipfile
import pytest

def make_kno_with_wheel(tmp_path, agent_name="wheelagent"):
    """Helper to create a .kno archive with a wheels/ directory and a dummy wheel."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    # Write a valid kinnoo.yaml manifest
    manifest = (
        'entrypoint: run.py\n'
        'dependencies: []\n'
        'inputs:\n  type: string\n'
        'outputs:\n  type: string\n'
        'runtime:\n'
        '  type: one-shot\n'
        '  language: python\n'
        '  version: "3.10"\n'
        'name: ' + agent_name + '\n'
        'version: 0.1.0\n'
    )
    (agent_dir / "kinnoo.yaml").write_text(manifest)
    (agent_dir / "run.py").write_text("print('hello')\n")
    wheels_dir = agent_dir / "wheels"
    wheels_dir.mkdir()
    # Create a dummy wheel file (not a real wheel, but enough for test to check install attempt)
    dummy_wheel = wheels_dir / "dummy-0.1-py3-none-any.whl"
    dummy_wheel.write_bytes(b"Fake wheel content")
    archive_path = tmp_path / f"{agent_name}.kno"
    with zipfile.ZipFile(archive_path, "w") as z:
        for file in agent_dir.rglob("*"):
            if file.is_file():
                z.write(file, arcname=str(file.relative_to(agent_dir)))
    return archive_path, agent_dir

def test_install_creates_venv_and_attempts_wheel_install(tmp_path):
    # Arrange: create .kno archive with wheels/
    archive_path, agent_dir = make_kno_with_wheel(tmp_path)
    shutil.rmtree(agent_dir)
    assert not agent_dir.exists()
    cli_path = os.path.abspath("src/kinnoo/cli.py")
    # Act: run kinnoo install <archive>
    result = subprocess.run([
        sys.executable, cli_path, "install", str(archive_path), "--yes"
    ], capture_output=True, text=True)
    # Assert: venv is created, wheel install attempted, error due to fake wheel
    # Should fail due to invalid wheel, and agent_dir should be cleaned up (atomic install)
    assert "Installing wheel: dummy-0.1-py3-none-any.whl" in result.stdout
    assert result.returncode != 0
    assert not agent_dir.exists()  # Directory should be cleaned up on failure
    assert (
        "pip install failed" in result.stderr
        or "not a supported wheel" in result.stderr
        or "Error: pip install failed" in result.stderr
    )
