import pytest


LEGACY_INIT_FRAMEWORK_REASON = "deprecated: legacy init --framework contract replaced by positional framework flow"


@pytest.mark.skip(reason=LEGACY_INIT_FRAMEWORK_REASON)
def test_gemini_template_uses_genai_and_flash_lite(tmp_path):
    """Test that Gemini template uses google-genai and gemini-2.5-flash-lite (test39).
    This covers test39 in TESTS.txt."""
    agent_name = "gemini-flash-lite-agent"
    code, out, err = run_cli(["init", agent_name, "--framework", "gemini"], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    # requirements.txt should contain google-genai and NOT google-generativeai
    reqs = (agent_dir / "requirements.txt").read_text()
    assert "google-genai" in reqs, "google-genai should be in requirements.txt"
    assert "google-generativeai" not in reqs, "google-generativeai should NOT be in requirements.txt"
    # run.py should reference gemini-2.5-flash-lite
    runpy = (agent_dir / "run.py").read_text()
    assert "gemini-2.5-flash-lite" in runpy, "run.py should reference gemini-2.5-flash-lite"
    # README.md should mention GOOGLE_API_KEY and usage
    readme = (agent_dir / "README.md").read_text()
    assert "GOOGLE_API_KEY" in readme, "README.md should mention GOOGLE_API_KEY"
    assert "python run.py" in readme, "README.md should show run.py usage"
@pytest.mark.skip(reason=LEGACY_INIT_FRAMEWORK_REASON)
@pytest.mark.parametrize("framework,dep,envvar,run_example,model_hint,test_id", [
    ("gemini", "google-genai", "GOOGLE_API_KEY", "Hello Gemini!", "gemini-2.5-flash-lite", "test29"),
    ("chatgpt", "openai", "OPENAI_API_KEY", "Hello ChatGPT!", "gpt-5-nano", "test30"),
    ("claude-chat", "anthropic", "ANTHROPIC_API_KEY", "Hello Claude!", "claude-sonnet-4-20250514", "test31"),
])
def test_framework_templates_generate_correct_files(framework, dep, envvar, run_example, model_hint, test_id):
    import tempfile
    from pathlib import Path
    import os
    agent_name = f"test_{framework}"
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = run_kinnoo_init([agent_name, "--framework", framework])
        finally:
            os.chdir(cwd)
        assert result.returncode == 0, f"Framework {framework} should succeed"
        agent_dir = Path(tmpdir) / agent_name
        # Directory and files
        assert agent_dir.exists()
        for fname in ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]:
            assert (agent_dir / fname).exists(), f"{fname} missing for {framework}"
        # requirements.txt
        reqs = (agent_dir / "requirements.txt").read_text()
        assert dep in reqs, f"Dependency {dep} missing in requirements.txt for {framework}"
        # README.md
        readme = (agent_dir / "README.md").read_text()
        assert envvar in readme, f"API key env var {envvar} missing in README for {framework}"
        assert run_example in readme, f"Run example missing in README for {framework}"
        # run.py
        runpy = (agent_dir / "run.py").read_text()
        assert model_hint in runpy, f"Model hint {model_hint} missing in run.py for {framework}"
        # tools/ and prompts/
        assert (agent_dir / "tools").is_dir()
        assert (agent_dir / "prompts").is_dir()
import os
import shutil
import subprocess
import tempfile
import sys

KINNOO_INIT_PATH = os.path.join(os.path.dirname(__file__), '../src/kinnoo/init_command.py')

def run_kinnoo_init(args):
    cmd = [sys.executable, KINNOO_INIT_PATH] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result

@pytest.mark.skip(reason=LEGACY_INIT_FRAMEWORK_REASON)
def test_framework_valid():
    # Should not error for supported frameworks (no file creation yet)
    import tempfile
    for fw in ["gemini", "chatgpt", "claude-chat", "mcp-server"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_name = f"myagent_{fw}"
            cwd = os.getcwd()
            os.chdir(tmpdir)
            result = run_kinnoo_init([agent_name, "--framework", fw])
            os.chdir(cwd)
            assert result.returncode == 0, f"Valid framework {fw} should not error"

@pytest.mark.skip(reason=LEGACY_INIT_FRAMEWORK_REASON)
def test_framework_invalid():
    # Should error for unsupported frameworks
    import tempfile
    for fw in ["pigglypoo", "openai", "invalid-name"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = run_kinnoo_init(["myagent", "--framework", fw])
            finally:
                os.chdir(cwd)
        assert result.returncode != 0, f"Invalid framework {fw} should error"
        assert b"Unsupported framework" in result.stderr, f"Error message missing for {fw}"
        assert b"Usage: kinnoo init" in result.stderr, f"Usage message missing for {fw}"

@pytest.mark.skip(reason=LEGACY_INIT_FRAMEWORK_REASON)
def test_missing_agent_name():
    # Should error and print usage if agent_name is missing
    result = run_kinnoo_init(["--framework", "gemini"])
    assert result.returncode != 0, "Missing agent_name should error"
    assert b"Usage: kinnoo init" in result.stderr, "Usage message missing for missing agent_name"
import subprocess
import sys
import re
import os
import io
import pytest
from pathlib import Path

from tests.helpers import run_cli as run_kinnoo_cli

KINNOO_CLI = [sys.executable, "-m", "kinnoo.cli"]
CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"


def run_cli(args, cwd=None):
    """Run kinnoo CLI with args, return (exit_code, stdout, stderr)"""
    result = run_kinnoo_cli(args, cwd=cwd)
    return result.returncode, result.stdout, result.stderr


def test_init_framework_positional_arg(tmp_path):
    import yaml

    agent_name = "task454-chatgpt-positional"
    code, out, err = run_cli(["init", "chatgpt", "--language", "python", agent_name], cwd=tmp_path)
    assert code == 0, err

    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["framework"] == "chatgpt"


def test_init_no_framework_barebones(tmp_path):
    import yaml

    agent_name = "task454-no-framework"
    code, out, err = run_cli(["init", "no-framework", agent_name], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    manifest_path = agent_dir / "kinnoo.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert "framework" not in manifest
    assert (agent_dir / "run.py").exists()


def test_init_interactive_wizard(tmp_path, monkeypatch, capsys):
    from kinnoo import cli as cli_module

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["kinnoo", "init"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(iter_inputs))

    class _TTYStdin(io.StringIO):
        def isatty(self):
            return True

    iter_inputs = iter(["1", "1"])
    monkeypatch.setattr(sys, "stdin", _TTYStdin())

    cli_module.main()
    output = capsys.readouterr().out
    assert "Select framework:" in output
    assert "Select language:" in output

    agent_dir = tmp_path / "gemini-agent"
    assert agent_dir.exists()
    assert (agent_dir / "kinnoo.yaml").exists()


def test_init_python_entrypoint_main_py(tmp_path):
    import yaml

    agent_name = "task456-main-py"
    code, out, err = run_cli(["init", "chatgpt", agent_name], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "main.py").exists()
    assert not (agent_dir / "run.py").exists()

    manifest = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest["entrypoint"] == "main.py"


def test_init_complete_template_folders(tmp_path):
    agent_name = "task457-complete"
    code, out, err = run_cli(["init", "chatgpt", agent_name], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    for folder in ("tools", "prompts", "evals", "tests", "data"):
        assert (agent_dir / folder).is_dir()
    assert (agent_dir / ".gitignore").exists()


def test_init_minimal_template(tmp_path):
    agent_name = "task457-minimal"
    code, out, err = run_cli(["init", "chatgpt", "--minimal", agent_name], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()
    assert (agent_dir / "main.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    for folder in ("tools", "prompts", "evals", "tests", "data"):
        assert not (agent_dir / folder).exists()
    assert not (agent_dir / ".gitignore").exists()


def test_init_openclaw_complete_template(tmp_path):
    agent_name = "task457-openclaw-complete"
    code, out, err = run_cli(["init", "openclaw", agent_name], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    for file_name in ("MEMORY.md", "BOOTSTRAP.md", "HEARTBEAT.md"):
        assert (agent_dir / file_name).exists()
    for folder_name in ("skills", "memory"):
        assert (agent_dir / folder_name).is_dir()
    assert not (agent_dir / "requirements.txt").exists()
    assert not (agent_dir / "main.py").exists()


def test_init_readme_content(tmp_path):
    agent_name = "task458-readme"
    code, out, err = run_cli(["init", "chatgpt", agent_name], cwd=tmp_path)
    assert code == 0, err

    readme = (tmp_path / agent_name / "README.md").read_text(encoding="utf-8")
    assert "main.py" in readme
    assert "kinnoo.yaml" in readme
    assert "| Folder | What goes here |" in readme
    assert "This agent was scaffolded with Kinnoo CLI v" in readme
    assert "using Schema 0.1.0" in readme


def test_init_python_gitignore(tmp_path):
    agent_name = "task459-python-gitignore"
    code, out, err = run_cli(["init", "chatgpt", "--language", "python", agent_name], cwd=tmp_path)
    assert code == 0, err

    gitignore = (tmp_path / agent_name / ".gitignore").read_text(encoding="utf-8")
    assert "__pycache__/" in gitignore
    assert ".venv/" in gitignore
    assert "*.py[cod]" in gitignore
    assert ".kinnoo/" in gitignore
    assert ".env" in gitignore
    assert "*.pem" in gitignore


def test_init_javascript_gitignore(tmp_path):
    agent_name = "task459-javascript-gitignore"
    code, out, err = run_cli(["init", "chatgpt", "--language", "javascript", agent_name], cwd=tmp_path)
    assert code == 0, err

    gitignore = (tmp_path / agent_name / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in gitignore
    assert ".npm" in gitignore
    assert "npm-debug.log*" in gitignore
    assert "__pycache__/" not in gitignore
    assert ".venv/" not in gitignore


def test_init_typescript_gitignore(tmp_path):
    agent_name = "task459-typescript-gitignore"
    code, out, err = run_cli(["init", "chatgpt", "--language", "typescript", agent_name], cwd=tmp_path)
    assert code == 0, err

    gitignore = (tmp_path / agent_name / ".gitignore").read_text(encoding="utf-8")
    assert "*.tsbuildinfo" in gitignore
    assert "coverage/" in gitignore
    assert ".vitest/" in gitignore
    assert "__pycache__/" not in gitignore
    assert ".venv/" not in gitignore


def test_init_openclaw_gitignore(tmp_path):
    agent_name = "task459-openclaw-gitignore"
    code, out, err = run_cli(["init", "openclaw", agent_name], cwd=tmp_path)
    assert code == 0, err

    gitignore = (tmp_path / agent_name / ".gitignore").read_text(encoding="utf-8")
    assert "memory/" in gitignore
    assert ".dreams/" in gitignore
    assert "scratch/" in gitignore
    assert ".openclaw/" in gitignore
    assert "credentials.json" in gitignore
    assert "__pycache__/" not in gitignore
    assert "node_modules/" not in gitignore


def test_init_javascript_manifest_runtime_language(tmp_path):
    import yaml

    agent_name = "js-agent"
    code, out, err = run_cli(["init", agent_name, "--language", "javascript"], cwd=tmp_path)
    assert code == 0, err

    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["runtime"]["language"] == "javascript"
    assert (tmp_path / agent_name / "run.js").exists()


def test_init_typescript_manifest_runtime_language(tmp_path):
    import yaml

    agent_name = "ts-agent"
    code, out, err = run_cli(["init", agent_name, "--language", "typescript"], cwd=tmp_path)
    assert code == 0, err

    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["runtime"]["language"] == "typescript"
    assert (tmp_path / agent_name / "run.ts").exists()


import pytest

@pytest.mark.parametrize("test_id,cli_args", [
    ("test7", ["init"]),
    ("test33", ["init"]),
])
def test_init_missing_name_prints_usage(tmp_path, test_id, cli_args):
    code, out, err = run_cli(cli_args, cwd=tmp_path)
    assert code != 0
    assert "Usage" in err
    assert "<agent-name>" in err

def test_init_invalid_name_rejected(tmp_path):
    invalid_names = ["_invalid-name", "My Agent", "MyAgent"]
    for name in invalid_names:
        code, out, err = run_cli(["init", name], cwd=tmp_path)
        assert code != 0
        assert "Invalid agent name" in err


def test_init_creates_directory_structure(tmp_path):
    agent_name = "test-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None  # dry-run or success
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    expected_files = ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]
    for fname in expected_files:
        assert (agent_dir / fname).exists()
    assert (agent_dir / "tools").is_dir()
    assert (agent_dir / "prompts").is_dir()


import pytest

@pytest.mark.parametrize("test_id,agent_name", [
    ("test10", "test-agent"),
    ("test37", "test-agent"),
])
def test_generated_manifest_passes_validation(tmp_path, test_id, agent_name):
    run_cli(["init", agent_name], cwd=tmp_path)
    from kinnoo.validator import validate
    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors


def test_generated_entrypoint_executes(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    run_py = tmp_path / agent_name / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "hello"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


def test_generated_entrypoint_has_asyncio(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    run_py = tmp_path / agent_name / "run.py"
    contents = run_py.read_text()
    assert "asyncio.run" in contents
    assert "async def" in contents


import pytest

@pytest.mark.parametrize("test_id,agent_name", [
    ("test13", "test-agent"),
    ("test34", "test-agent"),
])
def test_init_existing_directory_fails(tmp_path, test_id, agent_name):
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code != 0
    assert "already exists" in err
    # Directory should be unchanged (still exists)
    assert agent_dir.exists() and agent_dir.is_dir()


def test_init_full_workflow(tmp_path):
    agent_name = "my-first-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    # Directory and files exist
    assert agent_dir.exists() and agent_dir.is_dir()
    for fname in ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]:
        assert (agent_dir / fname).exists()
    assert (agent_dir / "tools").is_dir()
    assert (agent_dir / "prompts").is_dir()
    # Manifest passes validation
    from kinnoo.validator import validate
    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors
    # Entrypoint runs successfully
    run_py = agent_dir / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "test"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


import pytest

@pytest.mark.parametrize("framework,test_id", [
    ("gemini", "test32"),
    ("chatgpt", "test32"),
    ("claude-chat", "test32"),
])
def test_framework_manifests_pass_validation(framework, test_id):
    import tempfile
    from pathlib import Path
    from kinnoo.validator import validate
    import os
    agent_name = f"validate-{framework}"
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = run_kinnoo_init([agent_name, "--framework", framework])
            assert result.returncode == 0, f"Framework {framework} should succeed"
            manifest_path = Path(tmpdir) / agent_name / "kinnoo.yaml"
            is_valid, errors = validate(str(manifest_path))
            assert is_valid, f"Manifest for {framework} should be valid, got errors: {errors}"
            assert not errors, f"Manifest for {framework} should have no errors, got: {errors}"
        finally:
            os.chdir(cwd)


def test_init_vanilla_agent(tmp_path):
    agent_name = "vanilla-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    # requirements.txt should be empty (vanilla agent)
    reqs = (agent_dir / "requirements.txt").read_text()
    assert reqs.strip() == ""
    # README.md should not mention any API key
    readme = (agent_dir / "README.md").read_text()
    assert "API key" not in readme
    # run.py should be the hello-world template
    runpy = (agent_dir / "run.py").read_text()
    assert "Hello, world!" in runpy


def test_agent_name_with_underscore_is_accepted(tmp_path):
    agent_name = "agent_with_underscore"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    # Manifest passes validation
    from kinnoo.validator import validate
    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors
    # Entrypoint runs successfully
    run_py = agent_dir / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "test"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


def test_feature21_framework_invalid_lists_all_choices(tmp_path):
    code, out, err = run_cli(["init", "feature21-invalid", "--framework", "invalid-name"], cwd=tmp_path)
    assert code != 0
    for framework in [
        "gemini",
        "chatgpt",
        "claude-chat",
        "pydantic-ai",
        "langgraph",
        "openai-agents",
    ]:
        assert framework in err


def test_feature21_framework_values_accepted(tmp_path):
    for framework in ["pydantic-ai", "langgraph", "openai-agents"]:
        agent_name = f"feature21-{framework}-agent"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0
        agent_dir = tmp_path / agent_name
        assert agent_dir.exists() and agent_dir.is_dir()


def test_feature21_pydanticai_template_generation(tmp_path):
    agent_name = "feature21-pydanticai-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "pydantic-ai"], cwd=tmp_path)
    assert code == 0

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()

    run_py = (agent_dir / "run.py").read_text()
    readme = (agent_dir / "README.md").read_text()
    assert "pydantic-ai template" in run_py
    assert "pydantic-ai" in readme


def test_feature21_langgraph_template_generation(tmp_path):
    agent_name = "feature21-langgraph-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "langgraph"], cwd=tmp_path)
    assert code == 0

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()

    run_py = (agent_dir / "run.py").read_text()
    readme = (agent_dir / "README.md").read_text()
    assert "langgraph template" in run_py
    assert "langgraph" in readme


def test_feature21_openai_agents_template_generation(tmp_path):
    agent_name = "feature21-openai-agents-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "openai-agents"], cwd=tmp_path)
    assert code == 0

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()

    run_py = (agent_dir / "run.py").read_text()
    readme = (agent_dir / "README.md").read_text()
    assert "openai-agents template" in run_py
    assert "openai-agents" in readme


def test_feature21_requirements_major_version_pins(tmp_path):
    expected_dependency_patterns = {
        "pydantic-ai": r"^pydantic-ai>=\d+\.\d+,<\d+\.\d+$",
        "langgraph": r"^langgraph>=\d+\.\d+,<\d+\.\d+$",
        "openai-agents": r"^openai-agents>=\d+\.\d+,<\d+\.\d+$",
    }

    for framework, dependency_pattern in expected_dependency_patterns.items():
        agent_name = f"feature21-pins-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0

        requirements_path = tmp_path / agent_name / "requirements.txt"
        requirements_entry = requirements_path.read_text().strip()
        assert re.match(dependency_pattern, requirements_entry), (
            f"Requirements pin for {framework} did not match expected major-range format: {requirements_entry}"
        )


def test_feature21_manifests_pass_and_set_framework(tmp_path):
    import yaml
    from kinnoo.validator import validate

    frameworks = ["pydantic-ai", "langgraph", "openai-agents"]
    for framework in frameworks:
        agent_name = f"feature21-manifest-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0

        manifest_path = tmp_path / agent_name / "kinnoo.yaml"
        is_valid, errors = validate(str(manifest_path))
        assert is_valid, f"Manifest for {framework} should validate: {errors}"
        assert not errors

        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data.get("framework") == framework


def test_feature21_readme_setup_guidance(tmp_path):
    readme_expectations = {
        "pydantic-ai": ["OPENAI_API_KEY", "Model Configuration", "python run.py"],
        "langgraph": ["OPENAI_API_KEY", "Graph Configuration", "python run.py"],
        "openai-agents": ["OPENAI_API_KEY", "Agent Configuration", "python run.py"],
    }

    for framework, expected_terms in readme_expectations.items():
        agent_name = f"feature21-readme-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0

        readme_text = (tmp_path / agent_name / "README.md").read_text()
        for term in expected_terms:
            assert term in readme_text


def test_feature34_openclaw_scaffold_structure(tmp_path):
    """test287: openclaw scaffold includes required files and deterministic directories."""
    agent_name = "kinnoo_tmp_test_feature34-openclaw-agent"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = subprocess.run(
            [sys.executable, KINNOO_INIT_PATH, agent_name, "--framework", "openclaw"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    finally:
        os.chdir(cwd)
        subprocess.run(
            ["openclaw", "agents", "delete", "--force", agent_name],
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0

    agent_dir = tmp_path / ".openclaw" / f"workspace-{agent_name}"
    required_files = [
        "AGENTS.md",
        "SOUL.md",
        "USER.md",
        "TOOLS.md",
        "IDENTITY.md",
        "BOOTSTRAP.md",
        "HEARTBEAT.md",
        "kinnoo.yaml",
    ]
    for relative_path in required_files:
        target = agent_dir / relative_path
        assert target.exists() and target.is_file(), f"Missing required file: {relative_path}"

    required_dirs = [
        ".git",
        ".openclaw",
    ]
    for relative_path in required_dirs:
        target = agent_dir / relative_path
        assert target.exists() and target.is_dir(), f"Missing required directory: {relative_path}"


def test_feature34_openclaw_manifest_validation_contract(tmp_path):
    """test288 (deprecated): current OpenClaw scaffold includes unsupported fields rejected by schema."""
    import yaml
    from kinnoo.validator import validate

    agent_name = "kinnoo_tmp_test_feature34-openclaw-manifest"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "init", agent_name, "--framework", "openclaw"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    code = proc.returncode
    out = proc.stdout
    err = proc.stderr
    assert code == 0, err

    subprocess.run(
        ["openclaw", "agents", "delete", "--force", agent_name],
        capture_output=True,
        text=True,
        check=False,
    )

    manifest_path = tmp_path / ".openclaw" / f"workspace-{agent_name}" / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid is True, errors

    manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    runtime = manifest_data["runtime"]
    assert manifest_data.get("framework") == "openclaw"
    assert runtime.get("language") == "nodejs"
    assert runtime.get("type") == "daemon"
    assert "channels" not in manifest_data
    assert "skills" not in manifest_data
    assert "state_dirs" not in manifest_data


def test_feature34_openclaw_readme_setup_guidance(tmp_path):
    """test290: generated OpenClaw README includes setup and env guidance."""
    agent_name = "kinnoo_tmp_test_feature34-openclaw-readme"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "init", agent_name, "--framework", "openclaw"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    code = proc.returncode
    out = proc.stdout
    err = proc.stderr
    assert code == 0, err

    subprocess.run(
        ["openclaw", "agents", "delete", "--force", agent_name],
        capture_output=True,
        text=True,
        check=False,
    )

    workspace = tmp_path / ".openclaw" / f"workspace-{agent_name}"
    agents_text = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    soul_text = (workspace / "SOUL.md").read_text(encoding="utf-8")

    assert "# AGENTS.md - Your Workspace" in agents_text
    assert "Session Startup" in agents_text
    assert "# SOUL.md - Who You Are" in soul_text
    assert "Core Truths" in soul_text


@pytest.mark.skip(reason="Deprecated feature34 deterministic scaffold coverage; do not execute")
def test_feature34_scaffold_deterministic_without_openclaw_cli(tmp_path, monkeypatch):
    """test291: OpenClaw scaffold is deterministic and does not shell out to external openclaw CLI."""
    from kinnoo.init_command import init_agent

    agent_name = "feature34-openclaw-deterministic"
    run_one_root = tmp_path / "deterministic-run-one"
    run_two_root = tmp_path / "deterministic-run-two"
    run_one_root.mkdir()
    run_two_root.mkdir()

    original_run = subprocess.run
    original_popen = subprocess.Popen

    def _guard_openclaw_invocation(cmd, *args, **kwargs):
        command_tokens = cmd if isinstance(cmd, (list, tuple)) else [cmd]
        normalized = [str(token).strip() for token in command_tokens if token is not None]
        executable = normalized[0] if normalized else ""
        if os.path.basename(executable) == "openclaw":
            raise AssertionError("OpenClaw scaffold init must not invoke external openclaw CLI")
        return original_run(cmd, *args, **kwargs)

    def _guard_openclaw_popen(cmd, *args, **kwargs):
        command_tokens = cmd if isinstance(cmd, (list, tuple)) else [cmd]
        normalized = [str(token).strip() for token in command_tokens if token is not None]
        executable = normalized[0] if normalized else ""
        if os.path.basename(executable) == "openclaw":
            raise AssertionError("OpenClaw scaffold init must not invoke external openclaw CLI")
        return original_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", _guard_openclaw_invocation)
    monkeypatch.setattr(subprocess, "Popen", _guard_openclaw_popen)

    init_agent(agent_name, run_one_root, framework="openclaw")
    init_agent(agent_name, run_two_root, framework="openclaw")

    def _snapshot(agent_dir):
        snapshot = {}
        for path in sorted(agent_dir.rglob("*")):
            if path.is_file():
                snapshot[path.relative_to(agent_dir).as_posix()] = path.read_text(encoding="utf-8")
        return snapshot

    first_snapshot = _snapshot(run_one_root / agent_name)
    second_snapshot = _snapshot(run_two_root / agent_name)
    assert first_snapshot == second_snapshot

    cli_script = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
    pathless_root = tmp_path / "pathless-cli-run"
    pathless_root.mkdir()

    env = os.environ.copy()
    env["PATH"] = ""
    result = original_run(
        [sys.executable, str(cli_script), "init", "feature34-openclaw-pathless", "--framework", "openclaw"],
        cwd=pathless_root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_feature21_regression_existing_frameworks_unchanged(tmp_path):
    expected = {
        "gemini": {
            "dependency": "google-genai",
            "env_var": "GOOGLE_API_KEY",
            "model_hint": "gemini-2.5-flash-lite",
            "run_example": "Hello Gemini!",
        },
        "chatgpt": {
            "dependency": "openai",
            "env_var": "OPENAI_API_KEY",
            "model_hint": "gpt-5-nano",
            "run_example": "Hello ChatGPT!",
        },
        "claude-chat": {
            "dependency": "anthropic",
            "env_var": "ANTHROPIC_API_KEY",
            "model_hint": "claude-sonnet-4-20250514",
            "run_example": "Hello Claude!",
        },
    }

    for framework, checks in expected.items():
        agent_name = f"feature21-regression-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        agent_dir = tmp_path / agent_name
        requirements_text = (agent_dir / "requirements.txt").read_text()
        run_text = (agent_dir / "run.py").read_text()
        readme_text = (agent_dir / "README.md").read_text()

        assert checks["dependency"] in requirements_text
        assert checks["model_hint"] in run_text
        assert checks["env_var"] in readme_text
        assert checks["run_example"] in readme_text

        from kinnoo.validator import validate
        manifest_path = agent_dir / "kinnoo.yaml"
        is_valid, errors = validate(str(manifest_path))
        assert is_valid
        assert not errors


def _feature21_tested_compatibility_targets():
    # Keep this map aligned with template requirements constants.
    return {
        "pydantic-ai": "pydantic-ai>=0.0,<0.1",
        "langgraph": "langgraph>=0.2,<0.3",
        "openai-agents": "openai-agents>=0.1,<0.2",
    }


def _satisfies_feature21_dependency_policy(requirement_line: str) -> bool:
    exact_match = re.match(r"^[a-z0-9-]+==\d+\.\d+\.\d+$", requirement_line)
    if exact_match:
        return True

    bounded_range = re.match(
        r"^(?P<pkg>[a-z0-9-]+)>=(?P<lmajor>\d+)\.(?P<lminor>\d+),<(?P<umajor>\d+)\.(?P<uminor>\d+)$",
        requirement_line,
    )
    if not bounded_range:
        return False

    lower_major = int(bounded_range.group("lmajor"))
    lower_minor = int(bounded_range.group("lminor"))
    upper_major = int(bounded_range.group("umajor"))
    upper_minor = int(bounded_range.group("uminor"))

    if lower_major >= 1:
        # Stable-major policy: bounded major range (>=X.Y,<X+1.0).
        return upper_major == (lower_major + 1) and upper_minor == 0

    # Pre-1.0 policy: explicitly tested bounded range narrower than <1.0.
    return upper_major == 0 and upper_minor == (lower_minor + 1)


def test_feature21_requirements_tested_compatibility_ranges(tmp_path):
    expected_requirements = _feature21_tested_compatibility_targets()

    for framework, expected_line in expected_requirements.items():
        agent_name = f"feature21-compat-ranges-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        requirements_line = (tmp_path / agent_name / "requirements.txt").read_text().strip()
        assert requirements_line == expected_line
        assert "<1.0" not in requirements_line
        assert _satisfies_feature21_dependency_policy(requirements_line)


def test_feature21_dependency_policy_alignment(tmp_path):
    features_text = Path("FEATURES.txt").read_text(encoding="utf-8")
    assert "stable major versions" in features_text
    assert "pre-1.0 frameworks" in features_text
    assert "tested compatibility ranges" in features_text

    for framework in _feature21_tested_compatibility_targets().keys():
        agent_name = f"feature21-policy-alignment-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        requirements_line = (tmp_path / agent_name / "requirements.txt").read_text().strip()
        assert _satisfies_feature21_dependency_policy(requirements_line), (
            f"Generated requirement does not satisfy AC4 policy for {framework}: {requirements_line}"
        )


def test_feature21_pydantic_ai_framework_native_template(tmp_path):
    agent_name = "feature21-pydantic-ai-native"
    code, out, err = run_cli(["init", agent_name, "--framework", "pydantic-ai"], cwd=tmp_path)
    assert code == 0, err

    run_text = (tmp_path / agent_name / "run.py").read_text()
    assert "from pydantic_ai import Agent" in run_text
    assert "Agent(" in run_text
    assert "_run_framework_mode" in run_text
    assert "KINNOO_TEST_SAFE_MODE" in run_text
    assert "test-safe response" in run_text
    assert "Placeholder scaffold for pydantic-ai workflow" not in run_text


def test_feature21_langgraph_framework_native_template(tmp_path):
    agent_name = "feature21-langgraph-native"
    code, out, err = run_cli(["init", agent_name, "--framework", "langgraph"], cwd=tmp_path)
    assert code == 0, err

    run_text = (tmp_path / agent_name / "run.py").read_text()
    assert "from langgraph.graph import END, START, StateGraph" in run_text
    assert "class GraphState(TypedDict):" in run_text
    assert "graph_builder.add_edge(START, \"respond\")" in run_text
    assert "graph_builder.add_edge(\"respond\", END)" in run_text
    assert "KINNOO_TEST_SAFE_MODE" in run_text
    assert "test-safe response" in run_text
    assert "Placeholder scaffold for LangGraph-style node/edge orchestration" not in run_text


def test_feature21_openai_agents_framework_native_template(tmp_path):
    agent_name = "feature21-openai-agents-native"
    code, out, err = run_cli(["init", agent_name, "--framework", "openai-agents"], cwd=tmp_path)
    assert code == 0, err

    run_text = (tmp_path / agent_name / "run.py").read_text()
    assert "from agents import Agent" in run_text
    assert "from agents import Runner" in run_text
    assert "return Agent(" in run_text
    assert "await Runner.run(agent, input_text)" in run_text
    assert "KINNOO_TEST_SAFE_MODE" in run_text
    assert "test-safe response" in run_text
    assert "Placeholder scaffold for OpenAI Agents handoff/guardrail flow" not in run_text


def test_feature21_templates_emit_optional_model_metadata_when_known(tmp_path):
    import yaml
    from kinnoo.validator import validate

    expected_models = {
        "gemini": "gemini-2.5-flash-lite",
        "chatgpt": "gpt-5-nano",
        "claude-chat": "claude-sonnet-4-20250514",
        "pydantic-ai": "openai:gpt-4o-mini",
    }

    for framework, expected_model in expected_models.items():
        agent_name = f"feature21-model-known-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        manifest_path = tmp_path / agent_name / "kinnoo.yaml"
        is_valid, errors = validate(str(manifest_path))
        assert is_valid, errors

        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data.get("model") == expected_model

    for framework in ["langgraph", "openai-agents"]:
        agent_name = f"feature21-model-unknown-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        manifest_path = tmp_path / agent_name / "kinnoo.yaml"
        is_valid, errors = validate(str(manifest_path))
        assert is_valid, errors

        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "model" not in manifest_data


def test_feature9_init_manifest_includes_description_and_author(tmp_path):
    """test75: init-generated manifest includes description and author placeholders."""
    agent_name = "feature9-init-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None

    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    assert manifest_path.exists()

    import yaml

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert "description" in manifest
    assert isinstance(manifest["description"], str)
    assert manifest["description"].strip() != ""

    assert "author" in manifest
    assert isinstance(manifest["author"], str)
    assert manifest["author"].strip() != ""


def test_feature26_mcp_client_template_generation(tmp_path):
    """Feature26 test240: init generates SDK-based mcp-client template and workflow README."""
    agent_name = "feature26-mcp-client-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "mcp-client"], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "README.md").exists()

    run_text = (agent_dir / "run.py").read_text(encoding="utf-8")
    requirements_text = (agent_dir / "requirements.txt").read_text(encoding="utf-8")
    readme_text = (agent_dir / "README.md").read_text(encoding="utf-8")

    assert "ClientSession" in run_text
    assert "StdioServerParameters" in run_text
    assert "stdio_client" in run_text
    assert "BaseMCPAgent" in run_text
    assert "connect_to_server" in run_text
    assert "load_dotenv" in run_text
    assert "MCP_SERVER_CMD" in run_text
    assert "MCP_SERVER_ENV" in run_text
    assert "get_tools" in run_text
    assert "execute_tool" in run_text
    assert "mcp" in requirements_text
    assert "python-dotenv" in requirements_text
    assert "Suggested End-to-End Workflow" in readme_text
    assert "kinnoo/cli.py pack" in readme_text
    assert "kinnoo/cli.py install" in readme_text
    assert "MCP_SERVER_CMD" in readme_text
    assert "MCP_SERVER_ENV" in readme_text


def test_feature26_mcp_client_template_contract_and_validation(tmp_path):
    """Feature26 test241: generated mcp-client template follows runtime contract."""
    from kinnoo.validator import validate

    agent_name = "feature26-mcp-client-contract"
    code, out, err = run_cli(["init", agent_name, "--framework", "mcp-client"], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid is True, errors
    assert errors == []

    run_path = agent_dir / "run.py"
    run_text = run_path.read_text(encoding="utf-8")
    assert "sys.argv[1]" in run_text
    assert "print(" in run_text
    assert "BaseMCPAgent" in run_text
    assert "load_dotenv" in run_text

    result = subprocess.run([sys.executable, str(run_path), "contract-input"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Set MCP_SERVER_CMD" in result.stdout


def test_framework_mcp_server_scaffold_generation(tmp_path):
    """test354 (deprecated): mcp-server scaffold currently includes unsupported channels field."""
    import yaml
    from kinnoo.validator import validate

    agent_name = "feature45-mcp-server"
    code, out, err = run_cli(["init", agent_name, "--framework", "mcp-server"], cwd=tmp_path)
    assert code == 0, err

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "README.md").exists()
    assert (agent_dir / "requirements.txt").exists()

    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid is False
    assert any("Field 'channels' is not supported" in message for message in errors)

    manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data.get("framework") == "mcp-server"
    assert manifest_data.get("runtime", {}).get("type") == "mcp-server"


def test_init_help_includes_mcp_server_example(tmp_path):
    """test355: init help text includes an explicit mcp-server example."""
    code, out, err = run_cli(["init", "-h"], cwd=tmp_path)
    assert code == 0
    assert "kinnoo init my-mcp-server --framework mcp-server" in out


def test_feature77_init_delegation_and_existing_workspace_guard(tmp_path, monkeypatch):
    from kinnoo import init_command

    order: list[str] = []
    workspace = tmp_path / ".openclaw" / "workspace-foo"

    monkeypatch.setattr(init_command.Path, "home", staticmethod(lambda: tmp_path))

    def fake_preflight(command_name: str, minimum_version: str = "2026.3.28"):
        order.append(f"preflight:{command_name}:{minimum_version}")
        from kinnoo.openclaw_preflight import OpenClawPreflightResult

        return OpenClawPreflightResult(
            ok=True,
            category="openclaw_cli_precheck_ok",
            message="ok",
            version="2026.3.31",
        )

    def fake_run(args, capture_output, text, check):
        order.append("subprocess:agents-add")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(init_command, "run_openclaw_preflight_for_command", fake_preflight)
    monkeypatch.setattr(init_command.subprocess, "run", fake_run)

    init_command.init_agent("foo", tmp_path, framework="openclaw")

    assert workspace.exists()
    assert order[0].startswith("preflight:init")
    assert order[1] == "subprocess:agents-add"

    with pytest.raises(FileExistsError):
        init_command.init_agent("foo", tmp_path, framework="openclaw")


def test_feature77_init_manifest_and_summary(tmp_path, monkeypatch, capsys):
    from kinnoo import init_command
    from kinnoo.validator import validate

    workspace = tmp_path / ".openclaw" / "workspace-bar"
    monkeypatch.setattr(init_command.Path, "home", staticmethod(lambda: tmp_path))

    def fake_preflight(command_name: str, minimum_version: str = "2026.3.28"):
        from kinnoo.openclaw_preflight import OpenClawPreflightResult

        return OpenClawPreflightResult(
            ok=True,
            category="openclaw_cli_precheck_ok",
            message="ok",
            version="2026.3.31",
        )

    def fake_run(args, capture_output, text, check):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(init_command, "run_openclaw_preflight_for_command", fake_preflight)
    monkeypatch.setattr(init_command.subprocess, "run", fake_run)

    init_command.init_agent("bar", tmp_path, framework="openclaw")
    output = capsys.readouterr().out

    manifest_path = workspace / "kinnoo.yaml"
    assert manifest_path.exists()
    is_valid, errors = validate(str(manifest_path))
    assert is_valid is True, errors

    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "language: nodejs" in manifest_text
    assert "type: daemon" in manifest_text
    assert "channels:" not in manifest_text
    assert "skills:" not in manifest_text
    assert "state_dirs:" not in manifest_text

    assert "[kinnoo init][openclaw] agent=bar" in output
    assert f"workspace={workspace}" in output
    assert "next: edit SOUL.md" in output
