from pathlib import Path

from kinnoo.analyzer import AnalysisReport, analyze_project, infer_openclaw_project_hints


def _create_minimal_project_fixture(base_dir: Path) -> Path:
    project_dir = base_dir / "feature27-minimal-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")
    return project_dir


def _feature19_style_adapter(project_dir: Path) -> dict[str, object]:
    # Adapter intentionally consumes analyzer output contract directly and stays
    # free from detector duplication or CLI coupling.
    report = analyze_project(project_dir)
    return report.as_dict()


def test_feature27_analyzer_public_api_and_detector_hooks(tmp_path: Path) -> None:
    """test243: analyzer API is importable and returns detector-oriented report sections."""
    project_dir = _create_minimal_project_fixture(tmp_path)
    report = analyze_project(project_dir)

    assert isinstance(report, AnalysisReport)
    payload = report.as_dict()

    assert set(payload.keys()) == {"inferred", "confidence", "warnings"}

    expected_detector_fields = {
        "entrypoint",
        "runtime",
        "framework",
        "model",
        "dependencies",
        "deps_type",
        "inputs",
        "inputs_required",
        "async_entrypoint",
        "outputs",
        "env_vars",
        "assets",
        "services",
    }
    assert set(payload["inferred"].keys()) == expected_detector_fields
    assert set(payload["confidence"].keys()) == expected_detector_fields


def test_feature27_report_sections_are_stable(tmp_path: Path) -> None:
    """test249: report schema keeps stable inferred/confidence/warnings sections."""
    project_dir = _create_minimal_project_fixture(tmp_path)
    payload = analyze_project(project_dir).as_dict()

    assert isinstance(payload["inferred"], dict)
    assert isinstance(payload["confidence"], dict)
    assert isinstance(payload["warnings"], list)

    for field_name, metadata in payload["confidence"].items():
        assert isinstance(metadata, dict), f"confidence metadata for {field_name} must be a dict"
        assert "score" in metadata
        assert "evidence" in metadata
        assert isinstance(metadata["score"], float)
        assert isinstance(metadata["evidence"], str)


def test_feature27_analyzer_reusable_for_feature19_import_flow(tmp_path: Path) -> None:
    """test250: analyzer can be consumed through a non-CLI adapter path."""
    project_dir = _create_minimal_project_fixture(tmp_path)
    adapter_payload = _feature19_style_adapter(project_dir)

    assert set(adapter_payload.keys()) == {"inferred", "confidence", "warnings"}
    assert "entrypoint" in adapter_payload["inferred"]
    assert "runtime" in adapter_payload["inferred"]


def test_feature27_detect_entrypoint_runtime_framework_with_uncertainty(tmp_path: Path) -> None:
    """test244: detectors infer clear layouts and downgrade confidence for ambiguous ones."""
    clear_project = tmp_path / "feature27-clear-layout"
    clear_project.mkdir(parents=True, exist_ok=True)
    (clear_project / "run.py").write_text(
        "import openai\n"
        "RUNTIME_PORT = 8765\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (clear_project / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'clear-layout'\n"
        "requires-python = '>=3.11'\n",
        encoding="utf-8",
    )

    clear_payload = analyze_project(clear_project).as_dict()
    assert clear_payload["inferred"]["entrypoint"] == "run.py"
    assert clear_payload["inferred"]["runtime"]["language"] == "python"
    assert clear_payload["inferred"]["runtime"]["type"] == "one-shot"
    assert clear_payload["inferred"]["runtime"]["version"] == ">=3.11"
    assert clear_payload["inferred"]["runtime"]["port"] == 8765
    assert clear_payload["inferred"]["framework"] == "chatgpt"
    assert clear_payload["confidence"]["entrypoint"]["score"] >= 0.9
    assert clear_payload["confidence"]["runtime"]["score"] >= 0.8
    assert clear_payload["confidence"]["framework"]["score"] >= 0.8

    ambiguous_project = tmp_path / "feature27-ambiguous-layout"
    ambiguous_project.mkdir(parents=True, exist_ok=True)
    (ambiguous_project / "app.py").write_text(
        "import openai\n"
        "if __name__ == '__main__':\n"
        "    print('app')\n",
        encoding="utf-8",
    )
    (ambiguous_project / "worker.py").write_text(
        "import anthropic\n"
        "if __name__ == '__main__':\n"
        "    print('worker')\n",
        encoding="utf-8",
    )

    ambiguous_payload = analyze_project(ambiguous_project).as_dict()
    assert ambiguous_payload["inferred"]["entrypoint"] == "app.py"
    assert ambiguous_payload["inferred"]["framework"] is None
    assert ambiguous_payload["confidence"]["entrypoint"]["score"] >= 0.7
    assert ambiguous_payload["confidence"]["runtime"]["score"] >= 0.8
    assert ambiguous_payload["confidence"]["framework"]["score"] < 0.5
    warning_text = " ".join(ambiguous_payload["warnings"]).lower()
    assert "ambiguous" in warning_text


def test_feature27_detect_dependencies_from_requirements_and_pyproject(tmp_path: Path) -> None:
    """test245: dependency detector merges requirements and pyproject with normalization/dedup."""
    project_dir = tmp_path / "feature27-dependency-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "requirements.txt").write_text(
        "requests>=2.31\n"
        "PyYAML==6.0\n"
        "# comment line\n"
        "\n",
        encoding="utf-8",
    )
    (project_dir / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'dep-layout'\n"
        "dependencies = ['requests>=2.30', 'tomli>=2.0']\n"
        "\n"
        "[project.optional-dependencies]\n"
        "dev = ['pytest>=8.0']\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    dependencies = payload["inferred"]["dependencies"]

    assert "requests>=2.30" in dependencies or "requests>=2.31" in dependencies
    assert "pyyaml==6.0" in dependencies
    assert "tomli>=2.0" in dependencies
    assert "pytest>=8.0" in dependencies
    assert dependencies == sorted(set(dependencies))
    assert payload["confidence"]["dependencies"]["score"] >= 0.8


def test_feature27_detect_env_vars_patterns_and_dedup(tmp_path: Path) -> None:
    """test246: env var detector handles getenv/environ access and deduplicates names."""
    project_dir = tmp_path / "feature27-env-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "import os\n"
        "token = os.getenv('API_TOKEN')\n"
        "key = os.environ['OPENAI_API_KEY']\n"
        "region = os.environ.get('AWS_REGION')\n"
        "token_again = os.getenv('API_TOKEN', '')\n",
        encoding="utf-8",
    )
    (project_dir / "worker.py").write_text(
        "import os\n"
        "project = os.environ.get('GOOGLE_CLOUD_PROJECT')\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    env_vars = payload["inferred"]["env_vars"]

    assert env_vars == sorted(env_vars)
    assert env_vars == [
        "API_TOKEN",
        "AWS_REGION",
        "GOOGLE_CLOUD_PROJECT",
        "OPENAI_API_KEY",
    ]
    assert payload["confidence"]["env_vars"]["score"] >= 0.8


def test_feature27_detect_assets_with_path_safety_filter(tmp_path: Path) -> None:
    """test247: asset detector infers safe model/data candidates and filters unsafe path literals."""
    project_dir = tmp_path / "feature27-assets-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "models").mkdir()
    (project_dir / "data").mkdir()
    (project_dir / "models" / "model.onnx").write_text("binary-placeholder", encoding="utf-8")
    (project_dir / "data" / "train.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    (project_dir / "run.py").write_text(
        "MODEL_PATH = 'models/model.onnx'\n"
        "SAFE_DATA = 'data/train.csv'\n"
        "UNSAFE = '../secrets/api-key.txt'\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assets = payload["inferred"]["assets"]

    assert "models" in assets
    assert "data" in assets
    assert "models/model.onnx" in assets
    assert "data/train.csv" in assets
    assert all(".." not in asset for asset in assets)
    warning_text = " ".join(payload["warnings"]).lower()
    assert "unsafe asset path" in warning_text
    assert payload["confidence"]["assets"]["score"] >= 0.7


def test_feature27_detect_services_with_health_check_hints(tmp_path: Path) -> None:
    """test248: service detector infers endpoints with actionable health-check hints."""
    project_dir = tmp_path / "feature27-services-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "REDIS_URL = 'redis://localhost:6379/0'\n"
        "DB_DSN = 'postgresql://user:pass@db.local:5432/app'\n"
        "HEALTH_URL = 'https://api.example.com/health'\n"
        "STATUS_URL = 'https://api.example.com/v1/status'\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    services = payload["inferred"]["services"]

    def find_service(service_type: str, endpoint_prefix: str) -> dict[str, object]:
        return next(
            service
            for service in services
            if service["type"] == service_type and str(service["endpoint"]).startswith(endpoint_prefix)
        )

    redis_service = find_service("redis", "redis://")
    postgres_service = find_service("postgres", "postgresql://")
    health_service = find_service("http", "https://api.example.com/health")
    status_service = find_service("http", "https://api.example.com/v1/status")

    assert redis_service["health_check_hint"] == "PING"
    assert postgres_service["health_check_hint"] == "SELECT 1"
    assert health_service["health_check_hint"] == "GET /health"
    assert "health_check_hint" not in status_service
    assert payload["confidence"]["services"]["score"] >= 0.7


def test_feature27_detector_matrix_positive_and_ambiguous(tmp_path: Path) -> None:
    """test251: matrix-style detector coverage validates positive/ambiguous outcomes and diagnostics."""
    positive = tmp_path / "feature27-matrix-positive"
    positive.mkdir(parents=True, exist_ok=True)
    (positive / "models").mkdir()
    (positive / "data").mkdir()
    (positive / "models" / "agent.onnx").write_text("model", encoding="utf-8")
    (positive / "data" / "dataset.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (positive / "requirements.txt").write_text("requests>=2.31\n", encoding="utf-8")
    (positive / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'matrix-positive'\n"
        "requires-python = '>=3.11'\n"
        "dependencies = ['tomli>=2.0']\n",
        encoding="utf-8",
    )
    (positive / "run.py").write_text(
        "import openai\n"
        "import os\n"
        "PORT = 8080\n"
        "API_KEY = os.getenv('OPENAI_API_KEY')\n"
        "REDIS_URL = 'redis://localhost:6379/0'\n"
        "HEALTH_URL = 'https://service.example.com/healthz'\n"
        "MODEL_PATH = 'models/agent.onnx'\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )

    positive_payload = analyze_project(positive).as_dict()
    assert positive_payload["inferred"]["entrypoint"] == "run.py"
    assert positive_payload["inferred"]["runtime"]["language"] == "python"
    assert positive_payload["inferred"]["runtime"]["type"] == "one-shot"
    assert positive_payload["inferred"]["framework"] == "chatgpt"
    assert "requests>=2.31" in positive_payload["inferred"]["dependencies"]
    assert "tomli>=2.0" in positive_payload["inferred"]["dependencies"]
    assert "OPENAI_API_KEY" in positive_payload["inferred"]["env_vars"]
    assert "models/agent.onnx" in positive_payload["inferred"]["assets"]
    assert any(service["type"] == "redis" for service in positive_payload["inferred"]["services"])
    assert any(
        service.get("health_check_hint") == "GET /healthz"
        for service in positive_payload["inferred"]["services"]
        if service["type"] == "http"
    )
    for required_field in {
        "entrypoint",
        "runtime",
        "framework",
        "dependencies",
        "env_vars",
        "assets",
        "services",
    }:
        assert positive_payload["confidence"][required_field]["score"] > 0.0

    for optional_field in {"model", "inputs", "outputs"}:
        assert positive_payload["confidence"][optional_field]["score"] >= 0.0

    ambiguous = tmp_path / "feature27-matrix-ambiguous"
    ambiguous.mkdir(parents=True, exist_ok=True)
    (ambiguous / "app.py").write_text(
        "import openai\n"
        "if __name__ == '__main__':\n"
        "    print('app')\n"
        "UNSAFE_PATH = '../outside/secrets.txt'\n",
        encoding="utf-8",
    )
    (ambiguous / "worker.py").write_text(
        "import anthropic\n"
        "if __name__ == '__main__':\n"
        "    print('worker')\n",
        encoding="utf-8",
    )

    ambiguous_payload = analyze_project(ambiguous).as_dict()
    assert ambiguous_payload["inferred"]["entrypoint"] == "app.py"
    assert ambiguous_payload["inferred"]["framework"] is None
    assert "openai" in ambiguous_payload["inferred"]["dependencies"]
    assert "anthropic" in ambiguous_payload["inferred"]["dependencies"]
    assert ambiguous_payload["inferred"]["env_vars"] == []
    assert ambiguous_payload["confidence"]["entrypoint"]["score"] >= 0.7
    assert ambiguous_payload["confidence"]["framework"]["score"] < 0.5

    diagnostics_text = " ".join(ambiguous_payload["warnings"] + [
        ambiguous_payload["confidence"]["entrypoint"]["evidence"],
        ambiguous_payload["confidence"]["framework"]["evidence"],
        ambiguous_payload["confidence"]["dependencies"]["evidence"],
        ambiguous_payload["confidence"]["assets"]["evidence"],
    ]).lower()
    assert "ambiguous" in diagnostics_text
    assert "dependencies" in diagnostics_text or "requirements.txt" in diagnostics_text
    assert "unsafe asset path" in diagnostics_text or "assets" in diagnostics_text


def test_feature36_openclaw_weighted_detection_scores(tmp_path: Path) -> None:
    strong_project = tmp_path / "feature36-openclaw-strong"
    strong_project.mkdir(parents=True, exist_ok=True)
    (strong_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (strong_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-strong\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (strong_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (strong_project / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (strong_project / "memory").mkdir(parents=True, exist_ok=True)
    (strong_project / "run.py").write_text("print('hello')\n", encoding="utf-8")

    strong_report = analyze_project(strong_project).as_dict()
    assert strong_report["inferred"]["framework"] == "openclaw"
    assert strong_report["confidence"]["framework"]["score"] >= 0.6
    strong_evidence = str(strong_report["confidence"]["framework"]["evidence"]).lower()
    assert "weighted detection score" in strong_evidence
    assert "openclaw.json" in strong_evidence
    assert "package.json" in strong_evidence

    medium_only_project = tmp_path / "feature36-openclaw-medium-only"
    medium_only_project.mkdir(parents=True, exist_ok=True)
    (medium_only_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (medium_only_project / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (medium_only_project / "memory").mkdir(parents=True, exist_ok=True)
    (medium_only_project / "run.py").write_text("print('hello')\n", encoding="utf-8")

    medium_report = analyze_project(medium_only_project).as_dict()
    assert medium_report["inferred"]["framework"] is None
    medium_score = medium_report["confidence"]["framework"]["score"]
    assert 0.2 <= medium_score < 0.6
    medium_warnings = " ".join(medium_report["warnings"]).lower()
    assert "openclaw detection confidence is mixed" in medium_warnings


def test_feature36_openclaw_hint_inference_runtime_package_manager_skills_state_dirs(tmp_path: Path) -> None:
    project_dir = tmp_path / "feature36-openclaw-hints"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (project_dir / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-hints\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (project_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (project_dir / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (project_dir / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (project_dir / "memory").mkdir(parents=True, exist_ok=True)

    hints = infer_openclaw_project_hints(project_dir)
    runtime = hints["runtime"]

    assert hints["confidence"] >= 0.6
    assert "openclaw.json" in hints["evidence"]
    assert runtime["language"] == "nodejs"
    assert runtime["type"] == "daemon"
    assert runtime["package_manager"] == "pnpm"
    assert runtime["version"] == ">=20.0.0"
    assert hints["skills"] == ["skills/default/SKILL.md"]
    assert hints["state_dirs"] == ["memory"]


def test_feature36_identity_signal_detection(tmp_path: Path) -> None:
    with_user_project = tmp_path / "feature36-openclaw-identity-with-user"
    with_user_project.mkdir(parents=True, exist_ok=True)
    (with_user_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (with_user_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-identity-with-user\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (with_user_project / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (with_user_project / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (with_user_project / "USER.md").write_text("# User\n", encoding="utf-8")

    with_user_report = analyze_project(with_user_project).as_dict()
    with_user_evidence = str(with_user_report["confidence"]["framework"]["evidence"])
    assert "identity-file:SOUL.md" in with_user_evidence
    assert "identity-file:AGENTS.md" in with_user_evidence
    assert "identity-file:USER.md" in with_user_evidence

    no_user_project = tmp_path / "feature36-openclaw-identity-no-user"
    no_user_project.mkdir(parents=True, exist_ok=True)
    (no_user_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (no_user_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-identity-no-user\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (no_user_project / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (no_user_project / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")

    no_user_report = analyze_project(no_user_project).as_dict()
    no_user_evidence = str(no_user_report["confidence"]["framework"]["evidence"])
    assert no_user_report["inferred"]["framework"] == "openclaw"
    assert no_user_report["confidence"]["framework"]["score"] >= 0.6
    assert "identity-file:SOUL.md" in no_user_evidence
    assert "identity-file:AGENTS.md" in no_user_evidence
    assert "identity-file:USER.md" not in no_user_evidence


def test_framework_prefers_langchain_when_openai_and_langchain_both_present(tmp_path: Path) -> None:
    project_dir = tmp_path / "framework-langchain-plus-openai"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "from langchain_core.agents import AgentAction\n"
        "print(AgentAction)\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assert payload["inferred"]["framework"] == "langchain"
    assert payload["confidence"]["framework"]["score"] >= 0.85


def test_dependency_inference_uses_known_import_namespaces(tmp_path: Path) -> None:
    project_dir = tmp_path / "deps-from-imports-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "import anthropic\n"
        "from langchain_core.agents import AgentAction\n"
        "from langchain_openai import ChatOpenAI\n"
        "print(AgentAction, ChatOpenAI)\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    dependencies = payload["inferred"]["dependencies"]

    assert "openai" in dependencies
    assert "anthropic" in dependencies
    assert "langchain-core" in dependencies
    assert "langchain-openai" in dependencies
    assert payload["confidence"]["dependencies"]["score"] > 0.6


def _write_openclaw_like_readme(project_dir: Path) -> None:
    (project_dir / "README.source.md").write_text(
        "# OpenClaw derivative\n"
        "This project integrates OpenClaw gateway patterns.\n"
        "OpenClaw onboarding and OpenClaw runtime behavior are documented here.\n",
        encoding="utf-8",
    )


def test_feature47_openclaw_like_selfclaw_layout_inference(tmp_path: Path) -> None:
    """test410: selfclaw-like nested server layout infers openclaw metadata without root package.json."""
    project_dir = tmp_path / "feature47-openclaw-like-selfclaw"
    (project_dir / "server").mkdir(parents=True, exist_ok=True)
    _write_openclaw_like_readme(project_dir)

    (project_dir / "server" / "boot.mjs").write_text(
        "console.log('boot');\n",
        encoding="utf-8",
    )
    (project_dir / "server" / "index.ts").write_text(
        "export const started = true;\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assert payload["inferred"]["framework"] == "openclaw"
    assert payload["inferred"]["runtime"]["language"] == "nodejs"
    assert payload["inferred"]["entrypoint"] == "server/boot.mjs"
    assert payload["inferred"]["inputs"] == "text"


def test_feature47_openclaw_like_nanobot_layout_inference(tmp_path: Path) -> None:
    """test411: nanobot-like bridge layout infers node runtime and nested server entrypoint."""
    project_dir = tmp_path / "feature47-openclaw-like-nanobot"
    (project_dir / "bridge" / "src").mkdir(parents=True, exist_ok=True)
    _write_openclaw_like_readme(project_dir)

    (project_dir / "bridge" / "src" / "server.ts").write_text(
        "export const bridgeServer = true;\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assert payload["inferred"]["framework"] == "openclaw"
    assert payload["inferred"]["runtime"]["language"] == "nodejs"
    assert payload["inferred"]["entrypoint"] == "bridge/src/server.ts"


def test_feature47_openclaw_like_build_your_own_layout_inference(tmp_path: Path) -> None:
    """test412: build-your-own style deep tutorial layout still infers node runtime and entrypoint."""
    project_dir = tmp_path / "feature47-openclaw-like-build-your-own"
    nested_dir = project_dir / "11-multi-agent-routing" / "src" / "mybot" / "cli"
    nested_dir.mkdir(parents=True, exist_ok=True)
    _write_openclaw_like_readme(project_dir)

    (nested_dir / "index.ts").write_text(
        "export const run = () => 'ok';\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assert payload["inferred"]["runtime"]["language"] == "nodejs"
    assert payload["inferred"]["framework"] == "openclaw"
    assert payload["inferred"]["entrypoint"] == "11-multi-agent-routing/src/mybot/cli/index.ts"


def test_feature47_openclaw_like_core_layout_inference(tmp_path: Path) -> None:
    """test413: openclaw-core-like src layout prefers src/entry.ts over generic index.ts."""
    project_dir = tmp_path / "feature47-openclaw-like-core"
    (project_dir / "src").mkdir(parents=True, exist_ok=True)
    _write_openclaw_like_readme(project_dir)

    (project_dir / "src" / "entry.ts").write_text(
        "export const entry = true;\n",
        encoding="utf-8",
    )
    (project_dir / "src" / "index.ts").write_text(
        "export const index = true;\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assert payload["inferred"]["framework"] == "openclaw"
    assert payload["inferred"]["runtime"]["language"] == "nodejs"
    assert payload["inferred"]["entrypoint"] == "src/entry.ts"


def test_feature117_langgraph_compile_detection_py_and_node(tmp_path: Path) -> None:
    python_project = tmp_path / "feature117-langgraph-python"
    python_project.mkdir(parents=True, exist_ok=True)
    (python_project / "graph.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "builder = StateGraph(dict)\n"
        "compiled = builder.compile()\n"
        "print(compiled)\n",
        encoding="utf-8",
    )
    py_payload = analyze_project(python_project).as_dict()
    assert py_payload["inferred"]["framework"] == "langgraph"

    node_project = tmp_path / "feature117-langgraph-node"
    node_project.mkdir(parents=True, exist_ok=True)
    (node_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature117-langgraph-node\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@langchain/langgraph\": \"^0.2.0\",\n"
        "    \"@langchain/core\": \"^0.3.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (node_project / "graph.ts").write_text(
        "import { StateGraph } from '@langchain/langgraph';\n"
        "const graph = new StateGraph({});\n"
        "const app = graph.compile();\n"
        "console.log(app);\n",
        encoding="utf-8",
    )
    node_payload = analyze_project(node_project).as_dict()
    assert node_payload["inferred"]["framework"] == "langgraph"
    assert node_payload["inferred"]["framework"] != "langchain"


def test_feature117_poetry_dependency_extraction(tmp_path: Path) -> None:
    project_dir = tmp_path / "feature117-poetry-dependencies"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('poetry')\n", encoding="utf-8")
    (project_dir / "pyproject.toml").write_text(
        "[tool.poetry]\n"
        "name = \"feature117-poetry\"\n"
        "version = \"0.1.0\"\n"
        "\n"
        "[tool.poetry.dependencies]\n"
        "python = \">=3.11\"\n"
        "openai = \"^1.40.0\"\n"
        "langchain-openai = \"^0.2.0\"\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    dependencies = payload["inferred"]["dependencies"]
    assert any(dep.startswith("openai") for dep in dependencies)
    assert any(dep.startswith("langchain-openai") for dep in dependencies)
