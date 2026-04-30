from __future__ import annotations

import os
from io import StringIO

from kinnoo.terminal_colors import (
    colorize_cli_line_prefixes,
    install_cli_line_prefix_colorization,
)


def test_colorize_cli_line_prefixes_kinnoo_prefix() -> None:
    line = "[kinnoo install] Archive checksum verified."
    colored = colorize_cli_line_prefixes(line)
    assert "[kinnoo install]\x1b[0m" in colored
    assert ("\x1b[38;2;255;127;0m" in colored) or ("\x1b[38;5;208m" in colored)
    assert "Archive checksum verified." in colored


def test_colorize_cli_line_prefixes_status_keywords() -> None:
    error_colored = colorize_cli_line_prefixes("Error: install failed")
    warning_colored = colorize_cli_line_prefixes("warning: verification skipped")
    success_colored = colorize_cli_line_prefixes("Success: done")

    assert error_colored.endswith(" install failed")
    assert warning_colored.endswith(" verification skipped")
    assert success_colored.endswith(" done")
    assert (error_colored.startswith("\x1b[38;2;239;68;68mError:\x1b[0m") or error_colored.startswith("\x1b[38;5;203mError:\x1b[0m"))
    assert (warning_colored.startswith("\x1b[38;2;245;158;11mwarning:\x1b[0m") or warning_colored.startswith("\x1b[38;5;214mwarning:\x1b[0m"))
    assert (success_colored.startswith("\x1b[38;2;16;185;129mSuccess:\x1b[0m") or success_colored.startswith("\x1b[38;5;35mSuccess:\x1b[0m"))


def test_install_cli_line_prefix_colorization_disabled_for_non_tty() -> None:
    stdout = StringIO()
    stderr = StringIO()

    wrapped_stdout, wrapped_stderr = install_cli_line_prefix_colorization(stdout=stdout, stderr=stderr)

    assert wrapped_stdout is stdout
    assert wrapped_stderr is stderr


def test_install_cli_line_prefix_colorization_honors_no_color(monkeypatch) -> None:
    class _TTYStringIO(StringIO):
        def isatty(self) -> bool:  # noqa: D401
            return True

    monkeypatch.setenv("NO_COLOR", "1")
    stdout = _TTYStringIO()
    stderr = _TTYStringIO()

    wrapped_stdout, wrapped_stderr = install_cli_line_prefix_colorization(stdout=stdout, stderr=stderr)

    assert wrapped_stdout is stdout
    assert wrapped_stderr is stderr


def test_install_cli_line_prefix_colorization_wraps_tty(monkeypatch) -> None:
    class _TTYStringIO(StringIO):
        def isatty(self) -> bool:  # noqa: D401
            return True

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")

    stdout = _TTYStringIO()
    stderr = _TTYStringIO()

    wrapped_stdout, wrapped_stderr = install_cli_line_prefix_colorization(stdout=stdout, stderr=stderr)

    wrapped_stdout.write("[kinnoo] message\n")
    wrapped_stdout.flush()
    wrapped_stderr.write("Error: boom\n")
    wrapped_stderr.flush()

    stdout_value = stdout.getvalue()
    stderr_value = stderr.getvalue()

    assert "[kinnoo]\x1b[0m message" in stdout_value
    assert ("\x1b[38;2;255;127;0m" in stdout_value) or ("\x1b[38;5;208m" in stdout_value)
    assert "Error:\x1b[0m boom" in stderr_value
    assert ("\x1b[38;2;239;68;68m" in stderr_value) or ("\x1b[38;5;203m" in stderr_value)

    monkeypatch.delenv("TERM", raising=False)
    if "NO_COLOR" in os.environ:
        monkeypatch.delenv("NO_COLOR", raising=False)
