from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .runtime_language import is_nodejs_compatible_runtime


SUPPORTED_TEST_ASSERTION_TYPES: tuple[str, ...] = ("contains", "not_contains", "equals", "regex")


@dataclass(frozen=True)
class DeclarativeAssertion:
    assertion_type: str
    expected_value: str
    target_stream: str = "stdout"


@dataclass(frozen=True)
class DeclarativeTestCase:
    test_id: str
    name: str
    input_text: str
    assertions: tuple[DeclarativeAssertion, ...]
    timeout_seconds: float
    expected_exit_code: int
    tags: tuple[str, ...]


@dataclass(frozen=True)
class TestCaseExecutionResult:
    test_id: str
    name: str
    input_text: str
    passed: bool
    runtime_type: str
    actual_exit_code: int
    expected_exit_code: int
    assertions_passed: int
    assertions_total: int
    timed_out: bool
    duration_ms: int
    stdout_text: str
    stderr_text: str
    failure_reason: str


def _normalize_assertion(raw_assertion: Any, path_prefix: str) -> tuple[DeclarativeAssertion | None, list[str]]:
    errors: list[str] = []

    if isinstance(raw_assertion, str):
        value = raw_assertion.strip()
        if not value:
            return None, [f"{path_prefix} must be a non-empty string when shorthand form is used."]
        return DeclarativeAssertion(assertion_type="contains", expected_value=value), errors

    if not isinstance(raw_assertion, dict):
        return None, [f"{path_prefix} must be a string or object assertion."]

    if "type" in raw_assertion or "value" in raw_assertion:
        assertion_type = raw_assertion.get("type")
        assertion_value = raw_assertion.get("value")
        target_stream = raw_assertion.get("target", "stdout")

        if not isinstance(assertion_type, str) or assertion_type not in SUPPORTED_TEST_ASSERTION_TYPES:
            supported = ", ".join(SUPPORTED_TEST_ASSERTION_TYPES)
            errors.append(f"{path_prefix}.type must be one of: {supported}.")
        if not isinstance(assertion_value, str) or not assertion_value.strip():
            errors.append(f"{path_prefix}.value must be a non-empty string.")
        if target_stream not in ("stdout", "stderr", "json"):
            errors.append(f"{path_prefix}.target must be one of: 'stdout', 'stderr', 'json'.")

        if errors:
            return None, errors
        return (
            DeclarativeAssertion(
                assertion_type=assertion_type,
                expected_value=assertion_value,
                target_stream=target_stream,
            ),
            errors,
        )

    matching_keys = [key for key in SUPPORTED_TEST_ASSERTION_TYPES if key in raw_assertion]
    if len(matching_keys) != 1:
        supported = ", ".join(SUPPORTED_TEST_ASSERTION_TYPES)
        errors.append(f"{path_prefix} object form must include exactly one of: {supported}.")
        return None, errors

    assertion_type = matching_keys[0]
    raw_value = raw_assertion.get(assertion_type)
    if not isinstance(raw_value, str) or not raw_value.strip():
        errors.append(f"{path_prefix}.{assertion_type} must be a non-empty string.")
        return None, errors

    return DeclarativeAssertion(assertion_type=assertion_type, expected_value=raw_value), errors


def validate_kinnoo_tests_document(document: Any, *, prefix: str = "") -> list[str]:
    errors: list[str] = []
    base = f"{prefix}." if prefix else ""

    if not isinstance(document, dict):
        return [f"{prefix or 'tests document'} must be a YAML mapping."]

    version = document.get("version")
    if not isinstance(version, (int, str)):
        errors.append(f"{base}version must be an int or string.")

    tests = document.get("tests")
    if not isinstance(tests, list):
        errors.append(f"{base}tests must be a list.")
        return errors

    for index, test_case in enumerate(tests):
        path = f"{base}tests[{index}]"
        if not isinstance(test_case, dict):
            errors.append(f"{path} must be a mapping.")
            continue

        required_fields = (
            "id",
            "name",
            "input",
            "assertions",
            "timeout_seconds",
            "expected_exit_code",
        )
        for field_name in required_fields:
            if field_name not in test_case:
                errors.append(f"Missing required field: {path}.{field_name}")

        test_id = test_case.get("id")
        if test_id is not None and (not isinstance(test_id, str) or not test_id.strip()):
            errors.append(f"{path}.id must be a non-empty string.")

        test_name = test_case.get("name")
        if test_name is not None and (not isinstance(test_name, str) or not test_name.strip()):
            errors.append(f"{path}.name must be a non-empty string.")

        input_text = test_case.get("input")
        if input_text is not None and not isinstance(input_text, str):
            errors.append(f"{path}.input must be a string.")

        timeout_seconds = test_case.get("timeout_seconds")
        if timeout_seconds is not None:
            if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
                errors.append(f"{path}.timeout_seconds must be a numeric value.")
            elif float(timeout_seconds) <= 0:
                errors.append(f"{path}.timeout_seconds must be greater than zero.")

        expected_exit_code = test_case.get("expected_exit_code")
        if expected_exit_code is not None and (isinstance(expected_exit_code, bool) or not isinstance(expected_exit_code, int)):
            errors.append(f"{path}.expected_exit_code must be an int.")

        tags = test_case.get("tags")
        if tags is not None:
            if not isinstance(tags, list):
                errors.append(f"{path}.tags must be a list of strings.")
            else:
                for tag_index, tag in enumerate(tags):
                    if not isinstance(tag, str) or not tag.strip():
                        errors.append(f"{path}.tags[{tag_index}] must be a non-empty string.")

        assertions = test_case.get("assertions")
        if assertions is None:
            continue
        if not isinstance(assertions, list) or len(assertions) == 0:
            errors.append(f"{path}.assertions must be a non-empty list.")
            continue

        for assertion_index, assertion in enumerate(assertions):
            _, assertion_errors = _normalize_assertion(
                assertion,
                f"{path}.assertions[{assertion_index}]",
            )
            errors.extend(assertion_errors)

    return errors


def _parse_test_cases(document: dict[str, Any]) -> list[DeclarativeTestCase]:
    parsed_tests: list[DeclarativeTestCase] = []
    for test_case in document.get("tests", []):
        assertions: list[DeclarativeAssertion] = []
        for index, raw_assertion in enumerate(test_case["assertions"]):
            parsed, assertion_errors = _normalize_assertion(
                raw_assertion,
                f"tests[{test_case.get('id', '?')}].assertions[{index}]",
            )
            if assertion_errors or parsed is None:
                raise ValueError("Assertion normalization failed after validation.")
            assertions.append(parsed)

        tags = tuple(test_case.get("tags", []))
        parsed_tests.append(
            DeclarativeTestCase(
                test_id=str(test_case["id"]),
                name=str(test_case["name"]),
                input_text=str(test_case["input"]),
                assertions=tuple(assertions),
                timeout_seconds=float(test_case["timeout_seconds"]),
                expected_exit_code=int(test_case["expected_exit_code"]),
                tags=tags,
            )
        )

    return parsed_tests


def _read_yaml_file(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in {path}: {exc}") from exc


def load_kinnoo_test_cases(agent_dir_arg: str, tests_file_arg: str | None = None) -> tuple[list[DeclarativeTestCase], str]:
    agent_dir = Path(agent_dir_arg)
    if not agent_dir.exists() or not agent_dir.is_dir():
        raise ValueError(f"Agent directory not found: {agent_dir}")

    if tests_file_arg:
        tests_path = Path(tests_file_arg)
        if not tests_path.is_absolute():
            tests_path = agent_dir / tests_path
        if not tests_path.exists():
            raise ValueError(f"Tests file not found: {tests_path}")
        test_doc = _read_yaml_file(tests_path)
        errors = validate_kinnoo_tests_document(test_doc)
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(test_doc), str(tests_path)

    canonical_tests_path = agent_dir / "kinnoo.tests.yaml"
    if canonical_tests_path.exists():
        test_doc = _read_yaml_file(canonical_tests_path)
        errors = validate_kinnoo_tests_document(test_doc)
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(test_doc), str(canonical_tests_path)

    manifest_path = agent_dir / "kinnoo.yaml"
    if not manifest_path.exists():
        raise ValueError("No tests declaration found. Expected kinnoo.tests.yaml or kinnoo.yaml with tests/tests_file.")

    manifest_doc = _read_yaml_file(manifest_path)
    if not isinstance(manifest_doc, dict):
        raise ValueError("kinnoo.yaml must be a mapping to resolve tests declarations.")

    tests_file_ref = manifest_doc.get("tests_file")
    if isinstance(tests_file_ref, str) and tests_file_ref.strip():
        linked_path = agent_dir / tests_file_ref
        if not linked_path.exists():
            raise ValueError(f"Manifest tests_file target not found: {linked_path}")
        test_doc = _read_yaml_file(linked_path)
        errors = validate_kinnoo_tests_document(test_doc)
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(test_doc), str(linked_path)

    inline_tests = manifest_doc.get("tests")
    if inline_tests is not None:
        inline_doc = {
            "version": manifest_doc.get("tests_version", 1),
            "tests": inline_tests,
        }
        errors = validate_kinnoo_tests_document(inline_doc, prefix="kinnoo.yaml")
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(inline_doc), str(manifest_path)

    raise ValueError("No tests declaration found. Expected kinnoo.tests.yaml or kinnoo.yaml with tests/tests_file.")


def run_test_command(
    agent_dir_arg: str | None,
    tests_file_arg: str | None = None,
    validate_only: bool = False,
    json_output: bool = False,
    verbose: bool = False,
    create_file_name: str | None = None,
    append: bool = False,
) -> int:
    if append and not create_file_name:
        print("Error: --append requires --create.", flush=True)
        return 1

    if create_file_name is not None:
        try:
            generated_path = _create_tests_file_interactive(
                agent_dir_arg=agent_dir_arg,
                create_file_name=create_file_name,
                append=append,
            )
        except ValueError as exc:
            print(f"Error: {exc}", flush=True)
            return 1

        if json_output:
            print(
                json.dumps(
                    {
                        "created": True,
                        "append": append,
                        "source": generated_path,
                    },
                    sort_keys=True,
                )
            )
        else:
            action = "Appended" if append else "Created"
            print(f"[kinnoo test] {action} tests declaration: {generated_path}")
        return 0

    if agent_dir_arg is None:
        print("Error: agent_dir is required unless --create is used.", flush=True)
        return 1

    try:
        test_cases, tests_source = load_kinnoo_test_cases(agent_dir_arg, tests_file_arg)
    except ValueError as exc:
        print(f"Error: {exc}", flush=True)
        return 1

    if validate_only:
        if json_output:
            print(
                json.dumps(
                    {
                        "valid": True,
                        "source": tests_source,
                        "total": len(test_cases),
                        "verbose": bool(verbose),
                    },
                    sort_keys=True,
                )
            )
        else:
            print(f"[kinnoo test] Valid tests declaration loaded from: {tests_source}")
            print(f"[kinnoo test] Parsed {len(test_cases)} test case(s).")
        return 0

    try:
        manifest = _load_manifest(agent_dir_arg)
    except ValueError as exc:
        print(f"Error: {exc}", flush=True)
        return 1

    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        print("Error: kinnoo.yaml runtime block is required for test execution.", flush=True)
        return 1

    def _format_expected_output(test_case: DeclarativeTestCase) -> list[dict[str, str]]:
        return [
            {
                "type": assertion.assertion_type,
                "value": assertion.expected_value,
                "target": assertion.target_stream,
            }
            for assertion in test_case.assertions
        ]

    execution_results: list[TestCaseExecutionResult] = []
    for test_case in test_cases:
        execution_results.append(_execute_test_case(Path(agent_dir_arg), manifest, test_case))

    passed_count = sum(1 for result in execution_results if result.passed)
    total_count = len(execution_results)
    failed_count = total_count - passed_count

    if json_output:
        print(
            json.dumps(
                {
                    "source": tests_source,
                    "total": total_count,
                    "passed": passed_count,
                    "failed": failed_count,
                    "verbose": bool(verbose),
                    "results": [
                        _serialize_json_result(
                            result,
                            verbose=verbose,
                            expected_output=_format_expected_output(test_case),
                        )
                        for result, test_case in zip(execution_results, test_cases)
                    ],
                },
                sort_keys=True,
            )
        )
    else:
        print(f"[kinnoo test] Loaded {total_count} test case(s) from {tests_source}")
        for result, test_case in zip(execution_results, test_cases):
            label = "PASS" if result.passed else "FAIL"
            summary = (
                f"[{label}] {result.test_id} ({result.runtime_type}) "
                f"assertions {result.assertions_passed}/{result.assertions_total} "
                f"exit {result.actual_exit_code}/{result.expected_exit_code}"
            )
            if result.failure_reason:
                summary += f" reason={result.failure_reason}"
            print(summary)
            if verbose:
                _print_verbose_text_result(result=result, test_case=test_case)
        print(f"[kinnoo test] Summary: {passed_count}/{total_count} passed")

    return 0 if failed_count == 0 else 1


def _serialize_json_result(
    result: TestCaseExecutionResult,
    *,
    verbose: bool,
    expected_output: list[dict[str, str]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": result.test_id,
        "name": result.name,
        "status": "passed" if result.passed else "failed",
        "runtime_type": result.runtime_type,
        "exit_code": result.actual_exit_code,
        "expected_exit_code": result.expected_exit_code,
        "assertions_passed": result.assertions_passed,
        "assertions_total": result.assertions_total,
        "timed_out": result.timed_out,
        "duration_ms": result.duration_ms,
        "failure_reason": result.failure_reason,
    }

    if verbose:
        payload.update(
            {
                "input": result.input_text,
                "expected_output": expected_output,
                "actual_output": {
                    "stdout": result.stdout_text,
                    "stderr": result.stderr_text,
                },
                "runtime_duration_sec": round(result.duration_ms / 1000.0, 6),
                "actual_exit_code": result.actual_exit_code,
                "error_message": result.failure_reason if not result.passed else "",
            }
        )

    return payload


def _print_verbose_text_result(*, result: TestCaseExecutionResult, test_case: DeclarativeTestCase) -> None:
    expected_output = [
        {
            "type": assertion.assertion_type,
            "value": assertion.expected_value,
            "target": assertion.target_stream,
        }
        for assertion in test_case.assertions
    ]
    print(f"  input={result.input_text}")
    print(f"  expected_output={json.dumps(expected_output, sort_keys=True)}")
    print(
        "  actual_output="
        + json.dumps({"stdout": result.stdout_text, "stderr": result.stderr_text}, sort_keys=True)
    )
    print(f"  runtime_duration_sec={round(result.duration_ms / 1000.0, 6)}")
    print(f"  expected_exit_code={result.expected_exit_code}")
    print(f"  actual_exit_code={result.actual_exit_code}")
    if not result.passed:
        print(f"  error_message={result.failure_reason}")


def _create_tests_file_interactive(agent_dir_arg: str | None, create_file_name: str, append: bool) -> str:
    base_dir = Path.cwd()
    if agent_dir_arg is not None:
        agent_dir = Path(agent_dir_arg)
        if not agent_dir.exists() or not agent_dir.is_dir():
            raise ValueError(f"Agent directory not found: {agent_dir}")
        base_dir = agent_dir

    target_path = Path(create_file_name)
    if not target_path.is_absolute():
        target_path = base_dir / target_path

    if append and not target_path.exists():
        raise ValueError(f"Cannot append because tests file does not exist: {target_path}")
    if (not append) and target_path.exists():
        raise ValueError(
            f"Tests file already exists: {target_path}. Use --append to add test cases."
        )

    base_document: dict[str, Any]
    existing_tests: list[dict[str, Any]]
    if append:
        loaded_doc = _read_yaml_file(target_path)
        errors = validate_kinnoo_tests_document(loaded_doc)
        if errors:
            raise ValueError("Invalid existing tests spec:\n- " + "\n- ".join(errors))
        base_document = dict(loaded_doc)
        existing_tests = list(base_document.get("tests", []))
    else:
        base_document = {"version": 1, "tests": []}
        existing_tests = []

    _print_creation_guidance(target_path, append=append, existing_count=len(existing_tests))
    new_test_cases = _prompt_test_cases(start_index=len(existing_tests) + 1)
    base_document["tests"] = existing_tests + new_test_cases

    errors = validate_kinnoo_tests_document(base_document)
    if errors:
        raise ValueError("Generated tests spec is invalid:\n- " + "\n- ".join(errors))

    target_path.write_text(
        yaml.safe_dump(base_document, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    return str(target_path)


def _print_creation_guidance(target_path: Path, *, append: bool, existing_count: int) -> None:
    mode = "append" if append else "create"
    print(f"[kinnoo test] Interactive {mode} mode for {target_path}")
    if append:
        print(f"[kinnoo test] Existing test cases: {existing_count}")
    print("[kinnoo test] Assertion best practices:")
    print("  - contains: output must include a substring")
    print("  - not_contains: output must exclude a substring")
    print("  - equals: output must exactly match")
    print("  - regex: supports advanced matching, OR with hello|hi, ignore-case with (?i)")
    print("  - expected_exit_code is checked separately at the test-case level")


def _prompt_test_cases(*, start_index: int) -> list[dict[str, Any]]:
    test_cases: list[dict[str, Any]] = []
    index = start_index

    while True:
        default_id = f"smoke-{index}"
        test_id = _prompt_str(
            f"id for test case {index} [{default_id}]: ",
            default=default_id,
        )
        name = _prompt_str(
            f"name for test case {index} [test case {index}]: ",
            default=f"test case {index}",
        )
        input_text = _prompt_str(f"input for test case {index}: ")
        assertions = _prompt_assertions(index)
        timeout_seconds = _prompt_float(
            f"timeout in seconds allowed for test case {index} [10]: ",
            default=10.0,
            minimum=0.001,
        )
        expected_exit_code = _prompt_int(
            f"expected exit code for test case {index} [0]: ",
            default=0,
        )

        test_cases.append(
            {
                "id": test_id,
                "name": name,
                "input": input_text,
                "assertions": assertions,
                "timeout_seconds": timeout_seconds,
                "expected_exit_code": expected_exit_code,
            }
        )

        if not _prompt_yes_no("Add another test case? [y/N]: ", default=False):
            break
        index += 1

    return test_cases


def _prompt_assertions(index: int) -> list[dict[str, str]]:
    assertions: list[dict[str, str]] = []
    assertion_index = 1

    while True:
        assertion_type = _prompt_choice(
            (
                f"assertion type for test case {index}, assertion {assertion_index} "
                "[contains (default) / not_contains / equals / regex]: "
            ),
            choices=SUPPORTED_TEST_ASSERTION_TYPES,
            default="contains",
        )
        prompt_suffix = " (for OR, use regex with '|'; for ignore-case, use (?i) in regex)"
        assertion_value = _prompt_str(
            f"assertion value{prompt_suffix}: " if assertion_type == "regex" else "assertion value: "
        )
        target = _prompt_choice(
            "assertion target stream [stdout (default) / json]: ",
            choices=("stdout", "json"),
            default="stdout",
        )

        assertions.append(
            {
                "type": assertion_type,
                "value": assertion_value,
                "target": target,
            }
        )

        if not _prompt_yes_no("Add another assertion to this test case? [y/N]: ", default=False):
            break
        assertion_index += 1

    return assertions


def _prompt_str(prompt: str, default: str | None = None) -> str:
    while True:
        raw = input(prompt).strip()
        if raw:
            return raw
        if default is not None:
            return default
        print("Value cannot be empty.")


def _prompt_int(prompt: str, *, default: int) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print("Please enter a valid integer.")


def _prompt_float(prompt: str, *, default: float, minimum: float) -> float:
    while True:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            value = float(raw)
        except ValueError:
            print("Please enter a valid number.")
            continue
        if value < minimum:
            print(f"Value must be at least {minimum}.")
            continue
        return value


def _prompt_choice(prompt: str, *, choices: tuple[str, ...], default: str) -> str:
    normalized_choices = {choice.lower(): choice for choice in choices}
    while True:
        raw = input(prompt).strip().lower()
        if not raw:
            return default
        if raw in normalized_choices:
            return normalized_choices[raw]
        print("Invalid choice. Options: " + ", ".join(choices))


def _prompt_yes_no(prompt: str, *, default: bool) -> bool:
    default_text = "y" if default else "n"
    while True:
        raw = input(prompt).strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print(f"Please enter y or n (default: {default_text}).")


def _load_manifest(agent_dir_arg: str) -> dict[str, Any]:
    manifest_path = Path(agent_dir_arg) / "kinnoo.yaml"
    if not manifest_path.exists():
        raise ValueError(f"Manifest file not found: {manifest_path}")

    manifest_doc = _read_yaml_file(manifest_path)
    if not isinstance(manifest_doc, dict):
        raise ValueError("kinnoo.yaml must be a mapping.")
    return manifest_doc


def _build_runtime_command(agent_dir: Path, manifest: dict[str, Any], input_text: str) -> tuple[list[str], str]:
    runtime = manifest.get("runtime", {})
    if not isinstance(runtime, dict):
        return [], "unknown"

    runtime_type = str(runtime.get("type", "one-shot"))
    runtime_language = str(runtime.get("language", "python"))
    entrypoint = str(manifest.get("entrypoint", "run.py"))
    runtime_path = str(runtime.get("path", "")).strip()
    run_command = runtime.get("run_command")

    if runtime_type == "daemon" and isinstance(run_command, str) and run_command.strip():
        command = shlex.split(run_command.strip())
        command.append(input_text)
        return command, runtime_type

    if is_nodejs_compatible_runtime(runtime_language):
        executable = runtime_path or "node"
    else:
        executable = runtime_path or "python3"

    command = [executable, entrypoint, input_text]
    return command, runtime_type


def _execute_test_case(agent_dir: Path, manifest: dict[str, Any], test_case: DeclarativeTestCase) -> TestCaseExecutionResult:
    command, runtime_type = _build_runtime_command(agent_dir, manifest, test_case.input_text)
    if not command:
        return TestCaseExecutionResult(
            test_id=test_case.test_id,
            name=test_case.name,
            input_text=test_case.input_text,
            passed=False,
            runtime_type="unknown",
            actual_exit_code=1,
            expected_exit_code=test_case.expected_exit_code,
            assertions_passed=0,
            assertions_total=len(test_case.assertions),
            timed_out=False,
            duration_ms=0,
            stdout_text="",
            stderr_text="",
            failure_reason="runtime_command_unresolved",
        )

    started_at = time.time()
    timed_out = False
    try:
        result = subprocess.run(
            command,
            cwd=str(agent_dir),
            capture_output=True,
            text=True,
            timeout=test_case.timeout_seconds,
        )
        actual_exit_code = int(result.returncode)
        stdout_text = result.stdout
        stderr_text = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        actual_exit_code = 124
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""

    assertion_passes = 0
    for assertion in test_case.assertions:
        target_text = stdout_text if assertion.target_stream == "stdout" else stderr_text
        if _assertion_matches(assertion, target_text):
            assertion_passes += 1

    exit_code_match = actual_exit_code == test_case.expected_exit_code
    assertions_match = assertion_passes == len(test_case.assertions)
    passed = (not timed_out) and exit_code_match and assertions_match

    failure_reasons: list[str] = []
    if timed_out:
        failure_reasons.append("timeout")
    if not exit_code_match:
        failure_reasons.append("exit_code_mismatch")
    if not assertions_match:
        failure_reasons.append("assertions_failed")

    duration_ms = int((time.time() - started_at) * 1000)
    return TestCaseExecutionResult(
        test_id=test_case.test_id,
        name=test_case.name,
        input_text=test_case.input_text,
        passed=passed,
        runtime_type=runtime_type,
        actual_exit_code=actual_exit_code,
        expected_exit_code=test_case.expected_exit_code,
        assertions_passed=assertion_passes,
        assertions_total=len(test_case.assertions),
        timed_out=timed_out,
        duration_ms=duration_ms,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        failure_reason=",".join(failure_reasons),
    )


def _assertion_matches(assertion: DeclarativeAssertion, output_text: str) -> bool:
    if assertion.target_stream == "json":
        try:
            parsed = json.loads(output_text)
            output_text = json.dumps(parsed, sort_keys=True)
        except (TypeError, ValueError, json.JSONDecodeError):
            return False

    if assertion.assertion_type == "contains":
        return assertion.expected_value in output_text
    if assertion.assertion_type == "not_contains":
        return assertion.expected_value not in output_text
    if assertion.assertion_type == "equals":
        return output_text.strip() == assertion.expected_value.strip()
    if assertion.assertion_type == "regex":
        return re.search(assertion.expected_value, output_text, flags=re.MULTILINE) is not None
    return False
