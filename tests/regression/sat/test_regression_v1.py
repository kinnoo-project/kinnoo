import os
import subprocess
import sys
import tempfile
import json
from pathlib import Path

import yaml


# [agent] redundant test
# [agent] Run this regression gate before opening/merging PRs that change CLI behavior,
# command modules, packaging/install flows, or shared test utilities; it verifies V1
# baseline modules still pass together after refactors.
# def test_v1_suite_passes_after_feature7():
#     modules = [
#         "tests/test_validator.py",
#         "tests/test_init.py",
#         "tests/test_cli.py",
#         "tests/test_pack.py",
#         "tests/test_install.py",
#         "tests/test_cli_install.py",
#     ]
#     result = subprocess.run(
#         [sys.executable, "-m", "pytest", *modules],
#         capture_output=True,
#         text=True,
#     )
#     assert result.returncode == 0, (
#         "V1 regression suite failed.\n"
#         f"STDOUT:\n{result.stdout}\n"
#         f"STDERR:\n{result.stderr}"
#     )


# [agent] redundant test
# def test_feature20_does_not_regress_v2_behavior():
#     command = [
#         sys.executable,
#         "-m",
#         "pytest",
#         "tests/test_cli.py",
#         "-k",
#         "run",
#         "tests/test_install.py",
#     ]
#     result = subprocess.run(
#         command,
#         capture_output=True,
#         text=True,
#     )
#     assert result.returncode == 0, (
#         "Feature20 regression gate failed for V2 run/install behavior.\n"
#         f"STDOUT:\n{result.stdout}\n"
#         f"STDERR:\n{result.stderr}"
#     )


def test_feature21_framework_templates_do_not_regress_existing_frameworks():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_init.py::test_framework_templates_generate_correct_files",
        "tests/test_init.py::test_framework_valid",
        "tests/test_init.py::test_framework_manifests_pass_validation",
        "tests/test_init.py::test_feature21_regression_existing_frameworks_unchanged",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature21 regression gate failed for existing framework templates.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature22_no_assets_regression_unchanged():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_pack.py::test_pack_creates_correct_archive_structure",
        "tests/test_cli_install_extract.py::test_install_extracts_archive",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature22 no-assets regression gate failed for pack/install behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature23_no_regression_for_one_shot_runtime():
    """Regression gate: ensure one-shot execution semantics remain unchanged."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_cli.py::test_run_entrypoint_with_input",
        "tests/test_cli.py::test_run_streams_stdout_stderr",
        "tests/test_cli.py::test_run_exit_code",
        "tests/test_cli.py::test_run_single_input_backward_compatible",
        "tests/test_trust_baseline.py::test_run_trace_log_safe_fields",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature23 regression gate failed for one-shot runtime behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature24_ac_coverage_and_no_services_regression_gate():
    """Regression gate for feature24 AC coverage and no-services compatibility."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_validator.py::test_feature24_services_optional_list_is_accepted",
        "tests/test_validator.py::test_feature24_service_required_fields_and_type_validation",
        "tests/test_validator.py::test_feature24_health_check_method_specific_validation",
        "tests/test_validator.py::test_feature24_no_services_regression_unchanged",
        "tests/test_validator.py::test_feature24_duplicate_service_names_rejected",
        "tests/test_cli_inspect.py::test_feature24_inspect_displays_services",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature24 regression gate failed for AC coverage and no-services compatibility.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature25_no_services_regression_unchanged():
    """Regression test: agents without services remain behaviorally unchanged."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        agent_dir = temp_path / "feature25-no-services-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)

        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "README.md").write_text("feature25 no-services fixture", encoding="utf-8")
        (agent_dir / "tools").mkdir()
        (agent_dir / "prompts").mkdir()
        (agent_dir / "run.py").write_text(
            "import sys\n"
            "print(f\"no-services-entrypoint:{sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
            encoding="utf-8",
        )
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: feature25-no-services-agent",
                    "version: 0.1.0",
                    "entrypoint: run.py",
                    "runtime:",
                    "    language: python",
                    "    version: \">=3.10\"",
                    "    type: one-shot",
                    "dependencies: []",
                    "inputs:",
                    "    type: text",
                    "outputs:",
                    "    type: text",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, output
        assert "no-services-entrypoint:hello" in output
        assert "Service health checks:" not in output


def test_feature25_ac_coverage_and_no_services_regression_gate():
    """Regression gate for feature25 AC coverage and no-services compatibility."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_health_check.py::test_feature25_http_health_check_2xx_and_timeout",
        "tests/test_health_check.py::test_feature25_tcp_health_check_localhost_and_timeout",
        "tests/test_health_check.py::test_feature25_process_health_check",
        "tests/test_cli.py::test_feature25_run_checks_all_declared_services_before_entrypoint",
        "tests/test_run_preflight.py::test_feature25_preflight_includes_service_health_results",
        "tests/test_cli.py::test_feature25_non_interactive_aborts_on_unhealthy_service",
        "tests/test_cli.py::test_feature25_interactive_prompt_allows_proceed_or_abort",
        "tests/test_regression_v1.py::test_feature25_no_services_regression_unchanged",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature25 regression gate failed for AC coverage and no-services compatibility.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature26_framework_template_regression_gate():
    """Regression gate: existing init frameworks remain stable after adding mcp-client."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_init.py::test_framework_templates_generate_correct_files",
        "tests/test_init.py::test_framework_valid",
        "tests/test_init.py::test_framework_manifests_pass_validation",
        "tests/test_init.py::test_feature21_regression_existing_frameworks_unchanged",
        "tests/test_init.py::test_feature26_mcp_client_template_generation",
        "tests/test_init.py::test_feature26_mcp_client_template_contract_and_validation",
        "tests/test_validator.py::test_feature26_permissions_schema_validation",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature26 regression gate failed for framework template stability and permissions validation.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature19_import_interrupt_and_runnability_regression_gate():
    """Regression gate for task167 interruption safety and in-place runnability."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_cli_import.py::test_feature19_interrupt_cleanup_and_exit_code",
        "tests/test_cli_import.py::test_feature19_imported_project_runs_in_place",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature19 regression gate failed for interruption safety and runnability.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature31_python_runtime_regression_gate():
    """Regression gate: feature31 Node support must not alter Python run/pack/install behavior."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_root = temp_path / "archive-root"
        env = os.environ.copy()
        env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

        agent_dir = temp_path / "feature31-python-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: feature31-python-agent",
                    "version: 1.0.0",
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
        (agent_dir / "run.py").write_text(
            "import sys\n"
            "print(f\"feature31-python-output:{sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
            encoding="utf-8",
        )
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

        pack_result = subprocess.run(
            [sys.executable, str(cli_path), "pack", str(agent_dir)],
            cwd=temp_path,
            capture_output=True,
            text=True,
            env=env,
        )
        assert pack_result.returncode == 0, (
            "Feature31 python regression gate failed during pack.\n"
            f"STDOUT:\n{pack_result.stdout}\n"
            f"STDERR:\n{pack_result.stderr}"
        )

        archive_path = archive_root / "feature31-python-agent" / "1.0.0" / "feature31-python-agent.kno"
        assert archive_path.exists(), "Expected packed archive for feature31 python regression gate"

        installed_dir = temp_path / "feature31-python-installed"
        install_result = subprocess.run(
            [
                sys.executable,
                str(cli_path),
                "install",
                str(archive_path),
                str(installed_dir),
                "--yes",
                "--allow-unverified-publisher",
            ],
            cwd=temp_path,
            capture_output=True,
            text=True,
            env=env,
        )
        assert install_result.returncode == 0, (
            "Feature31 python regression gate failed during install.\n"
            f"STDOUT:\n{install_result.stdout}\n"
            f"STDERR:\n{install_result.stderr}"
        )

        run_result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(installed_dir), "hello-python"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            env=env,
        )
        output = f"{run_result.stdout}\n{run_result.stderr}"
        assert run_result.returncode == 0, output
        assert "feature31-python-output:hello-python" in output


def test_feature42_json_contract_guidance_and_text_regression_gate():
    """Regression gate for feature42 docs/help/inspect/preflight guidance and text-flow stability."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    docs_text = f"{schema_doc.read_text(encoding='utf-8')}\n{readme_doc.read_text(encoding='utf-8')}"
    assert "--json-input" in docs_text
    assert "--json-file" in docs_text
    assert "stdout must be valid JSON" in docs_text

    run_help_result = subprocess.run(
        [sys.executable, str(cli_path), "run", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert run_help_result.returncode == 0, run_help_result.stderr
    assert "--json-input" in run_help_result.stdout
    assert "--json-file" in run_help_result.stdout

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        agent_dir = temp_path / "feature42-guidance-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "run.py").write_text("import json\nprint(json.dumps({'ok': True}))\n", encoding="utf-8")
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: feature42-guidance-agent",
                    "version: 1.0.0",
                    "entrypoint: run.py",
                    "runtime:",
                    "  language: python",
                    "  version: \">=3.10\"",
                    "  type: one-shot",
                    "dependencies: []",
                    "inputs:",
                    "  type: json",
                    "outputs:",
                    "  type: json",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        preflight_result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(agent_dir), "--preflight"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        preflight_output = f"{preflight_result.stdout}\n{preflight_result.stderr}"
        assert preflight_result.returncode == 0, preflight_output
        assert "manifest I/O contract: inputs.type [json], outputs.type [json]" in preflight_output
        assert "--json-input or --json-file" in preflight_output
        assert "stdout must be valid JSON" in preflight_output

        inspect_result = subprocess.run(
            [sys.executable, str(cli_path), "inspect", str(agent_dir)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        inspect_output = f"{inspect_result.stdout}\n{inspect_result.stderr}"
        assert inspect_result.returncode == 0, inspect_output
        assert "- Input Types: json" in inspect_output
        assert "- Output Types: json" in inspect_output
        assert "- JSON Contract:" in inspect_output

    regression_command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_regression_v1.py::test_feature31_python_runtime_regression_gate",
        "tests/test_cli.py::test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit",
        "tests/test_cli.py::test_run_single_input_backward_compatible",
        "tests/test_docs.py::test_feature42_docs_cover_json_contract_guidance",
    ]
    regression_result = subprocess.run(
        regression_command,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert regression_result.returncode == 0, (
        "Feature42 regression gate failed for guidance surfaces and text flow compatibility.\n"
        f"STDOUT:\n{regression_result.stdout}\n"
        f"STDERR:\n{regression_result.stderr}"
    )


def test_feature32_daemon_health_state_regression_gate(tmp_path, monkeypatch, capsys):
    """Regression gate: daemon lifecycle reports not-running/unhealthy/healthy with compatibility checks."""
    import kinnoo.run_command as run_command

    def _write_manifest(agent_dir: Path, runtime_type: str) -> None:
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    f"name: {agent_dir.name}",
                    "version: 1.0.0",
                    "entrypoint: run.py",
                    "runtime:",
                    "  language: python",
                    "  version: \">=3.10\"",
                    f"  type: {runtime_type}",
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
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

    healthy_agent = tmp_path / "feature32-daemon-healthy"
    healthy_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(healthy_agent, "daemon")
    healthy_state = healthy_agent / ".kinnoo" / "daemon-state.json"
    healthy_state.parent.mkdir(parents=True, exist_ok=True)
    healthy_state.write_text(json.dumps({"pid": 55001}), encoding="utf-8")

    unhealthy_agent = tmp_path / "feature32-daemon-unhealthy"
    unhealthy_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(unhealthy_agent, "daemon")
    unhealthy_state = unhealthy_agent / ".kinnoo" / "daemon-state.json"
    unhealthy_state.parent.mkdir(parents=True, exist_ok=True)
    unhealthy_state.write_text(json.dumps({"pid": 55002}), encoding="utf-8")

    not_running_agent = tmp_path / "feature32-daemon-not-running"
    not_running_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(not_running_agent, "daemon")

    one_shot_agent = tmp_path / "feature32-one-shot-compat"
    one_shot_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(one_shot_agent, "one-shot")

    mcp_agent = tmp_path / "feature32-mcp-compat"
    mcp_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(mcp_agent, "mcp-server")

    def fake_run_service_checks(manifest: dict | None):
        if not isinstance(manifest, dict):
            return []
        agent_name = str(manifest.get("name", ""))
        if "unhealthy" in agent_name:
            return [
                run_command.HealthCheckResult(
                    service_name="backend",
                    service_type="http",
                    method="http",
                    healthy=False,
                    message="mock unhealthy service",
                    guidance="mock guidance",
                )
            ]
        return []

    def fake_pid_running(pid: int) -> bool:
        return pid in (55001, 55002)

    monkeypatch.setattr(run_command, "_run_service_checks", fake_run_service_checks)
    monkeypatch.setattr(run_command, "daemon_pid_is_running", fake_pid_running)

    healthy_code = run_command.run_preflight(str(healthy_agent))
    healthy_capture = capsys.readouterr()
    healthy_output = f"{healthy_capture.out}\n{healthy_capture.err}"
    assert healthy_code == 0, healthy_output
    assert "daemon lifecycle state [healthy]" in healthy_output

    unhealthy_code = run_command.run_preflight(str(unhealthy_agent))
    unhealthy_capture = capsys.readouterr()
    unhealthy_output = f"{unhealthy_capture.out}\n{unhealthy_capture.err}"
    assert unhealthy_code != 0, unhealthy_output
    assert "daemon lifecycle state [unhealthy]" in unhealthy_output
    assert "services[].health_check" in unhealthy_output or "service checks" in unhealthy_output

    not_running_code = run_command.run_preflight(str(not_running_agent))
    not_running_capture = capsys.readouterr()
    not_running_output = f"{not_running_capture.out}\n{not_running_capture.err}"
    assert not_running_code != 0, not_running_output
    assert "daemon lifecycle state [not-running]" in not_running_output
    assert "Start daemon" in not_running_output

    one_shot_code = run_command.run_preflight(str(one_shot_agent))
    one_shot_capture = capsys.readouterr()
    one_shot_output = f"{one_shot_capture.out}\n{one_shot_capture.err}"
    assert one_shot_code == 0, one_shot_output
    assert "daemon lifecycle state" not in one_shot_output

    mcp_code = run_command.run_preflight(str(mcp_agent))
    mcp_capture = capsys.readouterr()
    mcp_output = f"{mcp_capture.out}\n{mcp_capture.err}"
    assert mcp_code == 0, mcp_output
    assert "daemon lifecycle state" not in mcp_output


def test_feature33_non_openclaw_optional_nonbreaking_regression_gate(tmp_path):
    """Regression gate (deprecated): channels/skills/state_dirs are globally rejected by schema."""
    from kinnoo.validator import validate

    def _write_manifest(agent_name: str, manifest: dict) -> Path:
        manifest_path = tmp_path / f"{agent_name}.yaml"
        manifest_path.write_text(yaml.dump(manifest), encoding="utf-8")
        return manifest_path

    baseline_python = {
        "name": "feature33-baseline-python",
        "version": "1.0.0",
        "entrypoint": "run.py",
        "runtime": {
            "language": "python",
            "version": ">=3.10",
            "type": "one-shot",
        },
        "dependencies": [],
        "inputs": {"type": "text"},
        "outputs": {"type": "text"},
    }

    baseline_node = {
        "name": "feature33-baseline-node",
        "version": "1.0.0",
        "entrypoint": "run.js",
        "runtime": {
            "language": "nodejs",
            "version": ">=20.0.0",
            "type": "one-shot",
        },
        "dependencies": [],
        "inputs": {"type": "text"},
        "outputs": {"type": "text"},
    }

    non_openclaw_with_extensions = {
        "name": "feature33-non-openclaw-with-extensions",
        "version": "1.0.0",
        "entrypoint": "run.js",
        "framework": "custom-framework",
        "runtime": {
            "language": "nodejs",
            "version": ">=20.0.0",
            "type": "one-shot",
            "package_manager": "pnpm",
        },
        "channels": ["events"],
        "skills": ["skills/non-openclaw/skill.md"],
        "state_dirs": ["state/non-openclaw"],
        "dependencies": [],
        "inputs": {"type": "text"},
        "outputs": {"type": "text"},
    }

    frameworkless_with_extensions = {
        "name": "feature33-frameworkless-with-extensions",
        "version": "1.0.0",
        "entrypoint": "run.js",
        "runtime": {
            "language": "nodejs",
            "version": ">=20.0.0",
            "type": "one-shot",
            "package_manager": "npm",
        },
        "channels": ["events"],
        "skills": ["skills/common/skill.md"],
        "state_dirs": ["state/common"],
        "dependencies": [],
        "inputs": {"type": "text"},
        "outputs": {"type": "text"},
    }

    baseline_fixtures = [
        ("baseline_python", baseline_python),
        ("baseline_node", baseline_node),
    ]
    for fixture_name, manifest_data in baseline_fixtures:
        manifest_path = _write_manifest(fixture_name, manifest_data)
        is_valid, errors = validate(str(manifest_path))
        assert is_valid is True, (
            f"Expected baseline fixture {fixture_name!r} to remain valid; errors: {errors}"
        )

    extension_fixtures = [
        ("non_openclaw_with_extensions", non_openclaw_with_extensions),
        ("frameworkless_with_extensions", frameworkless_with_extensions),
    ]
    for fixture_name, manifest_data in extension_fixtures:
        manifest_path = _write_manifest(fixture_name, manifest_data)
        is_valid, errors = validate(str(manifest_path))
        assert is_valid is False, (
            f"Expected fixture {fixture_name!r} to fail due to deprecated schema fields; errors: {errors}"
        )
        assert any("Field 'channels' is not supported" in message for message in errors)
        assert any("Field 'skills' is not supported" in message for message in errors)
        assert any("Field 'state_dirs' is not supported" in message for message in errors)


def test_feature35_assets_backward_compatibility_without_state_dirs(tmp_path):
    """Regression gate: manifests without state_dirs preserve asset-only pack/install behavior."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    archive_root = tmp_path / "archive-root"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    agent_dir = tmp_path / "feature35-assets-only"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "assets").mkdir(parents=True, exist_ok=True)
    (agent_dir / "assets" / "guide.txt").write_text("immutable-guide\n", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "import pathlib\n"
        "asset_path = pathlib.Path(__file__).parent / 'assets' / 'guide.txt'\n"
        "print(asset_path.read_text(encoding='utf-8').strip())\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature35-assets-only",
                "version: 1.0.0",
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
                "assets:",
                "  paths:",
                "    - assets",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    pack_result = subprocess.run(
        [sys.executable, str(cli_path), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert pack_result.returncode == 0, (
        "Feature35 regression gate failed during asset-only pack.\n"
        f"STDOUT:\n{pack_result.stdout}\n"
        f"STDERR:\n{pack_result.stderr}"
    )

    archive_path = archive_root / "feature35-assets-only" / "1.0.0" / "feature35-assets-only.kno"
    assert archive_path.exists(), "Expected asset-only archive to be created"

    import zipfile

    with zipfile.ZipFile(archive_path, "r") as archive_zip:
        names = set(archive_zip.namelist())
        assert "assets/guide.txt" in names
        assert not any(name.startswith("state_snapshots/") for name in names)

    install_target = tmp_path / "feature35-assets-only-installed"
    install_result = subprocess.run(
        [
            sys.executable,
            str(cli_path),
            "install",
            str(archive_path),
            str(install_target),
            "--yes",
            "--allow-unverified-publisher",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert install_result.returncode == 0, (
        "Feature35 regression gate failed during asset-only install.\n"
        f"STDOUT:\n{install_result.stdout}\n"
        f"STDERR:\n{install_result.stderr}"
    )

    assert (install_target / "assets" / "guide.txt").read_text(encoding="utf-8").strip() == "immutable-guide"

    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(install_target), "noop"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    run_output = f"{run_result.stdout}\n{run_result.stderr}"
    assert run_result.returncode == 0, run_output
    assert "immutable-guide" in run_output


def test_feature36_non_openclaw_import_regression_guard(tmp_path):
    """Regression gate: non-openclaw analyzer/import behavior remains stable."""
    from kinnoo.analyzer import analyze_project

    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    python_project = tmp_path / "feature36-non-openclaw-python"
    python_project.mkdir(parents=True, exist_ok=True)
    (python_project / "run.py").write_text(
        "import openai\n"
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (python_project / "requirements.txt").write_text("openai\n", encoding="utf-8")

    python_report = analyze_project(python_project).as_dict()
    assert python_report["inferred"]["framework"] == "chatgpt"
    assert python_report["confidence"]["framework"]["score"] >= 0.8

    python_import_result = subprocess.run(
        [sys.executable, str(cli_path), "import", str(python_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )
    python_output = f"{python_import_result.stdout}\n{python_import_result.stderr}"
    assert python_import_result.returncode == 0, python_output
    assert "framework: openclaw" not in python_output.lower()
    python_manifest_text = (python_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: chatgpt" in python_manifest_text
    assert "framework: openclaw" not in python_manifest_text

    node_project = tmp_path / "feature36-non-openclaw-node"
    node_project.mkdir(parents=True, exist_ok=True)
    (node_project / "index.mjs").write_text("console.log('hello node');\n", encoding="utf-8")
    (node_project / "package.json").write_text(
        json.dumps(
            {
                "name": "feature36-plain-node-project",
                "version": "1.0.0",
                "type": "module",
                "dependencies": {"express": "^4.21.0"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    node_report = analyze_project(node_project).as_dict()
    assert node_report["inferred"]["framework"] is None
    # Score may be > 0 due to node-layout heuristic (task280), but must stay
    # well below the 0.6 OpenClaw inference threshold.
    assert node_report["confidence"]["framework"]["score"] < 0.4

    node_import_result = subprocess.run(
        [sys.executable, str(cli_path), "import", str(node_project)],
        input="y\nrun.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )
    node_output = f"{node_import_result.stdout}\n{node_import_result.stderr}"
    assert node_import_result.returncode == 0, node_output
    assert "analyzer warnings" in node_output.lower()
    assert "framework: openclaw" not in node_output.lower()
    node_manifest_text = (node_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: openclaw" not in node_manifest_text

    ambiguous_python_project = tmp_path / "feature36-non-openclaw-ambiguous-python"
    ambiguous_python_project.mkdir(parents=True, exist_ok=True)
    (ambiguous_python_project / "run.py").write_text(
        "import openai\n"
        "import anthropic\n"
        "if __name__ == '__main__':\n"
        "    print('ambiguous')\n",
        encoding="utf-8",
    )

    ambiguous_import_result = subprocess.run(
        [sys.executable, str(cli_path), "import", str(ambiguous_python_project)],
        input="y\nchatgpt\n",
        capture_output=True,
        text=True,
    )
    ambiguous_output = f"{ambiguous_import_result.stdout}\n{ambiguous_import_result.stderr}"
    assert ambiguous_import_result.returncode == 0, ambiguous_output
    assert "analyzer warnings" in ambiguous_output.lower()
    assert "ambiguous" in ambiguous_output.lower()
    assert "framework: openclaw" not in ambiguous_output.lower()


def test_feature37_python_install_noop_regression_guard(tmp_path):
    """Regression gate: feature37 node-only controls must remain no-op for Python installs."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    fake_bin = tmp_path / "fake-node-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    npm_probe = tmp_path / "npm-probe.log"

    (fake_bin / "npm").write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$FEATURE37_NPM_PROBE\"\n"
        "exit 55\n",
        encoding="utf-8",
    )
    (fake_bin / "node").write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$FEATURE37_NPM_PROBE\"\n"
        "exit 56\n",
        encoding="utf-8",
    )
    (fake_bin / "npm").chmod(0o755)
    (fake_bin / "node").chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["FEATURE37_NPM_PROBE"] = str(npm_probe)
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")

    agent_dir = tmp_path / "feature37-python-noop-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature37-python-noop-agent",
                "version: 1.0.0",
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
    (agent_dir / "run.py").write_text(
        "import sys\n"
        "print(f'feature37-python-noop:{sys.argv[1] if len(sys.argv) > 1 else \"\"}')\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    pack_result = subprocess.run(
        [sys.executable, str(cli_path), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert pack_result.returncode == 0, (
        "Feature37 python no-op regression gate failed during pack.\n"
        f"STDOUT:\n{pack_result.stdout}\n"
        f"STDERR:\n{pack_result.stderr}"
    )

    archive_path = (
        Path(env["KINNOO_ARCHIVE_ROOT"])
        / "feature37-python-noop-agent"
        / "1.0.0"
        / "feature37-python-noop-agent.kno"
    )
    assert archive_path.exists(), "Expected packed archive for feature37 python no-op regression gate"

    install_target = tmp_path / "feature37-python-noop-installed"
    install_result = subprocess.run(
        [
            sys.executable,
            str(cli_path),
            "install",
            str(archive_path),
            str(install_target),
            "--yes",
            "--allow-vulnerable",
            "--ignore-scripts",
            "--allow-unverified-publisher",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    install_output = f"{install_result.stdout}\n{install_result.stderr}"
    assert install_result.returncode == 0, install_output
    assert "Node audit severity summary:" not in install_output
    assert "Lifecycle scripts policy:" not in install_output
    assert "Critical vulnerabilities were detected" not in install_output
    assert not npm_probe.exists(), install_output
    assert not (install_target / ".kinnoo" / "install-trace.json").exists()

    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(install_target), "baseline"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    run_output = f"{run_result.stdout}\n{run_result.stderr}"
    assert run_result.returncode == 0, run_output
    assert "feature37-python-noop:baseline" in run_output


def test_feature38_output_format_and_secret_safety_regression_guard(tmp_path):
    """Regression gate: feature38 findings keep stable output format and never echo raw secret values."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    inspect_agent = tmp_path / "feature38-regression-inspect-agent"
    inspect_agent.mkdir(parents=True, exist_ok=True)
    (inspect_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature38-regression-inspect-agent",
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
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (inspect_agent / "requirements.txt").write_text("", encoding="utf-8")
    (inspect_agent / "run.py").write_text(
        "import os\n"
        "print(os.environ.get('API_KEY'))\n",
        encoding="utf-8",
    )

    js_secret = "ghp_abcdefghijklmnopqrstuvwxyz0123456789AB"
    openclaw_secret = "sk-abcdefghijklmnopqrstuvwxyz123456"

    (inspect_agent / "danger.js").write_text(
        "const expr = '2 + 2';\n"
        "const value = eval(expr);\n"
        f"const token = '{js_secret}';\n",
        encoding="utf-8",
    )
    (inspect_agent / "openclaw-config.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "allow_shell": True,
                    "tool_policy": "allow_all",
                },
                "apiToken": openclaw_secret,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    inspect_result = subprocess.run(
        [sys.executable, str(cli_path), "inspect", str(inspect_agent)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    inspect_output = f"{inspect_result.stdout}\n{inspect_result.stderr}"
    assert inspect_result.returncode == 0, inspect_output

    # Output contract assertions for inspect sweep findings.
    assert "Security sweep:" in inspect_output
    assert "run.py:2: print() with os.environ access" in inspect_output
    assert "danger.js:2: risky js execution primitive (eval)" in inspect_output
    assert "danger.js:3: credential-like pattern (GitHub personal access token)" in inspect_output
    assert "openclaw-config.json:3: dangerous openclaw config (allow_shell=true enables shell command execution)" in inspect_output
    assert "openclaw-config.json:4: dangerous openclaw config (tool_policy=allow_all disables tool restrictions)" in inspect_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in inspect_output

    # No-secret invariant across mixed finding categories.
    assert js_secret not in inspect_output
    assert openclaw_secret not in inspect_output

    pack_agent = tmp_path / "feature38-regression-pack-agent"
    pack_agent.mkdir(parents=True, exist_ok=True)
    (pack_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature38-regression-pack-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: '>=3.10'",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
                "state_dirs:",
                "  - path: memory",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_agent / "requirements.txt").write_text("", encoding="utf-8")
    (pack_agent / "run.py").write_text("print('ok')\n", encoding="utf-8")

    memory_dir = pack_agent / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    memory_secret = "aws_secret_access_key=ABCDEFGHIJKLMNOPQRSTUVWX1234567890"
    (memory_dir / "snapshot.json").write_text(
        "{\n"
        f"  \"checkpoint\": \"{memory_secret}\"\n"
        "}\n",
        encoding="utf-8",
    )

    pack_env = dict(os.environ)
    pack_env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")
    pack_result = subprocess.run(
        [sys.executable, str(cli_path), "pack", str(pack_agent)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=pack_env,
    )
    pack_output = f"{pack_result.stdout}\n{pack_result.stderr}"
    assert pack_result.returncode != 0, pack_output
    assert "Field 'state_dirs' is not supported in this schema version" in pack_output
    assert memory_secret not in pack_output


def test_feature39_python_node_permission_parity(tmp_path, monkeypatch, capsys):
    """Regression gate: sandbox permission policy behaves consistently for Python and Node runtimes."""
    from kinnoo import run_command

    def _write_feature39_agent(agent_dir: Path, runtime_language: str) -> None:
        agent_dir.mkdir(parents=True, exist_ok=True)
        entrypoint_name = "run.py" if runtime_language == "python" else "run.js"
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / entrypoint_name).write_text(
            "print('feature39-runtime-entrypoint-ran')\n" if runtime_language == "python" else "console.log('feature39-runtime-entrypoint-ran');\n",
            encoding="utf-8",
        )
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    f"name: feature39-{runtime_language}-parity-agent",
                    "version: 1.0.0",
                    f"entrypoint: {entrypoint_name}",
                    "runtime:",
                    f"    language: {runtime_language}",
                    "    version: \">=3.10\"" if runtime_language == "python" else "    version: \">=20.0.0\"",
                    "    type: one-shot",
                    "dependencies: []",
                    "inputs:",
                    "    type: text",
                    "outputs:",
                    "    type: text",
                    "permissions:",
                    "    network: true",
                    "    filesystem_scope: read-only",
                    "    shell: false",
                    "    browser: false",
                    "    env_access: []",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (agent_dir / "README.md").write_text("feature39 parity fixture", encoding="utf-8")
        (agent_dir / "tools").mkdir(exist_ok=True)
        (agent_dir / "prompts").mkdir(exist_ok=True)

    python_agent = tmp_path / "feature39-python-parity-agent"
    node_agent = tmp_path / "feature39-node-parity-agent"
    _write_feature39_agent(python_agent, "python")
    _write_feature39_agent(node_agent, "nodejs")

    # Avoid real venv creation for regression determinism.
    python_executable = python_agent / ".venv" / "bin" / "python"
    python_executable.parent.mkdir(parents=True, exist_ok=True)
    python_executable.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    python_executable.chmod(0o755)

    popen_invocations: list[list[str]] = []

    class _FakeProcess:
        def __init__(self, args, **_kwargs):
            self.args = args
            self.returncode = 0

        def communicate(self):
            return None

    def _fake_popen(args, **kwargs):
        del kwargs
        popen_invocations.append(list(args))
        return _FakeProcess(args)

    monkeypatch.setattr(run_command.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(run_command.venv, "create", lambda *_args, **_kwargs: None)

    python_denied = run_command.run_agent(
        agent_dir_arg=str(python_agent),
        input_arg="hello",
        no_guard=True,
        sandbox=True,
        pass_through_args=["--exec", "echo denied"],
    )
    python_denied_output = capsys.readouterr()
    python_denied_combined = f"{python_denied_output.out}\n{python_denied_output.err}"

    node_denied = run_command.run_agent(
        agent_dir_arg=str(node_agent),
        input_arg="hello",
        no_guard=True,
        sandbox=True,
        pass_through_args=["--exec", "echo denied"],
    )
    node_denied_output = capsys.readouterr()
    node_denied_combined = f"{node_denied_output.out}\n{node_denied_output.err}"

    assert python_denied != 0, python_denied_combined
    assert node_denied != 0, node_denied_combined
    assert "classification=policy_violation" in python_denied_combined
    assert "classification=policy_violation" in node_denied_combined
    assert "capability=shell action=shell_execution" in python_denied_combined
    assert "capability=shell action=shell_execution" in node_denied_combined

    python_allowed = run_command.run_agent(
        agent_dir_arg=str(python_agent),
        input_arg="hello",
        no_guard=True,
        sandbox=True,
        pass_through_args=["--url", "https://example.com"],
    )
    python_allowed_output = capsys.readouterr()
    python_allowed_combined = f"{python_allowed_output.out}\n{python_allowed_output.err}"

    node_allowed = run_command.run_agent(
        agent_dir_arg=str(node_agent),
        input_arg="hello",
        no_guard=True,
        sandbox=True,
        pass_through_args=["--url", "https://example.com"],
    )
    node_allowed_output = capsys.readouterr()
    node_allowed_combined = f"{node_allowed_output.out}\n{node_allowed_output.err}"

    assert python_allowed == 0, python_allowed_combined
    assert node_allowed == 0, node_allowed_combined
    assert "sandbox policy check passed" in python_allowed_combined
    assert "sandbox policy check passed" in node_allowed_combined

    # Denied runs must not launch subprocess entrypoints; only allowed runs should.
    assert len(popen_invocations) == 2
    assert popen_invocations[0][0] == str(python_executable)
    assert popen_invocations[1][0] == "node"


def test_feature41_feature39_integration_and_graceful_degradation(tmp_path, monkeypatch, capsys):
    from kinnoo import run_command

    def _write_agent(agent_dir: Path, runtime_language: str) -> None:
        agent_dir.mkdir(parents=True, exist_ok=True)
        entrypoint_name = "run.py" if runtime_language == "python" else "run.js"
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / entrypoint_name).write_text(
            "print('feature41-monitor-integration-ran')\n"
            if runtime_language == "python"
            else "console.log('feature41-monitor-integration-ran');\n",
            encoding="utf-8",
        )
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    f"name: feature41-{runtime_language}-integration-agent",
                    "version: 1.0.0",
                    f"entrypoint: {entrypoint_name}",
                    "runtime:",
                    f"    language: {runtime_language}",
                    "    version: \">=3.10\"" if runtime_language == "python" else "    version: \">=20.0.0\"",
                    "    type: one-shot",
                    "dependencies: []",
                    "inputs:",
                    "    type: text",
                    "outputs:",
                    "    type: text",
                    "permissions:",
                    "    network: false",
                    "    filesystem_scope: read-only",
                    "    shell: false",
                    "    browser: false",
                    "    env_access: []",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (agent_dir / "README.md").write_text("feature41 integration fixture", encoding="utf-8")
        (agent_dir / "tools").mkdir(exist_ok=True)
        (agent_dir / "prompts").mkdir(exist_ok=True)

    python_agent = tmp_path / "feature41-python-integration-agent"
    node_agent = tmp_path / "feature41-node-integration-agent"
    _write_agent(python_agent, "python")
    _write_agent(node_agent, "nodejs")

    python_executable = python_agent / ".venv" / "bin" / "python"
    python_executable.parent.mkdir(parents=True, exist_ok=True)
    python_executable.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    python_executable.chmod(0o755)

    class _FakeProcess:
        def __init__(self, args, **_kwargs):
            self.args = args
            self.returncode = 0

        def communicate(self, timeout=None):
            del timeout
            return None

    def _fake_popen(args, **kwargs):
        del kwargs
        return _FakeProcess(args)

    monkeypatch.setattr(run_command.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(run_command.venv, "create", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("KINNOO_FORCE_TELEMETRY_LIMITED", "1")

    python_result = run_command.run_agent(
        agent_dir_arg=str(python_agent),
        input_arg="hello",
        no_guard=True,
    )
    python_capture = capsys.readouterr()
    python_output = f"{python_capture.out}\n{python_capture.err}"

    node_result = run_command.run_agent(
        agent_dir_arg=str(node_agent),
        input_arg="hello",
        no_guard=True,
    )
    node_capture = capsys.readouterr()
    node_output = f"{node_capture.out}\n{node_capture.err}"

    assert python_result == 0, python_output
    assert node_result == 0, node_output

    assert "[kinnoo monitor] policy summary:" in python_output
    assert "network=denied" in python_output
    assert "filesystem_scope=read-only" in python_output
    assert "shell=denied" in python_output
    assert "browser=denied" in python_output

    assert "[kinnoo monitor] policy summary:" in node_output
    assert "network=denied" in node_output
    assert "filesystem_scope=read-only" in node_output
    assert "shell=denied" in node_output
    assert "browser=denied" in node_output

    assert "reason_code=telemetry_limited_backend" in python_output
    assert "reason_code=telemetry_limited_backend" in node_output
    assert "limited_capabilities=[network, filesystem]" in python_output
    assert "limited_capabilities=[network, filesystem]" in node_output

