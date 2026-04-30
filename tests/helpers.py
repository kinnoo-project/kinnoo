from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "src" / "kinnoo" / "cli.py"

CLI_COMMANDS: tuple[str, ...] = (
    "init",
    "run",
    "test",
    "install",
    "pack",
    "diff",
    "fetch",
    "uninstall",
    "keygen",
    "inspect",
    "publish",
    "list",
    "search",
    "login",
    "logout",
    "import",
    "check",
)


def cli_base_cmd() -> list[str]:
    return [sys.executable, str(CLI_PATH)]


def _to_argv(args: Iterable[object]) -> list[str]:
    return [str(arg) for arg in args]


def assert_known_command(command: str) -> None:
    if command not in CLI_COMMANDS:
        raise ValueError(f"Unknown kinnoo command: {command}")


def cli_cmd(*args: object) -> list[str]:
    return cli_base_cmd() + _to_argv(args)


def command_cmd(command: str, *args: object) -> list[str]:
    assert_known_command(command)
    return cli_cmd(command, *args)


def run_cli(
    args: Sequence[object],
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cli_cmd(*args),
        cwd=cwd,
        env=env,
        input=input_text,
        timeout=timeout,
        capture_output=True,
        text=True,
    )


def run_command(
    command: str,
    *args: object,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return run_cli([command, *args], cwd=cwd, env=env, input_text=input_text, timeout=timeout)


def command_exists(command: str) -> bool:
    result = run_command(command, "-h")
    return result.returncode == 0


# Per-command helpers (argv)
def init_cmd(*args: object) -> list[str]:
    return command_cmd("init", *args)


def run_cmd(*args: object) -> list[str]:
    return command_cmd("run", *args)


def test_cmd(*args: object) -> list[str]:
    return command_cmd("test", *args)


def install_cmd(*args: object) -> list[str]:
    return command_cmd("install", *args)


def pack_cmd(*args: object) -> list[str]:
    return command_cmd("pack", *args)


def diff_cmd(*args: object) -> list[str]:
    return command_cmd("diff", *args)


def fetch_cmd(*args: object) -> list[str]:
    return command_cmd("fetch", *args)


def uninstall_cmd(*args: object) -> list[str]:
    return command_cmd("uninstall", *args)


def keygen_cmd(*args: object) -> list[str]:
    return command_cmd("keygen", *args)


def inspect_cmd(*args: object) -> list[str]:
    return command_cmd("inspect", *args)


def publish_cmd(*args: object) -> list[str]:
    return command_cmd("publish", *args)


def list_cmd(*args: object) -> list[str]:
    return command_cmd("list", *args)


def search_cmd(*args: object) -> list[str]:
    return command_cmd("search", *args)


def login_cmd(*args: object) -> list[str]:
    return command_cmd("login", *args)


def logout_cmd(*args: object) -> list[str]:
    return command_cmd("logout", *args)


def import_cmd(*args: object) -> list[str]:
    return command_cmd("import", *args)


def check_cmd(*args: object) -> list[str]:
    return command_cmd("check", *args)


# Per-command helpers (execution)
def run_init(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("init", *args, **kwargs)


def run_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("run", *args, **kwargs)


def run_test(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("test", *args, **kwargs)


def run_install(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("install", *args, **kwargs)


def run_pack(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("pack", *args, **kwargs)


def run_diff(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("diff", *args, **kwargs)


def run_fetch(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("fetch", *args, **kwargs)


def run_uninstall(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("uninstall", *args, **kwargs)


def run_keygen(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("keygen", *args, **kwargs)


def run_inspect(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("inspect", *args, **kwargs)


def run_publish(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("publish", *args, **kwargs)


def run_list(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("list", *args, **kwargs)


def run_search(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("search", *args, **kwargs)


def run_login(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("login", *args, **kwargs)


def run_logout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("logout", *args, **kwargs)


def run_import(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("import", *args, **kwargs)


def run_check(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return run_command("check", *args, **kwargs)
