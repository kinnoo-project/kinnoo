import os
import shutil
import subprocess
import tempfile
import json
import base64
import hashlib
from pathlib import Path
import pytest
import yaml

def make_dummy_kno_archive(archive_path, files=None):
    import zipfile
    files = files or {
        "kinnoo.yaml": (
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
        ),
        "run.py": "print('hello')\n"
    }
    with zipfile.ZipFile(archive_path, "w") as z:
        for fname, content in files.items():
            z.writestr(fname, content)

@pytest.mark.integration
def test_install_extracts_to_user_specified_directory(tmp_path):
    # Setup: create dummy .kno archive
    archive_path = tmp_path / "test-agent.kno"
    make_dummy_kno_archive(archive_path)
    target_dir = tmp_path / "myagent_dir"

    # Step1: Run kinnoo install <archive.kno> myagent_dir
    result = subprocess.run([
        "python3", "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Install failed: {result.stderr}"
    assert target_dir.exists(), "Target directory not created"
    assert (target_dir / "kinnoo.yaml").exists(), "kinnoo.yaml missing"
    assert (target_dir / "run.py").exists(), "run.py missing"

    # Step2: Run kinnoo install <archive.kno> myagent_dir when directory exists (without --force)
    result2 = subprocess.run([
        "python3", "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"
    ], capture_output=True, text=True)
    assert result2.returncode != 0, "Should fail if directory exists and --force not used"
    assert "already exists" in result2.stderr, "Error message missing for existing directory"

    # Step3: --force is paused; skip this step


def test_feature72_lockfile_write_and_stability(tmp_path, monkeypatch):
    from kinnoo import install_command

    shared_lockfile_path = tmp_path / "shared-lock.yaml"
    monkeypatch.setenv("KINNOO_LOCKFILE_PATH", str(shared_lockfile_path))

    def _manifest(name: str, version: str) -> str:
        return (
            f"name: {name}\n"
            f"version: {version}\n"
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

    b_archive = tmp_path / "b-agent.kno"
    make_dummy_kno_archive(
        b_archive,
        files={
            "kinnoo.yaml": _manifest("b-agent", "1.0.0"),
            "run.py": "print('b')\n",
            "requirements.txt": "",
        },
    )
    b_target = tmp_path / "installed-b"
    b_result = subprocess.run(
        ["python3", "src/kinnoo/cli.py", "install", str(b_archive), str(b_target), "--yes"],
        capture_output=True,
        text=True,
    )
    assert b_result.returncode == 0, b_result.stderr

    a_archive = tmp_path / "a-agent.kno"
    make_dummy_kno_archive(
        a_archive,
        files={
            "kinnoo.yaml": _manifest("a-agent", "2.0.0"),
            "run.py": "print('a')\n",
            "requirements.txt": "",
        },
    )
    a_target = tmp_path / "installed-a"
    a_result = subprocess.run(
        ["python3", "src/kinnoo/cli.py", "install", str(a_archive), str(a_target), "--yes"],
        capture_output=True,
        text=True,
    )
    assert a_result.returncode == 0, a_result.stderr

    lockfile_doc = yaml.safe_load(shared_lockfile_path.read_text(encoding="utf-8"))
    assert isinstance(lockfile_doc, dict)
    assert lockfile_doc.get("lock_version") == 1
    assert isinstance(lockfile_doc.get("locked_at"), str)

    platform_info = lockfile_doc.get("platform")
    assert isinstance(platform_info, dict)
    assert isinstance(platform_info.get("python"), str)
    assert isinstance(platform_info.get("os"), str)

    agents = lockfile_doc.get("agents")
    assert isinstance(agents, dict)
    assert list(agents.keys()) == ["a-agent", "b-agent"]

    a_entry = agents["a-agent"]
    b_entry = agents["b-agent"]
    assert a_entry.get("version") == "2.0.0"
    assert b_entry.get("version") == "1.0.0"
    assert a_entry.get("source") == "archive-file"
    assert b_entry.get("source") == "archive-file"
    assert isinstance(a_entry.get("installed_at"), str)
    assert isinstance(b_entry.get("installed_at"), str)

    expected_a_checksum = hashlib.sha256(a_archive.read_bytes()).hexdigest()
    expected_b_checksum = hashlib.sha256(b_archive.read_bytes()).hexdigest()
    assert a_entry.get("archive_sha256") == expected_a_checksum
    assert b_entry.get("archive_sha256") == expected_b_checksum

    a_force_result = install_command.install_agent(
        archive_path=str(a_archive),
        target_dir_arg=str(a_target),
        assume_yes=True,
        force=True,
    )
    assert a_force_result == 0

    updated_doc = yaml.safe_load(shared_lockfile_path.read_text(encoding="utf-8"))
    assert isinstance(updated_doc, dict)
    updated_agents = updated_doc.get("agents")
    assert isinstance(updated_agents, dict)
    assert list(updated_agents.keys()) == ["a-agent", "b-agent"]
    assert updated_agents["a-agent"].get("archive_sha256") == expected_a_checksum
    assert updated_agents["a-agent"].get("source") == "archive-file"


def test_feature74_uninstall_metadata_and_errors(tmp_path, monkeypatch, capsys):
    from kinnoo import uninstall_command

    install_root = tmp_path / "feature74-install-root"
    target_agent_dir = install_root / "feature74-agent"
    other_agent_dir = install_root / "other-agent"
    target_agent_dir.mkdir(parents=True, exist_ok=True)
    other_agent_dir.mkdir(parents=True, exist_ok=True)
    (target_agent_dir / "run.py").write_text("print('target')\n", encoding="utf-8")
    (other_agent_dir / "run.py").write_text("print('other')\n", encoding="utf-8")

    lockfile_path = tmp_path / "feature74-lock.yaml"
    monkeypatch.setenv("KINNOO_LOCKFILE_PATH", str(lockfile_path))
    lockfile_path.write_text(
        (
            "lock_version: 1\n"
            "locked_at: 2026-03-30T00:00:00Z\n"
            "platform:\n"
            "  python: 3.12.0\n"
            "  os: darwin-arm64\n"
            "agents:\n"
            "  feature74-agent:\n"
            "    version: 1.0.0\n"
            "    source: archive-file\n"
            "    archive_sha256: aaa\n"
            "    installed_at: 2026-03-30T00:00:00Z\n"
            "  other-agent:\n"
            "    version: 1.0.0\n"
            "    source: archive-file\n"
            "    archive_sha256: bbb\n"
            "    installed_at: 2026-03-30T00:00:00Z\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    uninstall_exit_code = uninstall_command.uninstall_agent(
        target="feature74-agent",
        install_root_arg=str(install_root),
    )
    assert uninstall_exit_code == 0
    assert not target_agent_dir.exists()
    assert other_agent_dir.exists()

    updated_lockfile = yaml.safe_load(lockfile_path.read_text(encoding="utf-8"))
    assert isinstance(updated_lockfile, dict)
    updated_agents = updated_lockfile.get("agents")
    assert isinstance(updated_agents, dict)
    assert "feature74-agent" not in updated_agents
    assert "other-agent" in updated_agents

    uninstall_trace_path = install_root / ".kinnoo" / "uninstall-trace.jsonl"
    assert uninstall_trace_path.exists()
    uninstall_trace_lines = uninstall_trace_path.read_text(encoding="utf-8").strip().splitlines()
    assert uninstall_trace_lines
    latest_trace = json.loads(uninstall_trace_lines[-1])
    assert latest_trace.get("event") == "uninstall"
    assert latest_trace.get("agent") == "feature74-agent"
    assert latest_trace.get("removed_from_lockfile") is True

    missing_exit_code = uninstall_command.uninstall_agent(
        target="feature74-agent",
        install_root_arg=str(install_root),
    )
    captured = capsys.readouterr()
    combined_output = f"{captured.out}\n{captured.err}"
    assert missing_exit_code == 1
    assert "Nothing to uninstall for target 'feature74-agent'" in combined_output


def _node_manifest_yaml(package_manager: str | None = None) -> str:
    package_manager_line = ""
    if package_manager is not None:
        package_manager_line = f"  package_manager: {package_manager}\n"

    return (
        "name: feature31-node-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.js\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: nodejs\n"
        f"{package_manager_line}"
        "  version: \">=22\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )


@pytest.mark.integration
def test_feature31_node_dependency_install_npm_and_pnpm(monkeypatch, tmp_path, capsys):
    from kinnoo import install_command

    monkeypatch.setattr(
        install_command,
        "check_node_runtime_constraint",
        lambda _constraint: (True, "runtime version check passed: current Node 22.0.0 satisfies runtime.version '>=22'"),
    )

    def _fake_package_manager_check(package_manager: str):
        if package_manager == "pnpm":
            return True, "dependency readiness check passed: node package manager 'pnpm' is available at /mock/pnpm"
        return True, "dependency readiness check passed: node package manager 'npm' is available at /mock/npm"

    monkeypatch.setattr(
        install_command,
        "check_node_package_manager_availability",
        _fake_package_manager_check,
    )

    calls: list[tuple[list[str], Path | None]] = []
    state = {"fail_pnpm": False}

    class _Completed:
        def __init__(self, returncode: int, stderr_text: str = ""):
            self.returncode = returncode
            self.stderr = stderr_text
            self.stdout = ""

    def _fake_run(command, *args, **kwargs):
        del args
        cwd = kwargs.get("cwd")
        calls.append((list(command), cwd))
        executable = Path(command[0]).name
        if executable == "npm":
            return _Completed(0)
        if executable == "pnpm":
            if state["fail_pnpm"]:
                return _Completed(12, "pnpm simulated failure")
            return _Completed(0)
        return _Completed(0)

    monkeypatch.setattr(install_command.subprocess, "run", _fake_run)

    # Scenario 1: runtime.package_manager omitted -> defaults to npm.
    npm_archive = tmp_path / "feature31-node-npm.kno"
    make_dummy_kno_archive(
        npm_archive,
        files={
            "kinnoo.yaml": _node_manifest_yaml(),
            "run.js": "console.log('ok')\n",
            "package.json": '{"name":"feature31-node-agent","version":"1.0.0"}\n',
        },
    )
    npm_target = tmp_path / "installed-npm"
    npm_result = install_command.install_agent(
        archive_path=str(npm_archive),
        target_dir_arg=str(npm_target),
        assume_yes=True,
    )
    assert npm_result == 0
    assert (["npm", "install"], npm_target) in calls

    # Scenario 2: runtime.package_manager set to pnpm -> use pnpm install.
    pnpm_archive = tmp_path / "feature31-node-pnpm.kno"
    make_dummy_kno_archive(
        pnpm_archive,
        files={
            "kinnoo.yaml": _node_manifest_yaml("pnpm"),
            "run.js": "console.log('ok')\n",
            "package.json": '{"name":"feature31-node-agent","version":"1.0.0"}\n',
        },
    )
    pnpm_target = tmp_path / "installed-pnpm"
    pnpm_result = install_command.install_agent(
        archive_path=str(pnpm_archive),
        target_dir_arg=str(pnpm_target),
        assume_yes=True,
    )
    assert pnpm_result == 0
    assert (["pnpm", "install"], pnpm_target) in calls

    # Scenario 3: package-manager install failure returns actionable error output.
    state["fail_pnpm"] = True
    pnpm_fail_archive = tmp_path / "feature31-node-pnpm-fail.kno"
    make_dummy_kno_archive(
        pnpm_fail_archive,
        files={
            "kinnoo.yaml": _node_manifest_yaml("pnpm"),
            "run.js": "console.log('ok')\n",
            "package.json": '{"name":"feature31-node-agent","version":"1.0.0"}\n',
        },
    )
    pnpm_fail_target = tmp_path / "installed-pnpm-fail"
    pnpm_fail_result = install_command.install_agent(
        archive_path=str(pnpm_fail_archive),
        target_dir_arg=str(pnpm_fail_target),
        assume_yes=True,
    )
    assert pnpm_fail_result != 0
    captured = capsys.readouterr()
    assert "Node dependency installation failed while running 'pnpm install'" in captured.err
    assert "pnpm simulated failure" in captured.err


def test_feature35_install_state_overwrite_warning_and_force(tmp_path):
    """Feature35 test294 (deprecated): install rejects manifests that declare unsupported state_dirs."""
    archive_path = tmp_path / "feature35-state-restore.kno"
    make_dummy_kno_archive(
        archive_path,
        files={
            "kinnoo.yaml": (
                "name: feature35-agent\n"
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
                "state_dirs:\n"
                "  - memory\n"
            ),
            "run.py": "print('hello')\n",
            "requirements.txt": "",
            "memory/existing.txt": "keep-me\n",
            "state_snapshots/memory/from_snapshot.txt": "snapshot-state\n",
        },
    )

    target_no_overwrite = tmp_path / "installed-no-overwrite"
    result_no_overwrite = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_no_overwrite),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    combined_output = f"{result_no_overwrite.stdout}\n{result_no_overwrite.stderr}"
    assert result_no_overwrite.returncode != 0, "Expected install to fail for deprecated state_dirs"
    assert "Field 'state_dirs' is not supported" in combined_output


def test_feature40_install_signature_verification_gate(tmp_path):
    from src.kinnoo.signing import create_detached_signature_artifacts, generate_ed25519_keypair

    private_key_path = tmp_path / "publisher-private.pem"
    public_key_path = tmp_path / "publisher-public.pem"
    generate_ed25519_keypair(private_key_path=private_key_path, public_key_path=public_key_path)

    valid_archive = tmp_path / "feature40-signed-valid.kno"
    make_dummy_kno_archive(valid_archive)
    create_detached_signature_artifacts(
        archive_path=valid_archive,
        private_key_path=private_key_path,
    )

    valid_target = tmp_path / "installed-feature40-valid"
    valid_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(valid_archive),
            str(valid_target),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    valid_output = f"{valid_result.stdout}\n{valid_result.stderr}"
    assert valid_result.returncode == 0, valid_output
    assert "Archive signature verified" in valid_output
    assert (valid_target / "kinnoo.yaml").exists()

    invalid_archive = tmp_path / "feature40-signed-invalid.kno"
    make_dummy_kno_archive(invalid_archive)
    create_detached_signature_artifacts(
        archive_path=invalid_archive,
        private_key_path=private_key_path,
    )

    invalid_signature_metadata_path = Path(f"{invalid_archive}.sig.json")
    invalid_metadata = json.loads(invalid_signature_metadata_path.read_text(encoding="utf-8"))
    invalid_metadata["signature_base64"] = base64.b64encode(b"feature40-invalid-signature").decode("ascii")
    invalid_signature_metadata_path.write_text(
        json.dumps(invalid_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    invalid_target = tmp_path / "installed-feature40-invalid"
    invalid_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(invalid_archive),
            str(invalid_target),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    invalid_output = f"{invalid_result.stdout}\n{invalid_result.stderr}"
    assert invalid_result.returncode != 0
    assert "Signature verification failed" in invalid_output
    assert "Archive authenticity could not be verified" in invalid_output


def test_install_strict_embedded_signature_without_detached_sidecars(tmp_path):
    private_key_path = tmp_path / "publisher-private.pem"
    public_key_path = tmp_path / "publisher-public.pem"

    keygen_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "keygen",
            "--private-key",
            str(private_key_path),
            "--public-key",
            str(public_key_path),
        ],
        capture_output=True,
        text=True,
    )
    assert keygen_result.returncode == 0, f"{keygen_result.stdout}\n{keygen_result.stderr}"

    agent_dir = tmp_path / "strict-embedded-agent"
    agent_dir.mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        (
            "name: strict-embedded-agent\n"
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
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('strict embedded signature')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    archive_root = tmp_path / "archive-root"
    pack_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "pack",
            str(agent_dir),
            "--sign",
            str(private_key_path),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "KINNOO_ARCHIVE_ROOT": str(archive_root)},
    )
    assert pack_result.returncode == 0, f"{pack_result.stdout}\n{pack_result.stderr}"

    archive_path = archive_root / "strict-embedded-agent" / "1.0.0" / "strict-embedded-agent.kno"
    assert archive_path.exists()

    detached_signature_path = Path(f"{archive_path}.sig")
    detached_signature_metadata_path = Path(f"{archive_path}.sig.json")
    assert detached_signature_path.exists()
    assert detached_signature_metadata_path.exists()

    detached_signature_path.unlink()
    detached_signature_metadata_path.unlink()

    install_target = tmp_path / "installed-strict-embedded"
    install_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(install_target),
            "--strict",
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    install_output = f"{install_result.stdout}\n{install_result.stderr}"
    assert install_result.returncode == 0, install_output
    assert "Detached signature artifacts not found; falling back to embedded META-INF/signature.json verification." in install_output
    assert "[kinnoo install] Embedded signature verified." in install_output
    assert install_output.index("[kinnoo install] Embedded signature verified.") < install_output.index(
        "[kinnoo install] Install summary:"
    )
    assert "UNVERIFIED PUBLISHER" not in install_output


def test_install_non_strict_embedded_signature_prompts_without_unverified_label(tmp_path):
    private_key_path = tmp_path / "publisher-private.pem"
    public_key_path = tmp_path / "publisher-public.pem"

    keygen_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "keygen",
            "--private-key",
            str(private_key_path),
            "--public-key",
            str(public_key_path),
        ],
        capture_output=True,
        text=True,
    )
    assert keygen_result.returncode == 0, f"{keygen_result.stdout}\n{keygen_result.stderr}"

    agent_dir = tmp_path / "non-strict-embedded-agent"
    agent_dir.mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        (
            "name: non-strict-embedded-agent\n"
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
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('non-strict embedded signature')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    archive_root = tmp_path / "archive-root"
    pack_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "pack",
            str(agent_dir),
            "--sign",
            str(private_key_path),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "KINNOO_ARCHIVE_ROOT": str(archive_root)},
    )
    assert pack_result.returncode == 0, f"{pack_result.stdout}\n{pack_result.stderr}"

    archive_path = archive_root / "non-strict-embedded-agent" / "1.0.0" / "non-strict-embedded-agent.kno"
    assert archive_path.exists()

    detached_signature_path = Path(f"{archive_path}.sig")
    detached_signature_metadata_path = Path(f"{archive_path}.sig.json")
    assert detached_signature_path.exists()
    assert detached_signature_metadata_path.exists()

    detached_signature_path.unlink()
    detached_signature_metadata_path.unlink()

    install_target = tmp_path / "installed-non-strict-embedded"
    install_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(install_target),
        ],
        input="n\n",
        capture_output=True,
        text=True,
    )
    install_output = f"{install_result.stdout}\n{install_result.stderr}"
    assert install_result.returncode != 0
    assert "Warning: Signature metadata found, but signature verification is skipped in non-strict mode." in install_output
    assert "[kinnoo install] Continue without signature verification? [y/N]:" in install_output
    assert "Install aborted: signature verification not approved." in install_output
    assert "UNVERIFIED PUBLISHER" not in install_output


def _create_feature65_openclaw_archive(tmp_path: Path, name: str = "feature65-openclaw-direct") -> Path:
    archive_path = tmp_path / f"{name}.kno"
    make_dummy_kno_archive(
        archive_path,
        files={
            "kinnoo.yaml": (
                f"name: {name}\n"
                "version: 1.0.0\n"
                "type: openclaw-skill\n"
                "framework: openclaw\n"
                "entrypoint: index.js\n"
                "runtime:\n"
                "  type: daemon\n"
                "  language: nodejs\n"
                "  version: \">=20.0.0\"\n"
                "dependencies: []\n"
                "inputs:\n"
                "  type: text\n"
                "outputs:\n"
                "  type: text\n"
                "provenance:\n"
                "  source_registry: clawhub\n"
                "  source_slug: sample/skill\n"
                "  source_version: 1.0.0\n"
            ),
            "index.js": "console.log('skill run')\n",
        },
    )
    return archive_path


def test_feature80_openclaw_install_extracts_to_workspace_and_registers(monkeypatch, tmp_path):
    from kinnoo import install_command

    archive_path = _create_feature65_openclaw_archive(tmp_path, name="feature80-openclaw")
    monkeypatch.setenv("HOME", str(tmp_path))

    class _PreflightOK:
        ok = True
        message = "ok"

    monkeypatch.setattr(
        install_command,
        "run_openclaw_preflight_for_command",
        lambda _command: _PreflightOK(),
    )
    monkeypatch.setattr(
        install_command,
        "check_openclaw_cli_constraint",
        lambda _version: (True, "openclaw_cli_precheck_ok", "ok"),
    )

    captured_commands: list[list[str]] = []

    class _SuccessCompleted:
        returncode = 0
        stderr = ""
        stdout = "registered"

    def _capture_subprocess_run(command, *args, **kwargs):
        captured_commands.append([str(part) for part in command])
        return _SuccessCompleted()

    monkeypatch.setattr(install_command.subprocess, "run", _capture_subprocess_run)

    install_exit = install_command.install_agent(
        archive_path=str(archive_path),
        assume_yes=True,
        allow_unverified_publisher=True,
    )

    assert install_exit == 0
    expected_workspace = tmp_path / ".openclaw" / "workspace-feature80-openclaw"
    assert expected_workspace.exists()
    assert (expected_workspace / "kinnoo.yaml").exists()
    trace_payload = json.loads((expected_workspace / ".kinnoo" / "install-trace.json").read_text(encoding="utf-8"))
    assert trace_payload["delegated_install"]["agent"] == "feature80-openclaw"
    assert trace_payload["delegated_install"]["workspace"] == str(expected_workspace)
    assert trace_payload["delegated_install"]["command"] == [
        "openclaw",
        "agents",
        "add",
        "feature80-openclaw",
        "--workspace",
        str(expected_workspace),
    ]

    assert captured_commands == [
        [
            "openclaw",
            "agents",
            "add",
            "feature80-openclaw",
            "--workspace",
            str(expected_workspace),
        ]
    ]


def test_feature80_openclaw_validation_happens_before_delegation(monkeypatch, tmp_path):
    from kinnoo import install_command

    archive_path = tmp_path / "feature80-openclaw-invalid.kno"
    make_dummy_kno_archive(
        archive_path,
        files={
            "kinnoo.yaml": (
                "name: feature80-openclaw-invalid\n"
                "version: 1.0.0\n"
                "type: openclaw-skill\n"
                "framework: openclaw\n"
                "runtime:\n"
                "  type: daemon\n"
                "  language: nodejs\n"
                "  version: \">=20.0.0\"\n"
                "dependencies: []\n"
                "inputs:\n"
                "  type: text\n"
                "outputs:\n"
                "  type: text\n"
            ),
            "index.js": "console.log('invalid')\n",
        },
    )

    monkeypatch.setenv("HOME", str(tmp_path))

    class _PreflightOK:
        ok = True
        message = "ok"

    monkeypatch.setattr(
        install_command,
        "run_openclaw_preflight_for_command",
        lambda _command: _PreflightOK(),
    )
    monkeypatch.setattr(
        install_command,
        "check_openclaw_cli_constraint",
        lambda _version: (True, "openclaw_cli_precheck_ok", "ok"),
    )

    invoked = {"called": False}

    def _unexpected_subprocess_run(*args, **kwargs):
        invoked["called"] = True
        raise AssertionError("OpenClaw delegated subprocess should not run for invalid manifest")

    monkeypatch.setattr(install_command.subprocess, "run", _unexpected_subprocess_run)

    install_exit = install_command.install_agent(
        archive_path=str(archive_path),
        assume_yes=True,
        allow_unverified_publisher=True,
    )
    assert install_exit != 0
    assert invoked["called"] is False


def test_feature65_delegated_install_checks_and_traces(monkeypatch, tmp_path, capsys):
    from kinnoo import install_command

    archive_path = _create_feature65_openclaw_archive(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))

    class _PreflightOK:
        ok = True
        message = "ok"

    monkeypatch.setattr(
        install_command,
        "run_openclaw_preflight_for_command",
        lambda _command: _PreflightOK(),
    )
    workspace_target = tmp_path / ".openclaw" / "workspace-feature65-openclaw-direct"

    # Success path: delegated flow should preserve kinnoo validation and emit success trace category.
    monkeypatch.setattr(
        install_command,
        "check_openclaw_cli_constraint",
        lambda _version: (
            True,
            "openclaw_cli_precheck_ok",
            "delegated install precheck passed: OpenClaw CLI version 0.4.0 satisfies >= 0.2.0",
        ),
    )

    class _SuccessCompleted:
        returncode = 0
        stderr = ""
        stdout = "delegated-ok"

    monkeypatch.setattr(install_command.subprocess, "run", lambda *args, **kwargs: _SuccessCompleted())

    success_exit = install_command.install_agent(
        archive_path=str(archive_path),
        assume_yes=True,
        allow_unverified_publisher=True,
        minimum_openclaw_version="0.2.0",
    )
    success_output = capsys.readouterr()
    assert success_exit == 0
    assert "Manifest validated successfully" in success_output.out
    success_trace_path = workspace_target / ".kinnoo" / "install-trace.json"
    assert success_trace_path.exists()
    success_trace = json.loads(success_trace_path.read_text(encoding="utf-8"))
    assert success_trace["decision"] == {
        "outcome": "allowed",
        "category": "openclaw_cli_delegated_success",
        "reason": "openclaw_cli_delegated_install_succeeded",
        "delegated_exit_code": 0,
    }

    # Missing runtime / unsupported version categories are emitted deterministically.
    monkeypatch.setattr(
        install_command,
        "check_openclaw_cli_constraint",
        lambda _version: (
            False,
            "openclaw_cli_missing",
            "delegated install precheck failed: OpenClaw CLI was not found in PATH. Install OpenClaw CLI and retry.",
        ),
    )
    missing_exit = install_command.install_agent(
        archive_path=str(archive_path),
        assume_yes=True,
        allow_unverified_publisher=True,
        force=True,
        minimum_openclaw_version="0.2.0",
    )
    missing_output = capsys.readouterr()
    assert missing_exit != 0
    assert "category=openclaw_cli_missing" in missing_output.err
    missing_trace = json.loads((workspace_target / ".kinnoo" / "install-trace.json").read_text(encoding="utf-8"))
    assert missing_trace["decision"]["outcome"] == "blocked"
    assert missing_trace["decision"]["category"] == "openclaw_cli_missing"

    monkeypatch.setattr(
        install_command,
        "check_openclaw_cli_constraint",
        lambda _version: (
            False,
            "openclaw_cli_version_unsupported",
            "delegated install precheck failed: OpenClaw CLI version 0.1.0 is below required >= 0.2.0. Upgrade OpenClaw CLI and retry.",
        ),
    )
    unsupported_exit = install_command.install_agent(
        archive_path=str(archive_path),
        assume_yes=True,
        allow_unverified_publisher=True,
        force=True,
        minimum_openclaw_version="0.2.0",
    )
    unsupported_output = capsys.readouterr()
    assert unsupported_exit != 0
    assert "category=openclaw_cli_version_unsupported" in unsupported_output.err
    unsupported_trace = json.loads(
        (workspace_target / ".kinnoo" / "install-trace.json").read_text(encoding="utf-8")
    )
    assert unsupported_trace["decision"]["outcome"] == "blocked"
    assert unsupported_trace["decision"]["category"] == "openclaw_cli_version_unsupported"

    # Delegated backend non-zero exits are wrapped with deterministic failure category.
    monkeypatch.setattr(
        install_command,
        "check_openclaw_cli_constraint",
        lambda _version: (
            True,
            "openclaw_cli_precheck_ok",
            "delegated install precheck passed: OpenClaw CLI version 0.4.0 satisfies >= 0.2.0",
        ),
    )

    class _BackendFailureCompleted:
        returncode = 9
        stderr = "simulated delegated backend failure"
        stdout = ""

    monkeypatch.setattr(
        install_command.subprocess,
        "run",
        lambda *args, **kwargs: _BackendFailureCompleted(),
    )

    backend_fail_exit = install_command.install_agent(
        archive_path=str(archive_path),
        assume_yes=True,
        allow_unverified_publisher=True,
        force=True,
        minimum_openclaw_version="0.2.0",
    )
    backend_fail_output = capsys.readouterr()
    assert backend_fail_exit == 9
    assert "category=openclaw_cli_delegated_nonzero_exit" in backend_fail_output.err
    assert "simulated delegated backend failure" in backend_fail_output.err

    backend_fail_trace = json.loads(
        (workspace_target / ".kinnoo" / "install-trace.json").read_text(encoding="utf-8")
    )
    assert backend_fail_trace["decision"] == {
        "outcome": "failed",
        "category": "openclaw_cli_delegated_nonzero_exit",
        "reason": "openclaw_cli_delegated_install_failed:openclaw_cli_delegated_nonzero_exit",
        "delegated_exit_code": 9,
    }
