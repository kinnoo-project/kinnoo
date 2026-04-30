from __future__ import annotations

from pathlib import Path

from . import AdapterResult, detect_node_package_manager, read_text_files


LANGGRAPH_PY_MARKERS = (
    "import langgraph",
    "from langgraph",
    "StateGraph",
)

LANGGRAPH_TS_MARKERS = (
    "@langchain/langgraph",
    "StateGraph",
)
COMPILE_MARKERS = (".compile(",)


def apply(project_dir: Path, base_report: dict[str, object]) -> AdapterResult:
    inferred = base_report.get("inferred", {}) if isinstance(base_report.get("inferred"), dict) else {}
    python_sources = read_text_files(project_dir, {".py"})
    node_sources = read_text_files(project_dir, {".ts", ".tsx", ".js", ".mjs", ".cjs"})

    py_hits = sum(1 for marker in LANGGRAPH_PY_MARKERS if any(marker in source for source in python_sources))
    node_hits = sum(1 for marker in LANGGRAPH_TS_MARKERS if any(marker in source for source in node_sources))
    py_compile_hits = sum(1 for marker in COMPILE_MARKERS if any(marker in source for source in python_sources))
    node_compile_hits = sum(1 for marker in COMPILE_MARKERS if any(marker in source for source in node_sources))
    compile_hits = py_compile_hits + node_compile_hits

    if py_hits <= 0 and node_hits <= 0:
        return AdapterResult(
            framework="langgraph",
            detected=False,
            coverage_score=0.0,
            inferred_overrides={},
            confidence_overrides={},
            warnings=[],
            unresolved_guidance=[
                "LangGraph adapter could not confirm graph markers with compile() viability signals; using generic analyzer.",
            ],
        )

    inferred_runtime: dict[str, object]
    runtime_evidence: str
    runtime_score: float
    if node_hits > py_hits:
        inferred_runtime = {
            "language": "nodejs",
            "type": "one-shot",
            "version": ">=20.0.0",
            "package_manager": detect_node_package_manager(project_dir),
        }
        runtime_evidence = "LangGraph adapter selected Node.js runtime based on JS/TS graph markers."
        runtime_score = 0.9
    else:
        inferred_runtime = {
            "language": "python",
            "type": "one-shot",
            "version": ">=3.10",
        }
        runtime_evidence = "LangGraph adapter selected Python runtime based on Python graph markers."
        runtime_score = 0.9

    inferred_overrides = {
        "framework": "langgraph",
        "runtime": inferred_runtime,
    }
    existing_dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    dependencies = list(existing_dependencies)
    dependency_name = "langgraph" if node_hits <= py_hits else "@langchain/langgraph"
    if dependency_name not in dependencies:
        dependencies.append(dependency_name)
    inferred_overrides["dependencies"] = dependencies

    confidence_overrides = {
        "framework": {
            "score": 0.95,
            "evidence": (
                "LangGraph adapter markers matched "
                f"(python={py_hits}, node={node_hits}, compile={compile_hits})."
            ),
        },
        "runtime": {
            "score": runtime_score,
            "evidence": runtime_evidence,
        },
    }

    return AdapterResult(
        framework="langgraph",
        detected=True,
        coverage_score=min(
            1.0,
            (
                0.62 + 0.08 * (py_hits + node_hits)
                if compile_hits <= 0
                else 0.45 + 0.12 * (py_hits + node_hits) + 0.2 * compile_hits
            ),
        ),
        inferred_overrides=inferred_overrides,
        confidence_overrides=confidence_overrides,
        warnings=(
            []
            if compile_hits > 0
            else ["LangGraph compile() signal was not detected; verify graph construction viability."]
        ),
        unresolved_guidance=[
            "Validate graph entrypoint wiring and state schema before packaging.",
        ],
    )
