import subprocess
import sys
import os
import re
import signal
import tempfile
import time
from pathlib import Path
import json

import pytest
import yaml

from src.kinnoo.analyzer import analyze_project
from src.kinnoo.validator import validate as validate_manifest


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"
LARGE_PROJECT_FILE_COUNT = 240


def test_feature19_import_defaults_to_current_directory(tmp_path):
    project_dir = tmp_path / "feature19-default-path-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Detected values from analyzer:" in result.stdout
    assert "Usage:" not in result.stderr


def test_feature19_import_invalid_args_show_usage(tmp_path):
    project_dir = tmp_path / "feature19-invalid-args-project"
    project_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "extra-arg"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "usage:" in combined
    assert "import" in combined


def test_feature19_import_writes_manifest_in_place(tmp_path):
    project_dir = tmp_path / "feature19-write-in-place-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello from existing project')\n", encoding="utf-8")
    (project_dir / "notes.txt").write_text("keep me unchanged\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Imported project in-place:" in result.stdout
    manifest_path = project_dir / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text
    assert "runtime:" in manifest_text
    # Ensure no scaffold-copy behavior: only existing files plus kinnoo.yaml.
    assert not (project_dir / "prompts").exists()
    assert not (project_dir / "tools").exists()
    assert (project_dir / "notes.txt").read_text(encoding="utf-8") == "keep me unchanged\n"


def test_feature19_import_failure_rolls_back_partial_output(tmp_path):
    project_dir = tmp_path / "feature19-rollback-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('rollback project')\n", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_IMPORT_FAIL_AFTER_WRITE"] = "1"

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "rolled back partial artifacts" in combined
    assert not (project_dir / "kinnoo.yaml").exists()


def test_feature19_import_collision_requires_explicit_override(tmp_path):
    project_dir = tmp_path / "feature19-collision-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    existing_manifest = (
        "name: existing-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    manifest_path = project_dir / "kinnoo.yaml"
    manifest_path.write_text(existing_manifest, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "already exists" in combined
    assert "override" in combined
    assert manifest_path.read_text(encoding="utf-8") == existing_manifest

    force_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "--force"],
        input="y\nrun.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )

    assert force_result.returncode == 0
    assert "Imported project in-place:" in force_result.stdout
    assert manifest_path.read_text(encoding="utf-8") != existing_manifest


def test_feature19_import_uses_analyzer_inference_and_warnings(tmp_path):
    project_dir = tmp_path / "feature19-analyzer-integration-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "import anthropic\n"
        "import os\n"
        "token = os.getenv('API_TOKEN')\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\nchatgpt\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = (result.stdout + result.stderr).lower()
    assert "detected values from analyzer" in combined_output
    assert "analyzer warnings" in combined_output
    assert "ambiguous" in combined_output

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text
    assert "framework: chatgpt" in manifest_text
    assert "requests==2.31.0" in manifest_text
    assert "api_token" in manifest_text.lower()


def test_feature19_confirm_first_wizard_prompt_minimization(tmp_path):
    project_dir = tmp_path / "feature19-confirm-first-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("tomli>=2.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Detected values from analyzer:" in combined_output
    assert "Proceed with detected values?" in combined_output
    assert "Provide value for" not in combined_output


def test_feature19_import_keeps_inferred_entrypoint_without_reprompt(tmp_path):
    project_dir = tmp_path / "feature19-inferred-entrypoint-no-reprompt"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "base.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Detected values from analyzer:" in combined_output
    assert "Proceed with detected values?" in combined_output
    assert "Provide value for entrypoint" not in combined_output

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: base.py" in manifest_text


def test_feature19_conditional_prompts_for_runtime_services_permissions(tmp_path):
    high_confidence_project = tmp_path / "feature19-conditional-prompts-high"
    high_confidence_project.mkdir(parents=True, exist_ok=True)
    (high_confidence_project / "run.py").write_text(
        "import sys\n"
        "import openai\n"
        "service_url = 'https://api.example.com/health'\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )

    high_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(high_confidence_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert high_result.returncode == 0
    high_output = high_result.stdout + high_result.stderr
    assert "Provide value for runtime.type" not in high_output
    assert "Provide services" not in high_output
    assert "Configure permissions for mcp-server" not in high_output

    low_confidence_project = tmp_path / "feature19-conditional-prompts-low"
    low_confidence_project.mkdir(parents=True, exist_ok=True)
    (low_confidence_project / "README.md").write_text("no python files yet\n", encoding="utf-8")

    low_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(low_confidence_project)],
        input="y\nrun.py\nmcp-server\n\ny\ny\nn\nn\n/tmp\n",
        capture_output=True,
        text=True,
    )

    assert low_result.returncode == 0
    low_output = low_result.stdout + low_result.stderr
    assert "Provide value for runtime.type" in low_output
    assert "Provide services" not in low_output
    assert "Configure permissions for mcp-server" in low_output

    low_manifest = (low_confidence_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "runtime:" in low_manifest
    assert "type: mcp-server" in low_manifest
    assert "permissions:" in low_manifest


def test_feature19_entrypoint_warning_and_optional_wrapper(tmp_path):
    no_wrapper_project = tmp_path / "feature19-wrapper-default"
    no_wrapper_project.mkdir(parents=True, exist_ok=True)
    (no_wrapper_project / "run.py").write_text(
        "def run():\n"
        "    print('no argv contract')\n",
        encoding="utf-8",
    )

    no_wrapper_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(no_wrapper_project)],
        input="y\n\nn\n",
        capture_output=True,
        text=True,
    )

    assert no_wrapper_result.returncode == 0
    no_wrapper_output = no_wrapper_result.stdout + no_wrapper_result.stderr
    assert "Entrypoint compatibility warning:" in no_wrapper_output
    assert "Generate optional wrapper entrypoint bridge?" in no_wrapper_output
    assert not (no_wrapper_project / "kinnoo_wrapper.py").exists()

    wrapper_project = tmp_path / "feature19-wrapper-opt-in"
    wrapper_project.mkdir(parents=True, exist_ok=True)
    (wrapper_project / "run.py").write_text(
        "def run():\n"
        "    print('no argv contract')\n",
        encoding="utf-8",
    )

    wrapper_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(wrapper_project)],
        input="y\n\ny\n",
        capture_output=True,
        text=True,
    )

    assert wrapper_result.returncode == 0
    wrapper_output = wrapper_result.stdout + wrapper_result.stderr
    assert "Entrypoint compatibility warning:" in wrapper_output
    assert (wrapper_project / "kinnoo_wrapper.py").exists()

    wrapper_manifest = (wrapper_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: kinnoo_wrapper.py" in wrapper_manifest


def test_feature19_interrupt_cleanup_and_exit_code(tmp_path):
    eof_project = tmp_path / "feature19-interrupt-eof"
    eof_project.mkdir(parents=True, exist_ok=True)
    (eof_project / "README.md").write_text("force unresolved prompts\n", encoding="utf-8")

    # Non-interactive EOF should follow defaults for automation-safe behavior.
    eof_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(eof_project)],
        input="",
        capture_output=True,
        text=True,
    )

    assert eof_result.returncode == 0
    assert (eof_project / "kinnoo.yaml").exists()

    sigint_project = tmp_path / "feature19-interrupt-sigint"
    sigint_project.mkdir(parents=True, exist_ok=True)
    (sigint_project / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [sys.executable, str(CLI_PATH), "import", str(sigint_project)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.2)
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
    sigint_stdout, sigint_stderr = process.communicate(timeout=5)

    sigint_output = sigint_stdout + sigint_stderr
    assert process.returncode != 0
    assert "interrupted" in sigint_output.lower()
    assert not (sigint_project / "kinnoo.yaml").exists()
    assert not (sigint_project / "kinnoo_wrapper.py").exists()


def test_feature19_imported_project_runs_in_place(tmp_path):
    project_dir = tmp_path / "feature19-import-runnable"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "requirements.txt").write_text("\n", encoding="utf-8")
    (project_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(f\"imported-runnable:{sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
        encoding="utf-8",
    )

    import_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )

    assert import_result.returncode == 0
    assert (project_dir / "kinnoo.yaml").exists()

    run_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(project_dir), "hello-import"],
        capture_output=True,
        text=True,
    )

    combined_output = run_result.stdout + run_result.stderr
    assert run_result.returncode == 0
    assert "imported-runnable:hello-import" in combined_output


@pytest.mark.skip(reason="[agent - deprecated - do not execute]")
def test_feature36_openclaw_detection_weighted_confidence_output(tmp_path):
    # [agent - deprecated - do not execute]
    strong_project = tmp_path / "feature36-openclaw-import-strong"
    strong_project.mkdir(parents=True, exist_ok=True)
    (strong_project / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (strong_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (strong_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-import-strong\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (strong_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (strong_project / "skills" / "default" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (strong_project / "memory").mkdir(parents=True, exist_ok=True)

    strong_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(strong_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    strong_output = strong_result.stdout + strong_result.stderr
    assert strong_result.returncode == 0
    assert "framework: openclaw" in strong_output.lower()
    assert "Framework confidence metadata:" in strong_output
    assert "weighted detection score" in strong_output.lower()
    assert "openclaw.json" in strong_output

    medium_project = tmp_path / "feature36-openclaw-import-medium"
    medium_project.mkdir(parents=True, exist_ok=True)
    (medium_project / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (medium_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (medium_project / "skills" / "default" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (medium_project / "memory").mkdir(parents=True, exist_ok=True)

    medium_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(medium_project)],
        input="y\nopenclaw\n",
        capture_output=True,
        text=True,
    )

    medium_output = medium_result.stdout + medium_result.stderr
    assert medium_result.returncode == 0
    assert "openclaw detection confidence is mixed" in medium_output.lower()
    assert "weighted detection score" in medium_output.lower()


@pytest.mark.skip(reason="[agent - deprecated - do not execute]")
def test_feature36_infers_runtime_skills_state_dirs(tmp_path):
    # [agent - deprecated - do not execute]
    project_dir = tmp_path / "feature36-openclaw-inference"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (project_dir / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (project_dir / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-inference\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (project_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (project_dir / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (project_dir / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (project_dir / "memory" / "daily").mkdir(parents=True, exist_ok=True)
    (project_dir / "memory" / "daily" / "journal.md").write_text("entry\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "type: openclaw-skill" in manifest_text
    assert "language: nodejs" in manifest_text
    assert "type: daemon" in manifest_text
    assert "package_manager: pnpm" in manifest_text
    assert "skills:" not in manifest_text
    assert "state_dirs:" not in manifest_text
    assert "channels:" not in manifest_text


@pytest.mark.skip(reason="[agent - deprecated - do not execute]")
def test_feature36_manifest_valid_or_todo_guidance(tmp_path):
    # [agent - deprecated - do not execute]
    complete_project = tmp_path / "feature36-manifest-guidance-complete"
    complete_project.mkdir(parents=True, exist_ok=True)
    (complete_project / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (complete_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (complete_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-manifest-guidance-complete\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (complete_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (complete_project / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (complete_project / "memory").mkdir(parents=True, exist_ok=True)

    complete_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(complete_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    complete_output = complete_result.stdout + complete_result.stderr
    assert complete_result.returncode == 0
    assert "Generated manifest validation: PASS" in complete_output

    unresolved_project = tmp_path / "feature36-manifest-guidance-unresolved"
    unresolved_project.mkdir(parents=True, exist_ok=True)
    (unresolved_project / "README.md").write_text("import fixture without executable entrypoint\n", encoding="utf-8")

    unresolved_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(unresolved_project)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )

    unresolved_output = unresolved_result.stdout + unresolved_result.stderr
    assert unresolved_result.returncode == 0
    assert "Generated manifest validation: PASS" in unresolved_output
    assert "TODO guidance:" in unresolved_output
    assert "Verify 'entrypoint' points to an existing executable script in the project root." in unresolved_output
    assert "does not exist in target project" in unresolved_output


@pytest.mark.skip(reason="[agent - deprecated - do not execute]")
def test_feature62_import_openclaw_manifest_migration_guidance(tmp_path):
    # [agent - deprecated - do not execute]
    project_dir = tmp_path / "feature62-openclaw-import-migration"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (project_dir / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (project_dir / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature62-openclaw-import-migration\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("\n", encoding="utf-8")

    import_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert import_result.returncode == 0, import_result.stdout + import_result.stderr
    manifest_path = project_dir / "kinnoo.yaml"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "type: openclaw-skill" in manifest_text
    assert "channels:" not in manifest_text
    assert "skills:" not in manifest_text
    assert "state_dirs:" not in manifest_text

    manifest_data = yaml.safe_load(manifest_text)
    manifest_data["provenance"] = {
        "source_registry": "clawhub",
        "source_version": "1.0.0",
    }
    manifest_data["state_dirs"] = ["memory"]
    manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

    inspect_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "inspect", str(project_dir)],
        capture_output=True,
        text=True,
    )

    combined = inspect_result.stdout + inspect_result.stderr
    assert inspect_result.returncode != 0
    assert "provenance" in combined and "source_slug" in combined and "source_url" in combined
    assert "Field 'state_dirs' is not supported in this schema version" in combined


def test_import_rejects_deprecated_clawhub_flags():
    destination = Path.cwd() / "unused-destination"
    source_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--source",
            "clawhub",
            "weather/weather-skill",
            str(destination),
        ],
        capture_output=True,
        text=True,
    )
    source_output = source_result.stdout + source_result.stderr
    assert source_result.returncode != 0
    assert "unrecognized arguments:" in source_output.lower()
    assert "--source" in source_output

    fallback_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--live-fallback",
            "dummy-path",
        ],
        capture_output=True,
        text=True,
    )
    fallback_output = fallback_result.stdout + fallback_result.stderr
    assert fallback_result.returncode != 0
    assert "unrecognized arguments:" in fallback_output.lower()
    assert "--live-fallback" in fallback_output

    with tempfile.TemporaryDirectory(prefix="kinnoo-import-removed-flag-smoke-") as temp_dir:
        project_dir = Path(temp_dir) / "smoke-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
        success_result = subprocess.run(
            [sys.executable, str(CLI_PATH), "import", str(project_dir)],
            capture_output=True,
            text=True,
        )
        assert success_result.returncode == 0
        assert (project_dir / "kinnoo.yaml").exists()


def _make_feature78_fake_openclaw_cli(bin_dir: Path, *, agent_list_json: str = "[]") -> Path:
    script = bin_dir / "openclaw"
    script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'openclaw 2026.3.31'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"agents\" ] && [ \"$2\" = \"list\" ]; then\n"
        f"  echo '{agent_list_json}'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"agents\" ] && [ \"$2\" = \"add\" ]; then\n"
        "  if [ -n \"$KINNOO_OPENCLAW_INVOCATION_LOG\" ]; then\n"
        "    echo \"$*\" >> \"$KINNOO_OPENCLAW_INVOCATION_LOG\"\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported command >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_feature78_import_detection_manifest_and_error_paths(tmp_path):
    fake_bin = tmp_path / "feature78-openclaw-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    _make_feature78_fake_openclaw_cli(fake_bin, agent_list_json='[{"id":"feature78-openclaw"}]')

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    workspace = tmp_path / ".openclaw" / "workspace-feature78-openclaw"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (workspace / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature78-openclaw\",\n"
        "  \"version\": \"1.0.0\"\n"
        "}\n",
        encoding="utf-8",
    )
    (workspace / "index.mjs").write_text("console.log('ok')\n", encoding="utf-8")

    good_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(workspace)],
        input="y\n",
        capture_output=True,
        text=True,
        env=env,
    )
    assert good_result.returncode == 0, good_result.stdout + good_result.stderr
    manifest_path = workspace / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "language: nodejs" in manifest_text

    missing_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(tmp_path / "does-not-exist")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert missing_result.returncode != 0
    assert "import target does not exist" in (missing_result.stdout + missing_result.stderr).lower()

    file_target = tmp_path / "not-a-dir.txt"
    file_target.write_text("x\n", encoding="utf-8")
    file_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(file_target)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert file_result.returncode != 0
    assert "import target must be a directory" in (file_result.stdout + file_result.stderr).lower()


def test_feature78_copy_and_registration_flows(tmp_path):
    fake_bin = tmp_path / "feature78-openclaw-bin-copy"
    fake_bin.mkdir(parents=True, exist_ok=True)
    invocation_log = tmp_path / "feature78-openclaw-invocations.log"
    _make_feature78_fake_openclaw_cli(fake_bin, agent_list_json="[]")

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)
    env["KINNOO_OPENCLAW_INVOCATION_LOG"] = str(invocation_log)

    external_workspace = tmp_path / "external-openclaw-workspace"
    external_workspace.mkdir(parents=True, exist_ok=True)
    (external_workspace / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (external_workspace / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
    (external_workspace / "SOUL.md").write_text("# soul\n", encoding="utf-8")
    (external_workspace / "index.mjs").write_text("console.log('ok')\n", encoding="utf-8")

    copy_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(external_workspace)],
        input="y\ny\n",
        capture_output=True,
        text=True,
        env=env,
    )
    assert copy_result.returncode == 0, copy_result.stdout + copy_result.stderr

    copied_workspace = tmp_path / ".openclaw" / "workspace-external-openclaw-workspace"
    assert copied_workspace.exists()
    assert (copied_workspace / "kinnoo.yaml").exists()

    in_place_workspace = tmp_path / ".openclaw" / "workspace-inplace-openclaw"
    in_place_workspace.mkdir(parents=True, exist_ok=True)
    (in_place_workspace / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (in_place_workspace / "index.mjs").write_text("console.log('ok')\n", encoding="utf-8")

    in_place_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(in_place_workspace)],
        input="y\n",
        capture_output=True,
        text=True,
        env=env,
    )
    assert in_place_result.returncode == 0, in_place_result.stdout + in_place_result.stderr

    invocation_text = invocation_log.read_text(encoding="utf-8")
    assert "agents add external-openclaw-workspace" in invocation_text
    assert "agents add inplace-openclaw" in invocation_text


def test_feature19_import_generates_requirements_via_uv_export(tmp_path):
    project_dir = tmp_path / "feature19-uv-export-requirements"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    uv_path = fake_bin / "uv"
    uv_path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"export\" ]; then\n"
        "  echo 'requests==2.32.3'\n"
        "  exit 0\n"
        "fi\n"
        "echo 'unexpected uv invocation' >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    uv_path.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Generated requirements.txt via uv export." in output
    requirements_text = (project_dir / "requirements.txt").read_text(encoding="utf-8")
    assert requirements_text == "requests==2.32.3\n"


def test_feature19_import_generates_empty_requirements_when_detection_unavailable(tmp_path):
    project_dir = tmp_path / "feature19-empty-requirements-fallback"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    env = dict(os.environ)
    env["PATH"] = ""

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Generated empty requirements.txt" in output
    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "requirements.txt").read_text(encoding="utf-8") == ""


def test_feature19_import_generates_requirements_from_import_inference(tmp_path):
    project_dir = tmp_path / "feature19-import-inferred-deps"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "base.py").write_text(
        "from langchain_core.agents import AgentAction\n"
        "print(AgentAction)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\nbase.py\nlangchain\n\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Generated requirements.txt from analyzer-detected dependencies." in output
    requirements_text = (project_dir / "requirements.txt").read_text(encoding="utf-8")
    assert "langchain-core" in requirements_text


def test_feature75_adapter_inference_and_fallback(tmp_path):
    langchain_project = tmp_path / "feature75-langchain"
    langchain_project.mkdir(parents=True, exist_ok=True)
    (langchain_project / "run.py").write_text(
        "from langchain.agents import AgentExecutor\n"
        "print(AgentExecutor)\n",
        encoding="utf-8",
    )

    langchain_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(langchain_project), "--from", "langchain"],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    langchain_output = f"{langchain_result.stdout}\n{langchain_result.stderr}"
    assert langchain_result.returncode == 0, langchain_output
    assert "Applied langchain adapter" in langchain_output
    langchain_manifest = (langchain_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: langchain" in langchain_manifest
    assert "language: python" in langchain_manifest

    langgraph_project = tmp_path / "feature75-langgraph"
    langgraph_project.mkdir(parents=True, exist_ok=True)
    (langgraph_project / "graph.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "print(StateGraph)\n",
        encoding="utf-8",
    )

    langgraph_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(langgraph_project), "--from", "langgraph"],
        input="y\ngraph.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )
    langgraph_output = f"{langgraph_result.stdout}\n{langgraph_result.stderr}"
    assert langgraph_result.returncode == 0, langgraph_output
    assert "Applied langgraph adapter" in langgraph_output
    langgraph_manifest = (langgraph_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: langgraph" in langgraph_manifest

    openai_project = tmp_path / "feature75-openai"
    openai_project.mkdir(parents=True, exist_ok=True)
    (openai_project / "agent.py").write_text(
        "from agents import Agent\n"
        "print(Agent)\n",
        encoding="utf-8",
    )

    openai_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(openai_project), "--from", "openai"],
        input="y\nagent.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )
    openai_output = f"{openai_result.stdout}\n{openai_result.stderr}"
    assert openai_result.returncode == 0, openai_output
    assert "Applied openai adapter" in openai_output
    openai_manifest = (openai_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: openai-agents" in openai_manifest

    unsupported_project = tmp_path / "feature75-fallback"
    unsupported_project.mkdir(parents=True, exist_ok=True)
    (unsupported_project / "run.py").write_text("print('hello')\n", encoding="utf-8")

    fallback_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(unsupported_project), "--from", "langgraph"],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    fallback_output = f"{fallback_result.stdout}\n{fallback_result.stderr}"
    assert fallback_result.returncode == 0, fallback_output
    assert "falling back to generic analyzer output" in fallback_output


def test_feature75_adapter_confidence_tuning_and_guidance(tmp_path):
    project_dir = tmp_path / "feature75-confidence"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "from langchain.agents import AgentExecutor\n"
        "print(AgentExecutor)\n",
        encoding="utf-8",
    )

    generic_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "--force"],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    generic_output = f"{generic_result.stdout}\n{generic_result.stderr}"
    assert generic_result.returncode == 0, generic_output

    adapter_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            str(project_dir),
            "--force",
            "--from",
            "langchain",
        ],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    adapter_output = f"{adapter_result.stdout}\n{adapter_result.stderr}"
    assert adapter_result.returncode == 0, adapter_output
    assert "Applied langchain adapter" in adapter_output
    assert "Adapter guidance:" in adapter_output

    generic_score_match = re.search(r"Framework confidence metadata:\n\s*- score: ([0-9.]+)", generic_output)
    adapter_score_match = re.search(r"Framework confidence metadata:\n\s*- score: ([0-9.]+)", adapter_output)
    assert generic_score_match is not None
    assert adapter_score_match is not None
    assert float(adapter_score_match.group(1)) >= float(generic_score_match.group(1))

    fallback_project = tmp_path / "feature75-threshold-fallback"
    fallback_project.mkdir(parents=True, exist_ok=True)
    (fallback_project / "run.py").write_text("print('no markers')\n", encoding="utf-8")

    fallback_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            str(fallback_project),
            "--from",
            "openai",
        ],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    fallback_output = f"{fallback_result.stdout}\n{fallback_result.stderr}"
    assert fallback_result.returncode == 0, fallback_output
    assert "coverage is insufficient" in fallback_output
    assert "required>=0.60" in fallback_output


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.security_checks
def test_feature117_import_edge_cases_no_traceback(tmp_path):
    empty_project = tmp_path / "feature117-empty-project"
    empty_project.mkdir(parents=True, exist_ok=True)

    unsupported_project = tmp_path / "feature117-unsupported-language"
    unsupported_project.mkdir(parents=True, exist_ok=True)
    (unsupported_project / "main.java").write_text("class Main {}\n", encoding="utf-8")

    ambiguous_project = tmp_path / "feature117-ambiguous-framework"
    ambiguous_project.mkdir(parents=True, exist_ok=True)
    (ambiguous_project / "app.py").write_text("import openai\nprint('app')\n", encoding="utf-8")
    (ambiguous_project / "worker.py").write_text("import anthropic\nprint('worker')\n", encoding="utf-8")

    large_project = tmp_path / "feature117-large-project"
    large_project.mkdir(parents=True, exist_ok=True)
    for index in range(0, LARGE_PROJECT_FILE_COUNT):
        (large_project / f"module_{index}.py").write_text(f"print('module-{index}')\n", encoding="utf-8")
    (large_project / "run.py").write_text("print('large')\n", encoding="utf-8")

    for project in (empty_project, unsupported_project, ambiguous_project, large_project):
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "import", str(project)],
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}".lower()
        assert "traceback" not in output
        assert "imported project in-place:" in output or "error:" in output

    ambiguous_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(ambiguous_project), "--force"],
        capture_output=True,
        text=True,
    )
    assert "analyzer warnings" in f"{ambiguous_result.stdout}\n{ambiguous_result.stderr}".lower()


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.schema_contract
def test_feature117_generated_manifest_validation_gate(tmp_path):
    valid_project = tmp_path / "feature117-validation-gate-valid"
    valid_project.mkdir(parents=True, exist_ok=True)
    (valid_project / "run.py").write_text("print('ok')\n", encoding="utf-8")

    valid_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(valid_project)],
        capture_output=True,
        text=True,
    )
    assert valid_result.returncode == 0
    manifest_path = valid_project / "kinnoo.yaml"
    assert manifest_path.exists()
    is_valid, errors = validate_manifest(str(manifest_path))
    assert is_valid, errors

    invalid_project = tmp_path / "feature117-validation-gate-invalid"
    invalid_project.mkdir(parents=True, exist_ok=True)
    (invalid_project / "run.py").write_text("print('ok')\n", encoding="utf-8")
    env = dict(os.environ)
    env["KINNOO_IMPORT_FORCE_INVALID_MANIFEST"] = "1"

    invalid_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(invalid_project)],
        capture_output=True,
        text=True,
        env=env,
    )
    invalid_output = f"{invalid_result.stdout}\n{invalid_result.stderr}"
    assert invalid_result.returncode != 0
    assert "Generated kinnoo.yaml failed validation; import aborted before write." in invalid_output
    assert "Remediation:" in invalid_output
    assert not (invalid_project / "kinnoo.yaml").exists()


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
def test_feature117_error_message_contract_consistency(tmp_path):
    collision_project = tmp_path / "feature117-error-collision"
    collision_project.mkdir(parents=True, exist_ok=True)
    (collision_project / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (collision_project / "kinnoo.yaml").write_text("name: existing\nversion: 1.0.0\n", encoding="utf-8")

    invalid_target = tmp_path / "feature117-missing-target"
    extra_arg_project = tmp_path / "feature117-extra-arg-project"
    extra_arg_project.mkdir(parents=True, exist_ok=True)
    (extra_arg_project / "run.py").write_text("print('ok')\n", encoding="utf-8")

    scenarios = [
        [sys.executable, str(CLI_PATH), "import", str(collision_project)],
        [sys.executable, str(CLI_PATH), "import", str(invalid_target)],
        [sys.executable, str(CLI_PATH), "import", str(extra_arg_project), "extra-positional"],
    ]

    for command in scenarios:
        result = subprocess.run(command, capture_output=True, text=True)
        output = f"{result.stdout}\n{result.stderr}"
        lowered = output.lower()
        assert result.returncode != 0
        assert "error:" in lowered
        assert "traceback" not in lowered
        assert "remediation:" in lowered or "usage:" in lowered


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.analyzer
def test_feature117_langchain_subpackage_inference(tmp_path):
    project_dir = tmp_path / "feature117-langchain-subpackage"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "from langchain_openai import ChatOpenAI\n"
        "from langchain_core.runnables import RunnableLambda\n"
        "chain = RunnableLambda(lambda x: x)\n"
        "print(ChatOpenAI, chain)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "--from", "langchain"],
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "Applied langchain adapter" in output

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    requirements_text = (project_dir / "requirements.txt").read_text(encoding="utf-8")
    assert "framework: langchain" in manifest_text
    assert "OPENAI_API_KEY" in manifest_text
    assert "langchain-openai" in requirements_text
    assert "langchain-core" in requirements_text


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.analyzer
def test_feature117_openai_base_vs_agents_sdk_detection(tmp_path):
    base_project = tmp_path / "feature117-openai-base"
    base_project.mkdir(parents=True, exist_ok=True)
    (base_project / "run.py").write_text(
        "from openai import OpenAI\n"
        "client = OpenAI()\n"
        "print(client)\n",
        encoding="utf-8",
    )

    base_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(base_project), "--from", "openai"],
        capture_output=True,
        text=True,
    )
    base_output = f"{base_result.stdout}\n{base_result.stderr}"
    assert base_result.returncode == 0, base_output
    base_manifest = (base_project / "kinnoo.yaml").read_text(encoding="utf-8")
    base_requirements = (base_project / "requirements.txt").read_text(encoding="utf-8")
    assert "framework: openai\n" in base_manifest or "framework: openai\r\n" in base_manifest
    assert "openai-agents" not in base_requirements
    assert "openai" in base_requirements

    agents_project = tmp_path / "feature117-openai-agents"
    agents_project.mkdir(parents=True, exist_ok=True)
    (agents_project / "agent.py").write_text(
        "from agents import Agent\n"
        "agent = Agent(name='demo')\n"
        "print(agent)\n",
        encoding="utf-8",
    )

    agents_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(agents_project), "--from", "openai"],
        capture_output=True,
        text=True,
    )
    agents_output = f"{agents_result.stdout}\n{agents_result.stderr}"
    assert agents_result.returncode == 0, agents_output
    agents_manifest = (agents_project / "kinnoo.yaml").read_text(encoding="utf-8")
    agents_requirements = (agents_project / "requirements.txt").read_text(encoding="utf-8")
    assert "framework: openai-agents" in agents_manifest
    assert "openai-agents" in agents_requirements


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.client_cli_check
def test_feature117_openclaw_from_copy_contract(tmp_path):
    workspace = tmp_path / "feature117-openclaw-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (workspace / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")
    (workspace / "memory").mkdir(parents=True, exist_ok=True)
    (workspace / "memory" / "state.json").write_text("{\"k\":\"v\"}\n", encoding="utf-8")
    (workspace / "skills").mkdir(parents=True, exist_ok=True)
    (workspace / "skills" / "skill.md").write_text("# Skill\n", encoding="utf-8")
    (workspace / "run.py").write_text("print('openclaw import')\n", encoding="utf-8")

    (workspace / ".git").mkdir(parents=True, exist_ok=True)
    (workspace / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (workspace / ".openclaw").mkdir(parents=True, exist_ok=True)
    (workspace / ".openclaw" / "cache.txt").write_text("cache\n", encoding="utf-8")
    (workspace / ".clawhub").mkdir(parents=True, exist_ok=True)
    (workspace / ".clawhub" / "mirror.json").write_text("{}\n", encoding="utf-8")
    (workspace / "node_modules").mkdir(parents=True, exist_ok=True)
    (workspace / "node_modules" / "pkg.js").write_text("module.exports={};\n", encoding="utf-8")
    (workspace / ".venv").mkdir(parents=True, exist_ok=True)
    (workspace / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (workspace / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    if hasattr(os, "symlink"):
        outside_file = tmp_path / "feature117-outside.txt"
        outside_file.write_text("outside\n", encoding="utf-8")
        (workspace / "skills" / "outside-link.txt").symlink_to(outside_file)

    target = tmp_path / "feature117-openclaw-target"

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--from",
            "openclaw",
            str(target),
            str(workspace),
        ],
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "Imported OpenClaw workspace in-place:" in output

    assert (target / "SOUL.md").exists()
    assert (target / "IDENTITY.md").exists()
    assert (target / "memory" / "state.json").exists()
    assert (target / "skills" / "skill.md").exists()
    assert (target / "run.py").exists()
    assert not (target / "skills" / "outside-link.txt").exists()

    assert not (target / ".git").exists()
    assert not (target / ".openclaw").exists()
    assert not (target / ".clawhub").exists()
    assert not (target / "node_modules").exists()
    assert not (target / ".venv").exists()

    manifest_path = target / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    is_valid, errors = validate_manifest(str(manifest_path))
    assert is_valid, errors

    non_empty_target = tmp_path / "feature117-openclaw-target-non-empty"
    non_empty_target.mkdir(parents=True, exist_ok=True)
    (non_empty_target / "preexisting.txt").write_text("keep\n", encoding="utf-8")
    non_empty_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--from",
            "openclaw",
            str(non_empty_target),
            str(workspace),
        ],
        capture_output=True,
        text=True,
    )
    assert non_empty_result.returncode != 0
    assert "target is not empty" in f"{non_empty_result.stdout}\n{non_empty_result.stderr}".lower()


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.analyzer
def test_feature117_generic_llm_agent_import_contract(tmp_path):
    python_project = tmp_path / "feature117-generic-python-llm"
    python_project.mkdir(parents=True, exist_ok=True)
    (python_project / "agent.py").write_text(
        "import os\n"
        "import litellm\n"
        "key = os.getenv('LITELLM_API_KEY')\n"
        "print(litellm, key)\n",
        encoding="utf-8",
    )

    py_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(python_project)],
        capture_output=True,
        text=True,
    )
    py_output = f"{py_result.stdout}\n{py_result.stderr}"
    assert py_result.returncode == 0, py_output
    py_manifest = (python_project / "kinnoo.yaml").read_text(encoding="utf-8")
    py_requirements = (python_project / "requirements.txt").read_text(encoding="utf-8")
    assert "LITELLM_API_KEY" in py_manifest
    assert "litellm" in py_requirements
    py_valid, py_errors = validate_manifest(str(python_project / "kinnoo.yaml"))
    assert py_valid, py_errors

    node_project = tmp_path / "feature117-generic-node-llm"
    node_project.mkdir(parents=True, exist_ok=True)
    (node_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature117-generic-node-llm\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"main\": \"index.js\",\n"
        "  \"dependencies\": {\n"
        "    \"axios\": \"^1.7.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (node_project / "index.js").write_text(
        "const token = process.env.LLM_API_KEY;\n"
        "console.log(token || 'ok');\n",
        encoding="utf-8",
    )

    node_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(node_project)],
        capture_output=True,
        text=True,
    )
    node_output = f"{node_result.stdout}\n{node_result.stderr}"
    assert node_result.returncode == 0, node_output
    node_manifest = (node_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "LLM_API_KEY" in node_manifest
    assert "axios" in node_manifest.lower()
    node_valid, node_errors = validate_manifest(str(node_project / "kinnoo.yaml"))
    assert node_valid, node_errors


@pytest.mark.regression_integration
@pytest.mark.client_cli_import
@pytest.mark.analyzer
@pytest.mark.regression_sat
def test_feature117_import_regression_coverage_floor(tmp_path):
    required_import_regression_tests = {
        "test_feature117_openclaw_from_copy_contract",
        "test_feature117_generic_llm_agent_import_contract",
        "test_feature117_import_regression_coverage_floor",
    }
    missing_tests = [
        test_name
        for test_name in required_import_regression_tests
        if not callable(globals().get(test_name))
    ]
    assert not missing_tests, (
        "Critical import regression tests must remain present: "
        + ", ".join(sorted(missing_tests))
    )

    guard_project = tmp_path / "feature117-framework-accuracy-guard"
    guard_project.mkdir(parents=True, exist_ok=True)
    (guard_project / "graph.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "from langchain_openai import ChatOpenAI\n"
        "graph = StateGraph(dict)\n"
        "compiled = graph.compile()\n"
        "print(ChatOpenAI, compiled)\n",
        encoding="utf-8",
    )
    payload = analyze_project(guard_project).as_dict()
    assert payload["inferred"]["framework"] == "langgraph"
