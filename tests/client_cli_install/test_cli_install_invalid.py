import subprocess
import sys
from pathlib import Path
import zipfile
import pytest

def make_invalid_kno(tmp_path, archive_name="invalid.kno"):
    """Create a .kno archive that is not a valid zip file."""
    archive_path = tmp_path / archive_name
    archive_path.write_bytes(b"not a zip file")
    return archive_path

def make_missing_file_kno(tmp_path, agent_name="missingfileagent"):
    """Create a .kno archive missing kinnoo.yaml."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    # Only add run.py, omit kinnoo.yaml
    (agent_dir / "run.py").write_text("print('hello')\n")
    archive_path = tmp_path / f"{agent_name}.kno"
    with zipfile.ZipFile(archive_path, "w") as z:
        z.write(agent_dir / "run.py", arcname="run.py")
    return archive_path, agent_name

@pytest.mark.parametrize("archive_type", ["invalid_zip", "missing_kinnoo_yaml"])
def test_install_invalid_archive_or_missing_files(tmp_path, archive_type):
    """Test kinnoo install error handling for invalid archive or missing files (test56)."""
    cli_path = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
    import shutil
    if archive_type == "invalid_zip":
        archive_path = make_invalid_kno(tmp_path)
        agent_dir = tmp_path / "invalid"
    else:
        archive_path, agent_name = make_missing_file_kno(tmp_path)
        agent_dir = tmp_path / agent_name
        # Remove the agent directory so kinnoo install can create it
        shutil.rmtree(agent_dir)
    # Run kinnoo install
    result = subprocess.run([
        sys.executable, str(cli_path), "install", str(archive_path), "--yes"
    ], capture_output=True, text=True)
    assert result.returncode != 0, "kinnoo install should fail for invalid archive or missing files"
    if archive_type == "invalid_zip":
        assert "not a valid .kno (zip) archive" in result.stderr or "not a valid zip-based .kno file" in result.stderr
    else:
        assert "kinnoo.yaml not found" in result.stderr
    assert not agent_dir.exists() or not any(agent_dir.iterdir()), "Agent directory should not exist or be empty after failure"
