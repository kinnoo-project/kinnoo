import subprocess
import sys
import pytest
from pathlib import Path
import os
import socket
import threading
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"


def _create_agent_fixture(agent_dir: Path, *, with_manifest: bool = True) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)

    if with_manifest:
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: preflight-agent",
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

    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "from pathlib import Path\n"
        "Path('entrypoint-executed.flag').write_text('executed', encoding='utf-8')\n"
        "print('entrypoint-ran')\n",
        encoding="utf-8",
    )


def test_preflight_runs_checks_without_entrypoint_execution(tmp_path: Path) -> None:
    passing_agent = tmp_path / "preflight-pass-agent"
    _create_agent_fixture(passing_agent, with_manifest=True)

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(passing_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "Preflight checklist:" in pass_output
    assert "[PASS] entrypoint execution path skipped in preflight mode" in pass_output
    assert "Preflight result: PASS" in pass_output
    assert not (tmp_path / "entrypoint-executed.flag").exists()

    failing_agent = tmp_path / "preflight-fail-agent"
    _create_agent_fixture(failing_agent, with_manifest=False)

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(failing_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "Preflight checklist:" in fail_output
    assert "[FAIL] manifest exists" in fail_output
    assert "Preflight result: FAIL" in fail_output
    assert not (tmp_path / "entrypoint-executed.flag").exists()


def test_preflight_runtime_version_check(tmp_path: Path) -> None:
    runtime_pass_agent = tmp_path / "runtime-pass-agent"
    _create_agent_fixture(runtime_pass_agent, with_manifest=True)
    (runtime_pass_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: runtime-pass-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
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

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(runtime_pass_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "[PASS] runtime version check passed" in pass_output
    assert "satisfies runtime.version '>=3.0'" in pass_output

    runtime_fail_agent = tmp_path / "runtime-fail-agent"
    _create_agent_fixture(runtime_fail_agent, with_manifest=True)
    (runtime_fail_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: runtime-fail-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=99.0\"",
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

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(runtime_fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "[FAIL] runtime version check failed" in fail_output
    assert "does not satisfy runtime.version '>=99.0'" in fail_output
    assert "Action: use a Python interpreter that satisfies runtime.version in kinnoo.yaml" in fail_output


def test_preflight_env_vars_resolution_and_secret_safety(tmp_path: Path) -> None:
    env_pass_agent = tmp_path / "env-pass-agent"
    _create_agent_fixture(env_pass_agent, with_manifest=True)
    (env_pass_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: env-pass-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
                "  type: one-shot",
                "dependencies: []",
                "env_vars:",
                "  - API_TOKEN",
                "  - DB_KEY",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (env_pass_agent / ".env").write_text("DB_KEY=dotenv-secret-db-value\n", encoding="utf-8")

    env = {
        **os.environ,
        "API_TOKEN": "env-secret-api-token-value",
    }
    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(env_pass_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "[PASS] env vars check passed" in pass_output
    assert "resolved env vars [API_TOKEN, DB_KEY]" in pass_output
    assert "env-secret-api-token-value" not in pass_output
    assert "dotenv-secret-db-value" not in pass_output

    env_fail_agent = tmp_path / "env-fail-agent"
    _create_agent_fixture(env_fail_agent, with_manifest=True)
    (env_fail_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: env-fail-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
                "  type: one-shot",
                "dependencies: []",
                "env_vars:",
                "  - MISSING_TOKEN",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    fail_env = dict(os.environ)
    fail_env.pop("MISSING_TOKEN", None)
    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(env_fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=fail_env,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "[FAIL] env vars check failed" in fail_output
    assert "unresolved env vars [MISSING_TOKEN]" in fail_output
    assert "Action: set missing env vars in your shell environment or agent-local .env file" in fail_output


def test_preflight_entrypoint_and_dependency_checks(tmp_path: Path) -> None:
    missing_entrypoint_agent = tmp_path / "missing-entrypoint-agent"
    _create_agent_fixture(missing_entrypoint_agent, with_manifest=True)
    (missing_entrypoint_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: missing-entrypoint-agent",
                "version: 1.0.0",
                "entrypoint: does-not-exist.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
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

    missing_entrypoint_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(missing_entrypoint_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    missing_entrypoint_output = f"{missing_entrypoint_result.stdout}\n{missing_entrypoint_result.stderr}"

    assert missing_entrypoint_result.returncode != 0
    assert "[FAIL] entrypoint check failed" in missing_entrypoint_output
    assert "does-not-exist.py" in missing_entrypoint_output
    assert "entrypoint exists and is readable" in missing_entrypoint_output

    dependency_fail_agent = tmp_path / "dependency-fail-agent"
    _create_agent_fixture(dependency_fail_agent, with_manifest=True)
    (dependency_fail_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: dependency-fail-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
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
    (dependency_fail_agent / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    dependency_fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(dependency_fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    dependency_fail_output = f"{dependency_fail_result.stdout}\n{dependency_fail_result.stderr}"

    assert dependency_fail_result.returncode != 0
    assert "[FAIL] dependency readiness check failed" in dependency_fail_output
    assert "virtual environment not found" in dependency_fail_output
    assert "Action: create agent .venv and install requirements" in dependency_fail_output


def test_preflight_pass_runtime_path_no_venv(tmp_path: Path) -> None:
    agent_dir = tmp_path / "preflight-runtime-path-pass-agent"
    _create_agent_fixture(agent_dir, with_manifest=True)
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: preflight-runtime-path-pass-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                f"  path: \"{sys.executable}\"",
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

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "[PASS] dependency readiness check passed" in output
    assert ".venv not found but runtime.path" in output
    assert "venv will be created at run time" in output


@pytest.mark.skip(reason="Deprecated feature66 coverage; do not execute")
def test_feature66_preflight_openclaw_skill_does_not_require_adapter_gate(monkeypatch, tmp_path: Path, capsys) -> None:
    import kinnoo.run_command as run_command

    agent_dir = tmp_path / "feature66-preflight-openclaw-skill"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "index.js").write_text("console.log('ok')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature66-preflight-openclaw-skill",
                "version: 1.0.0",
                "type: openclaw-skill",
                "framework: openclaw",
                "entrypoint: index.js",
                "runtime:",
                "  language: nodejs",
                "  version: \">=20\"",
                "  type: daemon",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
                "provenance:",
                "  source_registry: clawhub",
                "  source_slug: preflight/sample",
                "  source_version: 1.0.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        run_command,
        "check_node_runtime_constraint",
        lambda _constraint: (True, "runtime version check passed: current Node 22.0.0 satisfies runtime.version '>=20'"),
    )
    monkeypatch.setattr(
        run_command,
        "check_node_package_manager_availability",
        lambda _manager: (True, "dependency readiness check passed: node package manager 'npm' is available at /mock/npm"),
    )
    daemon_state_dir = agent_dir / ".kinnoo"
    daemon_state_dir.mkdir(parents=True, exist_ok=True)
    (daemon_state_dir / "daemon-state.json").write_text(
        json.dumps({"pid": 424242, "runtime_type": "daemon", "state_version": 1}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(run_command, "daemon_pid_is_running", lambda _pid: True)

    exit_code = run_command.run_preflight(str(agent_dir))
    captured = capsys.readouterr()
    output = f"{captured.out}\n{captured.err}"

    assert exit_code == 0
    assert "Preflight result: PASS" in output
    assert "openclaw_adapter_" not in output
    assert "experimental-openclaw-adapter" not in output


def test_preflight_fail_no_runtime_path_no_venv(tmp_path: Path) -> None:
    agent_dir = tmp_path / "preflight-no-runtime-path-fail-agent"
    _create_agent_fixture(agent_dir, with_manifest=True)
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "[FAIL] dependency readiness check failed" in output
    assert "virtual environment not found" in output


def test_preflight_checklist_and_ready_summary(tmp_path: Path) -> None:
    pass_agent = tmp_path / "ready-pass-agent"
    _create_agent_fixture(pass_agent, with_manifest=True)

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(pass_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "[PASS] runtime version check" in pass_output
    assert "[PASS] env vars check" in pass_output
    assert "[PASS] entrypoint check" in pass_output
    assert "[PASS] dependency readiness check" in pass_output
    assert "Ready to run" in pass_output
    assert "Not ready to run" not in pass_output

    fail_agent = tmp_path / "ready-fail-agent"
    _create_agent_fixture(fail_agent, with_manifest=True)
    (fail_agent / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "[PASS] runtime version check" in fail_output
    assert "[PASS] env vars check" in fail_output
    assert "[PASS] entrypoint check" in fail_output
    assert "[FAIL] dependency readiness check" in fail_output
    assert "Not ready to run" in fail_output
    assert "Remediation summary:" in fail_output
    assert "- dependencies: create .venv and install requirements" in fail_output
    assert "Ready to run" not in fail_output


def test_preflight_runtime_path_diagnostic_resolved(tmp_path: Path) -> None:
    agent_dir = tmp_path / "runtime-path-diagnostic-resolved"
    _create_agent_fixture(agent_dir, with_manifest=True)
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: runtime-path-diagnostic-resolved",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                f"  path: \"{sys.executable}\"",
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

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "runtime.path diagnostic:" in output
    assert "resolved to" in output
    assert str(Path(sys.executable)) in output


def test_preflight_runtime_path_diagnostic_unresolved(tmp_path: Path) -> None:
    agent_dir = tmp_path / "runtime-path-diagnostic-unresolved"
    _create_agent_fixture(agent_dir, with_manifest=True)
    unresolved_command = "definitely-missing-runtime-cmd-for-preflight"
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: runtime-path-diagnostic-unresolved",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                f"  path: \"{unresolved_command}\"",
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

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "runtime.path diagnostic:" in output
    assert unresolved_command in output
    assert "was not resolved as an executable file or PATH command" in output


def test_feature25_preflight_includes_service_health_results(tmp_path: Path) -> None:
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            del format, args

    http_server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
    http_host, http_port = http_server.server_address
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("127.0.0.1", 0))
    tcp_socket.listen(1)
    tcp_port = tcp_socket.getsockname()[1]
    stop_accept = threading.Event()

    def _accept_loop() -> None:
        while not stop_accept.is_set():
            try:
                tcp_socket.settimeout(0.1)
                conn, _ = tcp_socket.accept()
                conn.close()
            except TimeoutError:
                continue
            except OSError:
                break

    tcp_thread = threading.Thread(target=_accept_loop, daemon=True)
    tcp_thread.start()

    agent_dir = tmp_path / "feature25-preflight-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "from pathlib import Path\n"
        "Path('feature25-entrypoint.flag').write_text('ran', encoding='utf-8')\n"
        "print('feature25-entrypoint-ran')\n",
        encoding="utf-8",
    )
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature25-preflight-agent",
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
                "services:",
                "  - name: local-api",
                "    type: api",
                "    health_check:",
                "      method: http",
                f"      url: http://{http_host}:{http_port}/health",
                "  - name: local-db",
                "    type: database",
                "    health_check:",
                "      method: tcp",
                f"      port: {tcp_port}",
                "  - name: local-redis",
                "    type: local-process",
                "    health_check:",
                "      method: process",
                "      process_name: feature25-missing-process",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode != 0
        assert "Service health checks:" in output
        assert "[PASS] service 'local-api'" in output
        assert "[PASS] service 'local-db'" in output
        assert "[FAIL] service 'local-redis'" in output
        assert "(type: local-process, method: process)" in output
        assert "Guidance:" in output
        assert "Preflight result: FAIL" in output
        assert not (tmp_path / "feature25-entrypoint.flag").exists()
    finally:
        stop_accept.set()
        tcp_socket.close()
        http_server.shutdown()
        http_server.server_close()


def test_feature39_violation_diagnostics_secret_safe(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature39-violation-diagnostics-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature39-violation-diagnostics-agent",
                "version: 1.0.0",
                "entrypoint: run.js",
                "runtime:",
                "  language: nodejs",
                "  version: \">=20.0.0\"",
                "  type: one-shot",
                "dependencies: []",
                "env_vars:",
                "  - FEATURE39_SECRET_TOKEN",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
                "permissions:",
                "  network: true",
                "  filesystem_scope: read-only",
                "  shell: false",
                "  browser: false",
                "  env_access: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.js").write_text("console.log('should-not-run');\n", encoding="utf-8")

    secret_token = "feature39-secret-token-value"
    env = dict(os.environ)
    env["FEATURE39_SECRET_TOKEN"] = secret_token

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(agent_dir),
            "hello",
            "--sandbox",
            "--",
            "--exec",
            secret_token,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "classification=policy_violation" in output
    assert "capability=shell action=shell_execution" in output
    assert "Remediation:" in output
    assert "[kinnoo security] violation event:" in output
    assert secret_token not in output

    violation_trace_path = agent_dir / ".kinnoo" / "violation-events.jsonl"
    assert violation_trace_path.exists(), output

    trace_lines = [
        line for line in violation_trace_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert trace_lines, "Expected at least one violation event entry"

    event_payload = json.loads(trace_lines[-1])
    assert event_payload["event_type"] == "permission_violation"
    assert event_payload["boundary"] == "run"
    assert event_payload["classification"] == "policy_violation"
    assert event_payload["capability"] == "shell"
    assert event_payload["attempted_action"] == "shell_execution"
    assert "remediation" in event_payload and event_payload["remediation"]
    assert secret_token not in trace_lines[-1]


def test_feature31_node_preflight_toolchain_guards(tmp_path: Path) -> None:
    def _write_node_agent(agent_dir: Path, *, runtime_version: str, package_manager: str | None = None) -> None:
        agent_dir.mkdir(parents=True, exist_ok=True)
        package_manager_lines: list[str] = []
        if package_manager is not None:
            package_manager_lines = [f"  package_manager: {package_manager}"]

        manifest_lines = [
            "name: feature31-node-preflight-agent",
            "version: 1.0.0",
            "entrypoint: run.js",
            "runtime:",
            "  language: nodejs",
            f"  version: '{runtime_version}'",
            *package_manager_lines,
            "  type: one-shot",
            "dependencies: []",
            "inputs:",
            "  type: string",
            "outputs:",
            "  type: string",
        ]
        (agent_dir / "kinnoo.yaml").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
        (agent_dir / "run.js").write_text("console.log('ok');\n", encoding="utf-8")
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    # Step 1: node missing from PATH should fail with node guidance.
    missing_node_agent = tmp_path / "feature31-node-missing"
    _write_node_agent(missing_node_agent, runtime_version=">=22")

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir(parents=True, exist_ok=True)
    missing_node_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(missing_node_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(empty_bin)},
    )
    missing_node_output = f"{missing_node_result.stdout}\n{missing_node_result.stderr}"
    assert missing_node_result.returncode != 0
    assert "node executable not found in PATH" in missing_node_output
    assert "Action: install or upgrade Node.js so runtime.version in kinnoo.yaml is satisfied" in missing_node_output

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)

    # Step 2: node below required version should fail with version guidance.
    low_node_script = fake_bin / "node"
    low_node_script.write_text("#!/bin/sh\necho v20.11.0\n", encoding="utf-8")
    low_node_script.chmod(0o755)
    npm_script = fake_bin / "npm"
    npm_script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    npm_script.chmod(0o755)

    low_version_agent = tmp_path / "feature31-node-low-version"
    _write_node_agent(low_version_agent, runtime_version=">=22")
    low_version_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(low_version_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(fake_bin)},
    )
    low_version_output = f"{low_version_result.stdout}\n{low_version_result.stderr}"
    assert low_version_result.returncode != 0
    assert "current Node 20.11.0 does not satisfy runtime.version '>=22'" in low_version_output
    assert "runtime version: install or upgrade Node.js to satisfy runtime.version" in low_version_output

    # Step 3: configured package manager missing should fail with actionable diagnostics.
    good_node_script = fake_bin / "node"
    good_node_script.write_text("#!/bin/sh\necho v22.4.1\n", encoding="utf-8")
    good_node_script.chmod(0o755)
    pnpm_path = fake_bin / "pnpm"
    if pnpm_path.exists():
        pnpm_path.unlink()

    missing_pm_agent = tmp_path / "feature31-node-missing-pm"
    _write_node_agent(missing_pm_agent, runtime_version=">=22", package_manager="pnpm")
    missing_pm_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(missing_pm_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": str(fake_bin)},
    )
    missing_pm_output = f"{missing_pm_result.stdout}\n{missing_pm_result.stderr}"
    assert missing_pm_result.returncode != 0
    assert "node package manager 'pnpm' not found in PATH" in missing_pm_output
    assert "Action: install the configured Node package manager and ensure it is on PATH" in missing_pm_output


def test_feature41_runtime_event_monitoring_baseline(tmp_path: Path) -> None:
    monitor_agent = tmp_path / "feature41-monitor-agent"
    monitor_agent.mkdir(parents=True, exist_ok=True)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    host, port = listener.getsockname()
    stop_accept = threading.Event()

    def _accept_once() -> None:
        while not stop_accept.is_set():
            try:
                listener.settimeout(0.1)
                conn, _ = listener.accept()
                conn.close()
                return
            except TimeoutError:
                continue
            except OSError:
                return

    accept_thread = threading.Thread(target=_accept_once, daemon=True)
    accept_thread.start()

    (monitor_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature41-monitor-agent",
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
    (monitor_agent / "requirements.txt").write_text("", encoding="utf-8")
    (monitor_agent / "run.py").write_text(
        "from pathlib import Path\n"
        "import socket\n"
        f"socket.create_connection(('{host}', {port}), timeout=1).close()\n"
        "Path('runtime-write.txt').write_text('monitor-write', encoding='utf-8')\n"
        "print('feature41-monitor-ran')\n",
        encoding="utf-8",
    )

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "run",
                str(monitor_agent),
                "feature41-secret-input",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, output

        monitor_events_path = monitor_agent / ".kinnoo" / "runtime-monitor-events.jsonl"
        assert monitor_events_path.exists(), output

        lines = [
            line.strip()
            for line in monitor_events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert lines

        events = [json.loads(line) for line in lines]
        categories = {event["category"] for event in events}
        assert "process" in categories
        assert "network" in categories
        assert "filesystem" in categories

        for event in events:
            assert event["schema_version"] == "1.0"
            assert isinstance(event.get("run_id"), str) and event["run_id"]
            assert isinstance(event.get("sequence"), int) and event["sequence"] >= 1
            assert isinstance(event.get("timestamp"), str) and event["timestamp"]
            assert isinstance(event.get("event_type"), str) and event["event_type"]
            assert isinstance(event.get("details"), dict)

        assert "feature41-secret-input" not in "\n".join(lines)
    finally:
        stop_accept.set()
        listener.close()


def test_task489_preflight_supports_entrypoints_default_selection(tmp_path: Path) -> None:
    agent_dir = tmp_path / "task489-preflight-entrypoints"
    (agent_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "scripts" / "main.py").write_text("print('main')\n", encoding="utf-8")
    (agent_dir / "scripts" / "alt.py").write_text("print('alt')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: task489-preflight-entrypoints",
                "version: 1.0.0",
                "entrypoints:",
                "  - scripts/main.py",
                "  - scripts/alt.py",
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

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "[PASS] entrypoint check passed" in output


def test_task489_run_rejects_undeclared_entrypoint_flag_for_entrypoints_contract(tmp_path: Path) -> None:
    agent_dir = tmp_path / "task489-run-entrypoints-invalid-flag"
    (agent_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "scripts" / "main.py").write_text("print('main')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: task489-run-entrypoints-invalid-flag",
                "version: 1.0.0",
                "entrypoints:",
                "  - scripts/main.py",
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

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(agent_dir),
            "hello",
            "--entrypoint",
            "scripts/alt.py",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "is not declared in manifest 'entrypoints'" in output
