import os
import subprocess
import sys
import zipfile
from pathlib import Path


def _pack_env(tmp_path: Path) -> dict[str, str]:
    return {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(tmp_path / "archive-root"),
    }


def _canonical_archive_path(tmp_path: Path, name: str, version: str) -> Path:
    return tmp_path / "archive-root" / name / version / f"{name}.kno"


def _create_agent_with_pinned_transitive_requirements(tmp_path: Path, agent_name: str = "robust-agent") -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: robust-agent
version: 1.0.0
entrypoint: run.py
runtime:
  language: python
  version: '>=3.10'
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\nhttpx==0.27.0\n")

    return agent_dir


def _collect_wheel_distribution_names(kno_path: Path) -> set[str]:
    distributions: set[str] = set()
    with zipfile.ZipFile(kno_path, "r") as archive:
        for name in archive.namelist():
            if not name.startswith("wheels/") or not name.endswith(".whl"):
                continue
            wheel_filename = Path(name).name
            distribution = wheel_filename.split("-", 1)[0].lower()
            distributions.add(distribution)
    return distributions


def test_pack_includes_transitive_wheels_for_pinned_deps(tmp_path):
    # [agent] test65 should be run for packaging changes that might impact dependency
    # closure behavior (resolver flags, wheel build strategy, or archive assembly).
    agent_dir = _create_agent_with_pinned_transitive_requirements(tmp_path)

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
        capture_output=True,
        text=True,
        env=_pack_env(tmp_path),
    )
    assert result.returncode == 0, f"kinnoo pack failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    kno_path = _canonical_archive_path(tmp_path, agent_dir.name, "1.0.0")
    assert kno_path.exists(), "Expected .kno archive to be created"

    distributions = _collect_wheel_distribution_names(kno_path)

    expected_subset = {
        "requests",   # direct
        "httpx",      # direct
        "urllib3",    # transitive via requests
        "certifi",    # transitive via requests/httpx
        "httpcore",   # transitive via httpx
        "anyio",      # transitive via httpcore
    }

    missing = expected_subset - distributions
    assert not missing, (
        "Expected direct + transitive dependency wheels in archive. "
        f"Missing: {sorted(missing)}. Found: {sorted(distributions)}"
    )


def test_kno_zip_format_is_canonical(tmp_path):
    # [agent] test66 should run for archive format or install/extract flow changes.
    # It enforces that `.kno` artifacts are true zip archives and installable.
    agent_dir = tmp_path / "zip-canonical-agent"
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: zip-canonical-agent
version: 1.0.0
entrypoint: run.py
runtime:
  language: python
  version: '>=3.10'
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('zip canonical ok')\n")
    (agent_dir / "requirements.txt").write_text("")

    pack_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
        capture_output=True,
        text=True,
        env=_pack_env(tmp_path),
    )
    assert pack_result.returncode == 0, (
        f"kinnoo pack failed\nSTDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    kno_path = _canonical_archive_path(tmp_path, "zip-canonical-agent", "1.0.0")
    assert kno_path.exists(), "Expected .kno archive to be created"
    assert zipfile.is_zipfile(kno_path), "Expected .kno archive to be a valid zip file"

    install_target = tmp_path / "installed-zip-canonical-agent"
    install_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(kno_path),
            str(install_target),
            "--yes",
            "--allow-unverified-publisher",
        ],
        capture_output=True,
        text=True,
    )
    assert install_result.returncode == 0, (
        f"kinnoo install failed\nSTDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
    )
    assert (install_target / "kinnoo.yaml").exists()
    assert (install_target / "run.py").exists()


def test_pack_continues_on_per_dependency_wheel_failure(tmp_path):
        agent_dir = tmp_path / "partial-wheel-agent"
        agent_dir.mkdir()

        (agent_dir / "kinnoo.yaml").write_text(
                """
name: partial-wheel-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: '>=3.10'
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""".strip()
                + "\n"
        )
        (agent_dir / "run.py").write_text("print('partial wheel ok')\n")
        (agent_dir / "requirements.txt").write_text(
                "requests==2.31.0\n"
                "nonexist-pkg-kinnoo-test==0.0.1\n"
        )

        result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
                capture_output=True,
                text=True,
                env=_pack_env(tmp_path),
        )

        assert result.returncode == 0, (
                "Expected pack to continue despite one failed dependency wheel build. "
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

        kno_path = _canonical_archive_path(tmp_path, "partial-wheel-agent", "1.0.0")
        assert kno_path.exists(), "Expected .kno archive to be created"

        warning_text = f"Could not build wheel for dependency 'nonexist-pkg-kinnoo-test==0.0.1'"
        assert warning_text in result.stderr

        with zipfile.ZipFile(kno_path, "r") as archive:
                assert "wheels/missing_wheels.txt" in archive.namelist()
                missing_wheels = archive.read("wheels/missing_wheels.txt").decode("utf-8")
                assert "nonexist-pkg-kinnoo-test==0.0.1" in missing_wheels


def test_pack_warns_on_platform_specific_wheels(tmp_path):
        # [agent] test70 should run for packaging changes that may affect wheel tag
        # parsing, warning messaging, or portability checks.
        agent_dir = tmp_path / "platform-wheel-agent"
        agent_dir.mkdir()

        (agent_dir / "kinnoo.yaml").write_text(
                """
name: platform-wheel-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: '>=3.10'
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""".strip()
                + "\n"
        )
        (agent_dir / "run.py").write_text("print('platform wheel ok')\n")
        (agent_dir / "requirements.txt").write_text(
            "orjson==3.10.6\n"
            "psutil==7.0.0\n"
        )

        result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
                capture_output=True,
                text=True,
            env=_pack_env(tmp_path),
        )

        assert result.returncode == 0, (
                "Expected pack to succeed while warning about portability risk. "
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert "Archive contains platform-specific wheels that may not install on other operating systems" in result.stderr

        kno_path = _canonical_archive_path(tmp_path, "platform-wheel-agent", "1.0.0")
        assert kno_path.exists(), "Expected .kno archive to be created"


def test_feature38_memory_snapshot_credential_warning_first(tmp_path):
    agent_dir = tmp_path / "feature38-memory-snapshot-agent"
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature38-memory-snapshot-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: '>=3.10'
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
state_dirs:
    - path: memory
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('memory snapshot ok')\n")
    (agent_dir / "requirements.txt").write_text("")

    memory_dir = agent_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    risky_snapshot = "aws_secret_access_key=ABCDEFGHIJKLMNOPQRSTUVWX1234567890"
    (memory_dir / "snapshot.json").write_text(
        "{\n"
        f"  \"checkpoint\": \"{risky_snapshot}\"\n"
        "}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
        capture_output=True,
        text=True,
        env=_pack_env(tmp_path),
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0, output
    assert "Field 'state_dirs' is not supported" in output
    assert risky_snapshot not in output

    kno_path = _canonical_archive_path(tmp_path, "feature38-memory-snapshot-agent", "1.0.0")
    assert not kno_path.exists(), "Archive should not be created when manifest is invalid"


def test_feature79_openclaw_pack_excludes_runtime_artifacts(tmp_path):
        agent_dir = tmp_path / "feature79-openclaw-excludes"
        agent_dir.mkdir(parents=True, exist_ok=True)

        (agent_dir / "kinnoo.yaml").write_text(
                """
name: feature79-openclaw-excludes
version: 1.0.0
type: openclaw-skill
framework: openclaw
entrypoint: index.js
runtime:
    language: nodejs
    version: '>=20'
    type: daemon
dependencies: []
inputs:
    type: text
outputs:
    type: text
""".strip()
                + "\n",
                encoding="utf-8",
        )
        (agent_dir / "index.js").write_text("console.log('openclaw')\n", encoding="utf-8")
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "package.json").write_text('{"name":"feature79-openclaw-excludes"}\n', encoding="utf-8")
        (agent_dir / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")

        (agent_dir / "skills" / "planner").mkdir(parents=True, exist_ok=True)
        (agent_dir / "skills" / "planner" / "SKILL.md").write_text("planner\n", encoding="utf-8")
        (agent_dir / "skills" / "node_modules" / "dep").mkdir(parents=True, exist_ok=True)
        (agent_dir / "skills" / "node_modules" / "dep" / "index.js").write_text("module.exports = {}\n", encoding="utf-8")
        (agent_dir / "skills" / ".git").mkdir(parents=True, exist_ok=True)
        (agent_dir / "skills" / ".git" / "config").write_text("gitdata\n", encoding="utf-8")
        (agent_dir / "memory" / ".openclaw").mkdir(parents=True, exist_ok=True)
        (agent_dir / "memory" / ".openclaw" / "cache.json").write_text("{}\n", encoding="utf-8")

        result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
                capture_output=True,
                text=True,
                env=_pack_env(tmp_path),
        )
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, output

        kno_path = _canonical_archive_path(tmp_path, "feature79-openclaw-excludes", "1.0.0")
        assert kno_path.exists(), "Expected .kno archive to be created"

        with zipfile.ZipFile(kno_path, "r") as archive:
                names = set(archive.namelist())
                assert "skills/planner/SKILL.md" in names
                assert "skills/node_modules/dep/index.js" not in names
                assert "skills/.git/config" not in names
                assert "memory/.openclaw/cache.json" not in names
