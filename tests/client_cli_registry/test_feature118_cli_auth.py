from __future__ import annotations

import base64
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import parse as urllib_parse
from urllib import request as urllib_request

import pytest

from kinnoo.auth_command import (
    _tenant_slug_from_token,
    login_command,
    logout_command,
    refresh_registry_auth_if_needed,
)
from kinnoo.config import load_registry_config


def _jwt_with_tenant(tenant_slug: str) -> str:
    payload = {"tenant_slug": tenant_slug}
    payload_segment = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{payload_segment}.signature"


def _jwt_with_payload(payload: dict[str, str]) -> str:
    payload_segment = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{payload_segment}.signature"


class _OIDCTestServer:
    def __init__(self, *, access_token: str | None = None, userinfo_email: str = "alice@example.com") -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self.refresh_calls = 0
        self.access_token = access_token or _jwt_with_tenant("team-alpha")
        self.userinfo_email = userinfo_email

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        outer = self

        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                params = urllib_parse.parse_qs(raw_body)

                if self.path == "/token":
                    grant_type = (params.get("grant_type") or [""])[0]
                    if grant_type == "authorization_code":
                        self._write_json(
                            200,
                            {
                                "access_token": outer.access_token,
                                "refresh_token": "refresh-1",
                                "expires_in": 30,
                                "token_type": "Bearer",
                            },
                        )
                        return
                    if grant_type == "refresh_token":
                        outer.refresh_calls += 1
                        self._write_json(
                            200,
                            {
                                "access_token": _jwt_with_tenant("team-alpha"),
                                "refresh_token": "refresh-2",
                                "expires_in": 3600,
                                "token_type": "Bearer",
                            },
                        )
                        return

                if self.path == "/revoke":
                    self._write_json(200, {"ok": True})
                    return

                self._write_json(404, {"error": "not found"})

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/api/auth/config":
                    self._write_json(
                        200,
                        {
                            "schema_version": 1,
                            "auth_mode": "oidc",
                            "issuer_url": f"{outer.base_url}",
                            "authorization_endpoint": f"{outer.base_url}/authorize",
                            "token_endpoint": f"{outer.base_url}/token",
                            "logout_endpoint": f"{outer.base_url}/logout",
                            "userinfo_endpoint": f"{outer.base_url}/userinfo",
                            "audience": "https://api.kinnoo.local",
                            "cli_client_id": "cli-client-id",
                        },
                    )
                    return
                if self.path == "/userinfo":
                    self._write_json(
                        200,
                        {
                            "email": outer.userinfo_email,
                            "sub": "kinde-user-123",
                        },
                    )
                    return
                self._write_json(404, {"error": "not found"})

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                del format, args

            def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return _Handler


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature118_test711_refresh_and_logout_no_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
#     ...


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
def test_feature118_cli_tenant_slug_prefers_email(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    token = _jwt_with_payload({
        "email": "jerryschen@example.com",
        "org_code": "org_90bd1f158ac",
    })
    assert _tenant_slug_from_token(token) == "jerryschen"


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
def test_feature118_cli_tenant_slug_falls_back_to_org_code_when_email_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    token = _jwt_with_payload({
        "org_code": "org_90bd1f158ac",
    })
    assert _tenant_slug_from_token(token) == "org_90bd1f158ac"


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
@pytest.mark.client_cli_registry
def test_feature118_hosted_login_discovers_auth_config_from_registry_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _OIDCTestServer()
    server.start()
    try:
        home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("KINNOO_REGISTRY_URL", server.base_url)

        # Simulate pip-user workflow: only registry URL is required.
        monkeypatch.delenv("AUTH_CLI_CLIENT_ID", raising=False)
        monkeypatch.delenv("KINDE_CLI_CLIENT_ID", raising=False)
        monkeypatch.delenv("AUTH_AUTHORIZATION_ENDPOINT", raising=False)
        monkeypatch.delenv("AUTHORIZATION_ENDPOINT", raising=False)
        monkeypatch.delenv("AUTH_TOKEN_ENDPOINT", raising=False)
        monkeypatch.delenv("TOKEN_ENDPOINT", raising=False)
        monkeypatch.delenv("AUTH_USERINFO_ENDPOINT", raising=False)
        monkeypatch.delenv("USERINFO_ENDPOINT", raising=False)
        monkeypatch.delenv("AUTH_AUDIENCE", raising=False)
        monkeypatch.delenv("KINDE_AUDIENCE", raising=False)

        def _fake_browser_open(url: str) -> bool:
            parsed = urllib_parse.urlparse(url)
            params = urllib_parse.parse_qs(parsed.query)
            assert parsed.path == "/authorize"
            assert (params.get("client_id") or [""])[0] == "cli-client-id"
            redirect_uri = (params.get("redirect_uri") or [""])[0]
            state = (params.get("state") or [""])[0]
            urllib_request.urlopen(f"{redirect_uri}?code=abc123&state={state}", timeout=2).read()
            return True

        monkeypatch.setattr("kinnoo.auth_command.webbrowser.open", _fake_browser_open)

        result = login_command(email=None, password=None)
        assert result == 0

        config = load_registry_config()
        assert config.registry_url == server.base_url
        assert config.registry_token is not None
        assert config.refresh_token == "refresh-1"
        assert config.token_endpoint == f"{server.base_url}/token"
        assert config.authorization_endpoint == f"{server.base_url}/authorize"
        assert config.oidc_client_id == "cli-client-id"
    finally:
        server.stop()


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
@pytest.mark.client_cli_registry
def test_feature118_login_with_explicit_registry_url_fails_when_discovery_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    monkeypatch.setenv("KINNOO_REGISTRY_URL", "https://registry.example.invalid")
    monkeypatch.delenv("KINNOO_LOGIN_ALLOW_LEGACY_FALLBACK", raising=False)

    monkeypatch.delenv("AUTH_CLI_CLIENT_ID", raising=False)
    monkeypatch.delenv("KINDE_CLI_CLIENT_ID", raising=False)
    monkeypatch.delenv("AUTH_AUTHORIZATION_ENDPOINT", raising=False)
    monkeypatch.delenv("AUTHORIZATION_ENDPOINT", raising=False)
    monkeypatch.delenv("AUTH_TOKEN_ENDPOINT", raising=False)
    monkeypatch.delenv("TOKEN_ENDPOINT", raising=False)

    monkeypatch.setattr(
        "kinnoo.auth_command._hosted_cli_config_from_registry",
        lambda *, registry_url: (None, f"HTTP 404 from {registry_url}/api/auth/config"),
    )

    result = login_command(email=None, password=None)
    captured = capsys.readouterr()
    combined = f"{captured.out}\n{captured.err}"

    assert result == 1
    assert "Hosted auth discovery failed; refusing silent fallback to legacy email/password login." in combined
    assert "KINNOO_LOGIN_ALLOW_LEGACY_FALLBACK=1" in combined
    assert "Email/Username:" not in combined


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
@pytest.mark.client_cli_registry
def test_feature118_login_with_explicit_registry_url_allows_opt_in_legacy_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KINNOO_REGISTRY_URL", "https://registry.example.invalid")
    monkeypatch.setenv("KINNOO_LOGIN_ALLOW_LEGACY_FALLBACK", "1")

    monkeypatch.delenv("AUTH_CLI_CLIENT_ID", raising=False)
    monkeypatch.delenv("KINDE_CLI_CLIENT_ID", raising=False)
    monkeypatch.delenv("AUTH_AUTHORIZATION_ENDPOINT", raising=False)
    monkeypatch.delenv("AUTHORIZATION_ENDPOINT", raising=False)
    monkeypatch.delenv("AUTH_TOKEN_ENDPOINT", raising=False)
    monkeypatch.delenv("TOKEN_ENDPOINT", raising=False)

    monkeypatch.setattr(
        "kinnoo.auth_command._hosted_cli_config_from_registry",
        lambda *, registry_url: (None, f"HTTP 404 from {registry_url}/api/auth/config"),
    )
    monkeypatch.setattr(
        "kinnoo.auth_command._issue_token",
        lambda *, registry_url, email, password, tenant_slug: (_jwt_with_tenant("team-alpha"), None),
    )

    result = login_command(email="user@example.com", password="test-password")
    assert result == 0
