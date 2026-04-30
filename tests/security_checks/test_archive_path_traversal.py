from __future__ import annotations

import zipfile
from pathlib import Path


def _make_zip_slip_archive(archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "kinnoo.yaml",
            (
                "name: zip-slip-agent\n"
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
            ),
        )
        archive.writestr("run.py", "print('safe')\n")
        archive.writestr("../../outside.txt", "owned\n")


def test_install_rejects_zip_slip_archive(tmp_path: Path):
    import subprocess
    import sys

    archive_path = tmp_path / "zip-slip-install.kno"
    target_dir = tmp_path / "install-target"
    _make_zip_slip_archive(archive_path)

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"],
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "unsafe archive entries" in output.lower() or "invalid archive payload" in output.lower()
    assert not target_dir.exists()


def test_fetch_rejects_zip_slip_archive(tmp_path: Path, monkeypatch, capsys):
    from kinnoo.fetch_command import fetch_agent

    registry_root = tmp_path / "registry"
    version_dir = registry_root / "zip-slip-agent" / "1.0.0"
    version_dir.mkdir(parents=True, exist_ok=True)

    archive_path = version_dir / "zip-slip-agent.kno"
    _make_zip_slip_archive(archive_path)

    monkeypatch.setenv("KINNOO_REGISTRY_ROOT", str(registry_root))

    exit_code = fetch_agent("zip-slip-agent==1.0.0", use_local=True)
    captured = capsys.readouterr()
    output = f"{captured.out}\n{captured.err}".lower()

    assert exit_code != 0
    assert "invalid archive payload" in output or "unsafe archive" in output
