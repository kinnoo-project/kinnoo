"""Remote registry client implementation backed by urllib.request."""

from __future__ import annotations

import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


class RemoteRegistryClientError(RuntimeError):
    """Actionable remote-registry client error surfaced to CLI callers."""


class RemoteRegistryClient:
    """HTTP client that implements registry backend semantics for remote servers."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        tenant_slug: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        normalized_base_url = base_url.strip().rstrip("/")
        if not normalized_base_url:
            raise ValueError("base_url must be a non-empty string")
        if not token.strip():
            raise ValueError("token must be a non-empty string")
        if not tenant_slug.strip():
            raise ValueError("tenant_slug must be a non-empty string")

        self._base_url = normalized_base_url
        self._token = token.strip()
        self._tenant_slug = tenant_slug.strip()
        self._timeout_seconds = timeout_seconds

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
        tenant: str | None = None,
    ) -> dict[str, Any]:
        """Upload archive payload to remote publish endpoint using multipart form data."""
        effective_tenant = self._effective_tenant(tenant)
        file_bytes = Path(archive_path).read_bytes()
        metadata_payload = manifest_metadata or {}
        body, content_type = _encode_multipart_form_data(
            fields={
                "tenant_slug": effective_tenant,
                "name": name,
                "version": version,
                "metadata": json.dumps(metadata_payload, sort_keys=True),
            },
            file_field_name="file",
            filename=Path(archive_path).name,
            file_bytes=file_bytes,
        )

        return self._request_json(
            method="POST",
            path="/api/publish",
            body=body,
            extra_headers={"Content-Type": content_type},
        )

    def resolve(
        self,
        *,
        name: str,
        version: Optional[str] = None,
        tenant: str | None = None,
    ) -> dict[str, Any]:
        """Fetch remote download metadata for an agent version."""
        effective_tenant = self._effective_tenant(tenant)
        selected_version = version or "latest"
        encoded_tenant = urllib_parse.quote(effective_tenant, safe="")
        encoded_name = urllib_parse.quote(name, safe="")
        encoded_version = urllib_parse.quote(selected_version, safe="")
        path = f"/api/agents/{encoded_tenant}/{encoded_name}/{encoded_version}/download"
        response = self._request_json(method="GET", path=path)
        if isinstance(response, dict):
            response = dict(response)
            raw_download_url = response.get("download_url")
            if isinstance(raw_download_url, str):
                normalized_download_url = raw_download_url.strip()
                if normalized_download_url:
                    parsed = urllib_parse.urlparse(normalized_download_url)
                    if not parsed.scheme:
                        if not normalized_download_url.startswith("/"):
                            normalized_download_url = "/" + normalized_download_url.lstrip("/")
                        normalized_download_url = f"{self._base_url}{normalized_download_url}"
                    response["download_url"] = normalized_download_url
        return response

    def search(self, *, query: str, tenant: str | None = None) -> list[dict[str, Any]]:
        """Search agents by name/description on remote registry."""
        _ = tenant
        encoded_query = urllib_parse.quote(query)
        response = self._request_json(method="GET", path=f"/api/search?q={encoded_query}")
        if isinstance(response, list):
            return response
        return response.get("items", []) if isinstance(response, dict) else []

    def list_agents(self, *, tenant: str | None = None) -> list[dict[str, Any]]:
        """List agents for a tenant on remote registry."""
        effective_tenant = self._effective_tenant(tenant)
        encoded_tenant = urllib_parse.quote(effective_tenant)
        response = self._request_json(method="GET", path=f"/api/agents?tenant={encoded_tenant}")
        if isinstance(response, list):
            return response
        return response.get("items", []) if isinstance(response, dict) else []

    def fetch_clawhub_mirror_record(self, *, slug: str) -> dict[str, Any] | None:
        """Fetch a mirrored ClawHub record by slug when backend supports this endpoint."""
        normalized_slug = slug.strip().strip("/")
        if not normalized_slug:
            return None

        encoded_slug = urllib_parse.quote(normalized_slug, safe="")
        try:
            response = self._request_json(method="GET", path=f"/api/mirror/clawhub/{encoded_slug}")
        except RemoteRegistryClientError as error:
            if "not found (404)" in str(error).lower():
                return None
            raise

        if isinstance(response, dict):
            return response
        return None

    def fetch_clawhub_mirror_index(
        self,
        *,
        full: bool = False,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch mirrored ClawHub index records for sync workflows."""
        query_params = {"mode": "full" if full else "incremental"}
        if since is not None and since.strip():
            query_params["since"] = since.strip()

        encoded_query = urllib_parse.urlencode(query_params)
        response = self._request_json(method="GET", path=f"/api/mirror/clawhub?{encoded_query}")
        if isinstance(response, list):
            return [item for item in response if isinstance(item, dict)]
        if isinstance(response, dict):
            items = response.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return []

    # Compatibility methods to satisfy the broader registry protocol shape used
    # by existing service code until remote CLI selection is introduced in task232.
    def list_entries(self) -> list[dict[str, Any]]:
        return self.list_agents()

    def list_latest_agents(self) -> list[dict[str, Any]]:
        return self.list_agents()

    def search_agents(self, *, query: str) -> list[dict[str, Any]]:
        return self.search(query=query)

    def _effective_tenant(self, tenant: str | None) -> str:
        return tenant.strip() if isinstance(tenant, str) and tenant.strip() else self._tenant_slug

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        body: bytes | None = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        }
        if extra_headers:
            headers.update(extra_headers)

        request = urllib_request.Request(
            url=url,
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with urllib_request.urlopen(request, timeout=self._timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except urllib_error.HTTPError as error:
            response_body = _read_http_error_body(error)
            raise RemoteRegistryClientError(
                _message_for_http_error(error.code, response_body=response_body)
            ) from None
        except urllib_error.URLError as error:
            reason = getattr(error, "reason", None)
            if isinstance(reason, ConnectionRefusedError):
                raise RemoteRegistryClientError(
                    "Remote registry server not reachable (connection refused). "
                    "Verify registry URL and that the server is running."
                ) from None
            raise RemoteRegistryClientError(
                "Remote registry request failed (network error). "
                "Check network connectivity and registry URL."
            ) from None

        if not raw_body.strip():
            return {}

        try:
            decoded = json.loads(raw_body)
        except json.JSONDecodeError:
            raise RemoteRegistryClientError(
                "Remote registry returned invalid JSON response. "
                "Please try again or contact the registry administrator."
            ) from None
        return decoded

    def request_bytes(self, *, path: str) -> bytes:
        """Fetch raw bytes from a remote API path using bearer auth."""
        normalized_path = path.strip()
        if not normalized_path:
            raise ValueError("path must be non-empty")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path

        url = f"{self._base_url}{normalized_path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "User-Agent": _http_user_agent(),
        }

        request = urllib_request.Request(
            url=url,
            headers=headers,
            method="GET",
        )

        try:
            with urllib_request.urlopen(request, timeout=self._timeout_seconds) as response:
                return response.read()
        except urllib_error.HTTPError as error:
            response_body = _read_http_error_body(error)
            raise RemoteRegistryClientError(
                _message_for_http_error(error.code, response_body=response_body)
            ) from None
        except urllib_error.URLError:
            raise RemoteRegistryClientError(
                "Remote registry request failed (network error). "
                "Check network connectivity and registry URL."
            ) from None


def _message_for_http_error(status_code: int, *, response_body: str = "") -> str:
    if status_code == 401:
        message = "Remote registry unauthorized (401). Check your token and sign in again."
        return _append_response_body(message, response_body)
    if status_code == 403:
        message = "Remote registry forbidden (403). Your account lacks required permissions."
        return _append_response_body(message, response_body)
    if status_code == 404:
        message = "Remote registry resource not found (404). Check agent name/version and tenant."
        return _append_response_body(message, response_body)
    if status_code == 409:
        message = "Remote registry conflict (409). This version may already be published."
        return _append_response_body(message, response_body)
    if status_code == 429:
        message = "Remote registry rate limited (429). Retry after a short delay."
        return _append_response_body(message, response_body)
    if status_code >= 500:
        message = "Remote registry server error. Please try again later."
        return _append_response_body(message, response_body)
    return _append_response_body(
        f"Remote registry request failed with HTTP {status_code}.",
        response_body,
    )


def _read_http_error_body(error: urllib_error.HTTPError) -> str:
    try:
        payload = error.read().decode("utf-8", errors="replace").strip()
    except Exception:
        return ""
    return payload


def _append_response_body(message: str, response_body: str) -> str:
    if not response_body:
        return message
    return f"{message} Response: {response_body}"


def _http_user_agent() -> str:
    configured = (os.environ.get("KINNOO_HTTP_USER_AGENT") or "").strip()
    if configured:
        return configured
    return "curl/8.7.1"


def _encode_multipart_form_data(
    *,
    fields: dict[str, str],
    file_field_name: str,
    filename: str,
    file_bytes: bytes,
) -> tuple[bytes, str]:
    """Encode multipart form payload for archive uploads."""

    boundary = f"kinnoo-{uuid.uuid4().hex}"
    content_type = f"multipart/form-data; boundary={boundary}"
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    body_parts: list[bytes] = []
    for key, value in fields.items():
        body_parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    body_parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )

    return b"".join(body_parts), content_type
