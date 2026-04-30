from __future__ import annotations

from pathlib import Path
import re

from . import AdapterResult, detect_node_package_manager, read_text_files


OPENAI_PY_MARKERS = (
    "from agents import",
    "import agents",
    "from openai import",
    "import openai",
)

OPENAI_TS_MARKERS = (
    "from 'openai'",
    'from "openai"',
    "@openai/agents",
)


def apply(project_dir: Path, base_report: dict[str, object]) -> AdapterResult:
    inferred = base_report.get("inferred", {}) if isinstance(base_report.get("inferred"), dict) else {}
    python_sources = read_text_files(project_dir, {".py"})
    node_sources = read_text_files(project_dir, {".ts", ".tsx", ".js", ".mjs", ".cjs"})

    py_hits = sum(1 for marker in OPENAI_PY_MARKERS if any(marker in source for source in python_sources))
    node_hits = sum(1 for marker in OPENAI_TS_MARKERS if any(marker in source for source in node_sources))
    has_agents_import_signal = any(
        marker in source
        for marker in ("from agents import", "import agents")
        for source in python_sources
    ) or any(
        marker in source
        for marker in ("@openai/agents",)
        for source in node_sources
    )
    agent_ctor_pattern = re.compile(r"\b(?:new\s+)?Agent\s*\(")
    agent_symbol_usage_pattern = re.compile(r"\bAgent\b")
    import_line_pattern = re.compile(r"^\s*(?:from\s+agents\s+import|import\s+agents\b|import\s+\{[^}]*Agent[^}]*\}\s+from)\b")

    def _has_agent_instantiation(sources: list[str]) -> bool:
        for source in sources:
            for line in source.splitlines():
                if import_line_pattern.search(line):
                    continue
                if agent_ctor_pattern.search(line) or agent_symbol_usage_pattern.search(line):
                    return True
        return False

    has_agent_viability_signal = _has_agent_instantiation(python_sources) or _has_agent_instantiation(node_sources)

    if py_hits <= 0 and node_hits <= 0:
        return AdapterResult(
            framework="openai",
            detected=False,
            coverage_score=0.0,
            inferred_overrides={},
            confidence_overrides={},
            warnings=[],
            unresolved_guidance=[
                "OpenAI adapter could not confirm SDK markers; using generic analyzer.",
            ],
        )

    inferred_runtime: dict[str, object]
    runtime_evidence: str
    if node_hits > py_hits:
        inferred_runtime = {
            "language": "nodejs",
            "type": "one-shot",
            "version": ">=20.0.0",
            "package_manager": detect_node_package_manager(project_dir),
        }
        runtime_evidence = "OpenAI adapter selected Node.js runtime from JS/TS SDK markers."
    else:
        inferred_runtime = {
            "language": "python",
            "type": "one-shot",
            "version": ">=3.10",
        }
        runtime_evidence = "OpenAI adapter selected Python runtime from SDK markers."

    inferred_framework = "openai-agents" if has_agents_import_signal and has_agent_viability_signal else "openai"
    existing_dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    dependencies = list(existing_dependencies)
    if "openai" not in dependencies:
        dependencies.append("openai")
    if inferred_framework == "openai-agents" and "openai-agents" not in dependencies:
        dependencies.append("openai-agents")

    env_vars = inferred.get("env_vars") if isinstance(inferred.get("env_vars"), list) else []
    normalized_env_vars = list(env_vars)
    if "OPENAI_API_KEY" not in normalized_env_vars:
        normalized_env_vars.append("OPENAI_API_KEY")

    inferred_overrides = {
        "framework": inferred_framework,
        "runtime": inferred_runtime,
        "dependencies": dependencies,
        "env_vars": normalized_env_vars,
    }

    confidence_overrides = {
        "framework": {
            "score": 0.94,
            "evidence": (
                "OpenAI adapter markers matched "
                f"(python={py_hits}, node={node_hits}, "
                f"agents_import={int(has_agents_import_signal)}, agents_viable={int(has_agent_viability_signal)})."
            ),
        },
        "runtime": {
            "score": 0.88,
            "evidence": runtime_evidence,
        },
    }

    return AdapterResult(
        framework="openai",
        detected=True,
        coverage_score=min(1.0, 0.55 + 0.15 * (py_hits + node_hits)),
        inferred_overrides=inferred_overrides,
        confidence_overrides=confidence_overrides,
        warnings=[],
        unresolved_guidance=[
            (
                "Confirm OpenAI credentials and tool wiring before first runtime execution."
                if inferred_framework == "openai-agents"
                else (
                    "Detected OpenAI SDK usage without Agent() viability markers; "
                    "treated as base OpenAI integration."
                    if has_agents_import_signal and not has_agent_viability_signal
                    else "Confirm OpenAI API key and model configuration before first runtime execution."
                )
            ),
        ],
    )
