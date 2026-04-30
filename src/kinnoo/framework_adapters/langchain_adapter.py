from __future__ import annotations

from pathlib import Path

from . import AdapterResult, read_text_files


LANGCHAIN_MARKERS = (
    "import langchain",
    "from langchain",
    "import langchain_core",
    "from langchain_core",
    "import langchain_openai",
    "from langchain_openai",
    "import langchain_anthropic",
    "from langchain_anthropic",
    "import langchain_community",
    "from langchain_community",
    "import langchain_google_genai",
    "from langchain_google_genai",
)


def apply(project_dir: Path, base_report: dict[str, object]) -> AdapterResult:
    sources = read_text_files(project_dir, {".py"})
    marker_hits = sum(1 for marker in LANGCHAIN_MARKERS if any(marker in source for source in sources))
    viability_hits = sum(
        1
        for marker in ("Chain(", "AgentExecutor", "Runnable", "create_react_agent", ".invoke(", ".stream(")
        if any(marker in source for source in sources)
    )

    if marker_hits <= 0:
        return AdapterResult(
            framework="langchain",
            detected=False,
            coverage_score=0.0,
            inferred_overrides={},
            confidence_overrides={},
            warnings=[],
            unresolved_guidance=[
                "LangChain adapter could not confirm package markers and runnable chain signals; using generic analyzer.",
            ],
        )

    inferred = base_report.get("inferred", {}) if isinstance(base_report.get("inferred"), dict) else {}
    existing_dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    existing_env_vars = inferred.get("env_vars") if isinstance(inferred.get("env_vars"), list) else []
    dependencies = list(existing_dependencies)
    env_vars = list(existing_env_vars)

    subpackage_to_dependency = (
        ("langchain_openai", "langchain-openai", "OPENAI_API_KEY"),
        ("langchain_anthropic", "langchain-anthropic", "ANTHROPIC_API_KEY"),
        ("langchain_google_genai", "langchain-google-genai", "GOOGLE_API_KEY"),
        ("langchain_community", "langchain-community", None),
    )
    for module_marker, dependency_name, env_var in subpackage_to_dependency:
        if any(module_marker in source for source in sources):
            if dependency_name not in dependencies:
                dependencies.append(dependency_name)
            if env_var and env_var not in env_vars:
                env_vars.append(env_var)

    if "langchain" not in dependencies:
        dependencies.append("langchain")
    if "langchain-core" not in dependencies:
        dependencies.append("langchain-core")

    inferred_overrides = {
        "framework": "langchain",
        "runtime": {
            "language": "python",
            "type": "one-shot",
            "version": ">=3.10",
        },
        "dependencies": dependencies,
        "env_vars": env_vars,
    }

    confidence_overrides = {
        "framework": {
            "score": 0.96,
            "evidence": (
                f"LangChain adapter markers matched ({marker_hits} package signal(s), "
                f"{viability_hits} viability signal(s))."
            ),
        },
        "runtime": {
            "score": 0.9,
            "evidence": "LangChain adapter enforces Python one-shot runtime defaults.",
        },
    }

    return AdapterResult(
        framework="langchain",
        detected=True,
        coverage_score=min(
            1.0,
            (0.62 + 0.08 * marker_hits) if viability_hits <= 0 else (0.5 + 0.08 * marker_hits + 0.1 * viability_hits),
        ),
        inferred_overrides=inferred_overrides,
        confidence_overrides=confidence_overrides,
        warnings=(
            []
            if viability_hits > 0
            else ["LangChain viability signal was not detected; verify runnable chain/agent construction."]
        ),
        unresolved_guidance=[
            "Verify model/provider env vars (for example OPENAI_API_KEY) before first run.",
        ],
    )
