from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol


SQL_INJECTION = "SQL_INJECTION"
SHELL_INJECTION = "SHELL_INJECTION"
PATH_TRAVERSAL = "PATH_TRAVERSAL"
SSRF = "SSRF"
XSS = "XSS"
TEMPLATE_INJECTION = "TEMPLATE_INJECTION"


PATTERNS: dict[str, list[tuple[str, str]]] = {
    SQL_INJECTION: [
        (r"\bunion\s+(all\s+)?select\b", "Possible SQL injection: UNION SELECT"),
        (r"\bdrop\s+(table|database)\b", "Possible SQL injection: DROP TABLE/DATABASE"),
        (r"\binsert\s+into\b[\s\S]{0,200}?\bvalues\b", "Possible SQL injection: INSERT INTO ... VALUES"),
        (r"\bdelete\s+from\b", "Possible SQL injection: DELETE FROM"),
        (
            r"['\"`]?\s*(or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
            "Possible SQL injection: tautology condition",
        ),
        (
            r"(?:['\"`][^\n]{0,40}(?:--|#|/\*)|\b(?:select|union|insert|update|delete|drop|where|from|or|and)\b[^\n]{0,40}(?:--|#|/\*))",
            "Possible SQL injection: SQL comment sequence",
        ),
        (r"\bwaitfor\s+delay\b", "Possible SQL injection: WAITFOR DELAY"),
        (r"\bexec\s+xp_\w+\b", "Possible SQL injection: EXEC xp_ stored procedure"),
        (
            r";\s*(select|insert|update|delete|drop)\b",
            "Possible SQL injection: stacked SQL query",
        ),
    ],
    SHELL_INJECTION: [
        (
            r"(?:[;&|]|&&|\|\|)\s*(rm|cat|wget|curl|sudo|sh|bash|python|chmod|chown|nc|ncat|mkfifo|dd|kill)\b",
            "Possible shell injection: command chaining with dangerous command",
        ),
        (r"\$\([^\)]*\)", "Possible shell injection: command substitution $(...)"),
        (r"`[^`]+`", "Possible shell injection: backtick command substitution"),
        (r"\|\s*(/bin/)?(sh|bash)\b", "Possible shell injection: pipe to shell"),
        (
            r">>?\s*/(?:etc|var|proc|dev)/",
            "Possible shell injection: redirecting output to sensitive path",
        ),
        (r"(?:\x00|%00)", "Possible shell injection: null byte sequence"),
    ],
    PATH_TRAVERSAL: [
        (r"(?:\.\./|\.\\)", "Possible path traversal: relative traversal sequence"),
        (
            r"(?:%2e%2e%2f|%2e%2e/|\.\.%2f)",
            "Possible path traversal: URL-encoded traversal sequence",
        ),
        (r"%252e%252e%252f", "Possible path traversal: double-encoded traversal"),
        (
            r"(?:^|/)(?:etc/passwd|etc/shadow|proc/self|dev/)",
            "Possible path traversal: sensitive absolute path",
        ),
    ],
    SSRF: [
        (r"\b(file|gopher|dict|ldap)://", "Possible SSRF: dangerous URL protocol"),
        (r"\b(?:127\.0\.0\.1|0\.0\.0\.0)\b", "Possible SSRF: loopback or wildcard IP"),
        (r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "Possible SSRF: private 10.x.x.x network"),
        (
            r"\b172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}\b",
            "Possible SSRF: private 172.16-31 network",
        ),
        (r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "Possible SSRF: private 192.168.x.x network"),
        (r"(?:\[::1\]|\b::1\b)", "Possible SSRF: IPv6 loopback"),
        (r"\blocalhost\b", "Possible SSRF: localhost hostname"),
        (r"\b0177\.0\.0\.1\b", "Possible SSRF: octal loopback IP representation"),
        (r"\b169\.254\.169\.254\b", "Possible SSRF: cloud metadata endpoint"),
    ],
    XSS: [
        (r"<\s*script\b", "Possible XSS: script tag"),
        (r"javascript:\s*", "Possible XSS: javascript URI"),
        (r"\bon\w+\s*=", "Possible XSS: inline event handler attribute"),
        (r"<\s*(img|iframe|svg|object|embed)\b", "Possible XSS: dangerous HTML tag"),
        (r"data:text/html", "Possible XSS: HTML data URI"),
    ],
    TEMPLATE_INJECTION: [
        (r"\{\{", "Possible template injection: Jinja/Twig opening delimiter"),
        (r"\}\}", "Possible template injection: Jinja/Twig closing delimiter"),
        (r"<%", "Possible template injection: ERB opening delimiter"),
        (r"%>", "Possible template injection: ERB closing delimiter"),
        (r"\$\{[^}]+\}", "Possible template injection: expression language ${...}"),
        (r"#\{[^}]+\}", "Possible template injection: expression language #{...}"),
    ],
}


TYPE_FILTER: dict[str, tuple[str, ...]] = {
    "text": (
        SQL_INJECTION,
        SHELL_INJECTION,
        PATH_TRAVERSAL,
        SSRF,
        XSS,
        TEMPLATE_INJECTION,
    ),
    "string": (
        SQL_INJECTION,
        SHELL_INJECTION,
        PATH_TRAVERSAL,
        SSRF,
        XSS,
        TEMPLATE_INJECTION,
    ),
    "file_path": (PATH_TRAVERSAL, SHELL_INJECTION),
    "url": (SSRF, SHELL_INJECTION),
    "id": (SQL_INJECTION, SHELL_INJECTION, TEMPLATE_INJECTION),
}


@dataclass(frozen=True)
class InputWarning:
    threat_category: str
    description: str
    param_name: str | None = None


@dataclass(frozen=True)
class InputGuardResult:
    safe: bool
    warnings: list[InputWarning]


class InputGuard(Protocol):
    def check(self, value: str, input_type: str = "text") -> InputGuardResult:
        ...

    def check_inputs(self, inputs: list[tuple[str, str, str]]) -> InputGuardResult:
        ...


class RegexInputGuard:
    """Regex-based input guard with category-level warnings."""

    def check(self, value: str, input_type: str = "text") -> InputGuardResult:
        applicable_categories = TYPE_FILTER.get(input_type, TYPE_FILTER["text"])
        warnings: list[InputWarning] = []

        for category in applicable_categories:
            for regex_str, description in PATTERNS.get(category, []):
                if re.search(regex_str, value, re.IGNORECASE):
                    warnings.append(
                        InputWarning(
                            threat_category=category,
                            description=description,
                            param_name=None,
                        )
                    )
                    # A single representative warning per category keeps output readable.
                    break

        return InputGuardResult(safe=len(warnings) == 0, warnings=warnings)

    def check_inputs(self, inputs: list[tuple[str, str, str]]) -> InputGuardResult:
        aggregate_warnings: list[InputWarning] = []
        for param_name, value, input_type in inputs:
            result = self.check(value=value, input_type=input_type)
            for warning in result.warnings:
                aggregate_warnings.append(
                    InputWarning(
                        threat_category=warning.threat_category,
                        description=warning.description,
                        param_name=param_name,
                    )
                )
        return InputGuardResult(safe=len(aggregate_warnings) == 0, warnings=aggregate_warnings)


def get_default_guard() -> InputGuard:
    return RegexInputGuard()
