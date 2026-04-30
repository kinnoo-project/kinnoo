from __future__ import annotations

import os
import re
import sys
from typing import TextIO

_RESET = "\033[0m"
_COLOR_CODES = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    # These shades intentionally mirror argparse's default help palette seen in
    # `kinnoo inspect -h` so top-level help appears consistent.
    "purple": "\033[34m",
    "pink": "\033[35m",
    "light_blue": "\033[36m",
    "neon_green": "\033[32m",
}
_BOLD = "\033[1m"

# Easy rollback switch: set to False to disable CLI line-prefix coloring globally.
ENABLE_CLI_OUTPUT_COLOR = True

_KINNOO_RGB = (255, 127, 0)   # #FF7F00
_ERROR_RGB = (239, 68, 68)    # #EF4444
_WARNING_RGB = (245, 158, 11) # #F59E0B
_SUCCESS_RGB = (16, 185, 129) # #10B981

_KINNOO_256 = 208
_ERROR_256 = 203
_WARNING_256 = 214
_SUCCESS_256 = 35


def _rgb_escape(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _ansi_256_escape(code: int) -> str:
    return f"\033[38;5;{code}m"


def _supports_truecolor() -> bool:
    color_term = (os.getenv("COLORTERM") or "").strip().lower()
    return color_term in {"truecolor", "24bit"}


def _named_color_escape(*, rgb: tuple[int, int, int], ansi_256_code: int) -> str:
    if _supports_truecolor():
        return _rgb_escape(*rgb)
    return _ansi_256_escape(ansi_256_code)


def _colorize_kinnoo_prefix(line: str) -> str:
    match = re.match(r"^(\[kinnoo(?: [^\]]+)?\])", line)
    if not match:
        return line
    prefix = match.group(1)
    colored_prefix = _named_color_escape(rgb=_KINNOO_RGB, ansi_256_code=_KINNOO_256) + prefix + _RESET
    return colored_prefix + line[len(prefix):]


def _colorize_first_word_status(line: str) -> str:
    match = re.match(r"^((?:error|warning|success):)", line, flags=re.IGNORECASE)
    if not match:
        return line

    token = match.group(1)
    normalized = token.lower()
    if normalized.startswith("error"):
        color = _named_color_escape(rgb=_ERROR_RGB, ansi_256_code=_ERROR_256)
    elif normalized.startswith("warning"):
        color = _named_color_escape(rgb=_WARNING_RGB, ansi_256_code=_WARNING_256)
    else:
        color = _named_color_escape(rgb=_SUCCESS_RGB, ansi_256_code=_SUCCESS_256)
    return color + token + _RESET + line[len(token):]


def colorize_cli_line_prefixes(line: str) -> str:
    colored = _colorize_kinnoo_prefix(line)
    colored = _colorize_first_word_status(colored)
    return colored


class _LinePrefixColorizingStream:
    def __init__(self, wrapped: TextIO) -> None:
        self._wrapped = wrapped
        self._buffer = ""

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            text = str(text)

        self._buffer += text
        emitted = ""
        while True:
            newline_index = self._buffer.find("\n")
            if newline_index == -1:
                break
            raw_line = self._buffer[: newline_index + 1]
            self._buffer = self._buffer[newline_index + 1 :]
            line_body = raw_line[:-1]
            emitted += colorize_cli_line_prefixes(line_body) + "\n"

        if emitted:
            self._wrapped.write(emitted)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self._wrapped.write(colorize_cli_line_prefixes(self._buffer))
            self._buffer = ""
        self._wrapped.flush()

    def isatty(self) -> bool:
        return bool(getattr(self._wrapped, "isatty", lambda: False)())

    def __getattr__(self, name: str):
        return getattr(self._wrapped, name)


def install_cli_line_prefix_colorization(*, stdout: TextIO, stderr: TextIO) -> tuple[TextIO, TextIO]:
    if not ENABLE_CLI_OUTPUT_COLOR:
        return stdout, stderr

    wrapped_stdout: TextIO = stdout
    wrapped_stderr: TextIO = stderr

    if color_enabled(stream=stdout):
        wrapped_stdout = _LinePrefixColorizingStream(stdout)
    if color_enabled(stream=stderr):
        wrapped_stderr = _LinePrefixColorizingStream(stderr)

    return wrapped_stdout, wrapped_stderr


def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def color_enabled(stream: TextIO | None = None) -> bool:
    if os.getenv("NO_COLOR") is not None:
        return False
    if os.getenv("TERM", "").strip().lower() == "dumb":
        return False
    if _env_truthy("KINNOO_FORCE_COLOR"):
        return True

    active_stream = stream or sys.stdout
    if not hasattr(active_stream, "isatty"):
        return False
    return bool(active_stream.isatty())


def style_text(text: str, *, color: str | None = None, bold: bool = False, stream: TextIO | None = None) -> str:
    if not color_enabled(stream=stream):
        return text

    segments: list[str] = []
    if bold:
        segments.append(_BOLD)
    if color in _COLOR_CODES:
        segments.append(_COLOR_CODES[color])

    if not segments:
        return text
    return "".join(segments) + text + _RESET


def status_color(status: str) -> str:
    normalized = status.strip().upper()
    if normalized == "PASS":
        return "green"
    if normalized == "FAIL":
        return "red"
    if normalized == "WARN":
        return "yellow"
    return "cyan"
