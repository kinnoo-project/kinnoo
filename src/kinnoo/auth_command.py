"""Authentication command handlers for kinnoo login/logout."""

from __future__ import annotations

import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import socket
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .config import (
    RegistryConfig,
    clear_registry_auth_state,
    load_registry_config,
    save_registry_auth_state,
)


DEFAULT_REGISTRY_URL = "https://registry.kinnoo.ai"
CALLBACK_PATH = "/auth/callback"
CALLBACK_TIMEOUT_SECONDS = 180
TOKEN_REFRESH_SKEW_SECONDS = 120
CALLBACK_SERVER_PORTS = (8765, 8766, 9872, 49527)
HOSTED_LOGIN_SCOPE = "openid profile email"


@dataclass(frozen=True)
class HostedCLIAuthConfig:
    authorization_endpoint: str
    token_endpoint: str
    logout_endpoint: str | None
    userinfo_endpoint: str | None
    client_id: str
    audience: str | None
    issuer_url: str | None
    revocation_endpoint: str | None


def _http_user_agent() -> str:
    configured = (os.environ.get("KINNOO_HTTP_USER_AGENT") or "").strip()
    if configured:
        return configured
    return "curl/8.7.1"


def _env_truthy(name: str) -> bool:
    value = (os.environ.get(name) or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _hosted_cli_config_from_env() -> HostedCLIAuthConfig | None:
    client_id = _auth_env("AUTH_CLI_CLIENT_ID", "KINDE_CLI_CLIENT_ID")
    authorization_endpoint = _auth_env("AUTH_AUTHORIZATION_ENDPOINT", "AUTHORIZATION_ENDPOINT")
    token_endpoint = _auth_env("AUTH_TOKEN_ENDPOINT", "TOKEN_ENDPOINT")
    if not client_id or not authorization_endpoint or not token_endpoint:
        return None

    return HostedCLIAuthConfig(
        authorization_endpoint=authorization_endpoint,
        token_endpoint=token_endpoint,
        logout_endpoint=_auth_env("AUTH_LOGOUT_ENDPOINT", "LOGOUT_ENDPOINT") or None,
        userinfo_endpoint=_auth_env("AUTH_USERINFO_ENDPOINT", "USERINFO_ENDPOINT") or None,
        client_id=client_id,
        audience=_auth_env("AUTH_AUDIENCE", "KINDE_AUDIENCE") or None,
        issuer_url=_auth_env("AUTH_ISSUER_URL", "KINDE_ISSUER_URL") or None,
        revocation_endpoint=_auth_env("AUTH_REVOCATION_ENDPOINT", "REVOCATION_ENDPOINT") or None,
    )


def _payload_value(payload: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _hosted_cli_config_from_registry(*, registry_url: str) -> tuple[HostedCLIAuthConfig | None, str | None]:
    normalized_registry = registry_url.strip().rstrip("/")
    if not normalized_registry:
        return None, "registry URL is empty"

    config_url = f"{normalized_registry}/api/auth/config"
    request = urllib_request.Request(
        url=config_url,
        headers={
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        },
        method="GET",
    )
    try:
        with urllib_request.urlopen(request, timeout=10.0) as response:
            body = response.read().decode("utf-8")
    except urllib_error.HTTPError as error:
        return None, f"HTTP {error.code} from {config_url}"
    except urllib_error.URLError as error:
        reason = getattr(error, "reason", None)
        return None, f"Failed to reach {config_url}. Reason: {reason}"
    except Exception as error:
        return None, f"Unexpected discovery error: {error}"

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None, "auth discovery endpoint returned invalid JSON"
    if not isinstance(payload, dict):
        return None, "auth discovery endpoint returned non-object payload"

    client_id = _payload_value(payload, "cli_client_id", "AUTH_CLI_CLIENT_ID", "KINDE_CLI_CLIENT_ID")
    authorization_endpoint = _payload_value(
        payload,
        "authorization_endpoint",
        "auth_authorization_endpoint",
        "AUTH_AUTHORIZATION_ENDPOINT",
        "AUTHORIZATION_ENDPOINT",
    )
    token_endpoint = _payload_value(
        payload,
        "token_endpoint",
        "auth_token_endpoint",
        "AUTH_TOKEN_ENDPOINT",
        "TOKEN_ENDPOINT",
    )
    if not client_id or not authorization_endpoint or not token_endpoint:
        return None, "auth discovery payload missing required fields (cli_client_id/authorization_endpoint/token_endpoint)"

    return HostedCLIAuthConfig(
        authorization_endpoint=authorization_endpoint,
        token_endpoint=token_endpoint,
        logout_endpoint=_payload_value(
            payload,
            "logout_endpoint",
            "auth_logout_endpoint",
            "AUTH_LOGOUT_ENDPOINT",
            "LOGOUT_ENDPOINT",
        ),
        userinfo_endpoint=_payload_value(
            payload,
            "userinfo_endpoint",
            "auth_userinfo_endpoint",
            "AUTH_USERINFO_ENDPOINT",
            "USERINFO_ENDPOINT",
        ),
        client_id=client_id,
        audience=_payload_value(payload, "audience", "AUTH_AUDIENCE", "KINDE_AUDIENCE"),
        issuer_url=_payload_value(payload, "issuer_url", "AUTH_ISSUER_URL", "KINDE_ISSUER_URL"),
        revocation_endpoint=_payload_value(
            payload,
            "revocation_endpoint",
            "auth_revocation_endpoint",
            "AUTH_REVOCATION_ENDPOINT",
            "REVOCATION_ENDPOINT",
        ),
    ), None


def _auth_env(canonical_name: str, alias_name: str) -> str:
    canonical_value = (os.environ.get(canonical_name) or "").strip()
    if canonical_value:
        return canonical_value
    return (os.environ.get(alias_name) or "").strip()


def login_command(
    *,
    email: str | None,
    password: str | None,
) -> int:
    config = load_registry_config()
    resolved_registry = (config.registry_url or DEFAULT_REGISTRY_URL).strip()
    registry_url_explicitly_set = bool((os.environ.get("KINNOO_REGISTRY_URL") or "").strip())
    allow_legacy_fallback = _env_truthy("KINNOO_LOGIN_ALLOW_LEGACY_FALLBACK")

    hosted_config = _hosted_cli_config_from_env()
    discovery_error: str | None = None
    if hosted_config is None:
        hosted_config, discovery_error = _hosted_cli_config_from_registry(registry_url=resolved_registry)
        if hosted_config is not None:
            print(f"[kinnoo login] Discovered hosted auth config from {resolved_registry}/api/auth/config")
    if hosted_config is not None:
        return _login_hosted_pkce(hosted_config=hosted_config, resolved_registry=resolved_registry)

    if registry_url_explicitly_set and not allow_legacy_fallback:
        print(
            "Error: Hosted auth discovery failed; refusing silent fallback to legacy email/password login.",
            file=sys.stderr,
        )
        if discovery_error:
            print(f"Error: {discovery_error}", file=sys.stderr)
        print(
            "Error: To use legacy login intentionally, set KINNOO_LOGIN_ALLOW_LEGACY_FALLBACK=1.",
            file=sys.stderr,
        )
        return 1

    return _legacy_login_with_password(
        email=email,
        password=password,
        resolved_registry=resolved_registry,
    )


def _legacy_login_with_password(
    *,
    email: str | None,
    password: str | None,
    resolved_registry: str,
) -> int:

    resolved_email = (email or "").strip()
    if not resolved_email:
        resolved_email = input("Email/Username: ").strip()

    resolved_password = password
    if resolved_password is None:
        resolved_password = _prompt_for_password()

    if not resolved_email:
        print("Error: Email is required.")
        return 1
    if not resolved_password:
        print("Error: Password is required.")
        return 1

    token, error_message = _issue_token(
        registry_url=resolved_registry,
        email=resolved_email,
        password=resolved_password,
        tenant_slug=None,
    )
    if error_message is not None:
        print(f"Error: {error_message}")
        return 1

    resolved_tenant = _tenant_slug_from_token(token)
    if not resolved_tenant:
        print(
            "Error: Registry auth response did not include tenant context. "
            "Contact the registry administrator.",
        )
        return 1

    save_registry_auth_state(
        registry_url=resolved_registry,
        registry_token=token,
        tenant_slug=resolved_tenant,
    )

    print("Login successful.")
    print(f"Registry: {resolved_registry}")
    print(f"Tenant: {resolved_tenant}")
    return 0


def _login_hosted_pkce(*, hosted_config: HostedCLIAuthConfig, resolved_registry: str) -> int:
    state = secrets.token_urlsafe(24)
    code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(code_verifier)

    callback_state = _CallbackState()
    server, callback_port = _start_callback_server(state=state, callback_state=callback_state)
    if server is None:
        print("Error: Unable to start local auth callback server.")
        return 1

    redirect_uri = f"http://127.0.0.1:{callback_port}{CALLBACK_PATH}"
    auth_url = _build_authorization_url(
        hosted_config=hosted_config,
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=code_challenge,
    )

    print("Starting hosted login flow...")
    if not webbrowser.open(auth_url):
        print("Open this URL in your browser to continue login:")
        print(auth_url)

    callback_state.event.wait(timeout=CALLBACK_TIMEOUT_SECONDS)
    server.shutdown()
    server.server_close()

    if callback_state.error:
        print(f"Error: {callback_state.error}")
        return 1
    if not callback_state.code:
        print("Error: Login callback timed out. Please run 'kinnoo login' again.")
        return 1

    token_payload, exchange_error = _exchange_authorization_code(
        hosted_config=hosted_config,
        code=callback_state.code,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
    )
    if exchange_error is not None or token_payload is None:
        print(f"Error: {exchange_error or 'Hosted token exchange failed.'}")
        return 1

    access_token = token_payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        print("Error: Hosted auth response did not include access_token.")
        return 1
    refresh_token = token_payload.get("refresh_token")
    resolved_refresh_token = refresh_token.strip() if isinstance(refresh_token, str) else None
    expires_in = token_payload.get("expires_in")
    expires_at_epoch = int(time.time()) + int(expires_in) if isinstance(expires_in, int) else None
    tenant_slug = _resolve_hosted_tenant_slug(
        hosted_config=hosted_config,
        access_token=access_token,
    )

    save_registry_auth_state(
        registry_url=resolved_registry,
        registry_token=access_token.strip(),
        tenant_slug=tenant_slug,
        refresh_token=resolved_refresh_token,
        expires_at_epoch=expires_at_epoch,
        token_endpoint=hosted_config.token_endpoint,
        authorization_endpoint=hosted_config.authorization_endpoint,
        revocation_endpoint=hosted_config.revocation_endpoint,
        logout_endpoint=hosted_config.logout_endpoint,
        oidc_client_id=hosted_config.client_id,
    )

    print("Login successful.")
    print(f"Registry: {resolved_registry}")
    print(f"Tenant: {tenant_slug}")
    return 0


def _resolve_hosted_tenant_slug(*, hosted_config: HostedCLIAuthConfig, access_token: str) -> str:
    # Keep CLI tenant derivation aligned with web UI auth flow:
    # prefer userinfo email -> email-based slug when available.
    from_userinfo = _tenant_slug_from_userinfo(
        hosted_config=hosted_config,
        access_token=access_token,
    )
    if from_userinfo:
        return from_userinfo
    return _tenant_slug_from_token(access_token) or "global"


def _tenant_slug_from_userinfo(*, hosted_config: HostedCLIAuthConfig, access_token: str) -> str | None:
    if not hosted_config.userinfo_endpoint:
        return None

    request = urllib_request.Request(
        url=hosted_config.userinfo_endpoint,
        headers={
            "Authorization": f"Bearer {access_token.strip()}",
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        },
        method="GET",
    )
    try:
        with urllib_request.urlopen(request, timeout=15.0) as response:
            body = response.read().decode("utf-8")
    except Exception:
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    email = payload.get("email")
    if isinstance(email, str) and email.strip():
        return _username_to_tenant_slug(email.strip().lower())

    subject = payload.get("sub")
    if isinstance(subject, str) and subject.strip():
        return _username_to_tenant_slug(f"{subject.strip()}@kinde.local")
    return None


def _build_authorization_url(
    *,
    hosted_config: HostedCLIAuthConfig,
    redirect_uri: str,
    state: str,
    code_challenge: str,
) -> str:
    params = {
        "response_type": "code",
        "client_id": hosted_config.client_id,
        "redirect_uri": redirect_uri,
        "scope": HOSTED_LOGIN_SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if hosted_config.audience:
        params["audience"] = hosted_config.audience
    return hosted_config.authorization_endpoint + "?" + urllib_parse.urlencode(params)


def _exchange_authorization_code(
    *,
    hosted_config: HostedCLIAuthConfig,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> tuple[dict[str, object] | None, str | None]:
    payload = urllib_parse.urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": hosted_config.client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
    ).encode("utf-8")
    request = urllib_request.Request(
        url=hosted_config.token_endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=20.0) as response:
            body = response.read().decode("utf-8")
    except urllib_error.HTTPError as error:
        return None, _extract_error_message(_read_http_error_payload(error)) or f"HTTP {error.code} during token exchange."
    except urllib_error.URLError as error:
        reason = getattr(error, "reason", None)
        return None, f"Failed to reach hosted token endpoint. Reason: {reason}"

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None, "Hosted token endpoint returned invalid JSON."
    if not isinstance(parsed, dict):
        return None, "Hosted token endpoint returned invalid payload."
    return parsed, None


class _CallbackState:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.code: str | None = None
        self.error: str | None = None


def _start_callback_server(*, state: str, callback_state: _CallbackState) -> tuple[ThreadingHTTPServer | None, int]:
    handler = _make_callback_handler(expected_state=state, callback_state=callback_state)
    for port in CALLBACK_SERVER_PORTS:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            return server, int(server.server_address[1])
        except OSError:
            continue
    return None, -1


def _make_callback_handler(*, expected_state: str, callback_state: _CallbackState) -> type[BaseHTTPRequestHandler]:
    class _CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib_parse.urlparse(self.path)
            if parsed.path != CALLBACK_PATH:
                self.send_response(404)
                self.end_headers()
                return

            query = urllib_parse.parse_qs(parsed.query)
            state = (query.get("state") or [""])[0]
            code = (query.get("code") or [""])[0]
            error = (query.get("error") or [""])[0]
            if error:
                callback_state.error = f"authorization failed: {error}"
            elif not state or state != expected_state:
                callback_state.error = "state validation failed"
            elif not code:
                callback_state.error = "callback did not include authorization code"
            else:
                callback_state.code = code

            callback_state.event.set()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h3>Login complete.</h3><p>You can close this tab.</p></body></html>"
            )

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            del format, args

    return _CallbackHandler


def _prompt_for_password() -> str:
    try:
        if sys.stdin.isatty():
            return getpass.getpass("Password: ")
    except Exception:
        pass
    return input("Password: ")


def _tenant_slug_from_token(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_segment = parts[1]
        padding = "=" * ((4 - len(payload_segment) % 4) % 4)
        decoded = base64.urlsafe_b64decode((payload_segment + padding).encode("utf-8"))
        payload = json.loads(decoded.decode("utf-8"))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    email = payload.get("email")
    if isinstance(email, str) and email.strip():
        return _username_to_tenant_slug(email)

    tenant_slug = payload.get("tenant_slug")
    if isinstance(tenant_slug, str) and tenant_slug.strip():
        return tenant_slug.strip()

    org_code = payload.get("org_code")
    if isinstance(org_code, str) and org_code.strip():
        return org_code.strip()
    return None


def _username_to_tenant_slug(username: str) -> str:
    raw = username.strip().lower()
    if "@" in raw:
        raw = raw.split("@", 1)[0]

    slug = re.sub(r"[^a-z0-9-]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "default"


def _generate_code_verifier() -> str:
    raw = secrets.token_urlsafe(72)
    return raw[:96]


def _generate_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def logout_command() -> int:
    config = load_registry_config()
    _attempt_token_revocation(config)
    removed = clear_registry_auth_state()
    if removed:
        print("Logout successful. Cleared stored registry auth state.")
    else:
        print("No stored registry auth state found.")
    return 0


def _attempt_token_revocation(config: RegistryConfig) -> None:
    if not config.revocation_endpoint or not config.refresh_token:
        return
    payload = urllib_parse.urlencode(
        {
            "token": config.refresh_token,
            "client_id": config.oidc_client_id or "",
        }
    ).encode("utf-8")
    request = urllib_request.Request(
        url=config.revocation_endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": _http_user_agent(),
        },
        method="POST",
    )
    try:
        urllib_request.urlopen(request, timeout=8.0).read()
    except Exception:
        return


def refresh_registry_auth_if_needed(*, config: RegistryConfig | None = None) -> tuple[RegistryConfig, str | None]:
    resolved = config or load_registry_config()
    if not resolved.registry_token:
        return resolved, None
    if not resolved.expires_at_epoch:
        return resolved, None

    now = int(time.time())
    if resolved.expires_at_epoch - now > TOKEN_REFRESH_SKEW_SECONDS:
        return resolved, None

    if not resolved.refresh_token or not resolved.token_endpoint or not resolved.oidc_client_id:
        return resolved, (
            "Access token is near expiry and cannot be refreshed automatically. "
            "Run 'kinnoo login' to re-authenticate."
        )

    payload = urllib_parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": resolved.refresh_token,
            "client_id": resolved.oidc_client_id,
        }
    ).encode("utf-8")
    request = urllib_request.Request(
        url=resolved.token_endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=15.0) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as error:
        message = _extract_error_message(_read_http_error_payload(error)) or "token refresh failed"
        return resolved, f"Token refresh failed: {message}. Run 'kinnoo login'."
    except urllib_error.URLError as error:
        return resolved, f"Token refresh network failure: {getattr(error, 'reason', 'unknown')}. Run 'kinnoo login'."

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return resolved, "Token refresh returned invalid JSON. Run 'kinnoo login'."
    if not isinstance(parsed, dict):
        return resolved, "Token refresh returned invalid payload. Run 'kinnoo login'."

    access_token = parsed.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        return resolved, "Token refresh response missing access_token. Run 'kinnoo login'."

    refreshed_refresh = parsed.get("refresh_token")
    expires_in = parsed.get("expires_in")
    expires_at_epoch = int(time.time()) + int(expires_in) if isinstance(expires_in, int) else None
    refreshed_tenant = _tenant_slug_from_token(access_token) or (resolved.tenant_slug or "global")

    save_registry_auth_state(
        registry_url=resolved.registry_url or DEFAULT_REGISTRY_URL,
        registry_token=access_token.strip(),
        tenant_slug=refreshed_tenant,
        refresh_token=(
            refreshed_refresh.strip()
            if isinstance(refreshed_refresh, str) and refreshed_refresh.strip()
            else resolved.refresh_token
        ),
        expires_at_epoch=expires_at_epoch,
        token_endpoint=resolved.token_endpoint,
        authorization_endpoint=resolved.authorization_endpoint,
        revocation_endpoint=resolved.revocation_endpoint,
        logout_endpoint=resolved.logout_endpoint,
        oidc_client_id=resolved.oidc_client_id,
    )
    return load_registry_config(), None


def _issue_token(
    *,
    registry_url: str,
    email: str,
    password: str,
    tenant_slug: str | None,
) -> tuple[str, str | None]:
    payload_data: dict[str, str] = {
        "username": email,
        "password": password,
    }
    if isinstance(tenant_slug, str) and tenant_slug.strip():
        payload_data["tenant_slug"] = tenant_slug.strip()

    payload = json.dumps(payload_data).encode("utf-8")

    token_url = f"{registry_url.rstrip('/')}/api/auth/token"
    request = urllib_request.Request(
        url=token_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _http_user_agent(),
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=15.0) as response:
            body = response.read().decode("utf-8")
    except urllib_error.HTTPError as error:
        message = _extract_error_message(_read_http_error_payload(error))
        if not message:
            message = f"Token request failed with HTTP {error.code}."
        return "", message
    except urllib_error.URLError as error:
        reason = getattr(error, "reason", None)
        reason_text = str(reason) if reason is not None else "unknown network error"
        return "", f"Failed to reach registry auth endpoint. Reason: {reason_text}"

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError:
        return "", "Registry auth endpoint returned invalid JSON."

    if not isinstance(decoded, dict):
        return "", "Registry auth endpoint returned invalid response payload."

    token = decoded.get("access_token")
    if not isinstance(token, str) or not token.strip():
        return "", "Registry auth response did not include access_token."

    return token.strip(), None


def _read_http_error_payload(error: urllib_error.HTTPError) -> dict[str, object] | None:
    try:
        body = error.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _extract_error_message(payload: dict[str, object] | None) -> str:
    if payload is None:
        return ""

    error_value = payload.get("error")
    if isinstance(error_value, str):
        return error_value
    if isinstance(error_value, dict):
        nested = error_value.get("message")
        if isinstance(nested, str):
            return nested

    message_value = payload.get("message")
    if isinstance(message_value, str):
        return message_value

    detail_value = payload.get("detail")
    if isinstance(detail_value, str):
        return detail_value

    title_value = payload.get("title")
    if isinstance(title_value, str):
        return title_value

    owner_action = payload.get("what_you_should_do")
    if isinstance(owner_action, str):
        return owner_action

    return ""
