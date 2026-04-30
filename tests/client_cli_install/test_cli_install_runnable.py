import subprocess
import sys
import tempfile
from pathlib import Path
import zipfile
import shutil
import os
import pytest

def make_minimal_kno(tmp_path, agent_name="runnableagent"):
    """Helper to create a minimal .kno archive with a valid manifest and run.py at the correct structure."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
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
    (agent_dir / "run.py").write_text(
        "import sys\nprint(f'agent ran: {sys.argv[1]}')\n"
    )
    archive_path = tmp_path / f"{agent_name}.kno"
    # Archive should contain kinnoo.yaml and run.py at the root
    with zipfile.ZipFile(archive_path, "w") as z:
        for file in ["kinnoo.yaml", "run.py"]:
            z.write(agent_dir / file, arcname=file)
    return archive_path, agent_name

@pytest.mark.integration
def test_install_makes_agent_runnable(tmp_path):
    """Test that kinnoo install makes agent runnable with kinnoo run (test55)."""
    import shutil
    archive_path, agent_name = make_minimal_kno(tmp_path)
    agent_dir = tmp_path / agent_name
    cli_path = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
    # Debug: print archive contents
    import zipfile
    with zipfile.ZipFile(archive_path, "r") as z:
        print("Archive contents:", z.namelist())
    # Remove the agent directory so kinnoo install can create it
    shutil.rmtree(agent_dir)
    # Install the agent
    result = subprocess.run([
        sys.executable, str(cli_path), "install", str(archive_path), "--yes"
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"kinnoo install failed: {result.stderr}"
    assert agent_dir.exists(), "Agent directory not created"
    # Run the agent
    run_result = subprocess.run([
        sys.executable, str(cli_path), "run", str(agent_dir), "test input"
    ], capture_output=True, text=True)
    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stderr}"
    assert "agent ran: test input" in run_result.stdout, f"Unexpected output: {run_result.stdout}"


@pytest.mark.integration
def test_run_subdirectory_entrypoint(tmp_path):
    """Feature47 test389: kinnoo run executes subdirectory entrypoint with import-safe PYTHONPATH."""
    agent_dir = tmp_path / "subdir-runnable-agent"
    source_dir = agent_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        "entrypoint: source/main.py\n"
        "dependencies: []\n"
        "inputs:\n  type: string\n"
        "outputs:\n  type: string\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "name: subdir-runnable-agent\n"
        "version: 0.1.0\n",
        encoding="utf-8",
    )
    (source_dir / "__init__.py").write_text("", encoding="utf-8")
    (source_dir / "helper.py").write_text(
        "def render(value: str) -> str:\n"
        "    return f'subdir ran: {value}'\n",
        encoding="utf-8",
    )
    (source_dir / "main.py").write_text(
        "import sys\n"
        "from source.helper import render\n\n"
        "if __name__ == '__main__':\n"
        "    print(render(sys.argv[1]))\n",
        encoding="utf-8",
    )

    cli_path = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
    )

    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stderr}"
    assert "subdir ran: hello" in run_result.stdout


@pytest.mark.integration
def test_run_typescript_entrypoint(tmp_path):
    """Feature47 test393: kinnoo run executes .ts entrypoints via npx tsx."""
    agent_dir = tmp_path / "ts-runnable-agent"
    src_dir = agent_dir / "src"
    bin_dir = tmp_path / "fake-bin"
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        "entrypoint: src/index.ts\n"
        "dependencies: []\n"
        "inputs:\n  type: string\n"
        "outputs:\n  type: string\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: nodejs\n"
        "  version: \">=20.0.0\"\n"
        "name: ts-runnable-agent\n"
        "version: 0.1.0\n",
        encoding="utf-8",
    )
    (src_dir / "index.ts").write_text("console.log('hello from ts')\n", encoding="utf-8")

    fake_npx = bin_dir / "npx"
    fake_npx.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == \"tsx\" ]]; then\n"
        "  shift\n"
        "  echo \"tsx executed: $*\"\n"
        "  exit 0\n"
        "fi\n"
        "echo \"unexpected npx invocation\" >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake_npx.chmod(0o755)

    cli_path = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stderr}"
    assert "tsx executed:" in run_result.stdout


@pytest.mark.integration
def test_run_json_input_pydanticai(tmp_path):
    """Feature47 test399: --json-input payload is passed through as structured JSON text."""
    agent_dir = tmp_path / "json-input-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        "entrypoint: run.py\n"
        "dependencies: []\n"
        "inputs:\n  type: json\n"
        "outputs:\n  type: string\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "name: json-input-agent\n"
        "version: 0.1.0\n",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text(
        "import json\n"
        "import sys\n\n"
        "payload = json.loads(sys.argv[1])\n"
        "print(f\"deps:{payload.get('account_id')}:{payload.get('amount')}\")\n",
        encoding="utf-8",
    )

    cli_path = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
    run_result = subprocess.run(
        [
            sys.executable,
            str(cli_path),
            "run",
            str(agent_dir),
            "--json-input",
            '{"account_id":"acct-123","amount":42}',
        ],
        capture_output=True,
        text=True,
    )

    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stderr}"
    assert "deps:acct-123:42" in run_result.stdout
