"""Project analyzer library for inferring manifest-relevant fields.

Feature27 task158 establishes a stable analyzer API and report contract.
Detector implementations are intentionally conservative at this stage and can
be extended by follow-up tasks without breaking API shape.
"""

from __future__ import annotations

import ast
import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Callable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


@dataclass(frozen=True)
class DetectorResult:
    """Single detector output value plus confidence/evidence metadata."""

    value: Any
    confidence: float
    evidence: str
    warning: str | None = None


@dataclass(frozen=True)
class AnalysisReport:
    """Stable analyzer report contract used by import/onboarding workflows."""

    inferred: dict[str, Any]
    confidence: dict[str, dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a dictionary representation with stable top-level keys."""
        return {
            "inferred": self.inferred,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


Detector = Callable[[Path], DetectorResult]


def _iter_python_files(project_dir: Path) -> list[Path]:
    return sorted(path for path in project_dir.rglob("*.py") if path.is_file())


def _iter_python_files_with_depth(project_dir: Path, *, max_depth: int) -> list[Path]:
    """Return python files up to max relative path depth from project root."""
    files: list[Path] = []
    for path in sorted(project_dir.rglob("*.py")):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(project_dir).parts
        except ValueError:
            continue
        # File depth measured by parent directories only.
        depth = len(relative_parts) - 1
        if depth <= max_depth:
            files.append(path)
    return files


def _iter_node_files_with_depth(project_dir: Path, *, max_depth: int) -> list[Path]:
    """Return JS/TS files up to max relative path depth from project root."""
    files: list[Path] = []
    valid_suffixes = {".js", ".mjs", ".cjs", ".ts", ".tsx"}
    ignored_segments = {"node_modules", ".git", ".venv", "dist", "build", "coverage"}

    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in valid_suffixes:
            continue
        try:
            relative_parts = path.relative_to(project_dir).parts
        except ValueError:
            continue

        if any(part in ignored_segments for part in relative_parts):
            continue

        depth = len(relative_parts) - 1
        if depth <= max_depth:
            files.append(path)

    return files


def _relative_path(project_dir: Path, file_path: Path) -> str:
    return file_path.relative_to(project_dir).as_posix()


def _has_main_guard(file_path: Path) -> bool:
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return "if __name__ == '__main__':" in source or "if __name__ == \"__main__\":" in source


def _load_package_json(project_dir: Path) -> dict[str, Any] | None:
    package_json_path = project_dir / "package.json"
    if not package_json_path.exists() or not package_json_path.is_file():
        return None

    try:
        payload = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _extract_entrypoint_from_start_script(start_script: str) -> str | None:
    try:
        tokens = shlex.split(start_script)
    except ValueError:
        return None

    for token in tokens:
        if token.startswith("-"):
            continue
        candidate = token.strip()
        if candidate.endswith((".js", ".mjs", ".cjs", ".ts", ".tsx")):
            return candidate
    return None


def _detect_node_entrypoint(project_dir: Path) -> tuple[str | None, str | None]:
    package_json = _load_package_json(project_dir)
    if not package_json:
        package_json = None

    if package_json is not None:
        main_value = package_json.get("main")
        if isinstance(main_value, str) and main_value.strip():
            return main_value.strip(), "Detected package.json main field."

        scripts = package_json.get("scripts")
        if isinstance(scripts, dict):
            start_value = scripts.get("start")
            if isinstance(start_value, str) and start_value.strip():
                entrypoint = _extract_entrypoint_from_start_script(start_value)
                if entrypoint:
                    return entrypoint, "Detected package.json scripts.start entrypoint command."

    conventional_root_candidates = [
        "src/entry.ts",
        "src/index.ts",
        "src/server.ts",
        "src/entry.js",
        "src/index.js",
        "src/server.js",
        "entry.ts",
        "index.ts",
        "server.ts",
        "entry.js",
        "index.js",
        "server.js",
        "boot.mjs",
    ]
    for candidate in conventional_root_candidates:
        if (project_dir / candidate).exists():
            return candidate, "Detected conventional Node.js entrypoint path."

    priority_filenames = [
        "boot.mjs",
        "entry.ts",
        "entry.mjs",
        "entry.js",
        "server.ts",
        "server.mjs",
        "server.js",
        "index.ts",
        "index.mjs",
        "index.js",
        "main.ts",
        "main.mjs",
        "main.js",
        "cli.ts",
        "cli.mjs",
        "cli.js",
    ]
    priority_rank = {name: index for index, name in enumerate(priority_filenames)}
    conventional_dirs = {"src", "server", "bridge", "app", "cli", "bin", "daemon", "gateway"}

    node_files = _iter_node_files_with_depth(project_dir, max_depth=6)
    candidates = [
        path for path in node_files if path.name.lower() in priority_rank
    ]
    if candidates:
        selected = min(
            candidates,
            key=lambda path: (
                priority_rank[path.name.lower()],
                0 if any(part.lower() in conventional_dirs for part in path.relative_to(project_dir).parts[:-1]) else 1,
                len(path.relative_to(project_dir).parts) - 1,
                _relative_path(project_dir, path),
            ),
        )
        selected_entrypoint = _relative_path(project_dir, selected)
        return selected_entrypoint, (
            "Detected conventional Node.js/TS entrypoint candidate from nested project layout: "
            f"{selected_entrypoint}."
        )

    return None, None


def _entrypoint_candidate_score(project_dir: Path, file_path: Path, *, has_main_guard: bool) -> tuple[int, int, int, str]:
    """Score entrypoint candidates: guard, conventional dir, then shallower depth."""
    conventional_dirs = {"src", "source", "app", "backend", "python-backend", "lambda", "lib"}
    relative = file_path.relative_to(project_dir)
    parent_parts = [part.lower() for part in relative.parts[:-1]]
    filename = relative.name.lower()

    conventional_boost = 0
    if any(part in conventional_dirs for part in parent_parts):
        conventional_boost = 1

    conventional_filename = 1 if filename in {"main.py", "run.py", "app.py"} else 0
    depth = len(relative.parts) - 1
    # Higher tuple is better. Depth is inverted to prefer shallower paths.
    return (
        1 if has_main_guard else 0,
        conventional_boost,
        conventional_filename,
        f"{-depth:04d}",
    )


def _select_best_entrypoint_candidate(project_dir: Path, candidates: list[Path]) -> tuple[Path | None, bool]:
    """Pick a best candidate deterministically, returning ambiguity flag on ties."""
    if not candidates:
        return None, False

    scored: list[tuple[tuple[int, int, int, str], Path]] = []
    for path in candidates:
        scored.append(
            (
                _entrypoint_candidate_score(project_dir, path, has_main_guard=_has_main_guard(path)),
                path,
            )
        )
    scored.sort(key=lambda item: item[0], reverse=True)

    best_score, best_path = scored[0]
    tie_count = sum(1 for score, _ in scored if score == best_score)
    return best_path, tie_count > 1


def _name_from_ast_node(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _name_from_ast_node(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    return None


def _detect_class_entrypoint(project_dir: Path, python_files: list[Path]) -> DetectorResult:
    known_agent_bases = {
        "BaseSingleActionAgent",
        "BaseMultiActionAgent",
        "Agent",
    }
    candidates: list[dict[str, str]] = []

    for python_file in python_files:
        try:
            source = python_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        imported_modules: set[str] = set()
        imported_symbols: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)
                for alias in node.names:
                    imported_symbols.add(alias.name)

        has_langchain_signal = any(module.startswith("langchain") for module in imported_modules)
        has_openai_agents_signal = (
            "agents" in imported_modules
            or "Agent" in imported_symbols
        )

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            class_name = node.name
            base_names = [
                value for value in (_name_from_ast_node(base) for base in node.bases) if isinstance(value, str)
            ]
            has_known_base = any(
                base_name in known_agent_bases or base_name.split(".")[-1] in known_agent_bases
                for base_name in base_names
            )
            class_looks_like_agent = class_name.lower().endswith("agent")

            if not (has_known_base or (class_looks_like_agent and (has_langchain_signal or has_openai_agents_signal))):
                continue

            candidates.append(
                {
                    "agent_class": class_name,
                    "agent_module": _module_name_for_path(project_dir, python_file),
                    "module_path": _relative_path(project_dir, python_file),
                }
            )

    if len(candidates) == 1:
        candidate = candidates[0]
        return DetectorResult(
            value={
                "entrypoint": None,
                "entrypoint_type": "class",
                "agent_class": candidate["agent_class"],
                "agent_module": candidate["agent_module"],
            },
            confidence=0.60,
            evidence=(
                "Detected class-only agent candidate "
                f"{candidate['agent_class']} in {candidate['module_path']}."
            ),
            warning="Class-only agent detected; generate a wrapper entrypoint to run with kinnoo.",
        )

    if len(candidates) > 1:
        candidate_labels = ", ".join(
            f"{candidate['agent_class']} ({candidate['module_path']})" for candidate in candidates
        )
        return DetectorResult(
            value={
                "entrypoint": None,
                "entrypoint_type": "class",
                "candidates": candidates,
            },
            confidence=0.40,
            evidence=f"Detected multiple class-only agent candidates: {candidate_labels}.",
            warning="Multiple class-only agent candidates detected; choose one and generate wrapper manually.",
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No class-only agent candidates detected.",
        warning=None,
    )


def _detect_entrypoint(project_dir: Path) -> DetectorResult:
    run_py = project_dir / "run.py"
    if run_py.exists() and run_py.is_file():
        return DetectorResult(
            value="run.py",
            confidence=0.95,
            evidence="Found conventional run.py entrypoint.",
            warning=None,
        )

    node_entrypoint, node_evidence = _detect_node_entrypoint(project_dir)
    if isinstance(node_entrypoint, str) and node_entrypoint.strip():
        return DetectorResult(
            value=node_entrypoint,
            confidence=0.76,
            evidence=node_evidence or "Detected Node.js package.json entrypoint.",
            warning=None,
        )

    # Search entrypoint candidates up to depth 4 to better support common src/source layouts.
    python_files = _iter_python_files_with_depth(project_dir, max_depth=4)
    guarded = [path for path in python_files if _has_main_guard(path)]

    if len(guarded) == 1:
        entrypoint = _relative_path(project_dir, guarded[0])
        return DetectorResult(
            value=entrypoint,
            confidence=0.78,
            evidence=f"Found single __main__ guard in {entrypoint}.",
            warning=None,
        )

    if len(guarded) > 1:
        selected, ambiguous = _select_best_entrypoint_candidate(project_dir, guarded)
        if selected is not None and not ambiguous:
            entrypoint = _relative_path(project_dir, selected)
            return DetectorResult(
                value=entrypoint,
                confidence=0.72,
                evidence=(
                    "Multiple __main__ candidates detected; selected best candidate "
                    f"using conventional-directory and shallow-depth weighting: {entrypoint}."
                ),
                warning=None,
            )

        candidates = ", ".join(_relative_path(project_dir, path) for path in guarded)
        return DetectorResult(
            value=None,
            confidence=0.35,
            evidence=f"Multiple __main__ candidates detected: {candidates}.",
            warning="Entrypoint is ambiguous; multiple executable modules were found.",
        )

    class_candidate = _detect_class_entrypoint(project_dir, python_files)
    if class_candidate.confidence >= 0.4:
        return class_candidate

    if len(python_files) == 1:
        entrypoint = _relative_path(project_dir, python_files[0])
        return DetectorResult(
            value=entrypoint,
            confidence=0.55,
            evidence=f"Only one python file found: {entrypoint}.",
            warning="Entrypoint inferred from single-file layout; verify before import.",
        )

    conventional_candidates = [
        path for path in python_files if path.name.lower() in {"main.py", "run.py", "app.py"}
    ]
    if conventional_candidates:
        selected, ambiguous = _select_best_entrypoint_candidate(project_dir, conventional_candidates)
        if selected is not None and not ambiguous:
            entrypoint = _relative_path(project_dir, selected)
            return DetectorResult(
                value=entrypoint,
                confidence=0.50,
                evidence=(
                    "Detected conventional entrypoint filename and selected best candidate "
                    f"using directory/depth weighting: {entrypoint}."
                ),
                warning="Entrypoint inferred heuristically from conventional filenames; verify before import.",
            )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No clear entrypoint candidates found.",
        warning="Could not infer entrypoint; add run.py or a single __main__ module.",
    )


def _detect_python_version_from_pyproject(project_dir: Path) -> str | None:
    pyproject_path = project_dir / "pyproject.toml"
    if tomllib is None or not pyproject_path.exists():
        return None

    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None

    project_table = data.get("project")
    if isinstance(project_table, dict):
        requires_python = project_table.get("requires-python")
        if isinstance(requires_python, str) and requires_python.strip():
            return requires_python.strip()
    return None


def _detect_runtime_port_hint(project_dir: Path) -> int | None:
    port_pattern = re.compile(r"(?im)^\s*(?:runtime_)?port\s*=\s*(\d{2,5})\s*$")
    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        match = port_pattern.search(source)
        if not match:
            continue
        port = int(match.group(1))
        if 1 <= port <= 65535:
            return port
    return None


def _detect_node_runtime_version(project_dir: Path) -> str:
    package_json = _load_package_json(project_dir)
    if not package_json:
        return ">=20.0.0"

    engines = package_json.get("engines")
    if isinstance(engines, dict):
        node_constraint = engines.get("node")
        if isinstance(node_constraint, str) and node_constraint.strip():
            return node_constraint.strip()

    return ">=20.0.0"


def _detect_runtime(project_dir: Path) -> DetectorResult:
    package_json = _load_package_json(project_dir)
    if package_json is not None:
        runtime: dict[str, Any] = {
            "language": "nodejs",
            "version": _detect_node_runtime_version(project_dir),
            "type": "one-shot",
            "package_manager": _detect_node_package_manager(project_dir),
        }
        if (project_dir / "tsconfig.json").exists():
            runtime["typescript"] = True

        return DetectorResult(
            value=runtime,
            confidence=0.86,
            evidence="Detected package.json runtime metadata for Node.js project.",
            warning=None,
        )

    node_files = _iter_node_files_with_depth(project_dir, max_depth=6)
    if node_files:
        node_entrypoint, _ = _detect_node_entrypoint(project_dir)
        runtime = {
            "language": "nodejs",
            "version": _detect_node_runtime_version(project_dir),
            "package_manager": _detect_node_package_manager(project_dir),
        }
        if any(path.suffix.lower() in {".ts", ".tsx"} for path in node_files):
            runtime["typescript"] = True
        if node_entrypoint:
            runtime["type"] = "one-shot"

        confidence = 0.78 if node_entrypoint else 0.62
        evidence_parts = [f"Detected {len(node_files)} Node.js/TS source file(s)."]
        if node_entrypoint:
            evidence_parts.append(f"Entrypoint hint: {node_entrypoint}.")

        warning = None
        if not node_entrypoint:
            warning = "Runtime type is inferred from Node.js/TS source layout; verify entrypoint manually."

        return DetectorResult(
            value=runtime,
            confidence=confidence,
            evidence=" ".join(evidence_parts),
            warning=warning,
        )

    python_files = _iter_python_files(project_dir)
    if not python_files:
        return DetectorResult(
            value=None,
            confidence=0.0,
            evidence="No python files detected for runtime inference.",
            warning="Could not infer runtime; no python source files were found.",
        )

    version = _detect_python_version_from_pyproject(project_dir) or ">=3.10"
    port_hint = _detect_runtime_port_hint(project_dir)

    runtime: dict[str, Any] = {
        "language": "python",
        "version": version,
        "type": "one-shot",
    }
    evidence_parts = ["Detected python source files."]

    if _detect_entrypoint(project_dir).confidence < 0.5:
        runtime.pop("type", None)
        evidence_parts.append("Entrypoint confidence is low; omitted runtime.type.")

    if port_hint is not None:
        runtime["port"] = port_hint
        evidence_parts.append(f"Found runtime port hint: {port_hint}.")

    runtime_confidence = 0.82 if "type" in runtime else 0.45
    warning = None
    if "type" not in runtime:
        warning = "Runtime type is uncertain because entrypoint detection is ambiguous."

    return DetectorResult(
        value=runtime,
        confidence=runtime_confidence,
        evidence=" ".join(evidence_parts),
        warning=warning,
    )


def _module_name_for_path(project_dir: Path, file_path: Path) -> str:
    relative = file_path.relative_to(project_dir)
    parts = list(relative.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(part for part in parts if part and part != "__init__")


def _collect_import_names(project_dir: Path) -> set[str]:
    imports: set[str] = set()
    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        module_name = _module_name_for_path(project_dir, python_path)
        if module_name:
            imports.add(module_name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    return imports


def _collect_node_module_markers(project_dir: Path) -> tuple[set[str], list[str]]:
    modules: set[str] = set()
    evidence: list[str] = []

    import_pattern = re.compile(
        r"""(?:from\s+['"]([^'"]+)['"]|import\s+[^;\n]+?\s+from\s+['"]([^'"]+)['"])"""
    )
    require_pattern = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")

    for node_path in _iter_node_files_with_depth(project_dir, max_depth=8):
        try:
            source = node_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for match in import_pattern.finditer(source):
            module_name = match.group(1) or match.group(2)
            if module_name:
                modules.add(module_name)
        for match in require_pattern.finditer(source):
            module_name = match.group(1)
            if module_name:
                modules.add(module_name)

    package_json = _load_package_json(project_dir)
    if isinstance(package_json, dict):
        for dependency_section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            section = package_json.get(dependency_section)
            if not isinstance(section, dict):
                continue
            for dependency_name in section.keys():
                if isinstance(dependency_name, str) and dependency_name.strip():
                    modules.add(dependency_name.strip())
                    evidence.append(f"package.json.{dependency_section}:{dependency_name.strip()}")

    return modules, evidence


def _detect_langgraph_compile_signal(project_dir: Path) -> bool:
    compile_pattern = re.compile(r"\.compile\(")

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "langgraph" in source and compile_pattern.search(source):
            return True

    for node_path in _iter_node_files_with_depth(project_dir, max_depth=8):
        try:
            source = node_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if ("@langchain/langgraph" in source or "langgraph" in source.lower()) and compile_pattern.search(source):
            return True

    return False


def _detect_framework(project_dir: Path) -> DetectorResult:
    openclaw_signals = _detect_openclaw_weighted_signals(project_dir)
    openclaw_score = openclaw_signals["score"]
    openclaw_evidence = openclaw_signals["evidence"]

    if openclaw_score >= 0.6:
        strong_count = len(openclaw_signals["strong"])
        medium_count = len(openclaw_signals["medium"])
        evidence_line = (
            "OpenClaw weighted detection score "
            f"{openclaw_score:.2f} (strong={strong_count}, medium={medium_count}). "
            f"Evidence: {'; '.join(openclaw_evidence)}"
        )
        return DetectorResult(
            value="openclaw",
            confidence=min(0.98, openclaw_score),
            evidence=evidence_line,
            warning=None,
        )

    imports = _collect_import_names(project_dir)
    node_modules, node_evidence = _collect_node_module_markers(project_dir)

    framework_patterns: dict[str, tuple[str, ...]] = {
        "streamlit": ("streamlit",),
        "gradio": ("gradio",),
        "gemini": ("google.genai", "google.generativeai"),
        "langchain": (
            "langchain",
            "langchain_core",
            "langchain_classic",
            "langchain_openai",
            "langchain_community",
            "langchain_text_splitters",
            "langchain_experimental",
        ),
        "chatgpt": ("openai",),
        "claude-chat": ("anthropic",),
        "pydantic-ai": ("pydantic_ai",),
        "langgraph": ("langgraph",),
        "openai-agents": ("agents",),
        "mcp-client": ("mcp",),
    }

    matched: list[str] = []
    evidence_details: list[str] = []
    for framework, patterns in framework_patterns.items():
        hit = [name for name in imports if any(name == marker or name.startswith(f"{marker}.") for marker in patterns)]
        if hit:
            matched.append(framework)
            evidence_details.append(f"{framework}: {', '.join(sorted(hit))}")

    node_framework_patterns: dict[str, tuple[str, ...]] = {
        "langgraph": ("@langchain/langgraph",),
        "langchain": ("@langchain/core", "@langchain/openai", "langchain"),
        "openai-agents": ("@openai/agents",),
        "chatgpt": ("openai",),
    }
    for framework, patterns in node_framework_patterns.items():
        node_hit = [name for name in node_modules if any(name == marker or name.startswith(f"{marker}/") for marker in patterns)]
        if not node_hit:
            continue
        if framework not in matched:
            matched.append(framework)
        evidence_details.append(f"{framework} (node): {', '.join(sorted(node_hit))}")

    langgraph_compile_signal = _detect_langgraph_compile_signal(project_dir)
    if "langgraph" in matched and "langchain" in matched and langgraph_compile_signal:
        langgraph_evidence = [detail for detail in evidence_details if detail.startswith("langgraph")]
        langchain_evidence = [detail for detail in evidence_details if detail.startswith("langchain")]
        node_evidence_line = f" Node evidence: {'; '.join(node_evidence)}." if node_evidence else ""
        return DetectorResult(
            value="langgraph",
            confidence=0.9,
            evidence=(
                f"Framework signals detected -> {'; '.join(langgraph_evidence)}; "
                f"supporting langchain signals -> {'; '.join(langchain_evidence)}. "
                "Selected langgraph due to compile() graph-construction viability signal."
                f"{node_evidence_line}"
            ),
            warning=None,
        )

    # LangChain projects commonly import OpenAI SDK helpers directly. When
    # LangChain signals are present, treat chatgpt signal as secondary.
    if "langchain" in matched and "chatgpt" in matched:
        filtered_details = [detail for detail in evidence_details if not detail.startswith("chatgpt:")]
        openai_evidence = [detail for detail in evidence_details if detail.startswith("chatgpt:")]
        evidence_line = (
            f"Framework signals detected -> {'; '.join(filtered_details)}. "
            f"Also detected OpenAI SDK imports ({'; '.join(openai_evidence)}), "
            "which are treated as supporting evidence for LangChain workflows."
        )
        return DetectorResult(
            value="langchain",
            confidence=0.9,
            evidence=evidence_line,
            warning=None,
        )

    if len(matched) == 1:
        return DetectorResult(
            value=matched[0],
            confidence=0.85,
            evidence=f"Framework signals detected -> {evidence_details[0]}.",
            warning=None,
        )

    if len(matched) > 1:
        evidence_line = f"Multiple framework signals detected: {'; '.join(evidence_details)}."
        if openclaw_score > 0:
            evidence_line += (
                f" OpenClaw weighted score {openclaw_score:.2f}: "
                f"{'; '.join(openclaw_evidence)}."
            )
        return DetectorResult(
            value=None,
            confidence=0.3,
            evidence=evidence_line,
            warning="Framework inference is ambiguous; multiple framework indicators were found.",
        )

    if openclaw_score >= 0.2:
        return DetectorResult(
            value=None,
            confidence=openclaw_score,
            evidence=(
                f"OpenClaw weighted detection score {openclaw_score:.2f} is below inference threshold. "
                f"Evidence: {'; '.join(openclaw_evidence)}"
            ),
            warning=(
                "OpenClaw detection confidence is mixed; add stronger project markers "
                "(for example openclaw.json or package dependency markers) to remove ambiguity."
            ),
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No known framework import patterns detected.",
        warning="Could not infer framework; no recognized framework imports were found.",
    )


def _openclaw_dependency_marker_count(project_dir: Path) -> tuple[int, list[str]]:
    markers: list[str] = []
    dependency_sections = (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    )

    candidate_package_json_paths: list[Path] = []
    root_package_json = project_dir / "package.json"
    if root_package_json.exists() and root_package_json.is_file():
        candidate_package_json_paths.append(root_package_json)

    ignored_segments = {"node_modules", ".git", "dist", "build"}
    for path in sorted(project_dir.rglob("package.json")):
        if path == root_package_json:
            continue
        try:
            relative_parts = path.relative_to(project_dir).parts
        except ValueError:
            continue
        if any(part in ignored_segments for part in relative_parts):
            continue
        depth = len(relative_parts) - 1
        if depth > 4:
            continue
        candidate_package_json_paths.append(path)

    for package_json_path in candidate_package_json_paths:
        try:
            package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(package_data, dict):
            continue

        path_label = _relative_path(project_dir, package_json_path)

        package_name_value = package_data.get("name")
        if isinstance(package_name_value, str):
            normalized_name = package_name_value.strip().lower()
            if "openclaw" in normalized_name:
                markers.append(f"{path_label}:name:{package_name_value.strip()}")

        openclaw_section = package_data.get("openclaw")
        if isinstance(openclaw_section, (dict, list, str, bool, int, float)):
            markers.append(f"{path_label}:openclaw-config")

        for section_name in dependency_sections:
            section = package_data.get(section_name)
            if not isinstance(section, dict):
                continue

            for package_name in sorted(section.keys()):
                normalized = str(package_name).strip().lower()
                if not normalized:
                    continue
                if normalized == "openclaw" or normalized.startswith("@openclaw/") or "openclaw" in normalized:
                    markers.append(f"{path_label}:{section_name}:{package_name}")

    unique_markers = sorted(set(markers))
    return len(unique_markers), unique_markers


def _openclaw_readme_signal(project_dir: Path) -> tuple[float, list[str]]:
    candidate_files = [
        project_dir / "README.md",
        project_dir / "README.source.md",
    ]
    total_mentions = 0
    evidence: list[str] = []

    for candidate in candidate_files:
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            content = candidate.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue

        mentions = len(re.findall(r"\bopenclaw\b", content))
        if mentions <= 0:
            continue
        total_mentions += mentions
        evidence.append(f"readme-openclaw:{_relative_path(project_dir, candidate)}:{mentions}")

    if total_mentions >= 3:
        return 0.5, evidence
    if total_mentions >= 1:
        return 0.3, evidence
    return 0.0, []


def _openclaw_node_layout_signal(project_dir: Path) -> tuple[float, str | None]:
    node_files = _iter_node_files_with_depth(project_dir, max_depth=6)
    if not node_files:
        return 0.0, None

    python_files = _iter_python_files_with_depth(project_dir, max_depth=6)
    score = 0.08
    if not python_files:
        score += 0.12

    has_openclaw_style_dir = any(
        any(segment in {"server", "bridge", "gateway", "daemon"} for segment in path.relative_to(project_dir).parts[:-1])
        for path in node_files
    )
    if has_openclaw_style_dir:
        score += 0.08

    return min(0.3, score), (
        f"node-layout:node_files={len(node_files)};python_files={len(python_files)}"
    )


def _openclaw_skills_signal(project_dir: Path) -> tuple[bool, str | None]:
    skills_root = project_dir / "skills"
    if not skills_root.exists() or not skills_root.is_dir():
        return False, None

    skill_markdown_files = sorted(
        path for path in skills_root.rglob("SKILL.md") if path.is_file()
    )
    if not skill_markdown_files:
        return False, None

    first_match = skill_markdown_files[0]
    relative = _relative_path(project_dir, first_match)
    return True, f"skills-structure:{relative}"


def _openclaw_memory_signal(project_dir: Path) -> tuple[bool, str | None]:
    memory_root = project_dir / "memory"
    if not memory_root.exists() or not memory_root.is_dir():
        return False, None

    return True, "memory-directory:memory/"


def _openclaw_identity_signal(project_dir: Path) -> tuple[float, list[str]]:
    """Detect OpenClaw identity artifacts as explicit medium-confidence signals."""
    score = 0.0
    evidence: list[str] = []

    soul_path = project_dir / "SOUL.md"
    agents_path = project_dir / "AGENTS.md"
    user_path = project_dir / "USER.md"

    has_soul = soul_path.exists() and soul_path.is_file()
    has_agents = agents_path.exists() and agents_path.is_file()
    has_user = user_path.exists() and user_path.is_file()

    if has_soul and has_agents:
        score += 0.2
        evidence.extend(["identity-file:SOUL.md", "identity-file:AGENTS.md"])
    elif has_soul:
        score += 0.1
        evidence.append("identity-file:SOUL.md")
    elif has_agents:
        score += 0.1
        evidence.append("identity-file:AGENTS.md")

    # USER.md is optional context and only increases confidence when present.
    if has_user:
        score += 0.05
        evidence.append("identity-file:USER.md")

    return score, evidence


def _detect_openclaw_weighted_signals(project_dir: Path) -> dict[str, Any]:
    """Detect OpenClaw evidence using weighted strong/medium signals.

    Strong signals have higher confidence contribution than medium signals.
    """
    strong_evidence: list[str] = []
    medium_evidence: list[str] = []
    score = 0.0

    openclaw_json = project_dir / "openclaw.json"
    if openclaw_json.exists() and openclaw_json.is_file():
        strong_evidence.append("openclaw.json")
        score += 0.5

    dependency_marker_count, dependency_evidence = _openclaw_dependency_marker_count(project_dir)
    if dependency_marker_count > 0:
        score += 0.4
        strong_evidence.extend(dependency_evidence)

    has_skills_signal, skills_evidence = _openclaw_skills_signal(project_dir)
    if has_skills_signal and skills_evidence:
        score += 0.15
        medium_evidence.append(skills_evidence)

    has_memory_signal, memory_evidence = _openclaw_memory_signal(project_dir)
    if has_memory_signal and memory_evidence:
        score += 0.1
        medium_evidence.append(memory_evidence)

    identity_score, identity_evidence = _openclaw_identity_signal(project_dir)
    if identity_score > 0:
        score += identity_score
        medium_evidence.extend(identity_evidence)

    readme_score, readme_evidence = _openclaw_readme_signal(project_dir)
    if readme_score > 0:
        score += readme_score
        medium_evidence.extend(readme_evidence)

    node_layout_score, node_layout_evidence = _openclaw_node_layout_signal(project_dir)
    if node_layout_score > 0:
        score += node_layout_score
        if node_layout_evidence:
            medium_evidence.append(node_layout_evidence)

    normalized_score = min(1.0, score)
    evidence = strong_evidence + medium_evidence
    return {
        "score": normalized_score,
        "strong": strong_evidence,
        "medium": medium_evidence,
        "evidence": evidence,
    }


def _detect_node_package_manager(project_dir: Path) -> str:
    if (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_dir / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _infer_openclaw_skill_paths(project_dir: Path) -> list[str]:
    skills_root = project_dir / "skills"
    if not skills_root.exists() or not skills_root.is_dir():
        return []

    inferred_skills = sorted(
        _relative_path(project_dir, path)
        for path in skills_root.rglob("SKILL.md")
        if path.is_file()
    )
    return inferred_skills


def _infer_openclaw_state_dirs(project_dir: Path) -> list[str]:
    candidates: list[str] = []

    memory_root = project_dir / "memory"
    if memory_root.exists() and memory_root.is_dir():
        candidates.append("memory")

    state_root = project_dir / "state"
    if state_root.exists() and state_root.is_dir():
        candidates.append("state")

    return candidates


def infer_openclaw_project_hints(project_dir: str | Path) -> dict[str, Any]:
    """Infer OpenClaw runtime and structure hints for import workflows.

    This helper is intentionally additive and does not alter the stable
    `analyze_project()` report key contract from feature27.
    """
    resolved_project_dir = _validate_project_dir(project_dir)
    signals = _detect_openclaw_weighted_signals(resolved_project_dir)

    package_manager = _detect_node_package_manager(resolved_project_dir)
    skills = _infer_openclaw_skill_paths(resolved_project_dir)
    state_dirs = _infer_openclaw_state_dirs(resolved_project_dir)

    return {
        "confidence": float(signals["score"]),
        "evidence": list(signals["evidence"]),
        "runtime": {
            "language": "nodejs",
            "type": "daemon",
            "package_manager": package_manager,
            "version": ">=20.0.0",
        },
        "skills": skills,
        "state_dirs": state_dirs,
    }


def _normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


IMPORT_TO_PYPI: dict[str, str] = {
    "langchain": "langchain",
    "langchain_core": "langchain-core",
    "langchain_classic": "langchain-classic",
    "langchain_openai": "langchain-openai",
    "langchain_community": "langchain-community",
    "langchain_text_splitters": "langchain-text-splitters",
    "langchain_experimental": "langchain-experimental",
    "langchain_google_genai": "langchain-google-genai",
    "langgraph": "langgraph",
    "langsmith": "langsmith",
    "pydantic_ai": "pydantic-ai",
    "openai": "openai",
    "agents": "openai-agents",
    "anthropic": "anthropic",
    "google.genai": "google-genai",
    "google.generativeai": "google-generativeai",
    "cohere": "cohere",
    "mistralai": "mistralai",
    "vertexai": "google-cloud-aiplatform",
    "boto3": "boto3",
    "botocore": "botocore",
    "azure": "azure",
    "httpx": "httpx",
    "requests": "requests",
    "aiohttp": "aiohttp",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "flask": "flask",
    "django": "django",
    "streamlit": "streamlit",
    "gradio": "gradio",
    "litellm": "litellm",
    "tiktoken": "tiktoken",
    "tokenizers": "tokenizers",
    "transformers": "transformers",
    "sentence_transformers": "sentence-transformers",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "sklearn": "scikit-learn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "pydantic": "pydantic",
    "dotenv": "python-dotenv",
    "yaml": "pyyaml",
    "jinja2": "jinja2",
    "loguru": "loguru",
    "redis": "redis",
    "psycopg2": "psycopg2-binary",
    "asyncpg": "asyncpg",
    "sqlalchemy": "sqlalchemy",
    "chromadb": "chromadb",
    "pinecone": "pinecone-client",
    "faiss": "faiss-cpu",
    "mcp": "mcp",
    "crewai": "crewai",
    "crewai_tools": "crewai-tools",
}


def _stdlib_module_names() -> set[str]:
    stdlib = getattr(sys, "stdlib_module_names", None)
    if isinstance(stdlib, set):
        return set(stdlib)
    return {
        "argparse",
        "asyncio",
        "collections",
        "contextlib",
        "datetime",
        "functools",
        "hashlib",
        "itertools",
        "json",
        "logging",
        "math",
        "os",
        "pathlib",
        "random",
        "re",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "typing",
        "uuid",
    }


def _project_module_roots(project_dir: Path) -> set[str]:
    roots: set[str] = set()
    for python_path in _iter_python_files(project_dir):
        module_name = _module_name_for_path(project_dir, python_path)
        if module_name:
            roots.add(module_name.split(".")[0])
    return roots


def _map_import_to_package(import_name: str) -> str | None:
    if import_name in IMPORT_TO_PYPI:
        return IMPORT_TO_PYPI[import_name]

    for module_prefix, package_name in IMPORT_TO_PYPI.items():
        if import_name.startswith(f"{module_prefix}."):
            return package_name

    top_level = import_name.split(".")[0]
    if top_level in IMPORT_TO_PYPI:
        return IMPORT_TO_PYPI[top_level]
    return None


def _infer_requirements(project_dir: Path | str) -> list[str]:
    """Infer PyPI package names from Python imports, excluding stdlib and local modules."""
    resolved_project_dir = _validate_project_dir(project_dir)
    import_names = _collect_import_names(resolved_project_dir)
    stdlib_names = _stdlib_module_names()
    local_roots = _project_module_roots(resolved_project_dir)

    inferred_packages: set[str] = set()
    for import_name in sorted(import_names):
        top_level = import_name.split(".")[0]
        if top_level in stdlib_names or top_level in local_roots:
            continue
        package_name = _map_import_to_package(import_name)
        if package_name:
            inferred_packages.add(package_name)

    return sorted(inferred_packages)


def _split_requirement_name_and_constraint(requirement: str) -> tuple[str, str]:
    # Keep parsing intentionally narrow/deterministic: name + optional tail constraints.
    requirement = requirement.strip()
    if not requirement:
        return "", ""

    marker_index = requirement.find(";")
    if marker_index >= 0:
        requirement = requirement[:marker_index].strip()

    # Remove extras from name while keeping version constraint suffix intact.
    match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?(.*)$", requirement)
    if not match:
        return "", ""

    name = _normalize_package_name(match.group(1))
    constraint = match.group(2).strip()
    return name, constraint


def _collect_requirements_dependencies(project_dir: Path) -> tuple[dict[str, set[str]], list[str]]:
    requirements_path = project_dir / "requirements.txt"
    requirements: dict[str, set[str]] = {}
    evidence: list[str] = []

    if not requirements_path.exists():
        return requirements, evidence

    try:
        lines = requirements_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return requirements, evidence

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("-r", "--requirement", "-c", "--constraint", "-e", "--editable")):
            continue
        if "://" in stripped:
            continue

        name, constraint = _split_requirement_name_and_constraint(stripped)
        if not name:
            continue

        requirements.setdefault(name, set()).add(constraint)
        evidence.append(f"requirements.txt:{name}{constraint}")

    return requirements, evidence


def _collect_pyproject_dependencies(project_dir: Path) -> tuple[dict[str, set[str]], list[str]]:
    pyproject_path = project_dir / "pyproject.toml"
    dependencies: dict[str, set[str]] = {}
    evidence: list[str] = []

    if tomllib is None or not pyproject_path.exists():
        return dependencies, evidence

    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return dependencies, evidence

    def add_dep(raw_dep: str, source_label: str) -> None:
        name, constraint = _split_requirement_name_and_constraint(raw_dep)
        if not name:
            return
        dependencies.setdefault(name, set()).add(constraint)
        evidence.append(f"{source_label}:{name}{constraint}")

    project_table = data.get("project")
    if isinstance(project_table, dict):
        for dep in project_table.get("dependencies", []):
            if isinstance(dep, str) and dep.strip():
                add_dep(dep, "pyproject.project.dependencies")

        optional = project_table.get("optional-dependencies")
        if isinstance(optional, dict):
            for group_name, dep_list in optional.items():
                if not isinstance(dep_list, list):
                    continue
                for dep in dep_list:
                    if isinstance(dep, str) and dep.strip():
                        add_dep(dep, f"pyproject.project.optional-dependencies.{group_name}")

    tool_table = data.get("tool")
    if isinstance(tool_table, dict):
        poetry_table = tool_table.get("poetry")
        if isinstance(poetry_table, dict):
            poetry_deps = poetry_table.get("dependencies")
            if isinstance(poetry_deps, dict):
                for raw_name, raw_constraint in poetry_deps.items():
                    if not isinstance(raw_name, str) or not raw_name.strip():
                        continue
                    if raw_name.strip().lower() == "python":
                        continue
                    normalized_constraint = ""
                    if isinstance(raw_constraint, str):
                        normalized_constraint = raw_constraint.strip()
                    elif isinstance(raw_constraint, dict):
                        normalized_constraint = str(raw_constraint.get("version", "")).strip()
                    add_dep(f"{raw_name}{normalized_constraint}", "pyproject.tool.poetry.dependencies")

    return dependencies, evidence


def _collect_package_json_dependencies(project_dir: Path) -> tuple[dict[str, set[str]], list[str]]:
    dependencies: dict[str, set[str]] = {}
    evidence: list[str] = []
    package_json = _load_package_json(project_dir)
    if not isinstance(package_json, dict):
        return dependencies, evidence

    for section_name in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        section = package_json.get(section_name)
        if not isinstance(section, dict):
            continue
        for raw_name, raw_constraint in section.items():
            if not isinstance(raw_name, str) or not raw_name.strip():
                continue
            name = _normalize_package_name(raw_name)
            constraint = raw_constraint.strip() if isinstance(raw_constraint, str) else ""
            dependencies.setdefault(name, set()).add(constraint)
            evidence.append(f"package.json.{section_name}:{name}{constraint}")

    return dependencies, evidence


def _format_dependency_output(dependency_map: dict[str, set[str]]) -> list[str]:
    formatted: list[str] = []
    for package in sorted(dependency_map.keys()):
        constraints = sorted(constraint for constraint in dependency_map[package] if constraint)
        if constraints:
            formatted.append(f"{package}{constraints[0]}")
        else:
            formatted.append(package)
    return formatted


def _detect_dependencies(project_dir: Path) -> DetectorResult:
    requirements_map, requirements_evidence = _collect_requirements_dependencies(project_dir)
    pyproject_map, pyproject_evidence = _collect_pyproject_dependencies(project_dir)
    package_json_map, package_json_evidence = _collect_package_json_dependencies(project_dir)

    merged: dict[str, set[str]] = {}
    for source in (requirements_map, pyproject_map, package_json_map):
        for package, constraints in source.items():
            merged.setdefault(package, set()).update(constraints)

    dependencies = _format_dependency_output(merged)
    evidence_items = requirements_evidence + pyproject_evidence + package_json_evidence

    if dependencies:
        source_count = (
            int(bool(requirements_evidence))
            + int(bool(pyproject_evidence))
            + int(bool(package_json_evidence))
        )
        confidence = 0.92 if source_count >= 2 else 0.82
        return DetectorResult(
            value=dependencies,
            confidence=confidence,
            evidence=f"Detected {len(dependencies)} dependencies from {source_count} source(s): {'; '.join(evidence_items)}",
            warning=None,
        )

    inferred_from_imports = _infer_requirements(project_dir)
    import_evidence = [f"imports:{package_name}" for package_name in inferred_from_imports]

    if inferred_from_imports:
        return DetectorResult(
            value=inferred_from_imports,
            confidence=0.68,
            evidence=(
                "Inferred dependencies from known import namespaces in source files: "
                + "; ".join(import_evidence)
            ),
            warning=(
                "Dependency inference came from source imports; verify pinned versions in requirements.txt."
            ),
        )

    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence="No dependencies found in requirements.txt or pyproject.toml.",
        warning="Could not infer dependencies; review requirements.txt and pyproject.toml.",
    )


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_env_var_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "os" and node.func.attr == "getenv" and node.args:
                    key = _literal_string(node.args[0])
                    if key:
                        names.add(key)

            # Match os.environ.get("VAR")
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Attribute)
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "os"
                and node.func.value.attr == "environ"
                and node.args
            ):
                key = _literal_string(node.args[0])
                if key:
                    names.add(key)

        if isinstance(node, ast.Subscript):
            # Match os.environ["VAR"]
            if (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "os"
                and node.value.attr == "environ"
            ):
                key = _literal_string(node.slice)
                if key:
                    names.add(key)

    return names


def _is_sys_argv_subscript(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "sys"
        and node.value.attr == "argv"
    )


def _is_json_loads_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "loads"
    )


def _is_json_dumps_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "dumps"
    )


def _extract_pydanticai_deps_signature(project_dir: Path) -> tuple[str | None, list[str]]:
    deps_class_name: str | None = None
    deps_fields: list[str] = []

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        pydantic_agent_symbols: set[str] = set()
        pydantic_module_aliases: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pydantic_ai"):
                for alias in node.names:
                    if alias.name == "Agent":
                        pydantic_agent_symbols.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "pydantic_ai":
                        pydantic_module_aliases.add(alias.asname or "pydantic_ai")

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call_is_pydantic_agent = False
            if isinstance(node.func, ast.Name) and node.func.id in pydantic_agent_symbols:
                call_is_pydantic_agent = True
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "Agent"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in pydantic_module_aliases
            ):
                call_is_pydantic_agent = True

            if not call_is_pydantic_agent:
                continue

            for keyword in node.keywords:
                if keyword.arg != "deps_type":
                    continue

                if isinstance(keyword.value, ast.Name):
                    deps_class_name = keyword.value.id
                elif isinstance(keyword.value, ast.Attribute):
                    deps_class_name = keyword.value.attr
                elif isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    deps_class_name = keyword.value.value

                break

            if deps_class_name:
                break

        if not deps_class_name:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == deps_class_name:
                extracted_fields: list[str] = []
                for statement in node.body:
                    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                        extracted_fields.append(statement.target.id)
                    elif isinstance(statement, ast.Assign):
                        for target in statement.targets:
                            if isinstance(target, ast.Name):
                                extracted_fields.append(target.id)
                deps_fields = sorted(set(extracted_fields))
                break

        return deps_class_name, deps_fields

    return None, []


def _detect_pydanticai_deps_type(project_dir: Path) -> DetectorResult:
    deps_class_name, deps_fields = _extract_pydanticai_deps_signature(project_dir)
    if deps_class_name:
        return DetectorResult(
            value={"class_name": deps_class_name, "fields": deps_fields},
            confidence=0.9 if deps_fields else 0.82,
            evidence=(
                "Detected PydanticAI deps_type pattern "
                f"(deps_type={deps_class_name}, fields={len(deps_fields)})."
            ),
            warning=None,
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No PydanticAI deps_type pattern detected.",
        warning=None,
    )


def _detect_input_type(project_dir: Path) -> DetectorResult:
    deps_class_name, deps_fields = _extract_pydanticai_deps_signature(project_dir)
    if deps_class_name:
        return DetectorResult(
            value="json",
            confidence=0.92 if deps_fields else 0.85,
            evidence=(
                "Detected PydanticAI Agent(deps_type=...) pattern "
                f"(deps_type={deps_class_name}); mapped to inputs.type=json."
            ),
            warning=None,
        )

    parsed_files = 0
    sys_argv_usages = 0
    input_calls = 0
    argparse_add_argument_calls = 0
    parse_args_calls = 0
    json_loads_calls = 0

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        parsed_files += 1
        for node in ast.walk(tree):
            if _is_sys_argv_subscript(node):
                sys_argv_usages += 1

            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
                input_calls += 1

            if _is_json_loads_call(node):
                json_loads_calls += 1

            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "add_argument":
                    argparse_add_argument_calls += 1
                elif node.func.attr == "parse_args":
                    parse_args_calls += 1

    if json_loads_calls > 0 and (sys_argv_usages > 0 or parse_args_calls > 0):
        return DetectorResult(
            value="json",
            confidence=0.9,
            evidence=(
                "Detected json.loads usage alongside CLI argument handling "
                f"(json.loads={json_loads_calls}, sys.argv={sys_argv_usages}, parse_args={parse_args_calls})."
            ),
            warning=None,
        )

    if parse_args_calls > 0 and argparse_add_argument_calls > 0:
        # Parameterized CLI contracts map best to structured JSON payloads in kinnoo manifests.
        return DetectorResult(
            value="json",
            confidence=0.78,
            evidence=(
                "Detected argparse parameterized CLI input "
                f"(parse_args={parse_args_calls}, add_argument={argparse_add_argument_calls}); "
                "mapped to inputs.type=json for structured invocation."
            ),
            warning=None,
        )

    if sys_argv_usages > 0 or input_calls > 0:
        return DetectorResult(
            value="text",
            confidence=0.84 if sys_argv_usages > 0 else 0.74,
            evidence=(
                "Detected text-oriented input handling "
                f"(sys.argv={sys_argv_usages}, input()={input_calls})."
            ),
            warning=None,
        )

    return DetectorResult(
        value="text",
        confidence=0.3,
        evidence=f"No explicit input handling detected across {parsed_files} python file(s).",
        warning="Could not infer input contract; defaulting inputs.type to text.",
    )


def _detect_inputs_required(project_dir: Path) -> DetectorResult:
    parsed_files = 0
    sys_argv_usages = 0
    argparse_add_argument_calls = 0
    parse_args_calls = 0
    input_calls = 0
    hardcoded_run_calls = 0

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        parsed_files += 1
        for node in ast.walk(tree):
            if _is_sys_argv_subscript(node):
                sys_argv_usages += 1

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "input":
                    input_calls += 1

                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "add_argument":
                        argparse_add_argument_calls += 1
                    elif node.func.attr == "parse_args":
                        parse_args_calls += 1
                    elif node.func.attr in {"run", "run_sync"}:
                        if any(isinstance(arg, ast.Constant) and isinstance(arg.value, str) for arg in node.args):
                            hardcoded_run_calls += 1

    if sys_argv_usages > 0 or parse_args_calls > 0 or argparse_add_argument_calls > 0 or input_calls > 0:
        return DetectorResult(
            value=True,
            confidence=0.9,
            evidence=(
                "Detected parameterized input handling "
                f"(sys.argv={sys_argv_usages}, argparse={parse_args_calls}/{argparse_add_argument_calls}, input()={input_calls})."
            ),
            warning=None,
        )

    if hardcoded_run_calls > 0:
        return DetectorResult(
            value=False,
            confidence=0.85,
            evidence=(
                "Detected hardcoded literal input in agent execution calls "
                f"(run/run_sync literal call count={hardcoded_run_calls})."
            ),
            warning=None,
        )

    return DetectorResult(
        value=True,
        confidence=0.4,
        evidence=f"No explicit input-source patterns found across {parsed_files} python file(s).",
        warning="Input requiredness is uncertain; defaulting to required=true.",
    )


def _detect_async_entrypoint(project_dir: Path) -> DetectorResult:
    async_function_count = 0
    asyncio_run_calls = 0

    for python_path in _iter_python_files(project_dir):
        try:
            tree = ast.parse(python_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_function_count += 1

            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "asyncio"
                    and node.func.attr == "run"
                ):
                    asyncio_run_calls += 1

    is_async = async_function_count > 0 or asyncio_run_calls > 0
    if is_async:
        return DetectorResult(
            value=True,
            confidence=0.86,
            evidence=(
                "Detected async entrypoint signals "
                f"(async defs={async_function_count}, asyncio.run calls={asyncio_run_calls})."
            ),
            warning=None,
        )

    return DetectorResult(
        value=False,
        confidence=0.65,
        evidence="No async entrypoint signals detected.",
        warning=None,
    )


def _detect_output_type(project_dir: Path) -> DetectorResult:
    parsed_files = 0
    print_calls = 0
    json_dumps_calls = 0
    returns_collection_literal = 0

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        parsed_files += 1
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                print_calls += 1
            if _is_json_dumps_call(node):
                json_dumps_calls += 1
            if isinstance(node, ast.Return) and isinstance(node.value, (ast.Dict, ast.List, ast.Tuple)):
                returns_collection_literal += 1

    if json_dumps_calls > 0:
        return DetectorResult(
            value="json",
            confidence=0.88,
            evidence=f"Detected json.dumps output serialization calls: {json_dumps_calls}.",
            warning=None,
        )

    if returns_collection_literal > 0 and print_calls == 0:
        return DetectorResult(
            value="json",
            confidence=0.72,
            evidence=(
                "Detected structured return values (dict/list/tuple) without explicit print-based text output; "
                "mapped to outputs.type=json."
            ),
            warning=None,
        )

    if print_calls > 0:
        return DetectorResult(
            value="text",
            confidence=0.82,
            evidence=f"Detected print-based output calls: {print_calls}.",
            warning=None,
        )

    return DetectorResult(
        value="text",
        confidence=0.3,
        evidence=f"No explicit output patterns detected across {parsed_files} python file(s).",
        warning="Could not infer output contract; defaulting outputs.type to text.",
    )


def _detect_env_vars(project_dir: Path) -> DetectorResult:
    env_names: set[str] = set()
    parsed_python_files = 0
    parsed_node_files = 0

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        parsed_python_files += 1
        env_names.update(_extract_env_var_names(tree))

    node_env_patterns = (
        re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)"),
        re.compile(r"process\.env\[['\"]([A-Z][A-Z0-9_]+)['\"]\]"),
    )
    for node_path in _iter_node_files_with_depth(project_dir, max_depth=8):
        try:
            source = node_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        parsed_node_files += 1
        for pattern in node_env_patterns:
            env_names.update(match.group(1) for match in pattern.finditer(source))

    inferred = sorted(name for name in env_names if name)
    parsed_total = parsed_python_files + parsed_node_files
    if inferred:
        return DetectorResult(
            value=inferred,
            confidence=0.88,
            evidence=(
                f"Detected {len(inferred)} unique env var names across "
                f"{parsed_python_files} python file(s) and {parsed_node_files} node file(s)."
            ),
            warning=None,
        )

    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence=f"No env var patterns detected across {parsed_total} source file(s).",
        warning="Could not infer env vars from source patterns; verify required environment variables manually.",
    )


def _looks_like_safe_relative_path(value: str) -> bool:
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        return False
    if normalized.startswith(("/", "~")):
        return False
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        return False
    return True


def _candidate_asset_directories(project_dir: Path) -> set[str]:
    candidate_names = {"data", "dataset", "datasets", "model", "models", "assets", "artifacts", "checkpoints"}
    candidates: set[str] = set()

    for path in sorted(project_dir.rglob("*")):
        if not path.is_dir():
            continue
        if path.name.lower() not in candidate_names:
            continue
        candidates.add(_relative_path(project_dir, path))

    return candidates


def _candidate_asset_files(project_dir: Path) -> set[str]:
    asset_suffixes = {
        ".onnx",
        ".pt",
        ".pth",
        ".safetensors",
        ".pkl",
        ".pickle",
        ".joblib",
        ".h5",
        ".npy",
        ".npz",
        ".csv",
        ".parquet",
        ".jsonl",
    }
    candidates: set[str] = set()

    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in asset_suffixes:
            continue
        candidates.add(_relative_path(project_dir, path))

    return candidates


def _collect_string_literals(tree: ast.AST) -> list[str]:
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
    return literals


_MODEL_NAME_KEYS = {
    "model",
    "model_name",
    "model_id",
    "default_model",
}

_MODEL_LITERAL_PATTERNS = [
    re.compile(r"^(?:openai:)?gpt-[A-Za-z0-9_.:-]+$"),
    re.compile(r"^claude-[A-Za-z0-9_.:-]+$"),
    re.compile(r"^gemini-[A-Za-z0-9_.:-]+$"),
    re.compile(r"^(?:openai:)?o[0-9]+(?:-[A-Za-z0-9_.:-]+)?$"),
]


def _looks_like_model_identifier(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    return any(pattern.fullmatch(candidate) for pattern in _MODEL_LITERAL_PATTERNS)


def _detect_model(project_dir: Path) -> DetectorResult:
    explicit_model_hits: list[tuple[str, str]] = []
    assigned_model_hits: list[tuple[str, str]] = []
    heuristic_model_hits: list[tuple[str, str]] = []

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        rel_path = _relative_path(project_dir, python_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg not in _MODEL_NAME_KEYS:
                        continue
                    literal = _literal_string(keyword.value)
                    if literal and _looks_like_model_identifier(literal):
                        explicit_model_hits.append((literal, f"{rel_path}:{keyword.arg}"))

            if isinstance(node, ast.Assign):
                literal = _literal_string(node.value)
                if not literal or not _looks_like_model_identifier(literal):
                    continue

                for target in node.targets:
                    if isinstance(target, ast.Name):
                        target_name = target.id.strip().lower()
                        if target_name in _MODEL_NAME_KEYS:
                            assigned_model_hits.append((literal, f"{rel_path}:{target.id}"))

        for literal in _collect_string_literals(tree):
            if _looks_like_model_identifier(literal):
                heuristic_model_hits.append((literal, rel_path))

    if explicit_model_hits:
        model_name, evidence = explicit_model_hits[0]
        return DetectorResult(
            value=model_name,
            confidence=0.93,
            evidence=(
                "Detected model string literal via explicit model keyword "
                f"argument ({evidence})."
            ),
            warning=None,
        )

    if assigned_model_hits:
        model_name, evidence = assigned_model_hits[0]
        return DetectorResult(
            value=model_name,
            confidence=0.79,
            evidence=(
                "Detected model string literal via model-like variable assignment "
                f"({evidence})."
            ),
            warning=None,
        )

    if heuristic_model_hits:
        model_name, evidence = heuristic_model_hits[0]
        return DetectorResult(
            value=model_name,
            confidence=0.62,
            evidence=(
                "Detected model-like string literal in source text; "
                f"manual verification recommended ({evidence})."
            ),
            warning="Model inference confidence is moderate; verify inferred model in kinnoo.yaml.",
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No model string literals detected in project source.",
        warning="Could not infer model automatically.",
    )


def _collect_path_literal_assets(project_dir: Path) -> tuple[set[str], list[str]]:
    safe_assets: set[str] = set()
    blocked_candidates: list[str] = []

    for python_path in _iter_python_files(project_dir):
        try:
            tree = ast.parse(python_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for literal in _collect_string_literals(tree):
            if "/" not in literal and "\\" not in literal:
                continue

            normalized = literal.strip().replace("\\", "/")
            if not _looks_like_safe_relative_path(normalized):
                blocked_candidates.append(normalized)
                continue

            candidate_path = (project_dir / normalized).resolve()
            try:
                candidate_path.relative_to(project_dir.resolve())
            except ValueError:
                blocked_candidates.append(normalized)
                continue

            if candidate_path.exists() and (candidate_path.is_file() or candidate_path.is_dir()):
                safe_assets.add(_relative_path(project_dir, candidate_path))

    return safe_assets, sorted(set(blocked_candidates))


def _detect_assets(project_dir: Path) -> DetectorResult:
    dir_candidates = _candidate_asset_directories(project_dir)
    file_candidates = _candidate_asset_files(project_dir)
    literal_candidates, blocked_candidates = _collect_path_literal_assets(project_dir)

    inferred_assets = sorted(dir_candidates | file_candidates | literal_candidates)

    warning_parts: list[str] = []
    if blocked_candidates:
        warning_parts.append(
            "Ignored unsafe asset path candidates: "
            + ", ".join(blocked_candidates[:3])
            + (" ..." if len(blocked_candidates) > 3 else "")
        )

    if inferred_assets:
        evidence = (
            f"Detected {len(inferred_assets)} asset candidate(s) "
            f"from directories={len(dir_candidates)}, files={len(file_candidates)}, literals={len(literal_candidates)}."
        )
        confidence = 0.84 if (dir_candidates and file_candidates) else 0.72
        return DetectorResult(
            value=inferred_assets,
            confidence=confidence,
            evidence=evidence,
            warning=" ".join(warning_parts) if warning_parts else None,
        )

    warning_parts.append("Could not infer assets; review model/data files and manifest include paths manually.")
    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence="No model/data asset candidates detected.",
        warning=" ".join(warning_parts),
    )


def _extract_service_endpoints_from_tree(tree: ast.AST) -> set[str]:
    endpoints: set[str] = set()
    for literal in _collect_string_literals(tree):
        candidate = literal.strip()
        if candidate.startswith((
            "http://",
            "https://",
            "redis://",
            "postgres://",
            "postgresql://",
            "mongodb://",
        )):
            endpoints.add(candidate)
            continue

        lower_candidate = candidate.lower()
        if "localhost:11434" in lower_candidate:
            endpoints.add("http://localhost:11434")
        if "localhost:6379" in lower_candidate:
            endpoints.add("redis://localhost:6379")
        if "localhost:5432" in lower_candidate:
            endpoints.add("postgresql://localhost:5432")
        if "localhost:27017" in lower_candidate:
            endpoints.add("mongodb://localhost:27017")
        if "localhost:8000" in lower_candidate and "chroma" in lower_candidate:
            endpoints.add("http://localhost:8000")
    return endpoints


def _service_type_from_endpoint(endpoint: str) -> str:
    lower = endpoint.lower()
    if lower.startswith("redis://"):
        return "redis"
    if lower.startswith(("postgres://", "postgresql://")):
        return "postgres"
    if lower.startswith("mongodb://"):
        return "mongodb"
    if lower.startswith(("http://", "https://")):
        return "http"
    return "unknown"


def _service_name_from_endpoint(endpoint: str, service_type: str) -> str:
    lower = endpoint.lower()
    if "11434" in lower:
        return "ollama"
    if "8000" in lower and service_type == "http":
        return "chromadb"
    if service_type == "redis":
        return "redis"
    if service_type == "postgres":
        return "postgresql"
    if service_type == "mongodb":
        return "mongodb"
    parsed = urlsplit(endpoint)
    if parsed.hostname:
        hostname = parsed.hostname.replace(".", "-")
        if service_type == "http" and parsed.path not in {"", "/"}:
            sanitized_path = parsed.path.strip("/").replace("/", "-")
            if sanitized_path:
                return f"{hostname}-{sanitized_path}"
        return hostname
    return service_type


def _extract_import_names(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _services_from_imports(import_names: set[str]) -> list[dict[str, Any]]:
    service_markers: list[tuple[str, str, str, str | None]] = [
        ("ollama", "ollama", "api", "http://localhost:11434"),
        ("chromadb", "chromadb", "vector-db", "http://localhost:8000"),
        ("pinecone", "pinecone", "vector-db", None),
        ("redis", "redis", "redis", "redis://localhost:6379"),
        ("psycopg2", "postgresql", "postgres", "postgresql://localhost:5432"),
        ("asyncpg", "postgresql", "postgres", "postgresql://localhost:5432"),
        ("sqlalchemy", "postgresql", "postgres", "postgresql://localhost:5432"),
        ("pymongo", "mongodb", "mongodb", "mongodb://localhost:27017"),
    ]

    discovered: dict[str, dict[str, Any]] = {}
    for marker, service_name, service_type, endpoint in service_markers:
        if any(name == marker or name.startswith(f"{marker}.") for name in import_names):
            payload: dict[str, Any] = {
                "name": service_name,
                "type": service_type,
            }
            if endpoint is not None:
                payload["endpoint"] = endpoint
            discovered[payload["name"]] = payload
    return [discovered[key] for key in sorted(discovered)]


def _health_check_hint(service_type: str, endpoint: str) -> str | None:
    if service_type == "redis":
        return "PING"
    if service_type == "postgres":
        return "SELECT 1"
    if service_type == "http":
        parsed = urlsplit(endpoint)
        if parsed.path in {"/health", "/healthz", "/ready", "/readyz"}:
            return f"GET {parsed.path}"
    return None


def _detect_services(project_dir: Path) -> DetectorResult:
    discovered: dict[tuple[str, str], dict[str, Any]] = {}
    import_derived: dict[str, dict[str, Any]] = {}

    for python_path in _iter_python_files(project_dir):
        try:
            tree = ast.parse(python_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for service in _services_from_imports(_extract_import_names(tree)):
            import_derived[service["name"]] = service

        for endpoint in _extract_service_endpoints_from_tree(tree):
            service_type = _service_type_from_endpoint(endpoint)
            if service_type == "unknown":
                continue
            service_name = _service_name_from_endpoint(endpoint, service_type)
            key = (service_name, endpoint)
            service = {
                "name": service_name,
                "type": service_type,
                "endpoint": endpoint,
            }
            hint = _health_check_hint(service_type, endpoint)
            if hint:
                service["health_check_hint"] = hint
            discovered[key] = service

    services_by_name: dict[str, dict[str, Any]] = {}
    for service in import_derived.values():
        services_by_name[service["name"]] = service
    for service in [discovered[key] for key in sorted(discovered.keys())]:
        services_by_name[service["name"]] = service

    services = [services_by_name[key] for key in sorted(services_by_name.keys())]
    if services:
        with_hints = sum(1 for service in services if "health_check_hint" in service)
        return DetectorResult(
            value=services,
            confidence=0.8 if with_hints else 0.7,
            evidence=f"Detected {len(services)} service endpoint(s); {with_hints} include health-check hints.",
            warning=None,
        )

    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence="No recognizable service endpoint patterns found in source literals.",
        warning="Could not infer services; review external endpoint configuration manually.",
    )


def _detector_registry() -> dict[str, Detector]:
    """Return detector hooks keyed by inferred report field name."""
    return {
        "entrypoint": _detect_entrypoint,
        "runtime": _detect_runtime,
        "framework": _detect_framework,
        "model": _detect_model,
        "dependencies": _detect_dependencies,
        "deps_type": _detect_pydanticai_deps_type,
        "inputs": _detect_input_type,
        "inputs_required": _detect_inputs_required,
        "async_entrypoint": _detect_async_entrypoint,
        "outputs": _detect_output_type,
        "env_vars": _detect_env_vars,
        "assets": _detect_assets,
        "services": _detect_services,
    }


def _validate_project_dir(project_dir: str | Path) -> Path:
    resolved = Path(project_dir).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Project directory does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {resolved}")
    return resolved


def analyze_project(project_dir: str | Path) -> AnalysisReport:
    """Analyze a project path and return a stable inference report.

    The analyzer is intentionally side-effect free: no writes, prompts, network,
    or runtime execution. It only returns inference metadata.
    """
    resolved_project_dir = _validate_project_dir(project_dir)

    inferred: dict[str, Any] = {}
    confidence: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    for field_name, detector in _detector_registry().items():
        result = detector(resolved_project_dir)
        inferred[field_name] = result.value
        confidence[field_name] = {
            "score": float(result.confidence),
            "evidence": result.evidence,
        }
        if result.warning:
            warnings.append(result.warning)

    return AnalysisReport(inferred=inferred, confidence=confidence, warnings=warnings)


_ADAPTER_MINIMUM_COVERAGE: dict[str, float] = {
    "langchain": 0.6,
    "langgraph": 0.6,
    "openai": 0.6,
}


_ADAPTER_DEFAULT_GUIDANCE: dict[str, list[str]] = {
    "langchain": [
        "Confirm provider model configuration and related env vars before first run.",
    ],
    "langgraph": [
        "Validate graph state model and graph entrypoint wiring before packaging.",
    ],
    "openai": [
        "Verify OpenAI credentials and tool contract wiring before first run.",
    ],
}


def adapter_minimum_coverage(framework: str) -> float:
    """Return minimum adapter coverage threshold required to override generic analysis."""
    return float(_ADAPTER_MINIMUM_COVERAGE.get(framework, 0.6))


def adapter_default_unresolved_guidance(framework: str) -> list[str]:
    """Return deterministic default unresolved guidance for framework adapter flows."""
    return list(_ADAPTER_DEFAULT_GUIDANCE.get(framework, []))
