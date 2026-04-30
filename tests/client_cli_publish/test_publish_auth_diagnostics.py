from __future__ import annotations

import io
from urllib import error as urllib_error

from kinnoo.config import RegistryConfig
from kinnoo import publish_command


def test_publish_auth_includes_url_error_reason(monkeypatch) -> None:
    monkeypatch.setenv("REGISTRY_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("REGISTRY_ADMIN_PASSWORD", "secret")

    def _fake_urlopen(_request, timeout=15.0):
        del _request, timeout
        raise urllib_error.URLError("timed out")

    monkeypatch.setattr(publish_command.urllib_request, "urlopen", _fake_urlopen)

    result = publish_command._issue_registry_token_with_admin_credentials(
        config=RegistryConfig(
            registry_url="https://registry-dev.kinnoo.ai",
            registry_token=None,
            tenant_slug="global",
        )
    )

    assert isinstance(result, str)
    assert "Failed to reach registry auth endpoint." in result
    assert "Reason: timed out" in result


def test_publish_auth_includes_exception_type_when_reason_empty(monkeypatch) -> None:
    monkeypatch.setenv("REGISTRY_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("REGISTRY_ADMIN_PASSWORD", "secret")

    class _SilentError(Exception):
        def __str__(self) -> str:  # pragma: no cover - deterministic behavior assertion below
            return ""

    def _fake_urlopen(_request, timeout=15.0):
        del _request, timeout
        raise urllib_error.URLError(_SilentError())

    monkeypatch.setattr(publish_command.urllib_request, "urlopen", _fake_urlopen)

    result = publish_command._issue_registry_token_with_admin_credentials(
        config=RegistryConfig(
            registry_url="https://registry-dev.kinnoo.ai",
            registry_token=None,
            tenant_slug="global",
        )
    )

    assert isinstance(result, str)
    assert "Reason: _SilentError" in result


def test_publish_auth_http_error_includes_response_body_and_user_agent(monkeypatch) -> None:
    monkeypatch.setenv("REGISTRY_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("REGISTRY_ADMIN_PASSWORD", "secret")

    def _fake_urlopen(request, timeout=15.0):
        del timeout
        assert request.headers.get("User-agent") == "curl/8.7.1"
        raise urllib_error.HTTPError(
            request.full_url,
            403,
            "Forbidden",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"edge forbidden"}'),
        )

    monkeypatch.setattr(publish_command.urllib_request, "urlopen", _fake_urlopen)

    result = publish_command._issue_registry_token_with_admin_credentials(
        config=RegistryConfig(
            registry_url="https://registry-dev.kinnoo.ai",
            registry_token=None,
            tenant_slug="global",
        )
    )

    assert isinstance(result, str)
    assert "HTTP 403" in result
    assert "edge forbidden" in result


def test_publish_auth_user_agent_honors_env_override(monkeypatch) -> None:
    monkeypatch.setenv("REGISTRY_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("REGISTRY_ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("KINNOO_HTTP_USER_AGENT", "Mozilla/5.0 TestAgent")

    def _fake_urlopen(request, timeout=15.0):
        del timeout
        assert request.headers.get("User-agent") == "Mozilla/5.0 TestAgent"
        raise urllib_error.URLError("blocked")

    monkeypatch.setattr(publish_command.urllib_request, "urlopen", _fake_urlopen)

    result = publish_command._issue_registry_token_with_admin_credentials(
        config=RegistryConfig(
            registry_url="https://registry-dev.kinnoo.ai",
            registry_token=None,
            tenant_slug="global",
        )
    )

    assert isinstance(result, str)
    assert "Reason: blocked" in result
