import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"


def _test_home(root: Path) -> Path:
    home_root = root / ".test-home"
    home_root.mkdir(parents=True, exist_ok=True)
    return home_root


def _write_archive(
    archive_root: Path,
    *,
    name: str,
    version: str,
    run_content: str,
) -> Path:
    archive_path = archive_root / name / version / f"{name}.kno"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = (
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
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
        + "\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr("kinnoo.yaml", manifest_text)
        archive_zip.writestr("run.py", run_content)
        archive_zip.writestr("requirements.txt", "")

    return archive_path


def _write_archive_at_path(
    archive_path: Path,
    *,
    name: str,
    version: str,
    run_content: str,
) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = (
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
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
        + "\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr("kinnoo.yaml", manifest_text)
        archive_zip.writestr("run.py", run_content)
        archive_zip.writestr("requirements.txt", "")

    return archive_path


def _publish_from_local_archive(
    *,
    agent_name: str,
    archive_root: Path,
    registry_root: Path,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    home_root = _test_home(cwd)
    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(home_root),
    }
    return subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", agent_name, "--local"],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def test_install_file_path_mode_preserved(tmp_path: Path) -> None:
    registry_root = tmp_path / "registry-sandbox"

    archive_path = _write_archive_at_path(
        tmp_path / "file-path-install.kno",
        name="file-path-install",
        version="1.0.0",
        run_content="import sys\nprint('from-file-path:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )

    _write_archive(
        registry_root,
        name="file-path-install",
        version="9.9.9",
        run_content="import sys\nprint('from-registry:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )

    env = {
        **os.environ,
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(_test_home(tmp_path)),
    }

    install_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "install", "file-path-install.kno", "--yes"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    install_output = f"{install_result.stdout}\n{install_result.stderr}"

    assert install_result.returncode == 0
    assert "Resolved registry selector" not in install_output
    assert "Extracted 'file-path-install.kno'" in install_output

    installed_dir = archive_path.with_suffix("")
    assert installed_dir.exists()

    run_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(installed_dir),
            "hello",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    run_output = f"{run_result.stdout}\n{run_result.stderr}"

    assert run_result.returncode == 0
    assert "from-file-path:hello" in run_output
    assert "from-registry" not in run_output
