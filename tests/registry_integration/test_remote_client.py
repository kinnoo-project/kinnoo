from __future__ import annotations

import json
import io
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

import pytest

from kinnoo.remote_client import RemoteRegistryClient, RemoteRegistryClientError


class _FakeHTTPResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def test_remote_client_http_calls(monkeypatch, tmp_path: Path) -> None:
    captured_requests: list[urllib_request.Request] = []

    def fake_urlopen(request: urllib_request.Request, timeout: float = 0):
        captured_requests.append(request)

        if request.full_url.endswith("/api/publish"):
            return _FakeHTTPResponse({"ok": True, "request": "publish"})
        if "/download" in request.full_url:
            return _FakeHTTPResponse({"download_url": "https://example.test/file.kno"})
        if "/api/search" in request.full_url:
            return _FakeHTTPResponse({"items": [{"name": "demo"}]})
        if "/api/agents?tenant=" in request.full_url:
            return _FakeHTTPResponse({"items": [{"name": "demo", "version": "1.0.0"}]})

        return _FakeHTTPResponse({})

    monkeypatch.setattr(urllib_request, "urlopen", fake_urlopen)

    archive_path = tmp_path / "demo.kno"
    archive_path.write_text("archive-bytes", encoding="utf-8")

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    publish_result = client.publish(name="demo", version="1.0.0", archive_path=archive_path)
    assert publish_result["ok"] is True

    resolve_result = client.resolve(name="demo", version="1.0.0")
    assert resolve_result["download_url"] == "https://example.test/file.kno"

    search_result = client.search(query="demo")
    assert search_result == [{"name": "demo"}]

    list_result = client.list_agents()
    assert list_result == [{"name": "demo", "version": "1.0.0"}]

    assert len(captured_requests) == 4

    publish_request = captured_requests[0]
    assert publish_request.get_method() == "POST"
    assert publish_request.full_url == "https://registry.example.test/api/publish"
    assert publish_request.get_header("Authorization") == "Bearer secret-token"
    assert publish_request.get_header("User-agent") == "curl/8.7.1"
    publish_content_type = publish_request.get_header("Content-type") or ""
    assert "multipart/form-data" in publish_content_type
    publish_body = publish_request.data or b""
    assert b'name="file"; filename="demo.kno"' in publish_body
    assert b"archive-bytes" in publish_body

    resolve_request = captured_requests[1]
    assert resolve_request.get_method() == "GET"
    assert resolve_request.full_url == "https://registry.example.test/api/agents/acme/demo/1.0.0/download"
    assert resolve_request.get_header("Authorization") == "Bearer secret-token"

    search_request = captured_requests[2]
    assert search_request.get_method() == "GET"
    assert search_request.full_url == "https://registry.example.test/api/search?q=demo"
    assert search_request.get_header("Authorization") == "Bearer secret-token"

    list_request = captured_requests[3]
    assert list_request.get_method() == "GET"
    assert list_request.full_url == "https://registry.example.test/api/agents?tenant=acme"
    assert list_request.get_header("Authorization") == "Bearer secret-token"


def test_error_handling(monkeypatch, tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.kno"
    archive_path.write_text("archive-bytes", encoding="utf-8")

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    def _http_error(status_code: int) -> urllib_error.HTTPError:
        return urllib_error.HTTPError(
            url="https://registry.example.test/api/publish",
            code=status_code,
            msg=f"HTTP {status_code}",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"boom"}}'),
        )

    scenarios = [
        (
            urllib_error.URLError(ConnectionRefusedError("Connection refused")),
            "server not reachable",
        ),
        (_http_error(401), "unauthorized"),
        (_http_error(403), "forbidden"),
        (_http_error(404), "not found"),
        (_http_error(409), "conflict"),
        (_http_error(429), "rate limited"),
        (_http_error(500), "server error"),
    ]

    for raised_error, expected_message_part in scenarios:
        def _raise_error(_request, timeout: float = 0):
            del timeout
            raise raised_error

        monkeypatch.setattr(urllib_request, "urlopen", _raise_error)

        with pytest.raises(RemoteRegistryClientError) as exc_info:
            client.publish(name="demo", version="1.0.0", archive_path=archive_path)

        assert expected_message_part in str(exc_info.value).lower()


def test_resolve_normalizes_relative_download_url(monkeypatch) -> None:
    def fake_urlopen(request: urllib_request.Request, timeout: float = 0):
        del timeout
        assert request.full_url == "https://registry.example.test/api/agents/acme/demo/1.0.0/download"
        return _FakeHTTPResponse({"download_url": "/data/archives/demo.kno"})

    monkeypatch.setattr(urllib_request, "urlopen", fake_urlopen)

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    resolved = client.resolve(name="demo", version="1.0.0")
    assert resolved["download_url"] == "https://registry.example.test/data/archives/demo.kno"


def test_forbidden_error_includes_response_body(monkeypatch, tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.kno"
    archive_path.write_text("archive-bytes", encoding="utf-8")

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    raised_error = urllib_error.HTTPError(
        url="https://registry.example.test/api/publish",
        code=403,
        msg="HTTP 403",
        hdrs=None,
        fp=io.BytesIO(b'{"error":{"message":"policy block"}}'),
    )

    def _raise_error(_request, timeout: float = 0):
        del timeout
        raise raised_error

    monkeypatch.setattr(urllib_request, "urlopen", _raise_error)

    with pytest.raises(RemoteRegistryClientError) as exc_info:
        client.publish(name="demo", version="1.0.0", archive_path=archive_path)

    rendered = str(exc_info.value).lower()
    assert "forbidden" in rendered
    assert "policy block" in rendered


def test_remote_client_user_agent_honors_env_override(monkeypatch, tmp_path: Path) -> None:
    captured_requests: list[urllib_request.Request] = []

    def fake_urlopen(request: urllib_request.Request, timeout: float = 0):
        del timeout
        captured_requests.append(request)
        return _FakeHTTPResponse({"ok": True})

    monkeypatch.setenv("KINNOO_HTTP_USER_AGENT", "Mozilla/5.0 TestAgent")
    monkeypatch.setattr(urllib_request, "urlopen", fake_urlopen)

    archive_path = tmp_path / "demo.kno"
    archive_path.write_text("archive-bytes", encoding="utf-8")

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    result = client.publish(name="demo", version="1.0.0", archive_path=archive_path)
    assert result["ok"] is True
    assert captured_requests[0].get_header("User-agent") == "Mozilla/5.0 TestAgent"


def test_remote_client_request_bytes_uses_auth(monkeypatch) -> None:
    captured_requests: list[urllib_request.Request] = []

    class _BytesResponse:
        def read(self) -> bytes:
            return b"archive-bytes"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            del exc_type, exc_val, exc_tb
            return None

    def fake_urlopen(request: urllib_request.Request, timeout: float = 0):
        del timeout
        captured_requests.append(request)
        return _BytesResponse()

    monkeypatch.setattr(urllib_request, "urlopen", fake_urlopen)

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    payload = client.request_bytes(path="/api/download/demo")
    assert payload == b"archive-bytes"
    assert captured_requests[0].full_url == "https://registry.example.test/api/download/demo"
    assert captured_requests[0].get_header("Authorization") == "Bearer secret-token"


def test_remote_client_request_bytes_http_error(monkeypatch) -> None:
    raised_error = urllib_error.HTTPError(
        url="https://registry.example.test/api/download/demo",
        code=404,
        msg="HTTP 404",
        hdrs=None,
        fp=io.BytesIO(b'{"error":{"message":"missing"}}'),
    )

    def _raise_error(_request, timeout: float = 0):
        del timeout
        raise raised_error

    monkeypatch.setattr(urllib_request, "urlopen", _raise_error)

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    with pytest.raises(RemoteRegistryClientError) as exc_info:
        client.request_bytes(path="/api/download/demo")

    rendered = str(exc_info.value).lower()
    assert "not found" in rendered
    assert "missing" in rendered
