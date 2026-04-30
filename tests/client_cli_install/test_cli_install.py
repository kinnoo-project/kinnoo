import subprocess
import sys
import zipfile
import os
import json
import hashlib
import base64
from pathlib import Path

from tests.helpers import run_command

# Test51: kinnoo install usage error

def test_install_missing_archive_prints_usage():
    result = run_command("install")
    assert result.returncode != 0
    assert "Usage: kinnoo install" in result.stderr


def _create_valid_archive(tmp_path: Path) -> tuple[Path, Path]:
    archive_path = tmp_path / "test-agent.kno"
    expected_dir = tmp_path / "test-agent"
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
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('hello')\n")
    return archive_path, expected_dir


def _create_openclaw_agent_archive(tmp_path: Path, agent_name: str = "test-openclaw-agent") -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "framework: openclaw\n"
        "runtime:\n"
        "  type: daemon\n"
        "  language: nodejs\n"
        "  version: \">=18\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('openclaw-agent')\n")
        archive.writestr("package.json", '{"name":"feature115-openclaw","version":"1.0.0"}\n')
        archive.writestr("requirements.txt", "")
    return archive_path


def test_install_deprecated_options_removed(tmp_path: Path) -> None:
    deprecated_invocations = [
        ["--state-overwrite"],
        ["--allow-vulnerable"],
        ["--ignore-scripts"],
        ["--openclaw-min-version", "1.0"],
        ["--openclaw-skill", "test-skill"],
    ]

    for extra_args in deprecated_invocations:
        result = run_command("install", "dummy.kno", *extra_args)
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode != 0
        assert "unrecognized arguments" in output


def test_install_openclaw_default_path(tmp_path: Path) -> None:
    archive = _create_openclaw_agent_archive(tmp_path, agent_name="feature115-openclaw")
    home_dir = tmp_path / "home"

    default_env = {**os.environ, "HOME": str(home_dir)}
    default_result = run_command("install", str(archive), "--yes", env=default_env)
    default_output = f"{default_result.stdout}\n{default_result.stderr}"
    assert default_result.returncode == 0, default_output

    default_workspace = home_dir / ".openclaw" / "workspace-feature115-openclaw"
    assert default_workspace.exists(), default_output
    assert (default_workspace / "kinnoo.yaml").exists(), default_output

    custom_target = tmp_path / "custom-openclaw-workspace"
    custom_result = run_command(
        "install", str(archive), str(custom_target), "--yes", env=default_env
    )
    custom_output = f"{custom_result.stdout}\n{custom_result.stderr}"
    assert custom_result.returncode == 0, custom_output
    assert custom_target.exists(), custom_output
    assert (custom_target / "kinnoo.yaml").exists(), custom_output


def test_install_json_output(tmp_path: Path) -> None:
    archive, _ = _create_valid_archive(tmp_path)
    target_dir = tmp_path / "json-install-target"

    json_result = run_command("install", str(archive), str(target_dir), "--json", "-y")
    output = f"{json_result.stdout}\n{json_result.stderr}"
    assert json_result.returncode == 0, output

    payload = json.loads(json_result.stdout.strip())
    assert payload["agent_name"] == "test-agent"
    assert payload["agent_version"] == "1.0.0"
    assert payload["source_archive_path"] == str(archive)
    assert payload["install_path"] == str(target_dir.resolve())
    assert payload["success"] is True
    assert payload["exit_code"] == 0
    assert payload["error_code"] is None
    assert payload["error_message"] is None

    missing_yes_result = run_command("install", str(archive), "--json")
    missing_yes_output = f"{missing_yes_result.stdout}\n{missing_yes_result.stderr}"
    assert missing_yes_result.returncode != 0
    assert "--json requires -y" in missing_yes_output


def test_import_class_only_wrapper(tmp_path: Path) -> None:
    """Feature47 test385: class-only import flow can generate run.py wrapper."""
    agent_dir = tmp_path / "class-only-import-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "base.py").write_text(
        "from langchain.agents import BaseSingleActionAgent\n\n"
        "class MyAgent(BaseSingleActionAgent):\n"
        "    pass\n",
        encoding="utf-8",
    )

    # Prompt flow:
    # 1) Proceed with detected values? -> y
    # 2) Generate class-based run.py wrapper entrypoint? -> y
    result = run_command("import", str(agent_dir), "--force", cwd=tmp_path, input_text="y\ny\n")

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    generated_wrapper = agent_dir / "run.py"
    assert generated_wrapper.exists()
    wrapper_source = generated_wrapper.read_text(encoding="utf-8")
    assert "from base import MyAgent" in wrapper_source

    manifest_path = agent_dir / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text


def test_import_infer_requirements(tmp_path: Path) -> None:
    """Feature47 test391: import can generate requirements.txt from inferred imports."""
    agent_dir = tmp_path / "infer-reqs-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "main.py").write_text(
        "import openai\n"
        "import httpx\n"
        "import sys\n\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1])\n",
        encoding="utf-8",
    )

    result = run_command("import", str(agent_dir), "--force", cwd=tmp_path, input_text="y\ny\n")

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    requirements_path = agent_dir / "requirements.txt"
    assert requirements_path.exists()
    requirements_lines = requirements_path.read_text(encoding="utf-8").splitlines()
    assert "openai" in requirements_lines
    assert "httpx" in requirements_lines


def test_import_input_detection_yaml(tmp_path: Path) -> None:
    """Feature47 test395: import writes inputs.required=false for hardcoded agent input."""
    agent_dir = tmp_path / "hardcoded-input-import-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "main.py").write_text(
        "from agents import Runner, Agent\n"
        "agent = Agent(name='demo')\n"
        "result = Runner.run_sync(agent, 'hardcoded hello')\n"
        "print(result)\n",
        encoding="utf-8",
    )

    result = run_command("import", str(agent_dir), "--force", cwd=tmp_path, input_text="y\n")

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "inputs:" in manifest_text
    assert "required: false" in manifest_text


def test_import_service_detection_yaml(tmp_path: Path) -> None:
    """Feature47 test397: kinnoo import includes detected services in generated manifest."""
    agent_dir = tmp_path / "service-import-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "main.py").write_text(
        "import ollama\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )

    result = run_command("import", str(agent_dir), "--force", cwd=tmp_path, input_text="y\n")

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "services:" in manifest_text
    assert "name: ollama" in manifest_text


def test_install_delegates_to_install_command(tmp_path):
    cli_source = Path("src/kinnoo/cli.py").read_text()
    install_branch_start = cli_source.find('elif args.command == "install":')
    install_branch_end = cli_source.find('elif args.command == "pack":')
    install_branch = cli_source[install_branch_start:install_branch_end]

    assert "install_command import install_agent" in install_branch
    assert "install_agent(" in install_branch
    assert "extractall(" not in install_branch
    assert "Manifest validation failed" not in install_branch

    archive_path, expected_dir = _create_valid_archive(tmp_path)
    result = run_command("install", str(archive_path), "--yes")

    assert result.returncode == 0, result.stderr
    assert expected_dir.exists()
    assert (expected_dir / "kinnoo.yaml").exists()


def _create_archive_with_missing_required_wheel(tmp_path: Path) -> Path:
    agent_dir = tmp_path / "fallback-agent-src"
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: fallback-agent
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
  type: string
outputs:
  type: string
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('fallback-ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\n")

    wheels_dir = agent_dir / "wheels"
    wheels_dir.mkdir()
    wheel_build = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "requests==2.31.0",
            "--wheel-dir",
            str(wheels_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert wheel_build.returncode == 0, wheel_build.stderr

    requests_wheels = sorted(wheels_dir.glob("requests-*.whl"))
    assert requests_wheels, "Expected requests wheel to exist before removal"
    requests_wheels[0].unlink()

    archive_path = tmp_path / "fallback-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.write(agent_dir / "kinnoo.yaml", arcname="kinnoo.yaml")
        archive.write(agent_dir / "run.py", arcname="run.py")
        archive.write(agent_dir / "requirements.txt", arcname="requirements.txt")
        for wheel in wheels_dir.glob("*.whl"):
            archive.write(wheel, arcname=f"wheels/{wheel.name}")

    return archive_path


def test_install_falls_back_to_pypi_when_wheel_missing(tmp_path):
    archive_path = _create_archive_with_missing_required_wheel(tmp_path)
    target_dir = tmp_path / "installed-fallback-agent"

    result = run_command("install", str(archive_path), str(target_dir), "--yes")

    assert result.returncode == 0, (
        "Expected install to succeed via PyPI fallback when a required wheel is missing. "
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Missing packaged wheels for dependencies: requests" in result.stderr
    assert "Falling back to PyPI; internet access is required." in result.stderr

    python_exe = target_dir / ".venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = target_dir / ".venv" / "Scripts" / "python.exe"

    import_check = subprocess.run(
        [str(python_exe), "-c", "import requests; print(requests.__version__)"],
        capture_output=True,
        text=True,
    )
    assert import_check.returncode == 0, import_check.stderr
    assert "2.31.0" in import_check.stdout


def _create_packed_archive_with_complete_transitive_wheels(tmp_path: Path, agent_name: str = "offline-ready-agent") -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: {agent_name}
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
  type: string
outputs:
  type: string
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('offline-ready-ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\nhttpx==0.27.0\n")

    archive_root = tmp_path / "archive-root"
    pack_env = dict(os.environ)
    pack_env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    pack_result = run_command("pack", str(agent_dir), env=pack_env)
    assert pack_result.returncode == 0, (
        "Expected pack to succeed for offline-ready fixture. "
        f"STDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    archive_path = archive_root / agent_name / "1.0.0" / f"{agent_name}.kno"
    assert archive_path.exists(), (
        "Expected packed archive at canonical archive path. "
        f"STDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    return archive_path


def test_install_offline_succeeds_with_complete_wheels(tmp_path):
    # [agent] test69 validates AC5: complete bundled wheel sets should install
    # without network fallback when offline mode is explicitly enabled.
    archive_path = _create_packed_archive_with_complete_transitive_wheels(tmp_path)
    target_dir = tmp_path / "installed-offline-ready-agent"

    offline_env = dict(os.environ)
    offline_env["PIP_NO_INDEX"] = "1"
    offline_env["KINNOO_OFFLINE"] = "1"

    install_result = run_command(
        "install",
        str(archive_path),
        str(target_dir),
        "--yes",
        "--allow-unverified-publisher",
        env=offline_env,
    )
    assert install_result.returncode == 0, (
        "Expected offline install to succeed with complete wheels. "
        f"STDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
    )
    assert "Falling back to PyPI" not in install_result.stderr

    python_exe = target_dir / ".venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = target_dir / ".venv" / "Scripts" / "python.exe"

    dependency_check = subprocess.run(
        [str(python_exe), "-c", "import requests, httpx; print('ok')"],
        capture_output=True,
        text=True,
    )
    assert dependency_check.returncode == 0, dependency_check.stderr
    assert dependency_check.stdout.strip() == "ok"


def _create_node_archive(
    tmp_path: Path,
    agent_name: str = "feature37-node-agent",
    with_lifecycle_scripts: bool = False,
) -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
        "version: 1.0.0\n"
        "entrypoint: index.mjs\n"
        "runtime:\n"
        "  type: daemon\n"
        "  language: nodejs\n"
        "  version: \">=20.0.0\"\n"
        "  package_manager: npm\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )
    scripts_block = ""
    if with_lifecycle_scripts:
        scripts_block = (
            "  \"scripts\": {\n"
            "    \"prepare\": \"node ./scripts/prepare.mjs\",\n"
            "    \"postinstall\": \"node ./scripts/postinstall.mjs\"\n"
            "  },\n"
        )

    package_json = (
        "{\n"
        f"  \"name\": \"{agent_name}\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"type\": \"module\",\n"
        f"{scripts_block}"
        "  \"dependencies\": {\n"
        "    \"left-pad\": \"^1.3.0\"\n"
        "  }\n"
        "}\n"
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("index.mjs", "console.log('hello node')\n")
        archive.writestr("package.json", package_json)
    return archive_path


def _create_feature39_permissions_archive(tmp_path: Path, agent_name: str = "feature39-consent-agent") -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
        "permissions:\n"
        "  network: true\n"
        "  filesystem_scope: workspace-write\n"
        "  shell: false\n"
        "  browser: false\n"
        "  env_access:\n"
        "    - OPENAI_API_KEY\n"
        "    - KINNOO_ENV\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('feature39-install-ok')\n")

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")

    return archive_path


def _create_feature40_unsigned_archive_with_checksum(
    tmp_path: Path,
    agent_name: str = "feature40-unsigned-publisher-agent",
) -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
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

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('feature40-unsigned-ok')\n")

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    return archive_path


def _make_fake_node_toolchain(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)

    node_script = bin_dir / "node"
    node_script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo v20.11.1\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported node invocation >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    node_script.chmod(0o755)

    npm_script = bin_dir / "npm"
    npm_script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"install\" ]; then\n"
        "  if [ -n \"$KINNOO_TEST_NPM_ARGS_LOG\" ]; then\n"
        "    printf '%s\\n' \"$*\" > \"$KINNOO_TEST_NPM_ARGS_LOG\"\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"audit\" ] && [ \"$2\" = \"--json\" ]; then\n"
        "  cat <<'JSON'\n"
        "{\"metadata\":{\"vulnerabilities\":{\"critical\":1,\"high\":2,\"moderate\":3,\"low\":4}}}\n"
        "JSON\n"
        "  exit 1\n"
        "fi\n"
        "echo unsupported npm invocation >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    npm_script.chmod(0o755)


def _create_openclaw_skill_archive(tmp_path: Path, agent_name: str = "feature65-openclaw-skill") -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
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
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("index.js", "console.log('openclaw-skill')\n")
    return archive_path


def _make_fake_openclaw_cli(bin_dir: Path, *, version: str = "2026.3.31") -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    openclaw_script = bin_dir / "openclaw"
    openclaw_script.write_text(
        "#!/bin/sh\n"
        "if [ -n \"$KINNOO_TEST_OPENCLAW_ARGS_LOG\" ]; then\n"
        "  printf '%s\\n' \"$*\" >> \"$KINNOO_TEST_OPENCLAW_ARGS_LOG\"\n"
        "fi\n"
        "case \"$1\" in\n"
        "  --version)\n"
        f"    echo openclaw {version}\n"
        "    exit 0\n"
        "    ;;\n"
        "  agents)\n"
        "    if [ \"$2\" = \"list\" ]; then\n"
        "      echo '[]'\n"
        "      exit 0\n"
        "    fi\n"
        "    if [ \"$2\" = \"add\" ]; then\n"
        "      echo delegated register ok\n"
        "      exit 0\n"
        "    fi\n"
        "    ;;\n"
        "esac\n"
        "echo unsupported openclaw invocation >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    openclaw_script.chmod(0o755)
    return openclaw_script


def test_feature65_delegated_install_with_prechecks(tmp_path):
    archive_path = _create_openclaw_skill_archive(tmp_path)
    isolated_env = dict(os.environ)
    isolated_env["PATH"] = ""
    isolated_env["HOME"] = str(tmp_path)

    missing_cli_target = tmp_path / "feature65-openclaw-missing-cli"
    missing_cli_result = run_command(
        "install",
        str(archive_path),
        str(missing_cli_target),
        "--yes",
        env=isolated_env,
    )
    missing_cli_output = f"{missing_cli_result.stdout}\n{missing_cli_result.stderr}"
    assert missing_cli_result.returncode != 0, missing_cli_output
    assert "OpenClaw CLI not found in PATH" in missing_cli_output
    assert "openclaw preflight failed" in missing_cli_output

    fake_bin = tmp_path / "fake-openclaw-bin"
    _make_fake_openclaw_cli(fake_bin, version="2026.3.31")
    invocation_log = tmp_path / "openclaw-invocations.log"

    delegated_env = dict(os.environ)
    delegated_env["PATH"] = f"{fake_bin}{os.pathsep}{delegated_env.get('PATH', '')}"
    delegated_env["HOME"] = str(tmp_path)
    delegated_env["KINNOO_TEST_OPENCLAW_ARGS_LOG"] = str(invocation_log)

    delegated_target = tmp_path / "feature65-openclaw-delegated"
    delegated_result = run_command(
        "install",
        str(archive_path),
        str(delegated_target),
        "--yes",
        env=delegated_env,
    )
    delegated_output = f"{delegated_result.stdout}\n{delegated_result.stderr}"
    assert delegated_result.returncode == 0, delegated_output
    assert "Delegating workspace registration to OpenClaw CLI" in delegated_output
    assert "Workspace registration completed successfully" in delegated_output

    invocations = invocation_log.read_text(encoding="utf-8").splitlines()
    assert "--version" in invocations
    assert "agents add feature65-openclaw-skill --workspace" in "\n".join(invocations)

    delegated_workspace = delegated_target
    trace_path = delegated_workspace / ".kinnoo" / "install-trace.json"
    assert trace_path.exists(), delegated_output
    trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
    assert trace_payload["delegated_install"]["backend"] == "openclaw-cli"
    assert trace_payload["delegated_install"]["minimum_version"] == "0.1.0"
    assert trace_payload["delegated_install"]["agent"] == "feature65-openclaw-skill"
    assert trace_payload["delegated_install"]["workspace"] == str(delegated_workspace)
    assert trace_payload["decision"] == {
        "outcome": "allowed",
        "category": "openclaw_cli_delegated_success",
        "reason": "openclaw_cli_delegated_install_succeeded",
        "delegated_exit_code": 0,
    }


def test_feature80_openclaw_workspace_conflict_diagnostics(tmp_path):
    archive_path = _create_openclaw_skill_archive(tmp_path, agent_name="feature80-conflict")
    fake_bin = tmp_path / "fake-openclaw-bin-conflict"
    _make_fake_openclaw_cli(fake_bin, version="2026.3.31")

    existing_workspace = tmp_path / ".openclaw" / "workspace-feature80-conflict"
    existing_workspace.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    result = run_command("install", str(archive_path), "--yes", env=env)
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0, output
    assert "OpenClaw workspace already exists" in output
    assert "Re-run with --force" in output


def test_feature83_skill_install_existing_agent_slug_and_url(tmp_path, monkeypatch):
    from kinnoo import install_command

    fake_bin = tmp_path / "feature83-openclaw-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    invocation_log = tmp_path / "feature83-openclaw-invocations.log"
    workspace_path = tmp_path / ".openclaw" / "workspace-feature83-existing"
    workspace_path.mkdir(parents=True, exist_ok=True)

    openclaw_script = fake_bin / "openclaw"
    openclaw_script.write_text(
        "#!/bin/sh\n"
        "if [ -n \"$KINNOO_TEST_OPENCLAW_ARGS_LOG\" ]; then\n"
        "  printf '%s\\n' \"$*\" >> \"$KINNOO_TEST_OPENCLAW_ARGS_LOG\"\n"
        "fi\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo openclaw 2026.3.31\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"gateway\" ] && [ \"$2\" = \"status\" ] && [ \"$3\" = \"--require-rpc\" ]; then\n"
        "  echo gateway healthy\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"agents\" ] && [ \"$2\" = \"list\" ]; then\n"
        f"  echo '[{{\"id\":\"feature83-existing\",\"workspace\":\"{workspace_path}\"}}]'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"skills\" ] && [ \"$2\" = \"install\" ]; then\n"
        "  echo delegated skill install ok\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported invocation >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    openclaw_script.chmod(0o755)

    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_ARGS_LOG", str(invocation_log))

    slug_result = install_command.install_agent(
        archive_path="feature83-existing",
        assume_yes=True,
        openclaw_skill_identifier="owner/skill-slug",
    )
    assert slug_result == 0

    url_result = install_command.install_agent(
        archive_path="feature83-existing",
        assume_yes=True,
        openclaw_skill_identifier="https://clawhub.ai/owner/skill-slug",
    )
    assert url_result == 0

    invocations = invocation_log.read_text(encoding="utf-8")
    assert "agents list" in invocations
    assert f"skills install owner/skill-slug --workspace {workspace_path}" in invocations
    assert invocations.count(f"skills install owner/skill-slug --workspace {workspace_path}") >= 2


def test_feature83_missing_agent_preflight_and_outcome_diagnostics(tmp_path, monkeypatch, capsys):
    from kinnoo import install_command

    fake_bin = tmp_path / "feature83-openclaw-diagnostics-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    invocation_log = tmp_path / "feature83-openclaw-diagnostics.log"
    workspace_path = tmp_path / ".openclaw" / "workspace-feature83-diagnostics"
    workspace_path.mkdir(parents=True, exist_ok=True)

    openclaw_script = fake_bin / "openclaw"
    openclaw_script.write_text(
        "#!/bin/sh\n"
        "if [ -n \"$KINNOO_TEST_OPENCLAW_ARGS_LOG\" ]; then\n"
        "  printf '%s\\n' \"$*\" >> \"$KINNOO_TEST_OPENCLAW_ARGS_LOG\"\n"
        "fi\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo openclaw 2026.3.31\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"gateway\" ] && [ \"$2\" = \"status\" ] && [ \"$3\" = \"--require-rpc\" ]; then\n"
        "  if [ \"$KINNOO_TEST_OPENCLAW_GATEWAY_DOWN\" = \"1\" ]; then\n"
        "    echo gateway unavailable >&2\n"
        "    exit 6\n"
        "  fi\n"
        "  echo gateway healthy\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"agents\" ] && [ \"$2\" = \"list\" ]; then\n"
        "  if [ -n \"$KINNOO_TEST_OPENCLAW_AGENTS_JSON\" ]; then\n"
        "    echo \"$KINNOO_TEST_OPENCLAW_AGENTS_JSON\"\n"
        "  else\n"
        "    echo '[]'\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"skills\" ] && [ \"$2\" = \"install\" ]; then\n"
        "  if [ \"$KINNOO_TEST_OPENCLAW_SKILL_OUTCOME\" = \"already\" ]; then\n"
        "    echo already installed\n"
        "    exit 0\n"
        "  fi\n"
        "  if [ \"$KINNOO_TEST_OPENCLAW_SKILL_OUTCOME\" = \"not-found\" ]; then\n"
        "    echo skill not found >&2\n"
        "    exit 3\n"
        "  fi\n"
        "  echo skill install success\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported invocation >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    openclaw_script.chmod(0o755)

    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_ARGS_LOG", str(invocation_log))

    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_AGENTS_JSON", "[]")
    missing_agent_result = install_command.install_agent(
        archive_path="feature83-missing",
        assume_yes=True,
        openclaw_skill_identifier="owner/missing-skill",
    )
    missing_agent_captured = capsys.readouterr()
    missing_agent_output = f"{missing_agent_captured.out}\n{missing_agent_captured.err}"
    assert missing_agent_result != 0
    assert "Create/register the agent first and retry" in missing_agent_output

    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_GATEWAY_DOWN", "1")
    preflight_fail_result = install_command.install_agent(
        archive_path="feature83-diagnostics",
        assume_yes=True,
        openclaw_skill_identifier="owner/skill-a",
    )
    preflight_fail_captured = capsys.readouterr()
    preflight_fail_output = f"{preflight_fail_captured.out}\n{preflight_fail_captured.err}"
    assert preflight_fail_result != 0
    assert "category=openclaw_gateway_unhealthy" in preflight_fail_output
    monkeypatch.delenv("KINNOO_TEST_OPENCLAW_GATEWAY_DOWN", raising=False)

    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_AGENTS_JSON", (
        f"[{{\"id\":\"feature83-diagnostics\",\"workspace\":\"{workspace_path}\"}}]"
    ))
    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_SKILL_OUTCOME", "success")
    success_result = install_command.install_agent(
        archive_path="feature83-diagnostics",
        assume_yes=True,
        openclaw_skill_identifier="https://clawhub.ai/owner/skill-a",
    )
    success_captured = capsys.readouterr()
    success_output = f"{success_captured.out}\n{success_captured.err}"
    assert success_result == 0, success_output
    assert "outcome=success" in success_output

    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_SKILL_OUTCOME", "already")
    already_result = install_command.install_agent(
        archive_path="feature83-diagnostics",
        assume_yes=True,
        openclaw_skill_identifier="owner/skill-a",
    )
    already_captured = capsys.readouterr()
    already_output = f"{already_captured.out}\n{already_captured.err}"
    assert already_result == 0, already_output
    assert "outcome=already-installed" in already_output

    monkeypatch.setenv("KINNOO_TEST_OPENCLAW_SKILL_OUTCOME", "not-found")
    not_found_result = install_command.install_agent(
        archive_path="feature83-diagnostics",
        assume_yes=True,
        openclaw_skill_identifier="owner/skill-a",
    )
    not_found_captured = capsys.readouterr()
    not_found_output = f"{not_found_captured.out}\n{not_found_captured.err}"
    assert not_found_result != 0
    assert "category=openclaw_skill_not_found" in not_found_output

    invocations = invocation_log.read_text(encoding="utf-8")
    assert f"skills install owner/skill-a --workspace {workspace_path}" in invocations


def test_feature37_node_audit_severity_summary(tmp_path):
    node_archive = _create_node_archive(tmp_path)
    node_target_dir = tmp_path / "feature37-node-installed"

    fake_bin = tmp_path / "fake-bin"
    _make_fake_node_toolchain(fake_bin)

    node_env = dict(os.environ)
    node_env["PATH"] = f"{fake_bin}{os.pathsep}{node_env.get('PATH', '')}"

    node_result = run_command(
        "install",
        str(node_archive),
        str(node_target_dir),
        "--yes",
        "--allow-vulnerable",
        env=node_env,
    )

    node_output = f"{node_result.stdout}\n{node_result.stderr}"
    assert node_result.returncode == 0, node_output
    assert "Node audit severity summary: critical=1 high=2 moderate=3 low=4" in node_output

    python_archive, _ = _create_valid_archive(tmp_path)
    python_target_dir = tmp_path / "feature37-python-installed"
    python_result = run_command("install", str(python_archive), str(python_target_dir), "--yes")

    python_output = f"{python_result.stdout}\n{python_result.stderr}"
    assert python_result.returncode == 0, python_output
    assert "Node audit severity summary:" not in python_output


def test_feature37_critical_gate_default_block_and_allow_override(tmp_path):
    node_archive = _create_node_archive(tmp_path, agent_name="feature37-node-critical-gate")

    fake_bin = tmp_path / "fake-bin-critical"
    _make_fake_node_toolchain(fake_bin)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    blocked_target_dir = tmp_path / "feature37-node-critical-blocked"
    blocked_result = run_command("install", str(node_archive), str(blocked_target_dir), "--yes", env=env)
    blocked_output = f"{blocked_result.stdout}\n{blocked_result.stderr}"
    assert blocked_result.returncode != 0, blocked_output
    assert "Node audit severity summary: critical=1 high=2 moderate=3 low=4" in blocked_output
    assert "--allow-vulnerable" in blocked_output
    assert "Critical vulnerabilities were detected" in blocked_output

    allowed_target_dir = tmp_path / "feature37-node-critical-allowed"
    allowed_result = run_command(
        "install",
        str(node_archive),
        str(allowed_target_dir),
        "--yes",
        "--allow-vulnerable",
        env=env,
    )
    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output
    assert "Node audit severity summary: critical=1 high=2 moderate=3 low=4" in allowed_output
    assert "Continuing install despite critical vulnerabilities" in allowed_output


def test_feature37_lifecycle_scripts_warning_and_ignore_scripts_mode(tmp_path):
    node_archive = _create_node_archive(
        tmp_path,
        agent_name="feature37-node-lifecycle",
        with_lifecycle_scripts=True,
    )

    fake_bin = tmp_path / "fake-bin-lifecycle"
    _make_fake_node_toolchain(fake_bin)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    allowed_target_dir = tmp_path / "feature37-node-lifecycle-allowed"
    allowed_args_log = tmp_path / "npm-allowed-args.log"
    env["KINNOO_TEST_NPM_ARGS_LOG"] = str(allowed_args_log)
    allowed_result = run_command(
        "install",
        str(node_archive),
        str(allowed_target_dir),
        "--yes",
        "--allow-vulnerable",
        env=env,
    )
    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output
    assert "Detected Node lifecycle scripts in package.json: postinstall, prepare." in allowed_output
    assert "Lifecycle scripts are allowed and may execute during dependency installation." in allowed_output
    assert allowed_args_log.read_text(encoding="utf-8").strip() == "install"

    ignored_target_dir = tmp_path / "feature37-node-lifecycle-ignored"
    ignored_args_log = tmp_path / "npm-ignored-args.log"
    env["KINNOO_TEST_NPM_ARGS_LOG"] = str(ignored_args_log)
    ignored_result = run_command(
        "install",
        str(node_archive),
        str(ignored_target_dir),
        "--yes",
        "--allow-vulnerable",
        "--ignore-scripts",
        env=env,
    )
    ignored_output = f"{ignored_result.stdout}\n{ignored_result.stderr}"
    assert ignored_result.returncode == 0, ignored_output
    assert "Detected Node lifecycle scripts in package.json: postinstall, prepare." in ignored_output
    assert "Lifecycle scripts policy: ignored (--ignore-scripts enabled)." in ignored_output
    assert ignored_args_log.read_text(encoding="utf-8").strip() == "install --ignore-scripts"


def test_feature37_install_trace_captures_audit_and_decisions(tmp_path):
    node_archive = _create_node_archive(
        tmp_path,
        agent_name="feature37-node-trace",
        with_lifecycle_scripts=True,
    )

    fake_bin = tmp_path / "fake-bin-trace"
    _make_fake_node_toolchain(fake_bin)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    blocked_target_dir = tmp_path / "feature37-node-trace-blocked"
    blocked_result = run_command("install", str(node_archive), str(blocked_target_dir), "--yes", env=env)
    blocked_output = f"{blocked_result.stdout}\n{blocked_result.stderr}"
    assert blocked_result.returncode != 0, blocked_output

    blocked_trace_path = blocked_target_dir / ".kinnoo" / "install-trace.json"
    assert blocked_trace_path.exists(), blocked_output
    blocked_trace = json.loads(blocked_trace_path.read_text(encoding="utf-8"))
    assert blocked_trace["schema_version"] == "1.0"
    assert blocked_trace["runtime_language"] == "nodejs"
    assert blocked_trace["package_manager"] == "npm"
    assert blocked_trace["lifecycle_scripts"] == {
        "detected": True,
        "names": ["postinstall", "prepare"],
        "policy": "allowed",
    }
    assert blocked_trace["audit"]["severity_counts"] == {
        "critical": 1,
        "high": 2,
        "moderate": 3,
        "low": 4,
    }
    assert blocked_trace["decision"] == {
        "outcome": "blocked",
        "reason": "critical_vulnerabilities_blocked",
        "allow_vulnerable": False,
        "ignore_scripts": False,
    }

    allowed_target_dir = tmp_path / "feature37-node-trace-allowed"
    allowed_result = run_command(
        "install",
        str(node_archive),
        str(allowed_target_dir),
        "--yes",
        "--allow-vulnerable",
        "--ignore-scripts",
        env=env,
    )
    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output

    allowed_trace_path = allowed_target_dir / ".kinnoo" / "install-trace.json"
    assert allowed_trace_path.exists(), allowed_output
    allowed_trace = json.loads(allowed_trace_path.read_text(encoding="utf-8"))
    assert allowed_trace["schema_version"] == "1.0"
    assert allowed_trace["runtime_language"] == "nodejs"
    assert allowed_trace["package_manager"] == "npm"
    assert allowed_trace["lifecycle_scripts"] == {
        "detected": True,
        "names": ["postinstall", "prepare"],
        "policy": "ignored",
    }
    assert allowed_trace["audit"]["severity_counts"] == {
        "critical": 1,
        "high": 2,
        "moderate": 3,
        "low": 4,
    }
    assert allowed_trace["decision"] == {
        "outcome": "allowed",
        "reason": "critical_vulnerabilities_overridden",
        "allow_vulnerable": True,
        "ignore_scripts": True,
    }


def test_feature39_install_permission_summary_and_consent(tmp_path):
    permissions_archive = _create_feature39_permissions_archive(tmp_path)

    denied_target_dir = tmp_path / "feature39-consent-denied"
    denied_result = run_command(
        "install",
        str(permissions_archive),
        str(denied_target_dir),
        input_text="y\nn\n",
    )
    denied_output = f"{denied_result.stdout}\n{denied_result.stderr}"
    assert denied_result.returncode != 0, denied_output
    assert "[kinnoo install] Install summary:" in denied_output
    assert "- Permissions:" in denied_output
    assert "Network: allowed" in denied_output
    assert "Filesystem Scope: workspace-write" in denied_output
    assert "Shell: denied" in denied_output
    assert "Browser: denied" in denied_output
    assert "Env Access: OPENAI_API_KEY, KINNOO_ENV" in denied_output
    assert "Install aborted: permissions consent not granted." in denied_output

    accepted_target_dir = tmp_path / "feature39-consent-accepted"
    accepted_result = run_command(
        "install",
        str(permissions_archive),
        str(accepted_target_dir),
        input_text="y\ny\ny\n",
    )
    accepted_output = f"{accepted_result.stdout}\n{accepted_result.stderr}"
    assert accepted_result.returncode == 0, accepted_output
    assert "Allow requested permissions? [y/N]:" in accepted_output
    assert "Continue with install? [y/N]:" in accepted_output
    assert accepted_target_dir.exists(), accepted_output

    override_without_flag_target_dir = tmp_path / "feature39-consent-missing-override"
    override_without_flag_result = run_command(
        "install",
        str(permissions_archive),
        str(override_without_flag_target_dir),
        "--yes",
        "--allow-unverified-publisher",
    )
    override_without_flag_output = (
        f"{override_without_flag_result.stdout}\n{override_without_flag_result.stderr}"
    )
    assert override_without_flag_result.returncode != 0, override_without_flag_output
    assert "--accept-permissions" in override_without_flag_output

    override_target_dir = tmp_path / "feature39-consent-override"
    override_result = run_command(
        "install",
        str(permissions_archive),
        str(override_target_dir),
        "--yes",
        "--accept-permissions",
        "--allow-unverified-publisher",
    )
    override_output = f"{override_result.stdout}\n{override_result.stderr}"
    assert override_result.returncode == 0, override_output
    assert "Permissions consent acknowledged via --accept-permissions override." in override_output
    assert "- Permissions:" in override_output
    assert override_target_dir.exists(), override_output


def test_feature40_unsigned_archive_warning_and_confirmation(tmp_path):
    unsigned_archive = _create_feature40_unsigned_archive_with_checksum(tmp_path)

    denied_target_dir = tmp_path / "feature40-unsigned-denied"
    denied_result = run_command(
        "install",
        str(unsigned_archive),
        str(denied_target_dir),
        input_text="n\n",
    )
    denied_output = f"{denied_result.stdout}\n{denied_result.stderr}"
    assert denied_result.returncode != 0, denied_output
    assert "UNVERIFIED PUBLISHER" in denied_output
    assert "Install aborted: unverified publisher not approved." in denied_output

    override_target_dir = tmp_path / "feature40-unsigned-override"
    override_result = run_command(
        "install",
        str(unsigned_archive),
        str(override_target_dir),
        "--yes",
        "--allow-unverified-publisher",
    )
    override_output = f"{override_result.stdout}\n{override_result.stderr}"
    assert override_result.returncode == 0, override_output
    assert "UNVERIFIED PUBLISHER" in override_output
    assert "Unverified publisher override acknowledged" in override_output
    assert override_target_dir.exists(), override_output


def test_feature71_strict_install_enforcement(tmp_path: Path) -> None:
    from src.kinnoo.signing import create_detached_signature_artifacts, generate_ed25519_keypair

    manifest = (
        "name: strict-install-agent\n"
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

    unsigned_archive = tmp_path / "strict-unsigned.kno"
    with zipfile.ZipFile(unsigned_archive, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('ok')\n")

    unsigned_result = run_command(
        "install",
        str(unsigned_archive),
        str(tmp_path / "unsigned-target"),
        "--yes",
        "--strict",
    )
    unsigned_output = f"{unsigned_result.stdout}\n{unsigned_result.stderr}"
    assert unsigned_result.returncode != 0
    assert "Strict mode requires archive integrity verification" in unsigned_output

    private_key_path = tmp_path / "strict-private.pem"
    public_key_path = tmp_path / "strict-public.pem"
    generate_ed25519_keypair(private_key_path=private_key_path, public_key_path=public_key_path)

    invalid_archive = tmp_path / "strict-invalid-signature.kno"
    with zipfile.ZipFile(invalid_archive, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('ok')\n")

    digest = hashlib.sha256(invalid_archive.read_bytes()).hexdigest()
    Path(f"{invalid_archive}.sha256").write_text(
        f"{digest}  {invalid_archive.name}\n",
        encoding="utf-8",
    )

    create_detached_signature_artifacts(
        archive_path=invalid_archive,
        private_key_path=private_key_path,
    )
    signature_metadata_path = Path(f"{invalid_archive}.sig.json")
    metadata = json.loads(signature_metadata_path.read_text(encoding="utf-8"))
    metadata["signature_base64"] = base64.b64encode(b"strict-invalid-signature").decode("ascii")
    signature_metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    invalid_result = run_command(
        "install",
        str(invalid_archive),
        str(tmp_path / "invalid-target"),
        "--yes",
        "--strict",
    )
    invalid_output = f"{invalid_result.stdout}\n{invalid_result.stderr}"
    assert invalid_result.returncode != 0
    assert "Strict mode requires valid signature metadata" in invalid_output

    strict_override_result = run_command(
        "install",
        str(invalid_archive),
        str(tmp_path / "override-target"),
        "--yes",
        "--strict",
        "--allow-unverified-publisher",
    )
    strict_override_output = f"{strict_override_result.stdout}\n{strict_override_result.stderr}"
    assert strict_override_result.returncode != 0
    assert "cannot be used with --strict" in strict_override_output


def test_feature72_frozen_install_and_docs(tmp_path: Path) -> None:
    archive_path = tmp_path / "frozen-agent.kno"
    manifest = (
        "name: frozen-agent\n"
        "version: 1.2.3\n"
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

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('frozen')\n")
        archive.writestr("requirements.txt", "")

    lockfile_path = tmp_path / "kinnoo-lock.yaml"
    archive_checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    lockfile_path.write_text(
        (
            "lock_version: 1\n"
            "locked_at: 2026-03-30T00:00:00Z\n"
            "platform:\n"
            "  python: 3.12.0\n"
            "  os: darwin-arm64\n"
            "agents:\n"
            "  frozen-agent:\n"
            "    version: 1.2.3\n"
            "    source: archive-file\n"
            f"    archive_sha256: {archive_checksum}\n"
            "    installed_at: 2026-03-30T00:00:00Z\n"
        ),
        encoding="utf-8",
    )
    original_lockfile_text = lockfile_path.read_text(encoding="utf-8")

    install_env = dict(os.environ)
    install_env["KINNOO_LOCKFILE_PATH"] = str(lockfile_path)

    frozen_ok_result = run_command(
        "install",
        str(archive_path),
        str(tmp_path / "frozen-target-ok"),
        "--yes",
        "--frozen",
        env=install_env,
    )
    frozen_ok_output = f"{frozen_ok_result.stdout}\n{frozen_ok_result.stderr}"
    assert frozen_ok_result.returncode == 0, frozen_ok_output
    assert "Frozen lockfile check passed for 'frozen-agent'" in frozen_ok_output
    assert "Frozen mode active; lockfile left unchanged." in frozen_ok_output
    assert lockfile_path.read_text(encoding="utf-8") == original_lockfile_text

    lockfile_path.write_text(
        (
            "lock_version: 1\n"
            "locked_at: 2026-03-30T00:00:00Z\n"
            "platform:\n"
            "  python: 3.12.0\n"
            "  os: darwin-arm64\n"
            "agents:\n"
            "  frozen-agent:\n"
            "    version: 9.9.9\n"
            "    source: archive-file\n"
            f"    archive_sha256: {archive_checksum}\n"
            "    installed_at: 2026-03-30T00:00:00Z\n"
        ),
        encoding="utf-8",
    )

    frozen_drift_result = run_command(
        "install",
        str(archive_path),
        str(tmp_path / "frozen-target-drift"),
        "--yes",
        "--frozen",
        env=install_env,
    )
    frozen_drift_output = f"{frozen_drift_result.stdout}\n{frozen_drift_result.stderr}"
    assert frozen_drift_result.returncode != 0
    assert "Frozen lock mismatch for agent 'frozen-agent'" in frozen_drift_output
    assert "Re-run install without --frozen to regenerate lockfile" in frozen_drift_output

    repo_root = Path(__file__).resolve().parents[2]
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "kinnoo install --frozen" in readme_text
    assert "Re-run install without --frozen to regenerate lockfile" in readme_text


def test_feature74_uninstall_confirmation_and_removal(tmp_path: Path) -> None:
    install_root = tmp_path / "agents-root"
    agent_dir = install_root / "feature74-agent"
    venv_marker = agent_dir / ".venv" / "pyvenv.cfg"
    run_file = agent_dir / "run.py"

    run_file.parent.mkdir(parents=True, exist_ok=True)
    venv_marker.parent.mkdir(parents=True, exist_ok=True)
    run_file.write_text("print('installed')\n", encoding="utf-8")
    venv_marker.write_text("home = /mock/python\n", encoding="utf-8")

    uninstall_env = dict(os.environ)
    uninstall_env["KINNOO_AGENT_INSTALL_ROOT"] = str(install_root)

    denied = run_command(
        "uninstall",
        "feature74-agent",
        input_text="n\n",
        env=uninstall_env,
    )
    denied_output = f"{denied.stdout}\n{denied.stderr}"
    assert denied.returncode != 0, denied_output
    assert "Uninstall aborted by user." in denied_output
    assert agent_dir.exists(), "Reject path must preserve installed artifacts"

    accepted = run_command(
        "uninstall",
        "feature74-agent",
        input_text="y\n",
        env=uninstall_env,
    )
    accepted_output = f"{accepted.stdout}\n{accepted.stderr}"
    assert accepted.returncode == 0, accepted_output
    assert "Removed installed agent 'feature74-agent'" in accepted_output
    assert not agent_dir.exists(), "Accepted uninstall must remove agent artifacts"
