import os
import zipfile
from pathlib import Path

import yaml

from tests.helpers import command_exists, run_command


def _run_inspect(*args: object, **kwargs: object):
    return run_command("inspect", *args, **kwargs)


def test_inspect_missing_target_prints_usage() -> None:
    assert command_exists("inspect")
    result = _run_inspect()

    assert result.returncode != 0
    assert "Usage: kinnoo inspect <target>" in result.stderr


def test_inspect_missing_required_files_prints_guidance(tmp_path: Path) -> None:
        missing_manifest_dir = tmp_path / "missing-manifest"
        missing_manifest_dir.mkdir(parents=True, exist_ok=True)
        (missing_manifest_dir / "requirements.txt").write_text("", encoding="utf-8")

        result_manifest = _run_inspect(str(missing_manifest_dir))

        assert result_manifest.returncode != 0
        assert "kinnoo.yaml" in result_manifest.stdout
        assert "Minimal example:" in result_manifest.stdout
        assert "Traceback" not in result_manifest.stdout
        assert "Traceback" not in result_manifest.stderr

        missing_requirements_dir = tmp_path / "missing-requirements"
        missing_requirements_dir.mkdir(parents=True, exist_ok=True)
        (missing_requirements_dir / "kinnoo.yaml").write_text(
                """
name: test-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: \">=3.10\"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
                encoding="utf-8",
        )

        result_requirements = _run_inspect(str(missing_requirements_dir))

        assert result_requirements.returncode != 0
        assert "requirements.txt" in result_requirements.stdout
        assert "pip install uv" in result_requirements.stdout
        assert "uv export --format requirements-txt > requirements.txt" in result_requirements.stdout
        assert "Traceback" not in result_requirements.stdout
        assert "Traceback" not in result_requirements.stderr


def test_inspect_reads_manifest_from_archive_without_extracting(tmp_path: Path) -> None:
        archive_path = tmp_path / "archive-agent.kno"
        manifest_content = """
name: archive-agent
version: 1.2.3
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
"""

        with zipfile.ZipFile(archive_path, "w") as archive_zip:
                archive_zip.writestr("kinnoo.yaml", manifest_content)
                archive_zip.writestr("run.py", "print('hello')\n")

        before_children = {path.name for path in tmp_path.iterdir()}

        result = _run_inspect(str(archive_path))

        after_children = {path.name for path in tmp_path.iterdir()}

        assert result.returncode == 0
        assert "Inspect target type: archive (.kno)" in result.stdout
        assert "Manifest metadata:" in result.stdout
        assert "- Name: archive-agent" in result.stdout
        assert "- Version: 1.2.3" in result.stdout
        assert before_children == after_children
        assert (tmp_path / "archive-agent").exists() is False


def test_inspect_formatting_optional_omission_and_missing_required_field_errors(tmp_path: Path) -> None:
    valid_dir = tmp_path / "valid-inspect-agent"
    valid_dir.mkdir(parents=True, exist_ok=True)
    (valid_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (valid_dir / "requirements.txt").write_text("", encoding="utf-8")
    (valid_dir / "kinnoo.yaml").write_text(
            """
name: readable-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies:
    - requests
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    valid_result = _run_inspect(str(valid_dir))

    assert valid_result.returncode == 0
    assert "Manifest metadata:" in valid_result.stdout
    assert "- Name: readable-agent" in valid_result.stdout
    assert "- Version: 1.0.0" in valid_result.stdout
    assert "- Runtime Type: one-shot" in valid_result.stdout
    assert "- Dependencies:" in valid_result.stdout
    assert "  - requests" in valid_result.stdout
    assert "Description:" not in valid_result.stdout
    assert "Author:" not in valid_result.stdout
    assert "License:" not in valid_result.stdout
    assert "{" not in valid_result.stdout

    invalid_dir = tmp_path / "invalid-inspect-agent"
    invalid_dir.mkdir(parents=True, exist_ok=True)
    (invalid_dir / "requirements.txt").write_text("", encoding="utf-8")
    (invalid_dir / "kinnoo.yaml").write_text(
        """
name: invalid-agent
version: 1.0.0
runtime:
    language: python
    version: ">=3.10"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
            encoding="utf-8",
    )

    invalid_result = _run_inspect(str(invalid_dir))

    assert invalid_result.returncode != 0
    assert "Error: Manifest validation failed." in invalid_result.stderr
    assert "Missing required field: 'entrypoint'" in invalid_result.stderr
    assert "Missing required field: 'runtime.type'" in invalid_result.stderr


def test_inspect_shows_env_var_names_not_values(tmp_path: Path) -> None:
    agent_dir = tmp_path / "env-var-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
            """
name: env-var-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
env_vars:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
""",
            encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        {
            "OPENAI_API_KEY": "sk-openai-secret-value",
            "ANTHROPIC_API_KEY": "sk-anthropic-secret-value",
        }
    )

    result = _run_inspect(str(agent_dir), env=env)

    combined_output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "- Env Vars:" in result.stdout
    assert "  - OPENAI_API_KEY" in result.stdout
    assert "  - ANTHROPIC_API_KEY" in result.stdout
    assert "sk-openai-secret-value" not in combined_output
    assert "sk-anthropic-secret-value" not in combined_output

def test_missing_manifest_guidance_uses_centralized_template_with_agent_note(tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        templates_path = repo_root / "src" / "kinnoo" / "templates.py"
        inspect_path = repo_root / "src" / "kinnoo" / "inspect_command.py"

        templates_text = templates_path.read_text(encoding="utf-8")
        inspect_text = inspect_path.read_text(encoding="utf-8")

        assert "INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE" in templates_text
        assert "[agent]" in templates_text
        assert "INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE" in inspect_text
        assert "name: my-agent" not in inspect_text

        missing_manifest_dir = tmp_path / "missing-manifest-centralized"
        missing_manifest_dir.mkdir(parents=True, exist_ok=True)
        (missing_manifest_dir / "requirements.txt").write_text("", encoding="utf-8")

        result = _run_inspect(str(missing_manifest_dir))

        assert result.returncode != 0
        assert "Minimal example:" in result.stdout
        assert "name: my-agent" in result.stdout
        assert "version: 0.1.0" in result.stdout
        assert "entrypoint:" in result.stdout or "entrypoints:" in result.stdout
        assert "runtime:" in result.stdout
        assert "dependencies: []" in result.stdout


def test_feature22_inspect_displays_asset_paths_and_sizes(tmp_path: Path) -> None:
        agent_dir = tmp_path / "inspect-asset-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "assets" / "nested").mkdir(parents=True, exist_ok=True)
        (agent_dir / "assets" / "nested" / "a.txt").write_text("A\n", encoding="utf-8")
        (agent_dir / "data").mkdir(parents=True, exist_ok=True)
        (agent_dir / "data" / "b.txt").write_text("B\n", encoding="utf-8")

        (agent_dir / "kinnoo.yaml").write_text(
            """
    name: inspect-asset-agent
    version: 1.0.0
    entrypoint: run.py
    runtime:
        language: python
        version: "3.10"
        type: one-shot
    dependencies: []
    inputs:
        type: string
    outputs:
        type: string
    assets:
        paths:
        - assets
        - data/b.txt
    """,
            encoding="utf-8",
        )
        (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

        inspect_dir_result = _run_inspect(str(agent_dir))
        assert inspect_dir_result.returncode == 0
        assert "- Asset Paths:" in inspect_dir_result.stdout
        assert "  - assets" in inspect_dir_result.stdout
        assert "  - data/b.txt" in inspect_dir_result.stdout
        assert "- Assets Size:" in inspect_dir_result.stdout
        assert "assets/nested/a.txt" in inspect_dir_result.stdout
        assert "data/b.txt" in inspect_dir_result.stdout

        archive_path = tmp_path / "inspect-asset-agent.kno"
        with zipfile.ZipFile(archive_path, "w") as archive_zip:
            archive_zip.write(agent_dir / "kinnoo.yaml", arcname="kinnoo.yaml")
            archive_zip.write(agent_dir / "run.py", arcname="run.py")
            archive_zip.write(agent_dir / "assets" / "nested" / "a.txt", arcname="assets/nested/a.txt")
            archive_zip.write(agent_dir / "data" / "b.txt", arcname="data/b.txt")

        inspect_archive_result = _run_inspect(str(archive_path))
        assert inspect_archive_result.returncode == 0
        assert "Inspect target type: archive (.kno)" in inspect_archive_result.stdout
        assert "- Asset Paths:" in inspect_archive_result.stdout
        assert "  - assets" in inspect_archive_result.stdout
        assert "  - data/b.txt" in inspect_archive_result.stdout
        assert "- Assets Size:" in inspect_archive_result.stdout
        assert "assets/nested/a.txt" in inspect_archive_result.stdout
        assert "data/b.txt" in inspect_archive_result.stdout


def test_feature24_inspect_displays_services(tmp_path: Path) -> None:
                agent_dir = tmp_path / "inspect-services-agent"
                agent_dir.mkdir(parents=True, exist_ok=True)
                (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
                (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

                manifest_text = "\n".join(
                    [
                        "name: inspect-services-agent",
                        "version: 1.0.0",
                        "entrypoint: run.py",
                        "runtime:",
                        "  language: python",
                        "  version: \"3.10\"",
                        "  type: one-shot",
                        "dependencies: []",
                        "inputs:",
                        "  type: string",
                        "outputs:",
                        "  type: string",
                        "services:",
                        "  - name: primary-db",
                        "    type: database",
                        "    health_check:",
                        "      method: tcp",
                        "      port: 5432",
                        "  - name: cache",
                        "    type: vector-db",
                        "    health_check:",
                        "      method: process",
                        "      process_name: redis-server",
                        "  - name: external-api",
                        "    type: api",
                        "    health_check:",
                        "      method: http",
                        "      url: http://localhost:8080/health",
                        "  - name: mcp-gateway",
                        "    type: mcp-server",
                        "  - name: telemetry",
                        "    type: local-process",
                        "  - name: legacy-worker",
                        "    type: process",
                        "",
                    ]
                )
                (agent_dir / "kinnoo.yaml").write_text(manifest_text, encoding="utf-8")

                result = _run_inspect(str(agent_dir))

                assert result.returncode == 0
                assert "- Services:" in result.stdout
                assert "  - primary-db (database)" in result.stdout
                assert "    - health_check.method: tcp" in result.stdout
                assert "    - health_check.port: 5432" in result.stdout
                assert "  - cache (vector-db)" in result.stdout
                assert "    - health_check.method: process" in result.stdout
                assert "    - health_check.process_name: redis-server" in result.stdout
                assert "  - external-api (api)" in result.stdout
                assert "    - health_check.method: http" in result.stdout
                assert "    - health_check.url: http://localhost:8080/health" in result.stdout
                assert "  - mcp-gateway (mcp-server)" in result.stdout
                assert "  - telemetry (local-process)" in result.stdout
                assert "  - legacy-worker (process)" in result.stdout
                # Service without health_check should not emit placeholder/noise lines.
                assert "health_check: (none)" not in result.stdout


def _create_feature48_agent(agent_dir: Path) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature48-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \"3.10\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_feature48_inspect_full_shows_all_known_fields_with_na(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-full-agent"
    _create_feature48_agent(agent_dir)

    result = _run_inspect(str(agent_dir), "--full")

    assert result.returncode == 0
    assert "- All Metadata Fields:" in result.stdout
    assert "  - description: N/A" in result.stdout
    assert "  - runtime.run_command: N/A" in result.stdout
    assert "  - runtime.type: one-shot" in result.stdout


def test_feature48_inspect_raw_shows_filled_dotted_fields(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-raw-agent"
    _create_feature48_agent(agent_dir)

    result = _run_inspect(str(agent_dir), "--raw")

    assert result.returncode == 0
    assert "Manifest metadata (raw):" in result.stdout
    assert "runtime.language: python" in result.stdout
    assert "runtime.type: one-shot" in result.stdout
    assert "description: N/A" not in result.stdout


def test_feature48_inspect_raw_full_shows_all_dotted_fields(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-raw-full-agent"
    _create_feature48_agent(agent_dir)

    result = _run_inspect(str(agent_dir), "--raw", "--full")

    assert result.returncode == 0
    assert "Manifest metadata (raw):" in result.stdout
    assert "runtime.language: python" in result.stdout
    assert "description: N/A" in result.stdout
    assert "runtime.run_command: N/A" in result.stdout


def test_feature48_inspect_update_prompts_and_applies_on_yes(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-update-yes-agent"
    _create_feature48_agent(agent_dir)

    result = _run_inspect(
        str(agent_dir),
        "--update",
        "runtime.language",
        "nodejs",
        input_text="y\n",
    )

    assert result.returncode == 0
    assert "Changing runtime.language" in result.stdout
    assert "Proceed? (y/N):" in result.stdout
    assert "Manifest metadata updated." in result.stdout

    manifest_data = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_data["runtime"]["language"] == "nodejs"


def test_feature48_inspect_update_aborts_on_default_no(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-update-no-agent"
    _create_feature48_agent(agent_dir)

    before_manifest = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    result = _run_inspect(
        str(agent_dir),
        "--update",
        "runtime.language",
        "nodejs",
        input_text="\n",
    )

    assert result.returncode != 0
    assert "Update aborted." in result.stdout
    after_manifest = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert after_manifest == before_manifest


def test_feature48_inspect_update_skip_warnings_bypasses_prompt(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-update-skip-agent"
    _create_feature48_agent(agent_dir)

    result = _run_inspect(
        str(agent_dir),
        "--skip-warnings",
        "--update",
        "runtime.language",
        "nodejs",
    )

    assert result.returncode == 0
    assert "Warning: are you sure you want to modify" not in result.stdout
    manifest_data = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_data["runtime"]["language"] == "nodejs"


def test_feature48_inspect_update_rejects_invalid_manifest_value(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature48-update-invalid-agent"
    _create_feature48_agent(agent_dir)

    before_manifest = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    result = _run_inspect(
        str(agent_dir),
        "--skip-warnings",
        "--update",
        "runtime.language",
        "ruby",
    )

    assert result.returncode != 0
    combined = f"{result.stdout}\n{result.stderr}"
    assert "Manifest validation failed" in combined
    assert "runtime.language" in combined
    after_manifest = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert after_manifest == before_manifest


def test_inspect_json_output(tmp_path: Path) -> None:
    agent_dir = tmp_path / "task473-inspect-json-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: task473-inspect-json-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    result = _run_inspect("--json", str(agent_dir))
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    payload = yaml.safe_load(result.stdout)
    assert payload["target_type"] == "directory"
    assert payload["raw"] is False
    assert payload["full"] is False
    assert payload["manifest"]["name"] == "task473-inspect-json-agent"
    assert payload["manifest"]["runtime"]["type"] == "one-shot"

    full_result = _run_inspect("--json", "--full", str(agent_dir))
    assert full_result.returncode == 0, f"{full_result.stdout}\n{full_result.stderr}"
    full_payload = yaml.safe_load(full_result.stdout)
    assert full_payload["full"] is True
    assert "all_metadata_fields" in full_payload


def test_inspect_update_two_args(tmp_path: Path) -> None:
    agent_dir = tmp_path / "task474-update-agent"
    _create_feature48_agent(agent_dir)

    before_order = _run_inspect(
        "--skip-warnings",
        "--update",
        "runtime.language",
        "nodejs",
        str(agent_dir),
    )
    assert before_order.returncode == 0, f"{before_order.stdout}\n{before_order.stderr}"

    manifest_after_first = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_after_first["runtime"]["language"] == "nodejs"

    after_order = _run_inspect(
        str(agent_dir),
        "--skip-warnings",
        "--update",
        "runtime.language",
        "python",
    )
    assert after_order.returncode == 0, f"{after_order.stdout}\n{after_order.stderr}"

    manifest_after_second = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_after_second["runtime"]["language"] == "python"


def test_inspect_update_confirmation_prompt(tmp_path: Path) -> None:
    agent_dir = tmp_path / "task475-confirm-agent"
    _create_feature48_agent(agent_dir)

    reject_result = _run_inspect(
        str(agent_dir),
        "--update",
        "runtime.language",
        "nodejs",
        input_text="N\n",
    )
    assert reject_result.returncode != 0
    assert "Changing runtime.language" in reject_result.stdout
    assert "Proceed? (y/N):" in reject_result.stdout
    assert "Update aborted." in reject_result.stdout
    manifest_after_reject = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_after_reject["runtime"]["language"] == "python"

    accept_result = _run_inspect(
        str(agent_dir),
        "--update",
        "runtime.language",
        "nodejs",
        input_text="y\n",
    )
    assert accept_result.returncode == 0, f"{accept_result.stdout}\n{accept_result.stderr}"
    manifest_after_accept = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_after_accept["runtime"]["language"] == "nodejs"

    bypass_result = _run_inspect(
        str(agent_dir),
        "--skip-warnings",
        "--update",
        "runtime.language",
        "python",
    )
    assert bypass_result.returncode == 0, f"{bypass_result.stdout}\n{bypass_result.stderr}"
    assert "Changing runtime.language" not in bypass_result.stdout
    manifest_after_bypass = yaml.safe_load((agent_dir / "kinnoo.yaml").read_text(encoding="utf-8"))
    assert manifest_after_bypass["runtime"]["language"] == "python"


def test_task489_inspect_supports_entrypoints_manifest(tmp_path: Path) -> None:
        agent_dir = tmp_path / "task489-inspect-entrypoints"
        (agent_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "scripts" / "main.py").write_text("print('ok')\n", encoding="utf-8")
        (agent_dir / "scripts" / "alt.py").write_text("print('ok')\n", encoding="utf-8")
        (agent_dir / "kinnoo.yaml").write_text(
                """
name: task489-inspect-entrypoints
version: 1.0.0
entrypoints:
    - scripts/main.py
    - scripts/alt.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
                encoding="utf-8",
        )

        result = _run_inspect(str(agent_dir), "--json")

        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
        payload = yaml.safe_load(result.stdout)
        assert payload["manifest"]["entrypoints"] == ["scripts/main.py", "scripts/alt.py"]


def test_task489_inspect_rejects_missing_entrypoints_path(tmp_path: Path) -> None:
        agent_dir = tmp_path / "task489-inspect-missing-path"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "kinnoo.yaml").write_text(
                """
name: task489-inspect-missing-path
version: 1.0.0
entrypoints:
    - scripts/main.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
                encoding="utf-8",
        )

        result = _run_inspect(str(agent_dir))

        assert result.returncode != 0
        assert "Declared entrypoint path not found: 'scripts/main.py'." in result.stderr
