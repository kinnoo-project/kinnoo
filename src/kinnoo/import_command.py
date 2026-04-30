"""Import command surface for in-place onboarding workflows."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

try:
    from kinnoo.analyzer import (
        analyze_project,
        infer_openclaw_project_hints,
        adapter_default_unresolved_guidance,
        adapter_minimum_coverage,
    )
except ImportError:
    from .analyzer import (
        analyze_project,
        infer_openclaw_project_hints,
        adapter_default_unresolved_guidance,
        adapter_minimum_coverage,
    )

try:
    from kinnoo.framework_adapters import merge_adapter_into_report
    from kinnoo.framework_adapters.langchain_adapter import apply as apply_langchain_adapter
    from kinnoo.framework_adapters.langgraph_adapter import apply as apply_langgraph_adapter
    from kinnoo.framework_adapters.openai_adapter import apply as apply_openai_adapter
except ImportError:
    from .framework_adapters import merge_adapter_into_report
    from .framework_adapters.langchain_adapter import apply as apply_langchain_adapter
    from .framework_adapters.langgraph_adapter import apply as apply_langgraph_adapter
    from .framework_adapters.openai_adapter import apply as apply_openai_adapter

try:
    from kinnoo.validator import validate as validate_manifest
    from kinnoo.validator import validate_manifest_data
except ImportError:
    from .validator import validate as validate_manifest
    from .validator import validate_manifest_data

try:
    from kinnoo.terminal_colors import style_text
except ImportError:
    from .terminal_colors import style_text

try:
    from kinnoo.openclaw_preflight import run_openclaw_preflight_for_command
except ImportError:
    from .openclaw_preflight import run_openclaw_preflight_for_command


DEFAULT_IMPORTED_MANIFEST = """name: imported-agent
version: 1.0.0
entrypoint: run.py
runtime:
    type: one-shot
    language: python
    version: \">=3.10\"
dependencies: []
inputs:
    type: string
outputs:
    type: string
"""


class ImportWizardInterrupted(Exception):
    """Raised when import wizard input is interrupted by EOF or Ctrl+C."""


class PromptSession:
    """Track wizard input behavior to support automation-safe defaults."""

    def __init__(self) -> None:
        self.answers_received = 0
        self.non_interactive = not os.isatty(0)


_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def is_github_url(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    return _GITHUB_URL_RE.fullmatch(value.strip()) is not None


def github_repo_dir_name(url: str) -> str:
    match = _GITHUB_URL_RE.fullmatch(url.strip())
    if match is None:
        raise ValueError(f"Not a supported GitHub URL: {url}")

    repo_name = match.group("repo")
    if repo_name.lower().endswith(".git"):
        repo_name = repo_name[:-4]
    return repo_name


def clone_github_repo(url: str, destination: Path) -> tuple[bool, str]:
    git_executable = shutil.which("git")
    if git_executable is None:
        return False, "git is not installed or not available on PATH"

    result = subprocess.run(
        [git_executable, "clone", "--depth", "1", url, str(destination)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""

    combined = (result.stderr or result.stdout or "").strip()
    lowered = combined.lower()
    if "repository not found" in lowered or "not found" in lowered:
        return False, "repository URL not found or not accessible"
    if "authentication" in lowered or "permission denied" in lowered or "could not read" in lowered:
        return False, "authentication/credentials error while cloning repository"
    return False, combined or "git clone failed"


def _resolve_import_target(target_path_arg: str | None) -> Path:
    """Resolve the import target path, defaulting to the current directory."""
    if target_path_arg is None:
        return Path.cwd().resolve()
    return Path(target_path_arg).expanduser().resolve()


def _is_openclaw_workspace_candidate(target_path: Path) -> bool:
    if not target_path.exists() or not target_path.is_dir():
        return False
    strong_signals = [
        target_path / "openclaw.json",
        target_path / "AGENTS.md",
        target_path / "SOUL.md",
    ]
    if any(path.exists() for path in strong_signals):
        return True
    return (target_path / "skills").is_dir() and (target_path / "memory").is_dir()


def _openclaw_agent_id_from_workspace(workspace_path: Path) -> str:
    name = workspace_path.name
    if name.startswith("workspace-"):
        name = name[len("workspace-") :]
    return name or workspace_path.name


def _register_openclaw_workspace(agent_id: str, workspace_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["openclaw", "agents", "add", agent_id, "--workspace", str(workspace_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr or result.stdout or "").strip()
    return False, detail or "openclaw agents add failed"


def _openclaw_agent_registered(agent_id: str) -> tuple[bool, str | None]:
    result = subprocess.run(
        ["openclaw", "agents", "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, detail or "openclaw agents list failed"

    try:
        payload = json.loads(result.stdout.strip() or "[]")
    except json.JSONDecodeError:
        return False, "openclaw agents list produced non-JSON output"

    if not isinstance(payload, list):
        return False, "openclaw agents list JSON payload was not a list"

    for item in payload:
        if isinstance(item, dict) and str(item.get("id", "")) == agent_id:
            return True, None
        if isinstance(item, str) and item == agent_id:
            return True, None
    return False, None


_OPENCLAW_REQUIRED_PATHS = ("SOUL.md", "IDENTITY.md", "memory", "skills")
_OPENCLAW_EXCLUDED_DIRS = {".git", ".openclaw", ".clawhub", "node_modules", ".venv"}


def _missing_openclaw_required_paths(workspace_path: Path) -> list[str]:
    missing: list[str] = []
    for relative in _OPENCLAW_REQUIRED_PATHS:
        candidate = workspace_path / relative
        if not candidate.exists():
            missing.append(relative)
    return missing


def _iter_openclaw_workspace_copy_pairs(
    source_workspace: Path,
    target_path: Path,
) -> list[tuple[Path, Path]]:
    copy_pairs: list[tuple[Path, Path]] = []
    for root, dirs, files in os.walk(source_workspace, followlinks=False):
        root_path = Path(root)
        rel = root_path.relative_to(source_workspace)
        dirs[:] = [
            name
            for name in dirs
            if name not in _OPENCLAW_EXCLUDED_DIRS and not (root_path / name).is_symlink()
        ]

        for filename in files:
            source_file = root_path / filename
            if source_file.is_symlink():
                continue
            destination_file = target_path / rel / filename
            copy_pairs.append((source_file, destination_file))

    return copy_pairs


def _copy_openclaw_workspace_contents(
    source_workspace: Path,
    target_path: Path,
    *,
    force: bool,
) -> int:
    copy_pairs = _iter_openclaw_workspace_copy_pairs(source_workspace, target_path)
    if not force:
        colliding_paths = [
            str(destination_file) for _, destination_file in copy_pairs if destination_file.exists()
        ]
        if colliding_paths:
            collision_preview = ", ".join(colliding_paths[:5])
            if len(colliding_paths) > 5:
                collision_preview += ", ..."
            raise FileExistsError(
                "Refusing to overwrite existing files in target path: "
                f"{collision_preview}"
            )

    copied_file_count = 0
    for source_file, destination_file in copy_pairs:
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination_file)
        copied_file_count += 1
    return copied_file_count


def _import_from_openclaw_workspace_source(
    *,
    target_path_arg: str,
    workspace_path_arg: str,
    force: bool,
) -> int:
    target_path = _resolve_import_target(target_path_arg)
    workspace_path = _resolve_import_target(workspace_path_arg)

    if not workspace_path.exists():
        _emit_import_error(
            f"OpenClaw workspace source does not exist: {workspace_path}",
            "Provide an existing OpenClaw workspace path containing SOUL.md/IDENTITY.md/memory/skills.",
        )
        return 1

    if not workspace_path.is_dir():
        _emit_import_error(
            f"OpenClaw workspace source must be a directory: {workspace_path}",
            "Provide a directory path for the workspace source.",
        )
        return 1

    missing_paths = _missing_openclaw_required_paths(workspace_path)
    if missing_paths:
        _emit_import_error(
            f"OpenClaw workspace source is missing required path(s): {', '.join(missing_paths)}",
            "Ensure the source workspace contains SOUL.md, IDENTITY.md, memory/, and skills/.",
        )
        return 1

    if target_path.exists() and not target_path.is_dir():
        _emit_import_error(
            f"OpenClaw import target must be a directory: {target_path}",
            "Provide a directory target path (or a new directory path) for imported workspace content.",
        )
        return 1
    target_path.mkdir(parents=True, exist_ok=True)
    if not force and any(target_path.iterdir()):
        _emit_import_error(
            f"OpenClaw import target is not empty: {target_path}",
            "Use an empty target directory or pass --force to allow overwriting collisions.",
        )
        return 1

    manifest_path = target_path / "kinnoo.yaml"
    if manifest_path.exists() and not force:
        _emit_import_error(
            "Import aborted: kinnoo.yaml already exists. Use --force to explicitly override and overwrite.",
            "Re-run with '--force' only if you intend to replace the existing kinnoo.yaml.",
        )
        return 1

    try:
        copied_files = _copy_openclaw_workspace_contents(
            workspace_path,
            target_path,
            force=force,
        )
    except FileExistsError as exc:
        _emit_import_error(
            str(exc),
            "Use --force if you explicitly want to overwrite colliding files.",
        )
        return 1
    if copied_files <= 0:
        _emit_import_error(
            "OpenClaw workspace source did not contain any copyable files.",
            "Verify source workspace content and exclusion paths before retrying import.",
        )
        return 1

    report = analyze_project(target_path).as_dict()
    inferred = report.get("inferred", {}) if isinstance(report.get("inferred"), dict) else {}
    confidence = report.get("confidence", {}) if isinstance(report.get("confidence"), dict) else {}
    inferred["framework"] = "openclaw"
    confidence["framework"] = {
        "score": 0.98,
        "evidence": "Explicitly selected openclaw source import flow via '--from openclaw'.",
    }
    report["inferred"] = inferred
    report["confidence"] = confidence

    manifest_text = _build_manifest_from_analysis(target_path, report, session=PromptSession())
    is_manifest_valid, manifest_errors = _validate_manifest_text_before_write(target_path, manifest_text)
    if not is_manifest_valid:
        _emit_import_error(
            "Generated kinnoo.yaml failed validation; OpenClaw import aborted before write.",
            "Ensure copied workspace includes a valid executable entrypoint and required runtime metadata.",
        )
        for error in manifest_errors:
            print(f"  - {error}")
        return 1

    _write_manifest_in_place(target_path, manifest_text, force=force)
    _print_manifest_validation_and_guidance(manifest_path, report, entrypoint_warning=None)
    print(style_text(f"Imported OpenClaw workspace in-place: {target_path}", color="green", bold=True))
    return 0


def _build_manifest_text(target_path: Path) -> str:
    """Return a deterministic baseline manifest for in-place import writes."""
    agent_name = target_path.name.replace("_", "-").lower() or "imported-agent"
    manifest = DEFAULT_IMPORTED_MANIFEST.replace("name: imported-agent", f"name: {agent_name}")
    return manifest


def _prompt_with_default(prompt: str, default: str, session: PromptSession | None = None) -> str:
    """Read a prompt value and raise when wizard interaction is interrupted."""
    try:
        value = input(prompt)
    except EOFError as exc:
        # In non-interactive automation, allow default-driven progression.
        if session and session.non_interactive:
            return default
        raise ImportWizardInterrupted("EOF") from exc
    except KeyboardInterrupt as exc:
        raise ImportWizardInterrupted("CTRL_C") from exc
    if session:
        session.answers_received += 1
    value = value.strip()
    return value if value else default


def _emit_import_error(message: str, remediation: str | None = None) -> None:
    print(style_text(f"Error: {message}", color="red"))
    if remediation:
        print(f"Remediation: {remediation}")


def _show_detected_values(report: dict[str, Any]) -> None:
    inferred = report.get("inferred", {})
    confidence = report.get("confidence", {})
    print(style_text("Detected values from analyzer:", color="cyan", bold=True))
    for key in ("entrypoint", "runtime", "framework", "model", "dependencies", "inputs", "outputs", "env_vars", "services"):
        print(f"  - {key}: {inferred.get(key)}")

    framework_confidence = confidence.get("framework")
    if isinstance(framework_confidence, dict):
        score = framework_confidence.get("score", 0.0)
        evidence = framework_confidence.get("evidence", "")
        print("Framework confidence metadata:")
        print(f"  - score: {score:.2f}" if isinstance(score, (int, float)) else f"  - score: {score}")
        if isinstance(evidence, str) and evidence:
            print(f"  - evidence: {evidence}")


def _get_confidence(report: dict[str, Any], field_name: str) -> float:
    confidence_meta = report.get("confidence", {}).get(field_name, {})
    score = confidence_meta.get("score", 0.0)
    try:
        return float(score)
    except (TypeError, ValueError):
        return 0.0


def _should_prompt_field(report: dict[str, Any], field_name: str, current_value: Any) -> bool:
    if current_value in (None, ""):
        return True
    if isinstance(current_value, list) and not current_value:
        # Empty inferred list means "none detected" and should not force prompts.
        return False
    return _get_confidence(report, field_name) < 0.6


def _prompt_yes_no(prompt: str, default: bool, session: PromptSession | None = None) -> bool:
    default_str = "y" if default else "n"
    value = _prompt_with_default(prompt, default_str, session=session).strip().lower()
    if value in {"y", "yes"}:
        return True
    if value in {"n", "no"}:
        return False
    return default


def _map_service_type(raw_type: str) -> str:
    lowered = raw_type.strip().lower()
    mapping = {
        "http": "api",
        "https": "api",
        "api": "api",
        "http-api": "api",
        "postgres": "database",
        "postgresql": "database",
        "database": "database",
        "redis": "database",
        "mongodb": "database",
        "postgres": "database",
        "vector-db": "vector-db",
        "mcp-server": "mcp-server",
        "local-process": "local-process",
        "process": "local-process",
    }
    return mapping.get(lowered, "api")


def _normalize_inferred_services(services_value: Any) -> list[dict[str, Any]]:
    if not isinstance(services_value, list):
        return []

    normalized: list[dict[str, Any]] = []
    # Normalize analyzer-specific payloads to manifest-valid service objects.
    for index, service in enumerate(services_value, start=1):
        if not isinstance(service, dict):
            continue
        service_type = _map_service_type(str(service.get("type", "api")))
        endpoint = service.get("endpoint") if isinstance(service.get("endpoint"), str) else None
        service_name = service.get("name") if isinstance(service.get("name"), str) else f"service-{index}"
        if endpoint:
            parsed = urlsplit(endpoint)
            if service_name.startswith("service-") and parsed.hostname:
                service_name = parsed.hostname.replace(".", "-")

        normalized_service: dict[str, Any] = {
            "name": service_name,
            "type": service_type,
        }
        if service_type == "api" and endpoint:
            normalized_service["health_check"] = {
                "method": "http",
                "url": endpoint,
            }
        normalized.append(normalized_service)

    return normalized


def _prompt_services(default_services: list[dict[str, Any]], session: PromptSession | None = None) -> list[dict[str, Any]]:
    raw = _prompt_with_default(
        "Provide services (comma-separated service types, blank for none): ",
        "",
        session=session,
    )
    if not raw.strip():
        return default_services

    services: list[dict[str, Any]] = []
    for index, token in enumerate(raw.split(","), start=1):
        cleaned = token.strip()
        if not cleaned:
            continue
        services.append(
            {
                "name": f"service-{index}",
                "type": _map_service_type(cleaned),
            }
        )
    return services


def _prompt_permissions(session: PromptSession | None = None) -> dict[str, Any]:
    read_only = _prompt_yes_no("permissions.read_only? [Y/n]: ", True, session=session)
    allow_write = _prompt_yes_no("permissions.allow_write? [y/N]: ", False, session=session)
    allow_create = _prompt_yes_no("permissions.allow_create? [y/N]: ", False, session=session)
    allowed_paths_raw = _prompt_with_default(
        "permissions.allowed_paths (comma-separated, blank for none): ",
        "",
        session=session,
    )
    allowed_paths = [value.strip() for value in allowed_paths_raw.split(",") if value.strip()]
    return {
        "read_only": read_only,
        "allow_write": allow_write,
        "allow_create": allow_create,
        "allowed_paths": allowed_paths,
    }


def _extract_entrypoint_from_manifest(manifest_text: str) -> str | None:
    for line in manifest_text.splitlines():
        if line.startswith("entrypoint:"):
            value = line.split(":", 1)[1].strip()
            return value or None
    return None


def _replace_manifest_entrypoint(manifest_text: str, new_entrypoint: str) -> str:
    lines = manifest_text.splitlines()
    replaced: list[str] = []
    for line in lines:
        if line.startswith("entrypoint:"):
            replaced.append(f"entrypoint: {new_entrypoint}")
        else:
            replaced.append(line)
    return "\n".join(replaced) + "\n"


def _assess_entrypoint_contract(target_path: Path, entrypoint: str | None) -> str | None:
    if not entrypoint:
        return "Entrypoint is missing in generated manifest values."

    entrypoint_path = (target_path / entrypoint).resolve()
    if not entrypoint_path.exists():
        return f"Entrypoint '{entrypoint}' does not exist in target project."
    if entrypoint_path.suffix != ".py":
        return f"Entrypoint '{entrypoint}' is not a Python file."

    try:
        source = entrypoint_path.read_text(encoding="utf-8")
    except OSError:
        return f"Entrypoint '{entrypoint}' could not be inspected for compatibility."

    # This is intentionally heuristic and warning-only for migration safety.
    has_main_guard = "__name__" in source and "__main__" in source
    has_sys_argv = "sys.argv" in source
    if has_main_guard and has_sys_argv:
        return None

    return (
        f"Entrypoint '{entrypoint}' may not follow kinnoo one-shot CLI contract "
        "(expected __main__ guard and sys.argv input handling)."
    )


def _generate_entrypoint_wrapper(target_path: Path, original_entrypoint: str) -> str:
    wrapper_name = "kinnoo_wrapper.py"
    wrapper_path = target_path / wrapper_name
    if wrapper_path.exists():
        raise FileExistsError(
            "Optional wrapper generation aborted: kinnoo_wrapper.py already exists."
        )

    # Wrapper forwards argv and exit code so legacy scripts remain runnable.
    wrapper_source = (
        "import subprocess\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        "if __name__ == '__main__':\n"
        f"    target = Path(__file__).with_name({original_entrypoint!r})\n"
        "    result = subprocess.run([sys.executable, str(target), *sys.argv[1:]])\n"
        "    raise SystemExit(result.returncode)\n"
    )
    wrapper_path.write_text(wrapper_source, encoding="utf-8")
    return wrapper_name


def _load_wrapper_template(template_name: str) -> str:
    template_path = Path(__file__).resolve().parent / "wrapper_templates" / template_name
    return template_path.read_text(encoding="utf-8")


def _render_wrapper_template(template_text: str, agent_module: str, agent_class: str) -> str:
    return (
        template_text
        .replace("{{agent_module}}", agent_module)
        .replace("{{agent_class}}", agent_class)
    )


def _generate_class_wrapper_entrypoint(
    target_path: Path,
    *,
    framework: str | None,
    agent_module: str,
    agent_class: str,
    force: bool,
) -> str:
    wrapper_name = "run.py"
    wrapper_path = target_path / wrapper_name
    if wrapper_path.exists() and not force:
        raise FileExistsError(
            "Class-wrapper generation aborted: run.py already exists. Use --force to overwrite."
        )

    template_name = "langchain_wrapper.py.j2"
    if framework == "openai-agents":
        template_name = "openai_agents_wrapper.py.j2"

    template_text = _load_wrapper_template(template_name)
    wrapper_source = _render_wrapper_template(template_text, agent_module, agent_class)
    wrapper_path.write_text(wrapper_source, encoding="utf-8")
    return wrapper_name


def _build_manifest_from_analysis(
    target_path: Path,
    report: dict[str, Any],
    *,
    session: PromptSession | None = None,
) -> str:
    inferred = report.get("inferred", {})

    name = target_path.name.replace("_", "-").lower() or "imported-agent"
    entrypoint = inferred.get("entrypoint") or "run.py"

    runtime = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
    runtime_language = runtime.get("language") or "python"
    runtime_version = runtime.get("version") or ">=3.10"
    runtime_type = runtime.get("type")
    runtime_package_manager = runtime.get("package_manager") if isinstance(runtime.get("package_manager"), str) else None
    runtime_run_command = runtime.get("run_command") if isinstance(runtime.get("run_command"), str) else None

    framework = inferred.get("framework")
    model = inferred.get("model") if isinstance(inferred.get("model"), str) else None
    dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    env_vars = inferred.get("env_vars") if isinstance(inferred.get("env_vars"), list) else []
    services = _normalize_inferred_services(inferred.get("services"))
    permissions: dict[str, Any] | None = None
    inferred_input_type = inferred.get("inputs") if isinstance(inferred.get("inputs"), str) else "string"
    inferred_deps_type = inferred.get("deps_type")
    inferred_inputs_required = inferred.get("inputs_required")
    inferred_output_type = inferred.get("outputs") if isinstance(inferred.get("outputs"), str) else "string"
    allowed_io_types = {"text", "string", "file", "json"}
    if inferred_input_type not in allowed_io_types:
        inferred_input_type = "string"
    if inferred_output_type not in allowed_io_types:
        inferred_output_type = "string"
    if isinstance(inferred_deps_type, dict) and inferred_deps_type.get("class_name"):
        inferred_input_type = "json"
    if not isinstance(inferred_inputs_required, bool):
        inferred_inputs_required = True

    # If analyzer inferred an entrypoint and user confirmed detected values,
    # keep it without re-prompting even when confidence is low.
    if not isinstance(inferred.get("entrypoint"), str) or not str(inferred.get("entrypoint")).strip():
        entrypoint = _prompt_with_default("Provide value for entrypoint [run.py]: ", "run.py", session=session)

    if _should_prompt_field(report, "runtime", runtime_type):
        runtime_type = _prompt_with_default(
            "Provide value for runtime.type [one-shot]: ",
            "one-shot",
            session=session,
        )
    elif runtime_type is None:
        runtime_type = "one-shot"

    if _should_prompt_field(report, "framework", framework):
        framework_input = _prompt_with_default(
            "Provide value for framework (optional): ",
            "",
            session=session,
        )
        framework = framework_input or None

    if framework in {"streamlit", "gradio"}:
        runtime_type = "daemon"
        inferred_inputs_required = False
    if framework == "streamlit":
        runtime_run_command = f"streamlit run {entrypoint}"

    manifest_type: str | None = None
    if framework == "openclaw":
        manifest_type = "openclaw-skill"
        openclaw_hints = infer_openclaw_project_hints(target_path)
        hinted_runtime = openclaw_hints.get("runtime")
        if isinstance(hinted_runtime, dict):
            runtime_language = str(hinted_runtime.get("language", runtime_language))
            runtime_type = str(hinted_runtime.get("type", runtime_type or "daemon"))
            runtime_version = str(hinted_runtime.get("version", runtime_version))
            package_manager_hint = hinted_runtime.get("package_manager")
            if isinstance(package_manager_hint, str) and package_manager_hint:
                runtime_package_manager = package_manager_hint

    if _should_prompt_field(report, "services", services):
        services = _prompt_services(services, session=session)

    runtime_prompt_needed = _should_prompt_field(report, "runtime", runtime.get("type"))
    if runtime_type == "mcp-server" and runtime_prompt_needed:
        if _prompt_yes_no("Configure permissions for mcp-server? [y/N]: ", False, session=session):
            permissions = _prompt_permissions(session=session)

    dependency_lines = "\n".join(f"  - {item}" for item in dependencies)
    if not dependency_lines:
        dependency_lines = "  []"

    env_lines = "\n".join(f"  - {item}" for item in env_vars)
    manifest_lines = [
        f"name: {name}",
        "version: 1.0.0",
        f"entrypoint: {entrypoint}",
        "runtime:",
        f"  type: {runtime_type}",
        f"  language: {runtime_language}",
        f"  version: \"{runtime_version}\"",
        "dependencies:",
        dependency_lines,
        "inputs:",
        f"  type: {inferred_input_type}",
        f"  required: {str(inferred_inputs_required).lower()}",
        "outputs:",
        f"  type: {inferred_output_type}",
    ]

    if runtime_package_manager:
        manifest_lines.insert(6, f"  package_manager: {runtime_package_manager}")
    if runtime_run_command and runtime_run_command.strip():
        dependencies_index = manifest_lines.index("dependencies:")
        manifest_lines.insert(dependencies_index, f"  run_command: {runtime_run_command.strip()}")

    if framework:
        manifest_lines.append(f"framework: {framework}")

    if manifest_type:
        manifest_lines.append(f"type: {manifest_type}")

    if model and model.strip():
        manifest_lines.append(f"model: {model.strip()}")

    if env_lines:
        manifest_lines.append("env_vars:")
        manifest_lines.append(env_lines)

    if services:
        manifest_lines.append("services:")
        for service in services:
            manifest_lines.append(f"  - name: {service['name']}")
            manifest_lines.append(f"    type: {service['type']}")
            health_check = service.get("health_check")
            if isinstance(health_check, dict):
                method = health_check.get("method")
                if method:
                    manifest_lines.append("    health_check:")
                    manifest_lines.append(f"      method: {method}")
                    if method == "http" and health_check.get("url"):
                        manifest_lines.append(f"      url: {health_check['url']}")

    if permissions:
        manifest_lines.append("permissions:")
        manifest_lines.append(f"  read_only: {str(permissions['read_only']).lower()}")
        manifest_lines.append(f"  allow_write: {str(permissions['allow_write']).lower()}")
        manifest_lines.append(f"  allow_create: {str(permissions['allow_create']).lower()}")
        manifest_lines.append("  allowed_paths:")
        for path in permissions["allowed_paths"]:
            manifest_lines.append(f"    - {path}")

    return "\n".join(manifest_lines) + "\n"


def _write_manifest_in_place(target_path: Path, manifest_text: str, *, force: bool = False) -> None:
    manifest_path = target_path / "kinnoo.yaml"
    if manifest_path.exists() and not force:
        raise FileExistsError(
            "Import aborted: kinnoo.yaml already exists. "
            "Use an explicit override path in a later import step before overwriting."
        )

    wrote_manifest = False
    try:
        manifest_path.write_text(manifest_text, encoding="utf-8")
        wrote_manifest = True

        # Test-only failure injection to prove rollback safety for task164.
        if os.getenv("KINNOO_IMPORT_FAIL_AFTER_WRITE") == "1":
            raise RuntimeError("Simulated import failure after manifest write")
    except Exception:
        if wrote_manifest and manifest_path.exists():
            manifest_path.unlink()
        raise


def _normalize_dependency_list(raw_dependencies: Any) -> list[str]:
    """Normalize inferred dependency values to deterministic requirements lines."""
    if not isinstance(raw_dependencies, list):
        return []

    normalized: list[str] = []
    for value in raw_dependencies:
        if not isinstance(value, str):
            continue
        candidate = value.strip()
        if not candidate:
            continue
        normalized.append(candidate)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(normalized))


def _attempt_uv_requirements_export(target_path: Path) -> tuple[bool, str | None]:
    """Try generating requirements text via uv export for Python projects."""
    if shutil.which("uv") is None:
        return False, "uv executable not found"

    command = [
        "uv",
        "export",
        "--directory",
        str(target_path),
        "--format",
        "requirements-txt",
        "--no-hashes",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "uv export failed").strip()
        return False, detail

    exported = result.stdout.strip()
    if exported:
        return True, exported + "\n"
    return True, ""


def _ensure_import_requirements_file(
    target_path: Path,
    *,
    inferred_dependencies: Any,
    runtime_language: str,
    session: PromptSession | None = None,
) -> bool:
    """Create requirements.txt for imported Python projects when missing.

    Returns True when a new requirements.txt file is created by this function.
    """
    requirements_path = target_path / "requirements.txt"
    if requirements_path.exists():
        return False

    if runtime_language.strip().lower() != "python":
        return False

    dependencies = _normalize_dependency_list(inferred_dependencies)
    if dependencies:
        should_generate = _prompt_yes_no(
            "No requirements.txt found. Generate one from inferred imports? [Y/n]: ",
            True,
            session=session,
        )
        if not should_generate:
            print("Skipped requirements.txt generation by user choice.")
            return False
        requirements_path.write_text("\n".join(dependencies) + "\n", encoding="utf-8")
        print("Generated requirements.txt from analyzer-detected dependencies.")
        return True

    exported_ok, exported_text_or_error = _attempt_uv_requirements_export(target_path)
    if exported_ok:
        requirements_path.write_text(exported_text_or_error or "", encoding="utf-8")
        print("Generated requirements.txt via uv export.")
        return True

    requirements_path.write_text("", encoding="utf-8")
    print(
        "Generated empty requirements.txt (no Python dependencies detected). "
        f"uv export was unavailable or failed: {exported_text_or_error}"
    )
    return True


def _collect_unresolved_todo_guidance(
    report: dict[str, Any],
    entrypoint_warning: str | None,
) -> list[str]:
    guidance: list[str] = []

    if _get_confidence(report, "entrypoint") < 0.6:
        guidance.append("Verify 'entrypoint' points to an existing executable script in the project root.")

    if _get_confidence(report, "runtime") < 0.6:
        guidance.append("Verify runtime fields (runtime.type, runtime.language, runtime.version) before first run.")

    inferred_framework = report.get("inferred", {}).get("framework")
    framework_confidence = _get_confidence(report, "framework")
    if inferred_framework is None and framework_confidence > 0.0:
        guidance.append(
            "Framework inference is ambiguous; set 'framework' explicitly if this project depends on one."
        )

    if entrypoint_warning:
        guidance.append(entrypoint_warning)

    adapter_meta = report.get("adapter")
    if isinstance(adapter_meta, dict):
        unresolved = adapter_meta.get("unresolved_guidance")
        if isinstance(unresolved, list):
            for item in unresolved:
                if isinstance(item, str) and item.strip():
                    guidance.append(item.strip())

    # Preserve deterministic order while removing duplicates.
    return list(dict.fromkeys(guidance))


def _apply_framework_adapter(
    target_path: Path,
    report: dict[str, Any],
    framework_from: str,
) -> tuple[dict[str, Any], list[str], str | None]:
    adapter_map = {
        "langchain": apply_langchain_adapter,
        "langgraph": apply_langgraph_adapter,
        "openai": apply_openai_adapter,
    }
    adapter = adapter_map[framework_from]
    adapter_result = adapter(target_path, report)
    minimum_coverage = adapter_minimum_coverage(framework_from)
    if not adapter_result.detected or adapter_result.coverage_score < minimum_coverage:
        fallback_message = (
            f"[kinnoo import] {framework_from} adapter coverage is insufficient "
            f"(score={adapter_result.coverage_score:.2f}, required>={minimum_coverage:.2f}); "
            "falling back to generic analyzer output."
        )
        return report, [], fallback_message

    combined_guidance = adapter_default_unresolved_guidance(framework_from)
    for item in adapter_result.unresolved_guidance:
        if item not in combined_guidance:
            combined_guidance.append(item)

    adapter_result = type(adapter_result)(
        framework=adapter_result.framework,
        detected=adapter_result.detected,
        coverage_score=adapter_result.coverage_score,
        inferred_overrides=adapter_result.inferred_overrides,
        confidence_overrides=adapter_result.confidence_overrides,
        warnings=adapter_result.warnings,
        unresolved_guidance=combined_guidance,
    )

    merged_report = merge_adapter_into_report(
        base_report=report,
        adapter_result=adapter_result,
    )
    adapter_banner = (
        f"[kinnoo import] Applied {framework_from} adapter "
        f"(coverage={adapter_result.coverage_score:.2f})."
    )
    return merged_report, list(adapter_result.unresolved_guidance), adapter_banner


def _print_manifest_validation_and_guidance(
    manifest_path: Path,
    report: dict[str, Any],
    entrypoint_warning: str | None,
) -> None:
    is_valid, errors = validate_manifest(str(manifest_path))
    if is_valid:
        print(style_text("Generated manifest validation: PASS", color="green", bold=True))
    else:
        print(style_text("Generated manifest validation: WARNING", color="yellow", bold=True))
        for error in errors:
            print(f"  - {error}")

    unresolved_guidance = _collect_unresolved_todo_guidance(report, entrypoint_warning)
    if is_valid and not unresolved_guidance:
        return

    print(style_text("TODO guidance:", color="yellow", bold=True))
    for item in unresolved_guidance:
        print(f"  - {item}")

    if not is_valid:
        print("  - Update kinnoo.yaml to resolve validation warnings before packaging or distribution.")


def _validate_manifest_text_before_write(
    target_path: Path,
    manifest_text: str,
) -> tuple[bool, list[str]]:
    try:
        parsed = yaml.safe_load(manifest_text)
    except yaml.YAMLError as exc:
        return False, [f"Generated manifest YAML parse error: {exc}"]

    # Test-only failure injection hook for import validation-gate regression coverage.
    if os.getenv("KINNOO_IMPORT_FORCE_INVALID_MANIFEST") == "1" and os.getenv("PYTEST_CURRENT_TEST"):
        if not isinstance(parsed, dict):
            parsed = {}
        parsed["version"] = "invalid-version"

    if not isinstance(parsed, dict):
        return False, ["Generated manifest must be a YAML mapping (dict) at the top level."]

    is_valid, errors = validate_manifest_data(parsed, manifest_root=target_path)
    if is_valid:
        return True, []

    non_blocking_prefixes = (
        "Declared entrypoint path not found:",
    )
    blocking_errors = [
        error for error in errors
        if not any(error.startswith(prefix) for prefix in non_blocking_prefixes)
    ]
    if not blocking_errors:
        return True, errors
    return False, errors


def import_agent(
    target_path_arg: str | None,
    import_path_arg: str | None = None,
    *,
    force: bool = False,
    framework_from: str | None = None,
) -> int:
    """Import a project in-place by writing kinnoo.yaml safely into target root."""
    if framework_from == "openclaw":
        if target_path_arg is None or import_path_arg is None:
            _emit_import_error(
                "OpenClaw source import requires target and workspace paths.",
                "Usage: kinnoo import --from openclaw <target> <workspace-path>",
            )
            return 1
        return _import_from_openclaw_workspace_source(
            target_path_arg=target_path_arg,
            workspace_path_arg=import_path_arg,
            force=force,
        )

    target_arg = target_path_arg
    if target_arg is None:
        target_arg = str(Path.cwd())

    if import_path_arg is not None and not is_github_url(target_arg):
        _emit_import_error(
            "import-path positional argument is only supported for GitHub URL imports.",
            "Use 'kinnoo import <github-url> <import-path>' or remove the second positional argument.",
        )
        print("Usage: kinnoo import [target] [import-path] [--force]")
        return 1

    target_path: Path
    if is_github_url(target_arg):
        repo_url = target_arg.strip()
        if import_path_arg is None:
            destination = Path.cwd() / github_repo_dir_name(repo_url)
        else:
            destination = Path(import_path_arg).expanduser().resolve()

        if destination.exists():
            _emit_import_error(
                f"import target directory already exists: {destination}",
                "Choose a new destination path or remove the existing directory first.",
            )
            return 1

        cloned, clone_error = clone_github_repo(repo_url, destination)
        if not cloned:
            _emit_import_error(
                f"failed to download/clone agent code from GitHub URL '{repo_url}': {clone_error}",
                "Verify repository URL and access permissions, then retry.",
            )
            return 1

        target_path = destination
    else:
        target_path = _resolve_import_target(target_arg)

    manifest_path = target_path / "kinnoo.yaml"
    generated_wrapper_path: Path | None = None
    created_requirements_file = False

    if not target_path.exists():
        _emit_import_error(
            f"import target does not exist: {target_path}",
            "Create the target directory or provide an existing project path.",
        )
        return 1

    if not target_path.is_dir():
        _emit_import_error(
            f"import target must be a directory: {target_path}",
            "Provide a directory path instead of a file path.",
        )
        return 1

    if manifest_path.exists() and not force:
        _emit_import_error(
            "Import aborted: kinnoo.yaml already exists. Use --force to explicitly override and overwrite.",
            "Re-run with '--force' only if you intend to replace the existing kinnoo.yaml.",
        )
        return 1

    if _is_openclaw_workspace_candidate(target_path):
        preflight_result = run_openclaw_preflight_for_command("import")
        if not preflight_result.ok:
            print(style_text(f"Error: {preflight_result.message}", color="red"))
            return 1

        openclaw_home = Path.home() / ".openclaw"
        openclaw_workspace_root = openclaw_home.resolve()
        target_resolved = target_path.resolve()
        in_openclaw_workspace = (
            target_resolved.parent == openclaw_workspace_root
            and target_resolved.name.startswith("workspace-")
        )

        if not in_openclaw_workspace:
            session = PromptSession()
            should_copy = _prompt_yes_no(
                f"Copy OpenClaw workspace into {openclaw_workspace_root}? [Y/n]: ",
                True,
                session=session,
            )
            if not should_copy:
                print(style_text("Error: import cancelled: external OpenClaw workspace was not copied", color="red"))
                return 1

            destination = openclaw_workspace_root / f"workspace-{target_path.name}"
            if destination.exists():
                print(style_text(f"Error: import target directory already exists: {destination}", color="red"))
                return 1

            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target_path, destination)
            target_path = destination
            manifest_path = target_path / "kinnoo.yaml"

            copied_agent_id = _openclaw_agent_id_from_workspace(target_path)
            registered, register_error = _register_openclaw_workspace(copied_agent_id, target_path)
            if not registered:
                print(style_text(f"Error: failed to register OpenClaw workspace: {register_error}", color="red"))
                return 1
        else:
            agent_id = _openclaw_agent_id_from_workspace(target_path)
            already_registered, registration_error = _openclaw_agent_registered(agent_id)
            if registration_error is not None:
                print(style_text(f"Error: failed to query OpenClaw registrations: {registration_error}", color="red"))
                return 1
            if not already_registered:
                registered, register_error = _register_openclaw_workspace(agent_id, target_path)
                if not registered:
                    print(style_text(f"Error: failed to register OpenClaw workspace: {register_error}", color="red"))
                    return 1

    session = PromptSession()
    entrypoint_warning: str | None = None
    report_for_manifest: dict[str, Any] | None = None

    try:
        report = analyze_project(target_path).as_dict()
        adapter_guidance: list[str] = []
        if framework_from is not None:
            report, adapter_guidance, adapter_message = _apply_framework_adapter(
                target_path=target_path,
                report=report,
                framework_from=framework_from,
            )
            if adapter_message:
                print(adapter_message)
        report_for_manifest = report
        _show_detected_values(report)

        warning_messages = report.get("warnings", [])
        if warning_messages:
            print(style_text("Analyzer warnings:", color="yellow", bold=True))
            for warning in warning_messages:
                print(f"  - {warning}")

        confirmed = _prompt_with_default(
            "Proceed with detected values? [Y/n]: ",
            "y",
            session=session,
        ).lower()
        if confirmed not in {"y", "yes"}:
            print("Import cancelled by user.")
            return 1

        inferred = report.get("inferred", {})
        detected_entrypoint = inferred.get("entrypoint")
        if isinstance(detected_entrypoint, dict) and detected_entrypoint.get("entrypoint_type") == "class":
            agent_class = detected_entrypoint.get("agent_class")
            agent_module = detected_entrypoint.get("agent_module")
            if isinstance(agent_class, str) and isinstance(agent_module, str):
                if _prompt_yes_no(
                    "Generate class-based run.py wrapper entrypoint? [y/N]: ",
                    False,
                    session=session,
                ):
                    try:
                        wrapper_entrypoint = _generate_class_wrapper_entrypoint(
                            target_path,
                            framework=inferred.get("framework") if isinstance(inferred.get("framework"), str) else None,
                            agent_module=agent_module,
                            agent_class=agent_class,
                            force=force,
                        )
                        generated_wrapper_path = target_path / wrapper_entrypoint
                    except Exception as exc:
                        print(style_text(f"Error: class-wrapper generation failed: {exc}", color="red"))
                        return 1

                    manifest_inferred = dict(inferred)
                    manifest_inferred["entrypoint"] = wrapper_entrypoint
                    report_for_manifest = dict(report)
                    report_for_manifest["inferred"] = manifest_inferred

        manifest_text = _build_manifest_from_analysis(target_path, report_for_manifest or report, session=session)
        selected_entrypoint = _extract_entrypoint_from_manifest(manifest_text)
        entrypoint_warning = _assess_entrypoint_contract(target_path, selected_entrypoint)
        if entrypoint_warning:
            print(f"Entrypoint compatibility warning: {entrypoint_warning}")
            wrapper_eligible = "may not follow kinnoo one-shot CLI contract" in entrypoint_warning
            if wrapper_eligible and _prompt_yes_no(
                "Generate optional wrapper entrypoint bridge? [y/N]: ",
                False,
                session=session,
            ):
                if not selected_entrypoint:
                    print("Error: cannot generate wrapper without a valid entrypoint.")
                    return 1
                try:
                    wrapper_entrypoint = _generate_entrypoint_wrapper(target_path, selected_entrypoint)
                    generated_wrapper_path = target_path / wrapper_entrypoint
                except Exception as exc:
                    print(style_text(f"Error: optional wrapper generation failed: {exc}", color="red"))
                    return 1
                manifest_text = _replace_manifest_entrypoint(manifest_text, wrapper_entrypoint)
    except ImportWizardInterrupted:
        if manifest_path.exists():
            manifest_path.unlink()
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print("Import interrupted (Ctrl+C/EOF). No partial artifacts were left behind.")
        return 1

    is_manifest_valid, manifest_errors = _validate_manifest_text_before_write(target_path, manifest_text)
    if not is_manifest_valid:
        _emit_import_error(
            "Generated kinnoo.yaml failed validation; import aborted before write.",
            "Review inferred values (entrypoint/runtime/framework/dependencies) and retry import.",
        )
        for error in manifest_errors:
            print(f"  - {error}")
        return 1

    try:
        _write_manifest_in_place(target_path, manifest_text, force=force)

        inferred = report.get("inferred", {})
        runtime_info = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
        runtime_language = str(runtime_info.get("language") or "python")
        created_requirements_file = _ensure_import_requirements_file(
            target_path,
            inferred_dependencies=inferred.get("dependencies"),
            runtime_language=runtime_language,
            session=session,
        )
    except FileExistsError as exc:
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print(style_text(f"Error: {exc}", color="red"))
        return 1
    except Exception as exc:
        if created_requirements_file:
            requirements_path = target_path / "requirements.txt"
            if requirements_path.exists():
                requirements_path.unlink()
        if manifest_path.exists():
            manifest_path.unlink()
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print(style_text(f"Error: import failed and rolled back partial artifacts: {exc}", color="red"))
        return 1

    if framework_from is not None and adapter_guidance:
        print(style_text("Adapter guidance:", color="yellow", bold=True))
        for item in adapter_guidance:
            print(f"  - {item}")

    _print_manifest_validation_and_guidance(
        manifest_path,
        report,
        entrypoint_warning,
    )

    print(style_text(f"Imported project in-place: {target_path}", color="green", bold=True))
    return 0
