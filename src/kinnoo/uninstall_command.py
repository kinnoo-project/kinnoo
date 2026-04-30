from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

try:
    from kinnoo.config import resolve_lockfile_path
    from kinnoo.install_trace import write_uninstall_trace
except ImportError:
    from .config import resolve_lockfile_path
    from .install_trace import write_uninstall_trace


DEFAULT_AGENT_INSTALL_ROOT = Path.home() / ".kinnoo" / "agents"
DEFAULT_ARCHIVE_ROOT = Path.home() / ".kinnoo" / "archive"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_agent_install_root() -> Path:
    override = DEFAULT_AGENT_INSTALL_ROOT
    env_value = os.environ.get("KINNOO_AGENT_INSTALL_ROOT", "").strip()
    if env_value:
        try:
            return Path(env_value).expanduser().resolve()
        except OSError:
            return Path(env_value).expanduser()
    return override


def _remove_agent_from_lockfile(*, agent_name: str, install_root: Path) -> tuple[bool, str | None]:
    lockfile_path = resolve_lockfile_path(start_dir=install_root)
    if not lockfile_path.exists() or not lockfile_path.is_file():
        return False, None

    try:
        lockfile_doc = yaml.safe_load(lockfile_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        return False, f"failed to read lockfile '{lockfile_path}': {error}"

    if not isinstance(lockfile_doc, dict):
        return False, f"lockfile '{lockfile_path}' is not a valid mapping"

    agents = lockfile_doc.get("agents")
    if not isinstance(agents, dict):
        return False, f"lockfile '{lockfile_path}' is missing an 'agents' mapping"

    if agent_name not in agents:
        return False, None

    del agents[agent_name]
    ordered_agents: dict[str, object] = {}
    for key in sorted(agents.keys()):
        ordered_agents[str(key)] = agents[key]

    lockfile_doc["agents"] = ordered_agents
    lockfile_doc["locked_at"] = _utc_now_iso()

    try:
        lockfile_path.write_text(
            yaml.safe_dump(lockfile_doc, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as error:
        return False, f"failed to write lockfile '{lockfile_path}': {error}"

    return True, None


def _resolve_archive_root() -> Path:
    env_value = os.environ.get("KINNOO_ARCHIVE_ROOT", "").strip()
    if env_value:
        return Path(env_value).expanduser().resolve()
    return DEFAULT_ARCHIVE_ROOT


def _parse_uninstall_target(target: str) -> tuple[str, str | None, bool]:
    raw = target.strip()
    if not raw:
        return "", None, False

    if "==" in raw:
        name_part, version_part = raw.split("==", 1)
        version = version_part.strip() or None
    else:
        name_part, version = raw, None

    is_archive_target = name_part.strip().endswith(".kno")
    candidate = Path(name_part.strip()).name
    if candidate.endswith(".kno"):
        candidate = Path(candidate).stem

    return candidate.strip(), version, is_archive_target


def _version_sort_key(value: str) -> tuple[int, ...] | tuple[int, str]:
    parts = value.split(".")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return (2, int(parts[0]), int(parts[1]), int(parts[2]))
    return (1, value)


def _remove_archive_versions(*, archive_root: Path, agent_name: str, version: str | None) -> tuple[int, str]:
    agent_archive_root = archive_root / agent_name
    if not agent_archive_root.exists() or not agent_archive_root.is_dir():
        return 0, ""

    removed_count = 0
    if version is None:
        shutil.rmtree(agent_archive_root)
        return 1, "all"

    resolved_version = version.strip().lower()
    if resolved_version == "latest":
        versions = sorted(
            [path.name for path in agent_archive_root.iterdir() if path.is_dir()],
            key=_version_sort_key,
            reverse=True,
        )
        if not versions:
            return 0, ""
        resolved_version = versions[0]

    target_version_dir = agent_archive_root / resolved_version
    if target_version_dir.exists() and target_version_dir.is_dir():
        shutil.rmtree(target_version_dir)
        removed_count = 1

    if agent_archive_root.exists() and not any(path.is_dir() for path in agent_archive_root.iterdir()):
        agent_archive_root.rmdir()

    return removed_count, resolved_version


def uninstall_agent(
    target: str,
    install_root_arg: str | None = None,
    assume_yes: bool = False,
) -> int:
    normalized_name, requested_version, is_archive_target = _parse_uninstall_target(target)
    if not normalized_name:
        print("Error: uninstall requires a non-empty target.", file=sys.stderr)
        return 1

    if install_root_arg:
        install_root = Path(install_root_arg).expanduser().resolve()
    else:
        install_root = resolve_agent_install_root()

    target_dir = install_root / normalized_name
    archive_root = _resolve_archive_root()

    if not assume_yes:
        try:
            confirmation = input(
                f"Confirm uninstall target '{target}' for agent '{normalized_name}'? [y/N]: "
            ).strip().lower()
        except EOFError:
            print("Uninstall aborted by user.", file=sys.stderr)
            return 1

        if confirmation not in {"y", "yes"}:
            print("Uninstall aborted by user.", file=sys.stderr)
            return 1

    removed_install_dir = False
    should_remove_install_dir = not is_archive_target
    if should_remove_install_dir and target_dir.exists() and target_dir.is_dir():
        try:
            shutil.rmtree(target_dir)
            removed_install_dir = True
        except Exception as error:
            print(
                f"Error: Failed to remove installed agent directory '{target_dir}': {error}",
                file=sys.stderr,
            )
            return 1

    try:
        removed_archives, removed_version = _remove_archive_versions(
            archive_root=archive_root,
            agent_name=normalized_name,
            version=requested_version,
        )
    except Exception as error:
        print(f"Error: Failed to remove archive versions for '{normalized_name}': {error}", file=sys.stderr)
        return 1

    if not removed_install_dir and removed_archives == 0:
        print(
            f"Error: Nothing to uninstall for target '{target}'.",
            file=sys.stderr,
        )
        return 1

    removed_from_lockfile, lockfile_error = _remove_agent_from_lockfile(
        agent_name=normalized_name,
        install_root=install_root,
    )
    if lockfile_error is not None:
        print(
            f"Error: Agent files removed but metadata cleanup failed ({lockfile_error}).",
            file=sys.stderr,
        )
        return 1

    uninstall_trace_payload = {
        "schema_version": "1.0",
        "event": "uninstall",
        "agent": normalized_name,
        "removed_path": str(target_dir) if removed_install_dir else "",
        "removed_archive_versions": removed_archives,
        "removed_archive_version": removed_version,
        "removed_from_lockfile": removed_from_lockfile,
        "timestamp": _utc_now_iso(),
    }
    trace_path = write_uninstall_trace(install_root=install_root, payload=uninstall_trace_payload)
    if trace_path is not None:
        print(f"[kinnoo uninstall] Wrote uninstall trace: '{trace_path}'")

    print(f"[kinnoo uninstall] Removed target '{target}' for agent '{normalized_name}'.")
    return 0
