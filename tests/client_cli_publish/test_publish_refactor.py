import os
import subprocess
import sys
import zipfile
import json
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
    run_content: str = "print('ok')\n",
    manifest_override: str | None = None,
) -> Path:
    archive_path = archive_root / name / version / f"{name}.kno"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = manifest_override or (
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


def test_publish_errors_for_missing_or_invalid_archive_source(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(_test_home(tmp_path)),
    }

    missing_agent_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "missing-agent", "--local"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    missing_agent_output = f"{missing_agent_result.stdout}\n{missing_agent_result.stderr}"
    assert missing_agent_result.returncode != 0
    assert "Local archive source for agent 'missing-agent' was not found" in missing_agent_output

    empty_agent_dir = archive_root / "empty-agent"
    empty_agent_dir.mkdir(parents=True, exist_ok=True)
    no_versions_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "empty-agent", "--local"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    no_versions_output = f"{no_versions_result.stdout}\n{no_versions_result.stderr}"
    assert no_versions_result.returncode != 0
    assert "Local archive source for agent 'empty-agent' has no versions." in no_versions_output

    _write_archive(
        archive_root,
        name="broken-agent",
        version="3.0.0",
        manifest_override=(
            "\n".join(
                [
                    "name: broken-agent",
                    "version: not-a-semver",
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
        ),
    )

    invalid_metadata_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "broken-agent", "--local"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    invalid_metadata_output = f"{invalid_metadata_result.stdout}\n{invalid_metadata_result.stderr}"
    assert invalid_metadata_result.returncode != 0
    assert "Manifest validation failed for resolved local archive source." in invalid_metadata_output
    assert "version" in invalid_metadata_output


def test_publish_uses_home_absolute_mock_registry_path(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    simulated_home = tmp_path / "simulated-home"
    simulated_home.mkdir(parents=True, exist_ok=True)

    source_archive = _write_archive(
        archive_root,
        name="absolute-path-agent",
        version="1.0.0",
        run_content="print('absolute-path')\n",
    )

    publish_cwd = tmp_path / "publish-cwd"
    publish_cwd.mkdir(parents=True, exist_ok=True)
    cli_path = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "HOME": str(simulated_home),
    }
    env.pop("KINNOO_REGISTRY_ROOT", None)

    result = subprocess.run(
        [sys.executable, str(cli_path), "publish", "absolute-path-agent", "--local"],
        cwd=publish_cwd,
        capture_output=True,
        text=True,
        env=env,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    expected_target = (
        simulated_home
        / "kinnoo-mock-registry-scratch"
        / "jerry"
        / "absolute-path-agent"
        / "1.0.0"
        / "absolute-path-agent.kno"
    )

    assert result.returncode == 0
    assert expected_target.is_absolute()
    assert expected_target.exists()
    assert expected_target.read_bytes() == source_archive.read_bytes()
    assert f"Target registry path: {expected_target}" in combined_output
    assert "Target registry path: registry-scratch/jerry/" not in combined_output


def test_publish_local_remote_mutually_exclusive(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    _write_archive(archive_root, name="mutual-exclusion-agent", version="1.0.0")

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(_test_home(tmp_path)),
    }

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "publish",
            "mutual-exclusion-agent",
            "--local",
            "--remote",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "not allowed with argument" in output


def test_publish_json_output(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    source_archive = _write_archive(
        archive_root,
        name="json-publish-agent",
        version="1.0.0",
    )

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(_test_home(tmp_path)),
    }

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "publish",
            "json-publish-agent",
            "--local",
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    payload = json.loads(result.stdout.strip())
    assert payload["agent_name"] == "json-publish-agent"
    assert payload["agent_version"] == "1.0.0"
    assert payload["registry"] == "local"
    assert payload["source_archive_path"] == str(source_archive)
    assert payload["publish_result"] == "accepted"
    assert payload["error_code"] is None
    assert payload["error_message"] is None


def test_publish_pack_private_sets_private_visibility(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    agent_dir = _write_agent_dir(work_root, name="private-pack-publish-agent", version="1.0.0")
    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(_test_home(tmp_path)),
    }

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "publish",
            str(agent_dir),
            "--pack",
            "--private",
            "--local",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "Updated visibility to private" in output
    assert "Published private-pack-publish-agent==1.0.0" in output

    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "visibility: private" in manifest_text


def test_publish_public_flag_removed_and_private_flag_documented(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "HOME": str(_test_home(tmp_path)),
    }

    public_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "legacy-agent", "--public", "--local"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    public_output = f"{public_result.stdout}\n{public_result.stderr}"
    assert public_result.returncode != 0
    assert "unrecognized arguments: --public" in public_output

    help_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "-h"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    help_output = f"{help_result.stdout}\n{help_result.stderr}"
    assert help_result.returncode == 0
    assert "--public" not in help_output
    assert "--private" in help_output
    assert "With --pack, force private packaging behavior" in help_output
