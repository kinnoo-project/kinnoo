"""
CLI entry point for kinnoo.
Handles argument parsing and dispatches subcommands.
"""

import argparse
import contextlib
import io
import json
import subprocess
import sys
import re
from pathlib import Path


# Ensure direct script execution (`python src/kinnoo/cli.py ...`) imports this
# workspace's modules before any globally installed/shadowed `kinnoo` package.
_LOCAL_SRC_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_SRC_ROOT_STR = str(_LOCAL_SRC_ROOT)
if _LOCAL_SRC_ROOT_STR in sys.path:
    sys.path.remove(_LOCAL_SRC_ROOT_STR)
sys.path.insert(0, _LOCAL_SRC_ROOT_STR)

try:
    from kinnoo.schema import NAME_PATTERN
    from kinnoo import __version__ as KINNOO_VERSION
    from kinnoo.remote_client import RemoteRegistryClientError
    from kinnoo.terminal_colors import style_text, install_cli_line_prefix_colorization
except ImportError:
    # fallback for direct script execution
    from .schema import NAME_PATTERN
    from . import __version__ as KINNOO_VERSION
    from .remote_client import RemoteRegistryClientError
    from .terminal_colors import style_text, install_cli_line_prefix_colorization


RUN_USAGE_TEXT = (
    "Usage: kinnoo run <agent-dir> '<input>'\n"
    "       kinnoo run <agent-dir>\n"
    "       kinnoo run <agent-dir> --entrypoint <script> '<input>'\n"
    "       kinnoo run <agent-dir> '<input>' --json\n"
    "       kinnoo run <agent-dir> --json-input '<json>'\n"
    "       kinnoo run <agent-dir> --json-file <json-file>\n"
    "       kinnoo run <agent-dir> -- <args...>"
)

IMPORT_USAGE_TEXT = "Usage: kinnoo import [path]"


def _emit_bridge_path_deprecation_warning(*, path: str, replacement: str) -> None:
    print(
        "[kinnoo deprecation] category=openclaw_bridge_path_deprecated "
        f"path={path} replacement={replacement} "
        "message=legacy bridge path remains supported for compatibility but is deprecated",
        file=sys.stderr,
    )


def _resolve_short_commit_hash() -> str:
    """Resolve short git commit hash for CLI branding; fail closed to 'unknown'."""
    repo_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"

    commit_hash = result.stdout.strip()
    if not commit_hash:
        return "unknown"
    return commit_hash


def _print_remote_registry_error(error: RemoteRegistryClientError) -> None:
    """Render remote registry failures as concise CLI-facing lines on stdout."""
    raw_message = str(error).strip()
    if not raw_message:
        print("[kinnoo] ERROR: Remote registry request failed.")
        return

    response_marker = " Response: "
    if response_marker in raw_message:
        headline, response_payload = raw_message.split(response_marker, 1)
        print(f"[kinnoo] ERROR: {headline.strip()}")
        if response_payload.strip():
            print(f"[kinnoo] Response: {response_payload.strip()}")
        return

    print(f"[kinnoo] ERROR: {raw_message}")


def _format_top_level_help_text() -> str:
    commit_hash = _resolve_short_commit_hash()
    title = style_text(
        f"🍊 Kinnoo CLI v{KINNOO_VERSION} ({commit_hash})",
        color="cyan",
        bold=True,
        stream=sys.stdout,
    )
    usage_label = style_text("usage:", color="purple", bold=True, stream=sys.stdout)
    usage_kinnoo = style_text("kinnoo", color="pink", bold=True, stream=sys.stdout)
    usage_help = style_text("-h", color="neon_green", stream=sys.stdout)
    usage_version = style_text("--version", color="light_blue", bold=True, stream=sys.stdout)
    usage_commands = style_text(
        "{init,run,test,install,pack,keygen,inspect,publish,list,search,fetch,uninstall,login,logout,import,check}",
        color="neon_green",
        bold=True,
        stream=sys.stdout,
    )

    positional_header = style_text("positional arguments:", color="purple", bold=True, stream=sys.stdout)
    all_agents_header = style_text("all agents:", color="purple", bold=True, stream=sys.stdout)
    # [agent] daemon help section intentionally disabled for task476; commands will return later.
    daemon_header = style_text("daemon agents:", color="purple", bold=True, stream=sys.stdout)
    registry_header = style_text("registry:", color="purple", bold=True, stream=sys.stdout)
    other_header = style_text("other:", color="purple", bold=True, stream=sys.stdout)
    options_header = style_text("options:", color="purple", bold=True, stream=sys.stdout)

    all_agents_set = style_text("{init,run,test,install,pack,inspect, import,check}", color="neon_green", bold=True, stream=sys.stdout)
    daemon_set = style_text("{stop,attach,logs}", color="neon_green", bold=True, stream=sys.stdout)
    registry_set = style_text("{publish,install,list,search,fetch,uninstall,login,logout}", color="neon_green", bold=True, stream=sys.stdout)
    other_set = style_text("{keygen}", color="neon_green", bold=True, stream=sys.stdout)

    init_cmd = style_text("init", color="neon_green", bold=True, stream=sys.stdout)
    run_cmd = style_text("run", color="neon_green", bold=True, stream=sys.stdout)
    test_cmd = style_text("test", color="neon_green", bold=True, stream=sys.stdout)
    pack_cmd = style_text("pack", color="neon_green", bold=True, stream=sys.stdout)
    inspect_cmd = style_text("inspect", color="neon_green", bold=True, stream=sys.stdout)
    import_cmd = style_text("import", color="neon_green", bold=True, stream=sys.stdout)
    check_cmd = style_text("check", color="neon_green", bold=True, stream=sys.stdout)
    stop_cmd = style_text("stop", color="neon_green", bold=True, stream=sys.stdout)
    attach_cmd = style_text("attach", color="neon_green", bold=True, stream=sys.stdout)
    logs_cmd = style_text("logs", color="neon_green", bold=True, stream=sys.stdout)
    publish_cmd = style_text("publish", color="neon_green", bold=True, stream=sys.stdout)
    install_cmd = style_text("install", color="neon_green", bold=True, stream=sys.stdout)
    list_cmd = style_text("list", color="neon_green", bold=True, stream=sys.stdout)
    search_cmd = style_text("search", color="neon_green", bold=True, stream=sys.stdout)
    fetch_cmd = style_text("fetch", color="neon_green", bold=True, stream=sys.stdout)
    uninstall_cmd = style_text("uninstall", color="neon_green", bold=True, stream=sys.stdout)
    sync_cmd = style_text("sync", color="neon_green", bold=True, stream=sys.stdout)
    login_cmd = style_text("login", color="neon_green", bold=True, stream=sys.stdout)
    logout_cmd = style_text("logout", color="neon_green", bold=True, stream=sys.stdout)
    keygen_cmd = style_text("keygen", color="neon_green", bold=True, stream=sys.stdout)

    opt_help = style_text("--help", color="light_blue", bold=True, stream=sys.stdout)
    opt_version = style_text("--version", color="light_blue", bold=True, stream=sys.stdout)

    return (
        f"{title}\n\n"
        f"{usage_label} {usage_kinnoo} [{usage_help}] [{opt_version}] {usage_commands} ...\n\n"
        f"{positional_header}\n"
        f"{all_agents_header}\n"
        f"    {all_agents_set}\n"
        f"        {init_cmd}                Scaffold a new kinnoo agent\n"
        f"        {run_cmd}                 Run a kinnoo agent\n"
        f"        {test_cmd}                Execute standardized declarative tests for an agent\n"
        f"        {pack_cmd}                Package an agent directory into a .kno archive\n"
        f"        {inspect_cmd}             Inspect metadata from an agent directory or .kno archive\n"
        f"        {import_cmd}              Import an existing agent project in-place and prepare kinnoo metadata\n"
        f"        {check_cmd}               Run combined import/inspect/preflight compatibility checks\n\n"
        # [agent] daemon agents section intentionally commented out for task476.
        f"{registry_header}\n"
        f"    {registry_set}\n"
        f"        {publish_cmd}             Publish latest archived agent artifact to the registry\n"
        f"        {install_cmd}             Install a kinnoo agent from archive (.kno) or registry\n"
        f"        {list_cmd}                List agents from remote registry (default if configured) or local archive\n"
        f"        {search_cmd}              Search agents from remote registry (default if configured) or local archive\n"
        f"        {fetch_cmd}               Download an agent archive from registry into local archive storage\n"
        f"        {uninstall_cmd}           Remove installed agent directory and/or archived versions\n"
        # [agent] sync command help intentionally commented out for task476.
        f"        {login_cmd}               Authenticate to a registry and persist auth state locally\n"
        f"        {logout_cmd}              Clear persisted registry auth state\n\n"
        f"{other_header}\n"
        f"    {other_set}\n"
        f"        {keygen_cmd}              Generate an Ed25519 keypair for archive signing\n\n"
        f"{options_header}\n"
        f"    -h, {opt_help}            show this help message and exit\n"
        f"    {opt_version}             show program's version number and exit\n"
    )


def _print_top_level_help() -> None:
    print(_format_top_level_help_text())


def _orange_description(text: str) -> str:
    return text if text.startswith("🍊 ") else f"🍊 {text}"


class KinnooArgumentParser(argparse.ArgumentParser):
    """ArgumentParser variant that prints description before usage in help output."""

    def format_help(self) -> str:
        formatter = self._get_formatter()

        if self.description:
            formatter.add_text(self.description)

        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        formatter.add_text(self.epilog)
        return formatter.format_help()

def main():
    sys.stdout, sys.stderr = install_cli_line_prefix_colorization(
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if len(sys.argv) == 2 and sys.argv[1] in {"-h", "--help"}:
        _print_top_level_help()
        sys.exit(0)

    parser = KinnooArgumentParser(
        prog="kinnoo",
        description="Kinnoo CLI",
        # [agent] daemon command epilog intentionally disabled for task476.
        epilog=None,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=KINNOO_VERSION)
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=KinnooArgumentParser,
    )

    # init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Scaffold a new kinnoo agent",
        formatter_class=argparse.RawTextHelpFormatter,
        description="🍊 Scaffold a new kinnoo agent",
        epilog=(
            "Examples:\n"
            "  kinnoo init chatgpt my-agent\n"
            "  kinnoo init no-framework --language python my-bare-agent\n"
            "  kinnoo init openclaw --language typescript my-openclaw-agent\n"
            "  kinnoo init mcp-client my-mcp-client"
        ),
    )
    init_parser.add_argument(
        "framework",
        nargs="?",
        help=(
            "Framework template. Currently supported:\n"
            "  gemini         - Google Gemini API agent\n"
            "  chatgpt        - OpenAI ChatGPT API agent\n"
            "  claude-chat    - Anthropic Claude API agent\n"
            "  pydantic-ai    - PydanticAI structured agent with tools\n"
            "  langgraph      - LangGraph state machine agent\n"
            "  openai-agents  - OpenAI Agents SDK with handoffs\n"
            "  mcp-client     - Model Context Protocol client\n"
            "  mcp-server     - Model Context Protocol server\n"
            "  openclaw       - OpenClaw Node.js daemon agent\n"
            "  no-framework   - Barebones agent template - language should be specified (default: python)"
        ),
    )
    init_parser.add_argument("agent_name", nargs="?", help="Name of the agent to create")
    init_parser.add_argument(
        "--language",
        metavar="LANGUAGE",
        help="(Optional) Scaffold language (if supported for the specified framework): python, javascript, typescript",
    )
    init_parser.add_argument(
        "--minimal",
        action="store_true",
        help="Create minimal scaffold only (no tools/prompts/evals/tests/data extras).",
    )

    # Add 'run' subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Run a kinnoo agent",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Run a kinnoo agent"),
        epilog=(
            "Examples:\n"
            "  kinnoo run <agent-dir> '<input>'\n"
            "  kinnoo run <agent-dir>\n"
            "  kinnoo run <agent-dir> --entrypoint scripts/src/main.py '<input>'\n"
            "  kinnoo run <agent-dir> --json-input '{\"task\":\"ping\"}'\n"
            "  kinnoo run <agent-dir> --json-file ./payload.json\n"
            "  kinnoo run <agent-dir> -- -e <some-string> -p <some-file-path> -u <some-url>"
        ),
    )
    run_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory")
    run_parser.add_argument(
        "input",
        nargs="?",
        help=(
            "Optional input string to pass to the agent entrypoint. "
            "May be omitted for agents that accept no input, and is not required when --json-input or --json-file is used."
        ),
    )
    run_parser.add_argument(
        "--entrypoint",
        dest="entrypoint",
        help=(
            "Override manifest default entrypoint selection. Must match manifest entrypoint "
            "or one of manifest entrypoints values."
        ),
    )
    run_parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run readiness checks only; do not execute the agent entrypoint",
    )
    run_parser.add_argument(
        "--no-guard",
        action="store_true",
        help="Disable input safety check for CI/automation pipelines",
    )
    run_parser.add_argument(
        "--json-input",
        dest="json_input",
        help="Inline JSON payload for agents expecting structured input",
    )
    run_parser.add_argument(
        "--json-file",
        dest="json_file",
        help="Path to a JSON file payload for agents expecting structured input",
    )
    run_parser.add_argument(
        "--enforce-policy",
        dest="enforce_policy",
        action="store_true",
        help="Enforce manifest-declared runtime permission policy checks",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show predicted runtime behavior without executing full entrypoint side effects",
    )
    run_parser.add_argument(
        "--experimental-openclaw-adapter",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output (OpenClaw passthrough; non-OpenClaw structured envelope)",
    )
    run_parser.add_argument(
        "--max-seconds",
        type=float,
        help=(
            "Wall-clock timeout in seconds for run execution. "
            "If omitted, no wall-clock timeout is enforced by this option."
        ),
    )
    run_parser.add_argument(
        "--max-cpu-seconds",
        type=int,
        help=(
            "CPU time budget in seconds for supported platforms. "
            "If omitted, no CPU-time budget is enforced by this option."
        ),
    )
    run_parser.add_argument(
        "--max-memory-mb",
        type=int,
        help=(
            "Memory budget in MB for supported platforms. "
            "If omitted, no memory budget is enforced by this option."
        ),
    )

    test_parser = subparsers.add_parser(
        "test",
        help="Execute standardized declarative tests for an agent",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Execute standardized declarative tests for an agent"),
        epilog=(
            "Examples:\n"
            "  kinnoo test ./my-agent\n"
            "  kinnoo test ./my-agent --tests-file ./kinnoo.tests.yaml --validate-only\n"
            "  kinnoo test ./my-agent --verbose\n"
            "  kinnoo test ./my-agent --create\n"
            "  kinnoo test ./my-agent --create custom.tests.yaml --append"
        ),
    )
    test_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory")
    test_parser.add_argument(
        "--tests-file",
        dest="tests_file",
        help="Optional path to a kinnoo.tests.yaml file (relative to agent dir or absolute)",
    )
    test_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate and load test declarations without executing the runtime",
    )
    test_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON output",
    )
    test_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include per-test detailed diagnostics (input, expected/actual output, duration, exit codes)",
    )
    test_parser.add_argument(
        "--create",
        nargs="?",
        const="kinnoo.tests.yaml",
        metavar="file",
        help="Interactively create a tests YAML (uses agent dir when provided, else current directory; default file: kinnoo.tests.yaml)",
    )
    test_parser.add_argument(
        "--append",
        action="store_true",
        help="Append interactive test cases to an existing tests YAML (requires --create)",
    )

    # [agent] task476: stop command intentionally disabled for now; keep block as reference.
    # stop_parser = subparsers.add_parser(
    #     "stop",
    #     help="Stop a running daemon agent",
    #     description="Stop a running daemon agent",
    # )
    # stop_parser.add_argument("agent_dir", nargs="?", help="Path to daemon agent directory")

    # [agent] task476: attach command intentionally disabled for now; keep block as reference.
    # attach_parser = subparsers.add_parser(
    #     "attach",
    #     help="Attach to a running daemon agent session",
    #     description="Attach to a running daemon agent session",
    # )
    # attach_parser.add_argument("agent_dir", nargs="?", help="Path to daemon agent directory")

    # [agent] task476: logs command intentionally disabled for now; keep block as reference.
    # logs_parser = subparsers.add_parser(
    #     "logs",
    #     help="Show daemon logs (tail or follow)",
    #     description="Show daemon logs (tail or follow)",
    # )
    # logs_parser.add_argument("agent_dir", nargs="?", help="Path to daemon agent directory")
    # logs_parser.add_argument(
    #     "--daemon",
    #     choices=["openclaw"],
    #     help="Use delegated daemon logs backend (currently: openclaw)",
    # )
    # logs_parser.add_argument(
    #     "--follow",
    #     action="store_true",
    #     help="Stream new log lines until daemon exits or operator interrupts",
    # )
    # logs_parser.add_argument(
    #     "--json",
    #     action="store_true",
    #     help="(OpenClaw daemon logs) request machine-readable passthrough output",
    # )
    # logs_parser.add_argument(
    #     "--tail",
    #     type=int,
    #     default=20,
    #     help="Number of recent lines to show before follow/tail output (default: 20)",
    # )

    # Add 'install' subcommand
    install_parser = subparsers.add_parser(
        "install",
        help="Install a kinnoo agent from archive (.kno) or registry",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Install a kinnoo agent from archive (.kno) or registry"),
        epilog=(
            "Examples:\n"
            "  kinnoo install ./dist/my-agent-0.1.0.kno\n"
            "  kinnoo install ./dist/my-agent-0.1.0.kno ./agents/my-agent\n"
            "  kinnoo install my-agent==1.2.0 --remote\n"
            "  kinnoo install ./dist/my-openclaw-agent-0.3.0.kno\n"
            "  kinnoo install ./dist/my-agent-0.1.0.kno --json -y"
        ),
    )
    install_parser.add_argument(
        "archive_path",
        nargs="?",
        metavar="agent[==version]",
        help=(
            "agent name from registry (use kinnoo list / search to find available agents)\n"
            "OR specify a direct path to a local .kno archive"
        ),
    )
    install_parser.add_argument("target_dir", nargs="?", help="(Optional) Directory to extract agent to")
    install_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip install confirmation prompt (shows summary and proceeds)",
    )
    install_parser.add_argument(
        "--accept-permissions",
        action="store_true",
        help="Acknowledge and accept declared manifest permissions during non-interactive install",
    )
    install_parser.add_argument(
        "--allow-unverified-publisher",
        action="store_true",
        help="Allow non-interactive install when archive has no publisher signature metadata",
    )
    install_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require strict signature and integrity verification gates for install",
    )
    install_parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip all archive integrity/signature verification checks (development-only)",
    )
    install_parser.add_argument(
        "--frozen",
        action="store_true",
        help="Require lockfile-only reproducible install; fail on lock drift or missing entries",
    )
    install_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON install result (requires -y).",
    )
    install_source_group = install_parser.add_mutually_exclusive_group()
    install_source_group.add_argument(
        "--local",
        action="store_true",
        help="Force local registry backend resolution for registry install targets",
    )
    install_source_group.add_argument(
        "--remote",
        action="store_true",
        help="Force remote registry backend resolution for registry install targets",
    )

    # Add 'pack' subcommand
    pack_parser = subparsers.add_parser("pack", help="Package an agent directory into a .kno archive")
    pack_parser.description = _orange_description("Package an agent directory into a .kno archive")
    pack_parser.formatter_class = argparse.RawTextHelpFormatter
    pack_parser.epilog = (
        "Examples:\n"
        "  kinnoo pack ./my-agent\n"
        "  kinnoo pack ./my-agent --public\n"
        "  kinnoo pack ./my-agent --bump patch\n"
        "  kinnoo pack ./my-agent --sign ./keys/kinnoo-ed25519-private.pem\n"
        "  kinnoo pack ./my-agent --preflight\n"
        "  kinnoo pack ./my-agent --include data --exclude tools"
    )
    pack_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory to package")
    pack_parser.add_argument(
        "--public",
        action="store_true",
        help="Normalize kinnoo.yaml to default public packaging behavior by removing visibility: private when present (default behavior is public).",
    )
    pack_parser.add_argument(
        "--private",
        action="store_true",
        help="Force private packaging behavior and ensure kinnoo.yaml contains visibility: private.",
    )
    pack_parser.add_argument(
        "--bump",
        nargs="?",
        const="patch",
        choices=["patch", "minor", "major"],
        help="Increment manifest version before packaging. --bump without a version specified will bump the patch version by default.",
    )
    pack_parser.add_argument(
        "--sign",
        metavar="SIGNING_KEY",
        help=(
            "Sign packaged archive and emit detached signature artifacts. "
            "SIGNING_KEY is the path to a Ed25519 private key PEM "
            "(new key can be created with 'kinnoo keygen')."
        ),
    )
    pack_parser.add_argument(
        "--preflight",
        action="store_true",
        help="Show dry-run preflight report (files, estimated size, destination) without creating archive.",
    )
    pack_parser.add_argument(
        "--include",
        action="append",
        help="Include additional file/folder paths relative to agent root (can be specified multiple times).",
    )
    pack_parser.add_argument(
        "--exclude",
        action="append",
        help="Exclude file/folder paths relative to agent root (can be specified multiple times).",
    )
    pack_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output and suppress progress logs.",
    )

    # Add 'diff' subcommand
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare two .kno archives and report manifest/file changes",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Compare two .kno archives and report manifest/file changes"),
        epilog=(
            "Examples:\n"
            "  kinnoo diff ./dist/agent-1.0.0.kno ./dist/agent-1.1.0.kno"
        ),
    )
    diff_parser.add_argument("archive_a", help="Path to baseline .kno archive")
    diff_parser.add_argument("archive_b", help="Path to candidate .kno archive")
    diff_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable diff payload",
    )

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Download an agent archive from registry into local archive storage",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Download an agent archive from registry into local archive storage"),
        epilog=(
            "Examples:\n"
            "  kinnoo fetch my-agent\n"
            "  kinnoo fetch my-agent==1.2.3 --remote\n"
            "  kinnoo fetch my-agent --strict\n"
        ),
    )
    fetch_parser.add_argument("target", nargs="?", help="Registry selector: <name> or <name>==<version>")
    fetch_source_group = fetch_parser.add_mutually_exclusive_group()
    fetch_source_group.add_argument("--local", action="store_true", help="Fetch from local registry")
    fetch_source_group.add_argument("--remote", action="store_true", help="Fetch from remote registry")
    fetch_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require embedded signature verification in addition to integrity checks.",
    )
    fetch_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Remove installed agent and/or archived versions",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Remove installed agent and/or archived versions"),
        epilog=(
            "Examples:\n"
            "  kinnoo uninstall my-agent -y\n"
            "  kinnoo uninstall my-agent==1.2.3 -y\n"
            "  kinnoo uninstall my-agent==latest -y"
        ),
    )
    uninstall_parser.add_argument("target", nargs="?", help="Agent target: <name>, <name>==<version>, or <archive>.kno==<version>")
    uninstall_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # Add 'keygen' subcommand
    keygen_parser = subparsers.add_parser(
        "keygen",
        help="Generate an Ed25519 keypair for archive signing",
        description=_orange_description("Generate an Ed25519 keypair for archive signing"),
    )
    keygen_parser.add_argument(
        "--private-key",
        default="kinnoo-ed25519-private.pem",
        help="Path for private key PEM output (default: kinnoo-ed25519-private.pem)",
    )
    keygen_parser.add_argument(
        "--public-key",
        default="kinnoo-ed25519-public.pem",
        help="Path for public key PEM output (default: kinnoo-ed25519-public.pem)",
    )

    # Add 'inspect' subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect metadata from an agent directory or .kno archive",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Inspect metadata from an agent directory or .kno archive"),
        epilog=(
            "Reference:\n"
            "  docs/kinnoo-yaml-spec.md"
        ),
    )
    inspect_parser.add_argument(
        "target",
        nargs="?",
        help="Path to agent directory or .kno archive",
    )
    inspect_parser.add_argument(
        "--full",
        action="store_true",
        help="Show all known metadata fields, including N/A values",
    )
    inspect_parser.add_argument(
        "--raw",
        action="store_true",
        help="Show metadata as raw dotted-path key/value fields",
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON inspect output",
    )
    inspect_parser.add_argument(
        "--update",
        nargs=2,
        metavar=("KEY", "NEW_VALUE"),
        help="Update a manifest metadata field (for example: --update runtime.language nodejs)",
    )
    inspect_parser.add_argument(
        "--skip-warnings",
        action="store_true",
        help="Bypass interactive warning prompts for inspect update operations",
    )

    # Add 'publish' subcommand
    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish latest archived agent artifact to the registry",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Publish latest archived agent artifact to the registry"),
        epilog=(
            "Examples:\n"
            "  kinnoo publish my-agent --local\n"
            "  kinnoo publish my-agent --remote\n"
            "  kinnoo publish ./dist/my-agent-1.0.0.kno --remote\n"
            "  kinnoo publish ./my-agent --pack --bump minor --remote\n"
            "  kinnoo publish ./my-agent --pack --private --remote"
        ),
    )
    publish_parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Agent name (default archive-first mode), .kno path, or with --pack "
            "a file path to an agent directory"
        ),
    )
    publish_source_group = publish_parser.add_mutually_exclusive_group()
    publish_source_group.add_argument(
        "--local",
        action="store_true",
        help="Publish to local registry",
    )
    publish_source_group.add_argument(
        "--remote",
        action="store_true",
        help="Publish to remote registry (default)",
    )
    publish_parser.add_argument(
        "--pack",
        action="store_true",
        help="Pack first, then publish. With --pack, <target> must be a file path to an agent directory.",
    )
    publish_parser.add_argument(
        "--private",
        action="store_true",
        help="With --pack, force private packaging behavior by setting visibility: private before packaging.",
    )
    publish_parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Optional version bump applied during --pack flow before publish.",
    )
    publish_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require strict signature/trust gates before publish upload.",
    )
    publish_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON publish result.",
    )

    # Add 'list' subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List agents from remote registry (default if configured) or local archive",
        description=_orange_description("List agents from remote registry (default if configured) or local archive"),
    )
    list_source_group = list_parser.add_mutually_exclusive_group()
    list_source_group.add_argument(
        "--local",
        action="store_true",
        help="List agents from local archive",
    )
    list_source_group.add_argument(
        "--remote",
        action="store_true",
        help="List agents from user remote registry (default)",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON list results",
    )

    # Add 'search' subcommand
    search_parser = subparsers.add_parser(
        "search",
        help="Search agents from remote registry (default if configured) or local archive",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Search agents from remote registry (default if configured) or local archive"),
        epilog=(
            "Examples:\n"
            "  kinnoo search writer\n"
            "  kinnoo search mcp --local\n"
            "  kinnoo search openclaw --remote"
        ),
    )
    search_source_group = search_parser.add_mutually_exclusive_group()
    search_source_group.add_argument(
        "--local",
        action="store_true",
        help="Search agents from local archive",
    )
    search_source_group.add_argument(
        "--remote",
        action="store_true",
        help="Search agents from global remote registry (default)",
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Search query to match against agent name and description",
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON search results",
    )

    # [agent] task476: sync command intentionally disabled for now; keep block as reference.
    # sync_parser = subparsers.add_parser(
    #     "sync",
    #     help="Sync source metadata into local registry mirror",
    #     formatter_class=argparse.RawTextHelpFormatter,
    #     description="Sync source metadata into local registry mirror",
    #     epilog=(
    #         "Examples:\n"
    #         "  kinnoo sync clawhub\n"
    #         "  kinnoo sync clawhub --full\n"
    #         "  kinnoo sync clawhub --since 2026-03-01T00:00:00Z"
    #     ),
    # )
    # sync_parser.add_argument(
    #     "source",
    #     choices=["clawhub"],
    #     help="Source namespace to sync",
    # )
    # sync_parser.add_argument(
    #     "--full",
    #     action="store_true",
    #     help="Run full sync mode instead of incremental sync",
    # )
    # sync_parser.add_argument(
    #     "--since",
    #     help="Incremental sync cursor timestamp (ISO8601), if supported by source",
    # )
    # sync_source_group = sync_parser.add_mutually_exclusive_group()
    # sync_source_group.add_argument(
    #     "--local",
    #     action="store_true",
    #     help="Force local fixture-driven sync mode",
    # )
    # sync_source_group.add_argument(
    #     "--remote",
    #     action="store_true",
    #     help="Force configured remote sync mode",
    # )

    login_parser = subparsers.add_parser(
        "login",
        help="Authenticate to a registry and persist auth state locally",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Authenticate to a registry and persist auth state locally"),
    )

    logout_parser = subparsers.add_parser(
        "logout",
        help="Clear persisted registry auth state",
        description=_orange_description("Clear persisted registry auth state"),
    )
    del logout_parser

    # Add 'import' subcommand
    import_parser = subparsers.add_parser(
        "import",
        help="Import an existing project in-place and prepare kinnoo metadata",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Import an existing project in-place and prepare kinnoo metadata"),
        epilog=(
            "Examples:\n"
            "  kinnoo import\n"
            "  kinnoo import ./existing-project --force\n"
            "  kinnoo import https://github.com/org/repo\n"
            "  kinnoo import https://github.com/org/repo ./imported-agent\n"
        ),
    )
    import_parser.add_argument(
        "target",
        nargs="?",
        help=(
            "(Optional) Existing local project path (defaults to current directory), "
            "or a GitHub repository URL"
        ),
    )
    import_parser.add_argument(
        "import_path",
        nargs="?",
        help="(URL import only) Destination path for downloaded project",
    )
    import_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing kinnoo.yaml in target directory",
    )
    import_parser.add_argument(
        "--from",
        dest="framework_from",
        choices=["langchain", "langgraph", "openai", "openclaw"],
        help="Use framework-aware adapter hints for import inference",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Run import/inspect/preflight compatibility checks",
        formatter_class=argparse.RawTextHelpFormatter,
        description=_orange_description("Run import + inspect + preflight checks for a local project or GitHub URL"),
        epilog=(
            "Examples:\n"
            "  kinnoo check ./my-agent\n"
            "  kinnoo check https://github.com/org/repo"
        ),
    )
    check_parser.add_argument(
        "target",
        nargs="?",
        help="Path to local agent directory, or a GitHub repository URL",
    )

    # Pre-parse sys.argv for missing args to print custom usage before argparse error
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if (
            "-h" not in sys.argv
            and "--help" not in sys.argv
            and "--preflight" not in sys.argv
            and "--no-guard" not in sys.argv
            and len(sys.argv) < 3
        ):
            print(RUN_USAGE_TEXT, file=sys.stderr)
            sys.exit(1)

    run_pass_through_args: list[str] = []
    if len(sys.argv) > 1 and sys.argv[1] == "run" and "--" in sys.argv:
        separator_index = sys.argv.index("--")
        run_pass_through_args = sys.argv[separator_index + 1 :]
        args = parser.parse_args(sys.argv[1:separator_index])
    else:
        args = parser.parse_args()

    if args.command == "init":
        supported_frameworks = {
            "gemini",
            "chatgpt",
            "claude-chat",
            "pydantic-ai",
            "langgraph",
            "openai-agents",
            "mcp-client",
            "mcp-server",
            "openclaw",
            "no-framework",
        }

        positional_token = getattr(args, "framework", None)
        agent_name = getattr(args, "agent_name", None)
        resolved_framework = None
        resolved_language = getattr(args, "language", None)

        if positional_token in supported_frameworks:
            resolved_framework = positional_token
        elif positional_token and agent_name is None:
            # Backward-compatible path: `kinnoo init <agent-name>` without framework.
            agent_name = positional_token
        elif positional_token and agent_name is not None:
            print(
                "Unsupported framework. Supported frameworks: "
                + ", ".join(sorted(supported_frameworks))
                + ".",
                file=sys.stderr,
            )
            sys.exit(1)

        if resolved_language is not None and resolved_language not in {"python", "javascript", "typescript"}:
            print(
                "Error: --language must be one of: python, javascript, typescript.",
                file=sys.stderr,
            )
            sys.exit(1)

        if agent_name is None and resolved_framework is None:
            if sys.stdin.isatty():
                from kinnoo.init_command import interactive_init_wizard

                resolved_framework, resolved_language, agent_name = interactive_init_wizard(Path.cwd())
            else:
                print(
                    "Usage: kinnoo init [framework] [--language {python,javascript,typescript}] <agent-name>",
                    file=sys.stderr,
                )
                sys.exit(1)

        if not agent_name:
            print("Usage: kinnoo init [framework] [--language {python,javascript,typescript}] <agent-name>", file=sys.stderr)
            sys.exit(1)
        if not re.match(NAME_PATTERN, agent_name):
            print(f"Error: Invalid agent name '{agent_name}'. Must match pattern: {NAME_PATTERN}", file=sys.stderr)
            sys.exit(1)
        from kinnoo.init_command import init_agent
        # from pathlib import Path
        try:
            init_agent(
                agent_name,
                Path.cwd(),
                framework=resolved_framework,
                language=resolved_language,
                minimal=bool(getattr(args, "minimal", False)),
            )
            print(f"Initialized agent: {agent_name}")
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


    elif args.command == "run":
        preflight_mode = bool(getattr(args, "preflight", False))
        input_arg = args.input
        pass_through_args = run_pass_through_args
        if bool(getattr(args, "experimental_openclaw_adapter", False)):
            _emit_bridge_path_deprecation_warning(
                path="run_experimental_openclaw_adapter",
                replacement="kinnoo run <agent-dir> '<prompt>' [--json]",
            )
        if not hasattr(args, "agent_dir") or args.agent_dir is None:
            if preflight_mode:
                print("Usage: kinnoo run <agent-dir> --preflight", file=sys.stderr)
            else:
                print(RUN_USAGE_TEXT, file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.run_command import run_agent
        except ImportError:
            from .run_command import run_agent

        exit_code = run_agent(
            agent_dir_arg=args.agent_dir,
            input_arg=input_arg,
            entrypoint_arg=getattr(args, "entrypoint", None),
            json_input_arg=getattr(args, "json_input", None),
            json_file_arg=getattr(args, "json_file", None),
            preflight=preflight_mode,
            no_guard=bool(getattr(args, "no_guard", False)),
            pass_through_args=pass_through_args,
            sandbox=bool(getattr(args, "enforce_policy", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
            experimental_openclaw_adapter=bool(getattr(args, "experimental_openclaw_adapter", False)),
            openclaw_thinking=None,
            openclaw_json_output=bool(getattr(args, "json", False)),
            max_seconds=getattr(args, "max_seconds", None),
            max_cpu_seconds=getattr(args, "max_cpu_seconds", None),
            max_memory_mb=getattr(args, "max_memory_mb", None),
        )
        sys.exit(exit_code)

    elif args.command == "test":
        agent_dir = getattr(args, "agent_dir", None)
        create_file_name = getattr(args, "create", None)
        if agent_dir is None and create_file_name is None:
            print(
                "Usage: kinnoo test [<agent-dir>] [--tests-file path] [--validate-only] [--json] [--verbose] [--create [file]] [--append]",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            from kinnoo.test_command import run_test_command
        except ImportError:
            from .test_command import run_test_command

        exit_code = run_test_command(
            agent_dir_arg=agent_dir,
            tests_file_arg=getattr(args, "tests_file", None),
            validate_only=bool(getattr(args, "validate_only", False)),
            json_output=bool(getattr(args, "json_output", False)),
            verbose=bool(getattr(args, "verbose", False)),
            create_file_name=create_file_name,
            append=bool(getattr(args, "append", False)),
        )
        sys.exit(exit_code)

    elif args.command == "install":
        archive_path = getattr(args, "archive_path", None)
        target_dir_arg = getattr(args, "target_dir", None)
        if archive_path is None:
            print(
                "Usage: kinnoo install <archive-path | agent_name[==version]> [target-dir]",
                file=sys.stderr,
            )
            sys.exit(1)
        force = False
        if hasattr(args, "force"):
            force = args.force
        if "--force" in sys.argv:
            force = True
        assume_yes = bool(getattr(args, "yes", False))
        accept_permissions = bool(getattr(args, "accept_permissions", False))
        allow_unverified_publisher = bool(getattr(args, "allow_unverified_publisher", False))
        strict_mode = bool(getattr(args, "strict", False))
        json_output = bool(getattr(args, "json", False))
        skip_verify = bool(getattr(args, "skip_verify", False))
        frozen_mode = bool(getattr(args, "frozen", False))
        use_local = bool(getattr(args, "local", False))
        use_remote = bool(getattr(args, "remote", False))
        try:
            from kinnoo.install_command import install_agent
        except ImportError:
            from .install_command import install_agent

        if json_output and not assume_yes:
            print("Error: --json requires -y for non-interactive install mode.", file=sys.stderr)
            sys.exit(1)

        install_stdout = io.StringIO()
        install_kwargs = dict(
            archive_path=archive_path,
            target_dir_arg=target_dir_arg,
            force=force,
            assume_yes=assume_yes,
            accept_permissions=accept_permissions,
            allow_unverified_publisher=allow_unverified_publisher,
            strict_mode=strict_mode,
            skip_verify=skip_verify,
            frozen_mode=frozen_mode,
            use_local=use_local,
            use_remote=use_remote,
        )

        if json_output:
            with contextlib.redirect_stdout(install_stdout):
                exit_code = install_agent(**install_kwargs)
        else:
            exit_code = install_agent(**install_kwargs)

        if json_output:
            manifest_name = None
            manifest_version = None
            resolved_install_path = None
            archive_candidate = Path(archive_path).expanduser()
            if archive_candidate.exists() and archive_candidate.is_file() and archive_candidate.suffix == ".kno":
                try:
                    from kinnoo.inspect_command import read_manifest_from_kno_archive
                except ImportError:
                    from .inspect_command import read_manifest_from_kno_archive

                manifest_data = read_manifest_from_kno_archive(archive_candidate)
                if isinstance(manifest_data, dict):
                    raw_name = manifest_data.get("name")
                    raw_version = manifest_data.get("version")
                    if isinstance(raw_name, str) and raw_name.strip():
                        manifest_name = raw_name.strip()
                    if isinstance(raw_version, str) and raw_version.strip():
                        manifest_version = raw_version.strip()

                    if target_dir_arg:
                        resolved_install_path = str(Path(target_dir_arg).expanduser().resolve())
                    elif str(manifest_data.get("framework", "")).strip().lower() == "openclaw" and manifest_name:
                        resolved_install_path = str((Path.home() / ".openclaw" / f"workspace-{manifest_name}").resolve())
                    else:
                        resolved_install_path = str(archive_candidate.with_suffix("").resolve())

            json_payload = {
                "agent_name": manifest_name,
                "agent_version": manifest_version,
                "source_archive_path": str(archive_path),
                "install_path": resolved_install_path,
                "registry_source": "remote" if use_remote else ("local" if use_local else "auto"),
                "success": exit_code == 0,
                "exit_code": exit_code,
                "error_code": None if exit_code == 0 else "INSTALL_FAILED",
                "error_message": None if exit_code == 0 else "Install command failed",
            }
            print(json.dumps(json_payload, sort_keys=True))
        sys.exit(exit_code)

    # [agent] task476: stop/attach/logs dispatch intentionally disabled; keep implementation commented for later re-enable.
    # elif args.command == "stop":
    #     agent_dir = getattr(args, "agent_dir", None)
    #     if agent_dir is None:
    #         print("Usage: kinnoo stop <agent-dir>", file=sys.stderr)
    #         sys.exit(1)
    #
    #     try:
    #         from kinnoo.run_command import stop_agent
    #     except ImportError:
    #         from .run_command import stop_agent
    #
    #     exit_code = stop_agent(agent_dir)
    #     sys.exit(exit_code)
    #
    # elif args.command == "attach":
    #     agent_dir = getattr(args, "agent_dir", None)
    #     if agent_dir is None:
    #         print("Usage: kinnoo attach <agent-dir>", file=sys.stderr)
    #         sys.exit(1)
    #
    #     try:
    #         from kinnoo.run_command import attach_agent
    #     except ImportError:
    #         from .run_command import attach_agent
    #
    #     exit_code = attach_agent(agent_dir)
    #     sys.exit(exit_code)
    #
    # elif args.command == "logs":
    #     daemon = getattr(args, "daemon", None)
    #     if daemon == "openclaw":
    #         try:
    #             from kinnoo.logs_command import logs_openclaw
    #         except ImportError:
    #             from .logs_command import logs_openclaw
    #
    #         exit_code = logs_openclaw(
    #             follow=bool(getattr(args, "follow", False)),
    #             json_output=bool(getattr(args, "json", False)),
    #         )
    #         sys.exit(exit_code)
    #
    #     agent_dir = getattr(args, "agent_dir", None)
    #     if agent_dir is None:
    #         print("Usage: kinnoo logs <agent-dir> [--tail N] [--follow]", file=sys.stderr)
    #         sys.exit(1)
    #
    #     try:
    #         from kinnoo.run_command import logs_agent
    #     except ImportError:
    #         from .run_command import logs_agent
    #
    #     exit_code = logs_agent(
    #         agent_dir_arg=agent_dir,
    #         follow=bool(getattr(args, "follow", False)),
    #         tail_lines=int(getattr(args, "tail", 20)),
    #     )
    #     sys.exit(exit_code)

    elif args.command == "pack":
        agent_dir = args.agent_dir
        if agent_dir is None:
            print("Usage: kinnoo pack <agent-dir> [--public|--private] [--bump [patch|minor|major]]", file=sys.stderr)
            sys.exit(1)
        try:
            from kinnoo.pack_command import pack_agent
        except ImportError:
            from .pack_command import pack_agent

        exit_code = pack_agent(
            agent_dir,
            make_public=bool(getattr(args, "public", False)),
            make_private=bool(getattr(args, "private", False)),
            bump=getattr(args, "bump", None),
            sign=bool(getattr(args, "sign", None)),
            signing_key_path=getattr(args, "sign", None),
            preflight=bool(getattr(args, "preflight", False)),
            include=getattr(args, "include", None),
            exclude=getattr(args, "exclude", None),
            json_output=bool(getattr(args, "json", False)),
        )
        sys.exit(exit_code)

    elif args.command == "diff":
        archive_a = getattr(args, "archive_a", None)
        archive_b = getattr(args, "archive_b", None)
        if archive_a is None or archive_b is None:
            print("Usage: kinnoo diff <archive-a.kno> <archive-b.kno>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.diff_command import diff_archives
        except ImportError:
            from .diff_command import diff_archives

        exit_code = diff_archives(
            archive_a,
            archive_b,
            json_output=bool(getattr(args, "json", False)),
        )
        sys.exit(exit_code)

    # [agent] task476: sync dispatch intentionally disabled; keep implementation commented for later re-enable.
    # elif args.command == "sync":
    #     source = getattr(args, "source", None)
    #     if source is None:
    #         print("Usage: kinnoo sync <source>", file=sys.stderr)
    #         sys.exit(1)
    #
    #     if bool(getattr(args, "local", False)):
    #         mode = "local"
    #     elif bool(getattr(args, "remote", False)):
    #         mode = "remote"
    #     else:
    #         mode = "auto"
    #
    #     try:
    #         from kinnoo.sync_command import sync_source
    #     except ImportError:
    #         from .sync_command import sync_source
    #
    #     exit_code = sync_source(
    #         source=source,
    #         full=bool(getattr(args, "full", False)),
    #         since=getattr(args, "since", None),
    #         mode=mode,
    #     )
    #     sys.exit(exit_code)

    elif args.command == "uninstall":
        target = getattr(args, "target", None)
        if target is None:
            print("Usage: kinnoo uninstall <target>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.uninstall_command import uninstall_agent
        except ImportError:
            from .uninstall_command import uninstall_agent

        exit_code = uninstall_agent(target=target, assume_yes=bool(getattr(args, "yes", False)))
        sys.exit(exit_code)

    elif args.command == "fetch":
        target = getattr(args, "target", None)
        if target is None:
            print("Usage: kinnoo fetch <name|name==version>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.fetch_command import fetch_agent
        except ImportError:
            from .fetch_command import fetch_agent

        try:
            exit_code = fetch_agent(
                target=target,
                use_local=bool(getattr(args, "local", False)),
                use_remote=bool(getattr(args, "remote", False)),
                strict_mode=bool(getattr(args, "strict", False)),
                json_output=bool(getattr(args, "json", False)),
            )
        except RemoteRegistryClientError as error:
            _print_remote_registry_error(error)
            sys.exit(1)
        sys.exit(exit_code)

    elif args.command == "keygen":
        private_key_path = Path(getattr(args, "private_key"))
        public_key_path = Path(getattr(args, "public_key"))

        if private_key_path.resolve() == public_key_path.resolve():
            print("Error: --private-key and --public-key must be different paths", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.signing import generate_ed25519_keypair
        except ImportError:
            from .signing import generate_ed25519_keypair

        try:
            result = generate_ed25519_keypair(
                private_key_path=private_key_path,
                public_key_path=public_key_path,
            )
        except (OSError, ValueError) as exc:
            print(f"Error: Failed to generate keypair: {exc}", file=sys.stderr)
            sys.exit(1)

        print("[kinnoo keygen] Generated Ed25519 keypair.")
        print(f"[kinnoo keygen] Private key: {result.private_key_path}")
        print(f"[kinnoo keygen] Public key: {result.public_key_path}")
        print(f"[kinnoo keygen] Public key fingerprint (SHA256): {result.public_key_fingerprint}")
        sys.exit(0)

    elif args.command == "inspect":
        update_args = getattr(args, "update", None)
        target = getattr(args, "target", None)
        full = bool(getattr(args, "full", False))
        raw = bool(getattr(args, "raw", False))
        json_output = bool(getattr(args, "json", False))
        skip_warnings = bool(getattr(args, "skip_warnings", False))

        try:
            from kinnoo.inspect_command import inspect_target, inspect_update_target
        except ImportError:
            from .inspect_command import inspect_target, inspect_update_target

        if update_args is not None:
            if full or raw:
                print("Error: --full/--raw cannot be combined with --update.", file=sys.stderr)
                sys.exit(1)
            if target is None:
                print("Usage: kinnoo inspect <target> --update <key> <new-value>", file=sys.stderr)
                sys.exit(1)
            old_key, new_value = update_args
            exit_code = inspect_update_target(
                target,
                old_key,
                new_value,
                skip_warnings=skip_warnings,
                json_output=json_output,
            )
            sys.exit(exit_code)

        if target is None:
            print("Usage: kinnoo inspect <target>", file=sys.stderr)
            sys.exit(1)

        exit_code = inspect_target(target, full=full, raw=raw, json_output=json_output)
        sys.exit(exit_code)

    elif args.command == "publish":
        target = getattr(args, "target", None)
        if target is None:
            print(
                "Usage: kinnoo publish <agent-name|archive.kno|agent-dir-path> "
                "[--pack] [--private] [--bump {major,minor,patch}] [--local|--remote]",
                file=sys.stderr,
            )
            sys.exit(1)

        use_local = bool(getattr(args, "local", False))
        use_remote = bool(getattr(args, "remote", False))
        use_pack = bool(getattr(args, "pack", False))
        make_private = bool(getattr(args, "private", False))
        bump = getattr(args, "bump", None)
        strict_mode = bool(getattr(args, "strict", False))
        json_output = bool(getattr(args, "json", False))

        if use_local and use_remote:
            print("Error: --local and --remote cannot be used together.", file=sys.stderr)
            sys.exit(1)

        if bump is not None and not use_pack:
            print("Error: --bump can only be used together with --pack.", file=sys.stderr)
            sys.exit(1)

        if make_private and not use_pack:
            print("Error: --private can only be used together with --pack.", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.publish_command import publish_agent
        except ImportError:
            from .publish_command import publish_agent

        try:
            exit_code = publish_agent(
                target=target,
                use_local=use_local,
                use_remote=use_remote,
                pack=use_pack,
                make_private=make_private,
                bump=bump,
                strict_mode=strict_mode,
                json_output=json_output,
            )
        except RemoteRegistryClientError as error:
            _print_remote_registry_error(error)
            sys.exit(1)
        sys.exit(exit_code)

    elif args.command == "list":
        if bool(getattr(args, "local", False)):
            source = "local"
        elif bool(getattr(args, "remote", False)):
            source = "remote"
        else:
            source = "auto"

        try:
            from kinnoo.list_command import list_agents
        except ImportError:
            from .list_command import list_agents

        try:
            exit_code = list_agents(source=source, json_output=bool(getattr(args, "json", False)))
        except RemoteRegistryClientError as error:
            _print_remote_registry_error(error)
            sys.exit(1)
        sys.exit(exit_code)

    elif args.command == "search":
        query = getattr(args, "query", None)
        if query is None:
            print("Usage: kinnoo search [--local | --remote] <query>", file=sys.stderr)
            sys.exit(1)

        if bool(getattr(args, "local", False)):
            source = "local"
        elif bool(getattr(args, "remote", False)):
            source = "remote"
        else:
            source = "auto"

        try:
            from kinnoo.search_command import search_agents
        except ImportError:
            from .search_command import search_agents

        try:
            exit_code = search_agents(query=query, source=source, json_output=bool(getattr(args, "json", False)))
        except RemoteRegistryClientError as error:
            _print_remote_registry_error(error)
            sys.exit(1)
        sys.exit(exit_code)

    elif args.command == "sync":
        source = getattr(args, "source", None)
        if source is None:
            print("Usage: kinnoo sync clawhub [--full] [--since <iso8601>]", file=sys.stderr)
            sys.exit(1)

        if str(source).strip().lower() == "clawhub":
            _emit_bridge_path_deprecation_warning(
                path="sync_clawhub",
                replacement=(
                    "kinnoo search --openclaw-skill <query> [--json]; "
                    "kinnoo install <agent-name> --openclaw-skill <owner/skill-or-url>"
                ),
            )

        try:
            from kinnoo.sync_command import sync_source
        except ImportError:
            from .sync_command import sync_source

        exit_code = sync_source(
            source=source,
            full=bool(getattr(args, "full", False)),
            since=getattr(args, "since", None),
            use_local=bool(getattr(args, "local", False)),
            use_remote=bool(getattr(args, "remote", False)),
        )
        sys.exit(exit_code)

    elif args.command == "login":
        try:
            from kinnoo.auth_command import login_command
        except ImportError:
            from .auth_command import login_command

        exit_code = login_command(email=None, password=None)
        sys.exit(exit_code)

    elif args.command == "logout":
        try:
            from kinnoo.auth_command import logout_command
        except ImportError:
            from .auth_command import logout_command

        exit_code = logout_command()
        sys.exit(exit_code)

    elif args.command == "import":
        target_path_arg = getattr(args, "target", None)
        import_path_arg = getattr(args, "import_path", None)
        force = bool(getattr(args, "force", False))
        framework_from = getattr(args, "framework_from", None)

        try:
            from kinnoo.import_command import import_agent
        except ImportError:
            from .import_command import import_agent

        exit_code = import_agent(
            target_path_arg=target_path_arg,
            import_path_arg=import_path_arg,
            force=force,
            framework_from=framework_from,
        )
        sys.exit(exit_code)

    elif args.command == "check":
        target = getattr(args, "target", None)
        if target is None:
            print("Usage: kinnoo check <agent-dir | github-url>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.check_command import check_target
        except ImportError:
            from .check_command import check_target

        exit_code = check_target(target)
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
