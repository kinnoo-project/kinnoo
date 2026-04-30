from __future__ import annotations

from pathlib import Path

import pytest

_MARKER_DESCRIPTIONS: dict[str, str] = {
    "regression_unit": "unit regression tests",
    "regression_integration": "integration regression tests",
    "regression_smoke": "smoke regression tests",
    "regression_uat": "user acceptance regression tests",
    "regression_sat": "system acceptance regression tests",
    "client_cli_init": "tests for client CLI init command surface",
    "client_cli_run": "tests for client CLI run command surface",
    "client_cli_test": "tests for client CLI test command surface",
    "client_cli_install": "tests for client CLI install command surface",
    "client_cli_pack": "tests for client CLI pack command surface",
    "client_cli_diff": "tests for client CLI diff command surface",
    "client_cli_fetch": "tests for client CLI fetch command surface",
    "client_cli_uninstall": "tests for client CLI uninstall command surface",
    "client_cli_keygen": "tests for client CLI keygen command surface",
    "client_cli_inspect": "tests for client CLI inspect command surface",
    "client_cli_publish": "tests for client CLI publish command surface",
    "client_cli_list": "tests for client CLI list command surface",
    "client_cli_search": "tests for client CLI search command surface",
    "client_cli_login": "tests for client CLI login command surface",
    "client_cli_logout": "tests for client CLI logout command surface",
    "client_cli_import": "tests for client CLI import command surface",
    "client_cli_check": "tests for client CLI check command surface",
    "client_cli_registry": "aggregate marker for registry command surfaces",
    "schema_contract": "schema/API contract tests",
    "schema_unit": "unit tests for in-memory schema validation",
    "integration": "integration tests",
    "client_cli": "client command-line behavior tests",
    "e2e": "end-to-end workflow tests",
    "validator": "validator module tests",
    "analyzer": "analyzer module tests",
    "registry_client": "local registry client tests",
    "registry_remote": "remote registry contract tests",
    "server_api": "server-side API tests",
    "web_ui": "web frontend tests",
    "docs_contract": "documentation contract tests",
    "security_checks": "security and hardening tests",
    "ops": "operational/devops scripts and IaC tests",
}


def register_markers(config: pytest.Config) -> None:
    for marker, description in sorted(_MARKER_DESCRIPTIONS.items()):
        config.addinivalue_line("markers", f"{marker}: {description}")


def _add(item: pytest.Item, marker: str) -> None:
    item.add_marker(getattr(pytest.mark, marker))


def apply_auto_markers(items: list[pytest.Item]) -> None:
    for item in items:
        nodeid = item.nodeid.lower()
        path = Path(str(item.fspath)).as_posix().lower()
        name = item.name.lower()

        if "smoke" in name or "smoke" in nodeid:
            _add(item, "regression_smoke")
        if "uat" in name or "uat" in nodeid:
            _add(item, "regression_uat")
        if "sat" in name or "sat" in nodeid:
            _add(item, "regression_sat")
        if "schema_contract" in name or "schema_contract" in nodeid:
            _add(item, "schema_contract")

        if "/server/tests/" in path:
            _add(item, "server_api")
            _add(item, "integration")

        if path.endswith("test_web_frontend_setup.py"):
            _add(item, "web_ui")
            _add(item, "integration")

        if path.endswith("test_docs.py"):
            _add(item, "docs_contract")

        if "test_validator.py" in path:
            _add(item, "validator")
            if "entrypoint_path" in name or "entrypoints_union" in name:
                _add(item, "integration")
                _add(item, "regression_integration")
            elif "analyzer" in name:
                _add(item, "analyzer")
                _add(item, "integration")
                _add(item, "regression_integration")
            else:
                _add(item, "schema_unit")
                _add(item, "regression_unit")

        if "test_analyzer.py" in path:
            _add(item, "analyzer")
            _add(item, "integration")
            _add(item, "regression_integration")

        if "test_remote_client.py" in path:
            _add(item, "registry_client")
            _add(item, "registry_remote")
            _add(item, "integration")
            _add(item, "regression_integration")

        if "test_trust_baseline.py" in path or "test_input_guard" in path or "security" in name:
            _add(item, "security_checks")

        if "test_init.py" in path:
            _add(item, "client_cli_init")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_cli.py" in path:
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
            if " keygen" in f" {name}" or "_keygen" in name:
                _add(item, "client_cli_keygen")
            if " uninstall" in f" {name}" or "_uninstall" in name:
                _add(item, "client_cli_uninstall")
            if " fetch" in f" {name}" or "_fetch" in name:
                _add(item, "client_cli_fetch")
                _add(item, "client_cli_registry")
            if " diff" in f" {name}" or "_diff" in name:
                _add(item, "client_cli_diff")
            if " check" in f" {name}" or "_check" in name:
                _add(item, "client_cli_check")
            if " run" in f" {name}" or "_run" in name:
                _add(item, "client_cli_run")
            if " test" in f" {name}" or "_test" in name:
                _add(item, "client_cli_test")
        if "test_cli_inspect.py" in path:
            _add(item, "client_cli_inspect")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_pack" in path:
            _add(item, "client_cli_pack")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_install" in path or "test_cli_install" in path:
            _add(item, "client_cli_install")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_publish" in path:
            _add(item, "client_cli_publish")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_run_preflight" in path:
            _add(item, "client_cli_run")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_cli_import" in path:
            _add(item, "client_cli_import")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_cli_registry" in path or "test_registry" in path:
            _add(item, "registry_remote")
            _add(item, "client_cli_registry")
            _add(item, "client_cli_search")
            _add(item, "client_cli_list")
            _add(item, "client_cli_login")
            _add(item, "client_cli_logout")
            _add(item, "client_cli_fetch")
            _add(item, "client_cli_publish")
            _add(item, "client_cli_install")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_cli_remote_summary_shape" in path:
            _add(item, "registry_remote")
            _add(item, "client_cli_registry")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_cli_openclaw_preflight" in path:
            _add(item, "client_cli_check")
            _add(item, "client_cli")
            _add(item, "integration")
            _add(item, "regression_integration")
        if "test_archive_" in path:
            _add(item, "client_cli_pack")
            _add(item, "client_cli_install")
            _add(item, "integration")
            _add(item, "regression_integration")
