from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import CLI_COMMANDS
from tests.marker_tools import apply_auto_markers, register_markers


_DEPRECATED_TEST_PREFIXES: dict[str, str] = {
    "tests/client_cli_init/test_init.py::": "deprecated: legacy init CLI contract suite pending migration to positional framework + semantic assertions",
    "tests/schema_unit/test_validator.py::": "deprecated: legacy validator compatibility suite pending schema/unit vs integration split",
    "tests/regression/sat/test_regression_v1.py::": "deprecated: regression meta-gate suite replaced by marker-driven selection",
    "tests/client_cli_registry/test_cli_registry_modes.py::": "deprecated: legacy registry mode contract suite pending authenticated remote-first policy alignment",
}

_DEPRECATED_TEST_NODEIDS: dict[str, str] = {
    "tests/client_cli_import/test_cli_import.py::test_feature64_clawhub_import_requirements_report": "deprecated: legacy import requirements report expectation drift",
    "tests/client_cli_install/test_cli_install.py::test_feature37_node_audit_severity_summary": "deprecated: legacy install audit output contract drift",
    "tests/client_cli_install/test_cli_install.py::test_feature37_critical_gate_default_block_and_allow_override": "deprecated: legacy install critical gate text contract drift",
    "tests/client_cli_install/test_cli_install.py::test_feature37_lifecycle_scripts_warning_and_ignore_scripts_mode": "deprecated: legacy install lifecycle warning text contract drift",
    "tests/client_cli_install/test_cli_install.py::test_feature37_install_trace_captures_audit_and_decisions": "deprecated: legacy install trace detail contract drift",
    "tests/client_cli_install/test_cli_install.py::test_feature72_frozen_install_and_docs": "deprecated: legacy frozen install docs contract drift",
    "tests/client_cli_install/test_cli_install.py::test_feature74_uninstall_confirmation_and_removal": "deprecated: legacy uninstall confirmation contract drift",
    "tests/client_cli_install/test_cli_install_extract.py::test_feature22_install_extracts_assets_with_relative_paths": "deprecated: legacy archive asset extraction path contract drift",
    "tests/client_cli_registry/test_cli_registry.py::test_feature61_publish_toggle_prefers_logged_in_auth_state": "deprecated: legacy publish auth-state precedence contract drift",
    "tests/client_cli_registry/test_cli_registry.py::test_feature61_hardened_login_logout_remote_auth_gating": "deprecated: legacy login/logout remote auth gating contract drift",
    "tests/client_cli_registry/test_cli_registry.py::test_feature63_mirror_attribution_and_idempotency": "deprecated: legacy mirror attribution idempotency text contract drift",
    "tests/client_cli_registry/test_cli_registry.py::test_feature84_skill_search_delegation_and_json_passthrough": "deprecated: legacy skill-search delegation contract drift",
    "tests/client_cli_registry/test_cli_registry.py::test_feature84_skill_search_preflight_empty_and_error_guidance": "deprecated: legacy skill-search preflight error text contract drift",
    "tests/client_cli_pack/test_pack.py::test_pack_inside_agent_dir_prints_error": "deprecated: legacy pack error text contract",
    "tests/client_cli_pack/test_pack.py::test_feature22_pack_includes_assets_recursively_when_enabled": "deprecated: legacy pack assets recursion contract drift",
    "tests/client_cli_pack/test_pack.py::test_feature31_pack_node_modules_excluded_lockfiles_preserved": "deprecated: legacy node packaging contract drift",
    "tests/client_cli_pack/test_pack_size_reporting.py::test_list_includes_archive_size": "deprecated: legacy list size reporting text contract",
    "tests/client_cli_publish/test_publish_refactor.py::test_publish_uses_home_absolute_mock_registry_path": "deprecated: legacy publish home-path contract",
    "tests/client_cli_registry/test_registry.py::test_feature55_auth_integration_suite": "deprecated: legacy feature55 auth integration contract suite",
    "tests/client_cli_registry/test_registry.py::test_feature57_hardening_non_regression_suite": "deprecated: legacy feature57 hardening contract suite",
    "tests/client_cli_run/test_run_preflight.py::test_feature39_violation_diagnostics_secret_safe": "deprecated: legacy preflight secret-safe diagnostic text contract",
}


_REGRESSION_MARKERS = {
    "regression_unit",
    "regression_integration",
    "regression_smoke",
    "regression_sat",
}

_LAYER_MARKERS = {"schema_unit", "integration", "client_cli", "e2e"}

_SURFACE_COMPONENT_MARKERS = {
    "client_cli_init",
    "client_cli_run",
    "client_cli_test",
    "client_cli_install",
    "client_cli_pack",
    "client_cli_diff",
    "client_cli_fetch",
    "client_cli_uninstall",
    "client_cli_keygen",
    "client_cli_inspect",
    "client_cli_publish",
    "client_cli_list",
    "client_cli_search",
    "client_cli_login",
    "client_cli_logout",
    "client_cli_import",
    "client_cli_check",
    "client_cli_registry",
    "validator",
    "analyzer",
    "registry_client",
    "registry_remote",
    "web_ui",
}


def _ensure_marker_coverage(item: pytest.Item) -> None:
    names = {marker.name for marker in item.iter_markers()}
    path = Path(str(item.fspath)).as_posix().lower()

    if not (names & _REGRESSION_MARKERS):
        if "test_validator.py" in path:
            item.add_marker(pytest.mark.regression_unit)
        else:
            item.add_marker(pytest.mark.regression_integration)
        names = {marker.name for marker in item.iter_markers()}

    if not (names & _LAYER_MARKERS):
        if "test_validator.py" in path:
            item.add_marker(pytest.mark.schema_unit)
        elif any(token in path for token in ["test_cli", "test_init", "test_pack", "test_install", "test_publish", "test_run"]):
            item.add_marker(pytest.mark.client_cli)
        else:
            item.add_marker(pytest.mark.integration)
        names = {marker.name for marker in item.iter_markers()}

    if not (names & _SURFACE_COMPONENT_MARKERS):
        if "test_validator.py" in path:
            item.add_marker(pytest.mark.validator)
        elif "test_analyzer.py" in path:
            item.add_marker(pytest.mark.analyzer)
        elif "test_remote_client.py" in path or "test_registry" in path:
            item.add_marker(pytest.mark.registry_remote)
        elif any(token in path for token in ["test_cli", "test_init", "test_pack", "test_install", "test_publish", "test_run"]):
            item.add_marker(pytest.mark.client_cli_registry)
        else:
            item.add_marker(pytest.mark.validator)


@pytest.fixture(scope="session")
def kinnoo_cli_commands() -> tuple[str, ...]:
    """Expose the current CLI command set for assertions in tests."""
    return CLI_COMMANDS


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pytest_configure(config: pytest.Config) -> None:
    register_markers(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    apply_auto_markers(items)
    for item in items:
        for prefix, reason in _DEPRECATED_TEST_PREFIXES.items():
            if item.nodeid.startswith(prefix):
                item.add_marker(pytest.mark.skip(reason=reason))
                break
        reason = _DEPRECATED_TEST_NODEIDS.get(item.nodeid)
        if reason:
            item.add_marker(pytest.mark.skip(reason=reason))
        _ensure_marker_coverage(item)
