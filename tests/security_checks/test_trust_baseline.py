import subprocess
import sys
import zipfile
import json
import re
import os
from pathlib import Path

from kinnoo.checksum import write_checksum_sidecar_for_archive


def _create_trust_baseline_archive(
    tmp_path: Path,
    archive_name: str,
    create_checksum: bool = False,
) -> Path:
    archive_path = tmp_path / f"{archive_name}.kno"
    manifest = (
        f"name: {archive_name}\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "env_vars:\n"
        "  - OPENAI_API_KEY\n"
        "  - ANTHROPIC_API_KEY\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("requirements.txt", "pip\n")
        archive.writestr("run.py", "print('ok')\n")

    if create_checksum:
        write_checksum_sidecar_for_archive(archive_path)

    return archive_path


def test_install_summary_and_confirmation_prompt(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(
        tmp_path,
        "trust-agent",
        create_checksum=True,
    )

    target_yes = tmp_path / "installed-trust-agent-yes"
    yes_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_yes)],
        input="y\ny\n",
        capture_output=True,
        text=True,
    )

    yes_output = f"{yes_result.stdout}\n{yes_result.stderr}"
    assert yes_result.returncode == 0, yes_output
    assert "[kinnoo install] Install summary:" in yes_output
    assert "- Agent: trust-agent" in yes_output
    assert "- Runtime Type: one-shot" in yes_output
    assert "- Dependencies:" in yes_output
    assert "  - pip" in yes_output
    assert "- Env Vars:" in yes_output
    assert "  - OPENAI_API_KEY" in yes_output
    assert "  - ANTHROPIC_API_KEY" in yes_output
    assert "UNVERIFIED PUBLISHER" in yes_output
    assert "Continue with install? [y/N]:" in yes_output
    assert target_yes.exists()

    target_no = tmp_path / "installed-trust-agent-no"
    no_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_no)],
        input="n\n",
        capture_output=True,
        text=True,
    )

    no_output = f"{no_result.stdout}\n{no_result.stderr}"
    assert no_result.returncode != 0
    assert "UNVERIFIED PUBLISHER" in no_output
    assert "Install aborted: unverified publisher not approved." in no_output
    assert not target_no.exists()

    target_empty = tmp_path / "installed-trust-agent-empty"
    empty_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_empty)],
        input="\n",
        capture_output=True,
        text=True,
    )

    empty_output = f"{empty_result.stdout}\n{empty_result.stderr}"
    assert empty_result.returncode != 0
    assert "UNVERIFIED PUBLISHER" in empty_output
    assert "Install aborted: unverified publisher not approved." in empty_output
    assert not target_empty.exists()


def test_install_yes_flag_bypasses_prompt(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(
        tmp_path,
        "trust-agent-yes-flag",
        create_checksum=True,
    )

    target_long_flag = tmp_path / "installed-yes-long"
    long_flag_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_long_flag),
            "--yes",
            "--allow-unverified-publisher",
        ],
        capture_output=True,
        text=True,
    )

    long_flag_output = f"{long_flag_result.stdout}\n{long_flag_result.stderr}"
    assert long_flag_result.returncode == 0, long_flag_output
    assert "[kinnoo install] Install summary:" in long_flag_output
    assert "- Runtime Type: one-shot" in long_flag_output
    assert "  - pip" in long_flag_output
    assert "  - OPENAI_API_KEY" in long_flag_output
    assert "Continue with install? [y/N]:" not in long_flag_output
    assert "Unverified publisher override acknowledged" in long_flag_output
    assert target_long_flag.exists()

    target_short_flag = tmp_path / "installed-yes-short"
    short_flag_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_short_flag),
            "-y",
            "--allow-unverified-publisher",
        ],
        capture_output=True,
        text=True,
    )

    short_flag_output = f"{short_flag_result.stdout}\n{short_flag_result.stderr}"
    assert short_flag_result.returncode == 0, short_flag_output
    assert "[kinnoo install] Install summary:" in short_flag_output
    assert "- Runtime Type: one-shot" in short_flag_output
    assert "  - pip" in short_flag_output
    assert "  - OPENAI_API_KEY" in short_flag_output
    assert "Continue with install? [y/N]:" not in short_flag_output
    assert "Unverified publisher override acknowledged" in short_flag_output
    assert target_short_flag.exists()


def test_install_unverified_source_warning(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(tmp_path, "trust-agent-unverified")

    target_abort = tmp_path / "installed-unverified-abort"
    abort_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_abort)],
        input="n\n",
        capture_output=True,
        text=True,
    )

    abort_output = f"{abort_result.stdout}\n{abort_result.stderr}"
    assert abort_result.returncode != 0
    assert "This agent is from an unverified source." in abort_output
    assert "This agent is from an unverified source. Continue? (y/n):" in abort_output
    assert "Install aborted by user." in abort_output
    assert not target_abort.exists()

    target_yes = tmp_path / "installed-unverified-yes"
    yes_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_yes),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )

    yes_output = f"{yes_result.stdout}\n{yes_result.stderr}"
    assert yes_result.returncode == 0, yes_output
    assert "This agent is from an unverified source." in yes_output
    assert "This agent is from an unverified source. Continue? (y/n):" not in yes_output
    assert target_yes.exists()

    write_checksum_sidecar_for_archive(archive_path)

    target_verified = tmp_path / "installed-verified"
    verified_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_verified),
            "--yes",
            "--allow-unverified-publisher",
        ],
        capture_output=True,
        text=True,
    )

    verified_output = f"{verified_result.stdout}\n{verified_result.stderr}"
    assert verified_result.returncode == 0, verified_output
    assert "UNVERIFIED PUBLISHER" in verified_output
    assert target_verified.exists()


def _create_run_trace_agent(tmp_path: Path, agent_name: str) -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {agent_name}\n"
            "version: 1.2.0\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  type: one-shot\n"
            "  language: python\n"
            "  version: \">=3.10\"\n"
            "dependencies: []\n"
            "env_vars:\n"
            "  - TRACE_SECRET\n"
            "inputs:\n"
            "  type: string\n"
            "outputs:\n"
            "  type: string\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text(
        "import sys\n"
        "print(f\"run input: {sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    return agent_dir


def _latest_run_trace_log(home_dir: Path) -> Path:
    logs_dir = home_dir / ".kinnoo" / "logs"
    log_files = sorted(logs_dir.glob("run.*.log"))
    assert log_files, f"Expected run trace logs in {logs_dir}"
    return log_files[-1]


def test_run_trace_log_safe_fields(tmp_path: Path) -> None:
    agent_dir = _create_run_trace_agent(tmp_path, "trace-safe-agent")
    env = dict()
    env.update({"HOME": str(tmp_path), "TRACE_SECRET": "SAFE_TRACE_SECRET"})

    run_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello-trace",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert run_result.returncode == 0, f"STDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}"

    log_path = _latest_run_trace_log(tmp_path)
    assert re.fullmatch(r"run\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z\.log", log_path.name)

    log_text = log_path.read_text(encoding="utf-8")
    payload = json.loads(log_text)

    assert set(payload.keys()) == {"timestamp", "agent_name", "agent-version", "runtime_type", "exit_code"}
    assert payload["agent_name"] == "trace-safe-agent"
    assert payload["agent-version"] == "1.2.0"
    assert payload["runtime_type"] == "one-shot"
    assert payload["exit_code"] == 0
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", payload["timestamp"])
    assert "hello-trace" not in log_text


def test_run_trace_log_no_secrets(tmp_path: Path) -> None:
    agent_dir = _create_run_trace_agent(tmp_path, "trace-no-secret-agent")
    secret_value = "SECRET_VALUE_12345"
    undeclared_secret_value = "UNDECLARED_SECRET_67890"
    input_text = "SENSITIVE_INPUT_98765"
    env = dict()
    env.update(
        {
            "HOME": str(tmp_path),
            "TRACE_SECRET": secret_value,
            "OPENAI_API_KEY": undeclared_secret_value,
        }
    )

    run_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            input_text,
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert run_result.returncode == 0, f"STDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}"

    log_path = _latest_run_trace_log(tmp_path)
    log_text = log_path.read_text(encoding="utf-8")
    payload = json.loads(log_text)

    assert set(payload.keys()) == {"timestamp", "agent_name", "agent-version", "runtime_type", "exit_code"}
    assert payload["agent_name"] == "trace-no-secret-agent"
    assert payload["agent-version"] == "1.2.0"
    assert payload["runtime_type"] == "one-shot"
    assert secret_value not in log_text
    assert undeclared_secret_value not in log_text
    assert input_text not in log_text


def _assert_anchor_has_invariant_comment(file_path: Path, anchor_text: str) -> None:
    source_lines = file_path.read_text(encoding="utf-8").splitlines()
    anchor_indices = [index for index, line in enumerate(source_lines) if anchor_text in line]
    assert anchor_indices, f"Anchor not found in {file_path}: {anchor_text}"

    for anchor_index in anchor_indices:
        window_start = max(0, anchor_index - 4)
        context_window = source_lines[window_start:anchor_index + 1]
        has_invariant_comment = any(
            "SECURITY INVARIANT: only env var NAMES, never values" in context_line
            for context_line in context_window
        )
        assert has_invariant_comment, (
            f"Missing security invariant comment near anchor '{anchor_text}' in {file_path}"
        )


def test_trust_code_has_security_invariant_comments() -> None:
    root_dir = Path(__file__).resolve().parents[2]

    install_file = root_dir / "src" / "kinnoo" / "install_command.py"
    run_file = root_dir / "src" / "kinnoo" / "run_command.py"
    inspect_file = root_dir / "src" / "kinnoo" / "inspect_command.py"

    _assert_anchor_has_invariant_comment(install_file, 'print("- Env Vars:")')
    _assert_anchor_has_invariant_comment(
        run_file,
        'return False, f"env vars check failed: unresolved env vars [{missing_label}]"',
    )
    _assert_anchor_has_invariant_comment(
        run_file,
        'return True, f"env vars check passed: resolved env vars [{declared_label}]"',
    )
    _assert_anchor_has_invariant_comment(run_file, "log_file.write_text(serialized_payload, encoding=\"utf-8\")")
    _assert_anchor_has_invariant_comment(inspect_file, 'print("- Env Vars:")')


def _create_security_sweep_agent(tmp_path: Path, agent_name: str, dirty: bool) -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {agent_name}\n"
            "version: 1.0.0\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  type: one-shot\n"
            "  language: python\n"
            "  version: \"3.10\"\n"
            "dependencies: []\n"
            "env_vars:\n"
            "  - API_KEY\n"
            "inputs:\n"
            "  type: string\n"
            "outputs:\n"
            "  type: string\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    if dirty:
        run_py = (
            "import os\n"
            "print(os.environ.get('API_KEY'))\n"
        )
    else:
        run_py = "print('safe')\n"

    (agent_dir / "run.py").write_text(run_py, encoding="utf-8")

    venv_dir = agent_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "ignored.py").write_text(
        "import os\nprint(os.environ.get('SHOULD_NOT_APPEAR'))\n",
        encoding="utf-8",
    )

    return agent_dir


def test_inspect_security_sweep(tmp_path: Path) -> None:
    clean_agent = _create_security_sweep_agent(tmp_path, "inspect-clean-agent", dirty=False)
    clean_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(clean_agent)],
        capture_output=True,
        text=True,
    )

    clean_output = f"{clean_result.stdout}\n{clean_result.stderr}"
    assert clean_result.returncode == 0, clean_output
    assert "Security sweep: no env var exposure patterns detected (heuristic)" in clean_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in clean_output
    assert "ignored.py" not in clean_output

    dirty_agent = _create_security_sweep_agent(tmp_path, "inspect-dirty-agent", dirty=True)
    dirty_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(dirty_agent)],
        capture_output=True,
        text=True,
    )

    dirty_output = f"{dirty_result.stdout}\n{dirty_result.stderr}"
    assert dirty_result.returncode == 0, dirty_output
    assert "Security sweep:" in dirty_output
    assert "run.py:" in dirty_output
    assert "print() with os.environ access" in dirty_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in dirty_output
    assert "ignored.py" not in dirty_output


def test_pack_security_sweep_non_blocking(tmp_path: Path) -> None:
    dirty_agent = _create_security_sweep_agent(tmp_path, "pack-dirty-agent", dirty=True)
    dirty_env = os.environ.copy()
    dirty_env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archives")
    dirty_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(dirty_agent)],
        capture_output=True,
        text=True,
        env=dirty_env,
    )

    dirty_output = f"{dirty_result.stdout}\n{dirty_result.stderr}"
    assert dirty_result.returncode == 0, dirty_output
    assert "Security sweep warnings:" in dirty_output
    assert "run.py:" in dirty_output
    assert "print() with os.environ access" in dirty_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in dirty_output
    assert "[kinnoo pack] Archive created:" in dirty_output

    clean_agent = _create_security_sweep_agent(tmp_path, "pack-clean-agent", dirty=False)
    clean_env = os.environ.copy()
    clean_env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archives")
    clean_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(clean_agent)],
        capture_output=True,
        text=True,
        env=clean_env,
    )

    clean_output = f"{clean_result.stdout}\n{clean_result.stderr}"
    assert clean_result.returncode == 0, clean_output
    assert "Security sweep warnings:" not in clean_output
    assert "[kinnoo pack] Archive created:" in clean_output


def test_feature38_scans_jstsjson_credentials(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature38-multilang-sweep-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        (
            "name: feature38-multilang-sweep-agent\n"
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
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

    js_mock_secret_part_1 = "gh"
    js_mock_secret_part_2 = "p_abcdefghijklmnopqrstuvwxyz0123456789AB"
    js_mock_secret = js_mock_secret_part_1 + js_mock_secret_part_2

    mjs_mock_secret_part_1 = "sk"
    mjs_mock_secret_part_2 = "-abcdefghijklmnopqrstuvwxyz123456"
    mjs_mock_secret = mjs_mock_secret_part_1 + mjs_mock_secret_part_2

    ts_mock_secret = "[REDACTED]"

    json_mock_secret_part_1 = "AK"
    json_mock_secret_part_2 = "IAABCDEFGH"
    json_mock_secret_part_3 = "IJKLMNOP"
    json_mock_secret = (
        json_mock_secret_part_1
        + json_mock_secret_part_2
        + json_mock_secret_part_3
    )

    (agent_dir / "client.js").write_text(
        f"const token = '{js_mock_secret}';\nconsole.log('client loaded');\n",
        encoding="utf-8",
    )
    (agent_dir / "worker.mjs").write_text(
        f"export const apiToken = '{mjs_mock_secret}';\n",
        encoding="utf-8",
    )
    (agent_dir / "service.ts").write_text(
        f"const slackToken = '{ts_mock_secret}';\nexport default slackToken;\n",
        encoding="utf-8",
    )
    (agent_dir / "config.json").write_text(
        json.dumps(
            {
                "aws_access_key_id": json_mock_secret,
                "api_key": "very-secret-value-12345",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    inspect_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(agent_dir)],
        capture_output=True,
        text=True,
    )

    output = f"{inspect_result.stdout}\n{inspect_result.stderr}"
    assert inspect_result.returncode == 0, output
    assert "Security sweep:" in output
    assert "client.js:" in output
    assert "worker.mjs:" in output
    assert "service.ts:" in output
    assert "config.json:" in output
    assert "credential-like pattern" in output

    assert js_mock_secret not in output
    assert mjs_mock_secret not in output
    assert ts_mock_secret not in output
    assert json_mock_secret not in output


def test_feature38_flags_risky_js_execution_primitives_with_file_line(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature38-risky-js-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "kinnoo.yaml").write_text(
        (
            "name: feature38-risky-js-agent\n"
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
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

    (agent_dir / "danger-eval.js").write_text(
        "const payload = '2 + 2';\n"
        "const result = eval(payload);\n",
        encoding="utf-8",
    )
    (agent_dir / "danger-function.mjs").write_text(
        "const fn = new Function('a', 'b', 'return a + b');\n"
        "export default fn;\n",
        encoding="utf-8",
    )
    (agent_dir / "danger-child-process.ts").write_text(
        "import { execSync } from 'child_process';\n"
        "const output = execSync('echo hi');\n"
        "export default output;\n",
        encoding="utf-8",
    )

    inspect_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(agent_dir)],
        capture_output=True,
        text=True,
    )

    output = f"{inspect_result.stdout}\n{inspect_result.stderr}"
    assert inspect_result.returncode == 0, output
    assert "Security sweep:" in output
    assert "danger-eval.js:2: risky js execution primitive (eval)" in output
    assert "danger-function.mjs:1: risky js execution primitive (Function constructor)" in output
    assert "danger-child-process.ts:2: risky js execution primitive (child process execution)" in output


def test_feature38_openclaw_config_dangerous_settings_warning(tmp_path: Path) -> None:
    dangerous_agent = tmp_path / "feature38-openclaw-danger-agent"
    dangerous_agent.mkdir(parents=True, exist_ok=True)

    manifest_text = (
        "name: feature38-openclaw-danger-agent\n"
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
    (dangerous_agent / "kinnoo.yaml").write_text(manifest_text, encoding="utf-8")
    (dangerous_agent / "requirements.txt").write_text("", encoding="utf-8")
    (dangerous_agent / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (dangerous_agent / "openclaw-config.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "allow_shell": True,
                    "disable_sandbox": True,
                    "tool_policy": "allow_all",
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    dangerous_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(dangerous_agent)],
        capture_output=True,
        text=True,
    )
    dangerous_output = f"{dangerous_result.stdout}\n{dangerous_result.stderr}"
    assert dangerous_result.returncode == 0, dangerous_output
    assert "Security sweep:" in dangerous_output
    assert "openclaw-config.json" in dangerous_output
    assert "dangerous openclaw config (allow_shell=true enables shell command execution)" in dangerous_output
    assert "dangerous openclaw config (disable_sandbox=true removes runtime isolation)" in dangerous_output
    assert "dangerous openclaw config (tool_policy=allow_all disables tool restrictions)" in dangerous_output

    safe_agent = tmp_path / "feature38-openclaw-safe-agent"
    safe_agent.mkdir(parents=True, exist_ok=True)
    (safe_agent / "kinnoo.yaml").write_text(
        manifest_text.replace("feature38-openclaw-danger-agent", "feature38-openclaw-safe-agent"),
        encoding="utf-8",
    )
    (safe_agent / "requirements.txt").write_text("", encoding="utf-8")
    (safe_agent / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (safe_agent / "openclaw-config.json").write_text(
        json.dumps(
            {
                "openclaw": {
                    "allow_shell": False,
                    "disable_sandbox": False,
                    "tool_policy": "allowlist",
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    safe_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(safe_agent)],
        capture_output=True,
        text=True,
    )
    safe_output = f"{safe_result.stdout}\n{safe_result.stderr}"
    assert safe_result.returncode == 0, safe_output
    assert "dangerous openclaw config" not in safe_output


def _create_mcp_trace_agent(tmp_path: Path, agent_name: str) -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {agent_name}\n"
            "version: 1.0.0\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  type: mcp-server\n"
            "  language: python\n"
            "  version: \">=3.10\"\n"
            "  shutdown_timeout_seconds: 0.25\n"
            "  readiness_probe:\n"
            "    method: stdout\n"
            "    marker: SERVER_READY\n"
            "dependencies: []\n"
            "inputs:\n"
            "  type: string\n"
            "  required: false\n"
            "outputs:\n"
            "  type: string\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text(
        "import time\n"
        "print('SERVER_READY', flush=True)\n"
        "time.sleep(0.2)\n"
        "print('SERVER_STOPPING', flush=True)\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    return agent_dir


def test_feature23_trace_log_server_lifecycle_fields(tmp_path: Path) -> None:
    agent_dir = _create_mcp_trace_agent(tmp_path, "trace-mcp-agent")
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(agent_dir)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    log_path = _latest_run_trace_log(tmp_path)
    payload = json.loads(log_path.read_text(encoding="utf-8"))

    assert payload["runtime_type"] == "mcp-server"
    assert "start_timestamp" in payload
    assert "stop_timestamp" in payload
    assert "server_exit_code" in payload
    assert "server_exit_signal" in payload
    assert "shutdown_sigterm_sent" in payload
    assert "shutdown_sigkill_sent" in payload
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", str(payload["start_timestamp"]))
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", str(payload["stop_timestamp"]))
