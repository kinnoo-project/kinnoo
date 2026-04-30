from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .analyzer import analyze_project
from .import_command import clone_github_repo, github_repo_dir_name, is_github_url
from .inspect_command import inspect_target
from .run_command import run_preflight
from .terminal_colors import style_text


def _emit_step_result(step: str, passed: bool, detail: str, guidance: str | None = None) -> None:
    status = "PASS" if passed else "FAIL"
    color = "green" if passed else "red"
    print(style_text(f"- [{status}] {step}: {detail}", color=color))
    if not passed and guidance:
        print(style_text(f"  - Guidance: {guidance}", color="yellow"))


def _prepare_check_target(target: str) -> tuple[Path | None, str | None]:
    if is_github_url(target):
        repo_dir_name = github_repo_dir_name(target)
        temp_root = Path(tempfile.gettempdir()) / "kinnoo-agent-check"
        temp_root.mkdir(parents=True, exist_ok=True)
        destination = temp_root / repo_dir_name

        if destination.exists():
            shutil.rmtree(destination)

        cloned, clone_error = clone_github_repo(target, destination)
        if not cloned:
            return None, (
                "failed to clone check target from GitHub URL: "
                f"{clone_error}"
            )
        return destination, None

    local_path = Path(target).expanduser().resolve()
    if not local_path.exists() or not local_path.is_dir():
        return None, f"target path does not exist or is not a directory: {local_path}"
    return local_path, None


def check_target(target: str) -> int:
    """Run import-compatibility, inspect, and preflight checks for a target."""
    print(style_text("Kinnoo compatibility check:", color="cyan", bold=True))
    working_dir, error = _prepare_check_target(target)
    if error is not None or working_dir is None:
        _emit_step_result(
            "target preparation",
            False,
            error or "unable to prepare target",
            guidance="verify path/URL and credentials, then retry",
        )
        print(style_text("Check result: FAIL", color="red", bold=True))
        return 1

    _emit_step_result("target preparation", True, f"using target: {working_dir}")

    import_check_ok = False
    try:
        report = analyze_project(working_dir).as_dict()
        inferred = report.get("inferred", {})
        entrypoint = inferred.get("entrypoint")
        runtime = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
        language = runtime.get("language") if isinstance(runtime.get("language"), str) else None

        if isinstance(entrypoint, str) and entrypoint.strip() and isinstance(language, str) and language.strip():
            import_check_ok = True
            _emit_step_result(
                "import compatibility",
                True,
                f"analyzer inferred entrypoint={entrypoint} runtime.language={language}",
            )
        else:
            _emit_step_result(
                "import compatibility",
                False,
                "analyzer could not infer a clear entrypoint/runtime combination",
                guidance="add a runnable entrypoint and explicit runtime metadata before import",
            )
    except Exception as exc:
        _emit_step_result(
            "import compatibility",
            False,
            f"analyzer error: {exc}",
            guidance="resolve syntax/project structure issues and rerun check",
        )

    inspect_exit = inspect_target(str(working_dir))
    inspect_ok = inspect_exit == 0
    _emit_step_result(
        "inspect",
        inspect_ok,
        "inspect command succeeded" if inspect_ok else "inspect command failed",
        guidance=(
            None
            if inspect_ok
            else "ensure kinnoo.yaml, entrypoint, and requirements are present and valid"
        ),
    )

    preflight_exit = run_preflight(str(working_dir))
    preflight_ok = preflight_exit == 0
    _emit_step_result(
        "preflight",
        preflight_ok,
        "preflight checks passed" if preflight_ok else "preflight checks failed",
        guidance=(
            None
            if preflight_ok
            else "follow remediation lines from preflight output and retry"
        ),
    )

    if import_check_ok and inspect_ok and preflight_ok:
        print(style_text("Check result: PASS", color="green", bold=True))
        return 0

    print(style_text("Check result: FAIL", color="red", bold=True))
    return 1
