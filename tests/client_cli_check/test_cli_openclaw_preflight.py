from __future__ import annotations

import subprocess

from kinnoo.openclaw_preflight import ensure_openclaw_cli, parse_openclaw_version
from kinnoo.openclaw_preflight import run_openclaw_preflight_for_command


def test_feature76_cli_detection_version_gate(monkeypatch):
    # Missing CLI path should fail deterministically.
    monkeypatch.setattr("kinnoo.openclaw_preflight.shutil.which", lambda _name: None)
    missing = ensure_openclaw_cli("2026.3.28")
    assert missing.ok is False
    assert missing.category == "openclaw_cli_missing"

    # Present CLI but old version should fail with upgrade guidance.
    monkeypatch.setattr("kinnoo.openclaw_preflight.shutil.which", lambda _name: "/usr/bin/openclaw")

    def fake_run_old(_args, capture_output, text, check):
        return subprocess.CompletedProcess(_args, 0, stdout="openclaw 2026.3.27\n", stderr="")

    monkeypatch.setattr("kinnoo.openclaw_preflight.subprocess.run", fake_run_old)
    old = ensure_openclaw_cli("2026.3.28")
    assert old.ok is False
    assert old.category == "openclaw_cli_version_unsupported"
    assert "Upgrade OpenClaw CLI" in old.message

    # Suffix versions must parse and pass when >= minimum.
    def fake_run_new(_args, capture_output, text, check):
        return subprocess.CompletedProcess(_args, 0, stdout="v2026.3.31-beta.1\n", stderr="")

    monkeypatch.setattr("kinnoo.openclaw_preflight.subprocess.run", fake_run_new)
    modern = ensure_openclaw_cli("2026.3.28")
    assert modern.ok is True
    assert modern.category == "openclaw_cli_precheck_ok"
    assert modern.version == "2026.3.31"

    assert parse_openclaw_version("openclaw 2026.4.1") == (2026, 4, 1)
    assert parse_openclaw_version("v2026.3.31-beta.1") == (2026, 3, 31)
    assert parse_openclaw_version("no-version") is None


def test_feature76_preflight_reuse_and_gateway_modes(monkeypatch):
    calls = {"cli": 0, "gateway": 0}

    def fake_cli(minimum_version: str):
        calls["cli"] += 1
        from kinnoo.openclaw_preflight import OpenClawPreflightResult

        return OpenClawPreflightResult(
            ok=True,
            category="openclaw_cli_precheck_ok",
            message=f"ok {minimum_version}",
            version="2026.3.31",
        )

    def fake_gateway():
        calls["gateway"] += 1
        from kinnoo.openclaw_preflight import OpenClawPreflightResult

        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_gateway_unhealthy",
            message="gateway down",
        )

    monkeypatch.setattr("kinnoo.openclaw_preflight.ensure_openclaw_cli", fake_cli)
    monkeypatch.setattr("kinnoo.openclaw_preflight.ensure_openclaw_gateway", fake_gateway)

    # init/import/install should not require gateway checks.
    init_result = run_openclaw_preflight_for_command("init")
    import_result = run_openclaw_preflight_for_command("import")
    install_result = run_openclaw_preflight_for_command("install")

    assert init_result.ok is True
    assert import_result.ok is True
    assert install_result.ok is True

    # run/logs/skill flows should require gateway checks.
    run_result = run_openclaw_preflight_for_command("run")
    logs_result = run_openclaw_preflight_for_command("logs")
    skill_install_result = run_openclaw_preflight_for_command("openclaw-skill-install")
    skill_search_result = run_openclaw_preflight_for_command("openclaw-skill-search")

    assert run_result.ok is False
    assert logs_result.ok is False
    assert skill_install_result.ok is False
    assert skill_search_result.ok is False
    assert run_result.category == "openclaw_gateway_unhealthy"

    assert calls["cli"] == 7
    assert calls["gateway"] == 4
