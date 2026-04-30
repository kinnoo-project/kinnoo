from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
import socket
import subprocess
from urllib import error as urllib_error
from urllib import request as urllib_request

from .schema import (
	DEFAULT_HTTP_HEALTH_CHECK_TIMEOUT_SECONDS,
	DEFAULT_TCP_HEALTH_CHECK_TIMEOUT_SECONDS,
)


_RUN_SUBPROCESS = subprocess.run


@dataclass(frozen=True)
class HealthCheckResult:
	"""Normalized health-check result for downstream renderers and policies."""

	service_name: str
	service_type: str
	method: str
	healthy: bool
	message: str
	guidance: str


@dataclass(frozen=True)
class DaemonLifecycleResult:
	"""Normalized daemon lifecycle state classification for operator diagnostics."""

	state: str
	healthy: bool
	message: str
	guidance: str


def classify_daemon_lifecycle_state(
	*,
	has_state_metadata: bool,
	process_running: bool,
	service_results: list[HealthCheckResult],
) -> DaemonLifecycleResult:
	"""Classify daemon lifecycle state as not-running, unhealthy, or healthy."""
	if not has_state_metadata:
		return DaemonLifecycleResult(
			state="not-running",
			healthy=False,
			message="daemon state is not-running: no persisted daemon metadata was found",
			guidance="Start daemon with `kinnoo run <agent-dir> <input>` before checking daemon health.",
		)

	if not process_running:
		return DaemonLifecycleResult(
			state="not-running",
			healthy=False,
			message="daemon state is not-running: tracked daemon process is not active",
			guidance="Restart daemon and verify `kinnoo stop` completed cleanly for any prior stale state.",
		)

	unhealthy_services = [result.service_name for result in service_results if not result.healthy]
	if unhealthy_services:
		service_label = ", ".join(unhealthy_services)
		return DaemonLifecycleResult(
			state="unhealthy",
			healthy=False,
			message=(
				"daemon state is unhealthy: process is running but service checks failed for "
				f"[{service_label}]"
			),
			guidance="Resolve failing service checks or update services[].health_check configuration.",
		)

	return DaemonLifecycleResult(
		state="healthy",
		healthy=True,
		message="daemon state is healthy: process is running and all service checks passed",
		guidance="No action needed.",
	)


def _as_float_timeout(value: object, *, default: float) -> float:
	if value is None:
		return default
	try:
		timeout = float(value)
	except (TypeError, ValueError):
		return default
	if timeout <= 0:
		return default
	return timeout


def _check_http(
	service_name: str,
	service_type: str,
	*,
	url: str,
	timeout_seconds: float,
) -> HealthCheckResult:
	timeout_label = f"{timeout_seconds:g}s"
	try:
		request = urllib_request.Request(url=url, method="GET")
		with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
			status = getattr(response, "status", None)
			if isinstance(status, int) and 200 <= status <= 299:
				return HealthCheckResult(
					service_name=service_name,
					service_type=service_type,
					method="http",
					healthy=True,
					message=(
						f"HTTP health check passed for {url} (status {status}, timeout {timeout_label})"
					),
					guidance="No action needed.",
				)

			return HealthCheckResult(
				service_name=service_name,
				service_type=service_type,
				method="http",
				healthy=False,
				message=(
					f"HTTP health check failed for {url}: unexpected status {status} "
					f"(timeout {timeout_label})"
				),
				guidance="Verify the endpoint is healthy and returns HTTP 2xx.",
			)
	except urllib_error.HTTPError as exc:
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="http",
			healthy=False,
			message=(
				f"HTTP health check failed for {url}: status {exc.code} "
				f"(timeout {timeout_label})"
			),
			guidance="Verify the endpoint is healthy and returns HTTP 2xx.",
		)
	except urllib_error.URLError as exc:
		if isinstance(exc.reason, TimeoutError):
			return HealthCheckResult(
				service_name=service_name,
				service_type=service_type,
				method="http",
				healthy=False,
				message=(
					f"HTTP health check failed for {url}: timed out after {timeout_label}"
				),
				guidance="Increase timeout or ensure the service responds faster.",
			)
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="http",
			healthy=False,
			message=(
				f"HTTP health check failed for {url}: {exc.reason} "
				f"(timeout {timeout_label})"
			),
			guidance="Confirm URL, host reachability, and service availability.",
		)
	except TimeoutError:
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="http",
			healthy=False,
			message=f"HTTP health check failed for {url}: timed out after {timeout_label}",
			guidance="Increase timeout or ensure the service responds faster.",
		)


def _check_tcp(
	service_name: str,
	service_type: str,
	*,
	port: int,
	timeout_seconds: float,
) -> HealthCheckResult:
	timeout_label = f"{timeout_seconds:g}s"
	try:
		with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout_seconds):
			return HealthCheckResult(
				service_name=service_name,
				service_type=service_type,
				method="tcp",
				healthy=True,
				message=(
					"TCP health check passed for "
					f"127.0.0.1:{port} (timeout {timeout_label})"
				),
				guidance="No action needed.",
			)
	except TimeoutError:
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="tcp",
			healthy=False,
			message=(
				"TCP health check failed for "
				f"127.0.0.1:{port}: timed out after {timeout_label}"
			),
			guidance="Increase timeout or ensure the target port is reachable.",
		)
	except OSError as exc:
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="tcp",
			healthy=False,
			message=(
				"TCP health check failed for "
				f"127.0.0.1:{port}: {exc} (timeout {timeout_label})"
			),
			guidance="Ensure the service is running and listening on the expected localhost port.",
		)


def _check_process(service_name: str, service_type: str, *, process_name: str) -> HealthCheckResult:
	result = _RUN_SUBPROCESS(
		["pgrep", "-f", process_name],
		capture_output=True,
		text=True,
	)
	if result.returncode == 0 and result.stdout.strip():
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="process",
			healthy=True,
			message=f"Process health check passed for pattern '{process_name}'.",
			guidance="No action needed.",
		)

	return HealthCheckResult(
		service_name=service_name,
		service_type=service_type,
		method="process",
		healthy=False,
		message=f"Process health check failed for pattern '{process_name}'.",
		guidance=(
			"Start the required process, or update services[].health_check.process_name "
			"to match the running command."
		),
	)


def run_service_health_check(service: dict[str, object]) -> HealthCheckResult:
	"""Run one service health check using feature24 service declarations."""

	service_name = str(service.get("name", "<unknown-service>"))
	service_type = str(service.get("type", "<unknown-type>"))

	health_check = service.get("health_check")
	if not isinstance(health_check, dict):
		return HealthCheckResult(
			service_name=service_name,
			service_type=service_type,
			method="unknown",
			healthy=False,
			message="Service health check configuration is missing.",
			guidance="Add services[].health_check with a supported method (http, tcp, process).",
		)

	method = str(health_check.get("method", "")).strip().lower()
	if method == "http":
		url = str(health_check.get("url", "")).strip()
		if not url:
			return HealthCheckResult(
				service_name=service_name,
				service_type=service_type,
				method="http",
				healthy=False,
				message="HTTP health check failed: missing services[].health_check.url.",
				guidance="Set services[].health_check.url to the service health endpoint.",
			)
		timeout_seconds = _as_float_timeout(
			health_check.get("timeout_seconds"),
			default=DEFAULT_HTTP_HEALTH_CHECK_TIMEOUT_SECONDS,
		)
		return _check_http(
			service_name,
			service_type,
			url=url,
			timeout_seconds=timeout_seconds,
		)

	if method == "tcp":
		port_value = health_check.get("port")
		if not isinstance(port_value, int):
			return HealthCheckResult(
				service_name=service_name,
				service_type=service_type,
				method="tcp",
				healthy=False,
				message="TCP health check failed: missing or invalid services[].health_check.port.",
				guidance="Set services[].health_check.port to a localhost TCP port number.",
			)
		timeout_seconds = _as_float_timeout(
			health_check.get("timeout_seconds"),
			default=DEFAULT_TCP_HEALTH_CHECK_TIMEOUT_SECONDS,
		)
		return _check_tcp(
			service_name,
			service_type,
			port=port_value,
			timeout_seconds=timeout_seconds,
		)

	if method == "process":
		process_name = str(health_check.get("process_name", "")).strip()
		if not process_name:
			return HealthCheckResult(
				service_name=service_name,
				service_type=service_type,
				method="process",
				healthy=False,
				message="Process health check failed: missing services[].health_check.process_name.",
				guidance="Set services[].health_check.process_name to a stable process pattern.",
			)
		return _check_process(service_name, service_type, process_name=process_name)

	return HealthCheckResult(
		service_name=service_name,
		service_type=service_type,
		method=method or "unknown",
		healthy=False,
		message=f"Unsupported health check method '{method or '<empty>'}'.",
		guidance="Use one of: http, tcp, process.",
	)


def _parse_numeric_version(version: str) -> tuple[int, ...] | None:
	if not version:
		return None

	if not re.fullmatch(r"\d+(?:\.\d+)*", version):
		return None

	return tuple(int(part) for part in version.split("."))


def _parse_node_version_output(version_output: str) -> tuple[int, ...] | None:
	match = re.search(r"v?(\d+(?:\.\d+)*)", version_output.strip())
	if match is None:
		return None
	return _parse_numeric_version(match.group(1))


def _compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
	max_len = max(len(left), len(right))
	padded_left = left + (0,) * (max_len - len(left))
	padded_right = right + (0,) * (max_len - len(right))
	if padded_left < padded_right:
		return -1
	if padded_left > padded_right:
		return 1
	return 0


def _version_constraint_satisfied(constraint: str, current_version: tuple[int, ...]) -> bool:
	normalized_constraint = constraint.strip()
	if not normalized_constraint:
		return False

	operator = "=="
	value = normalized_constraint
	for candidate in (">=", "<=", "==", ">", "<"):
		if normalized_constraint.startswith(candidate):
			operator = candidate
			value = normalized_constraint[len(candidate):].strip()
			break

	required_version = _parse_numeric_version(value)
	if required_version is None:
		return False

	comparison = _compare_versions(current_version, required_version)
	if operator == "==":
		return comparison == 0
	if operator == ">=":
		return comparison >= 0
	if operator == "<=":
		return comparison <= 0
	if operator == ">":
		return comparison > 0
	if operator == "<":
		return comparison < 0
	return False


def check_node_runtime_constraint(runtime_constraint: str) -> tuple[bool, str]:
	node_executable = shutil.which("node")
	if node_executable is None:
		return False, "runtime version check failed: node executable not found in PATH"

	try:
		version_result = _RUN_SUBPROCESS(
			[node_executable, "--version"],
			capture_output=True,
			text=True,
		)
	except OSError as error:
		return False, f"runtime version check failed: unable to execute node --version: {error}"

	if version_result.returncode != 0:
		stderr = version_result.stderr.strip()
		stderr_suffix = f" ({stderr})" if stderr else ""
		return False, f"runtime version check failed: node --version failed{stderr_suffix}"

	current_version = _parse_node_version_output(version_result.stdout or "")
	if current_version is None:
		return (
			False,
			(
				"runtime version check failed: could not parse Node version from "
				f"output '{(version_result.stdout or '').strip()}'"
			),
		)

	normalized = runtime_constraint.strip()
	if not normalized:
		return False, "runtime version check failed: runtime.version constraint is empty"

	constraints = [segment.strip() for segment in normalized.split(",") if segment.strip()]
	if not constraints:
		return False, "runtime version check failed: runtime.version constraint is empty"

	invalid_constraints: list[str] = []
	for constraint in constraints:
		if not _version_constraint_satisfied(constraint, current_version):
			invalid_constraints.append(constraint)

	current_label = ".".join(str(part) for part in current_version)
	if invalid_constraints:
		constraint_label = ", ".join(constraints)
		return (
			False,
			(
				"runtime version check failed: "
				f"current Node {current_label} does not satisfy runtime.version '{constraint_label}'"
			),
		)

	return (
		True,
		(
			"runtime version check passed: "
			f"current Node {current_label} satisfies runtime.version '{normalized}'"
		),
	)


def check_node_package_manager_availability(package_manager: str) -> tuple[bool, str]:
	normalized = package_manager.strip().lower()
	if not normalized:
		return False, "dependency readiness check failed: runtime.package_manager is empty"

	resolved_path = shutil.which(normalized)
	if resolved_path is None:
		return (
			False,
			f"dependency readiness check failed: node package manager '{normalized}' not found in PATH",
		)

	return (
		True,
		f"dependency readiness check passed: node package manager '{normalized}' is available at {resolved_path}",
	)


def check_openclaw_cli_constraint(minimum_version: str) -> tuple[bool, str, str]:
	"""Validate OpenClaw CLI availability and minimum version constraint."""
	normalized_minimum = minimum_version.strip()
	if not normalized_minimum:
		return (
			False,
			"openclaw_cli_minimum_constraint_invalid",
			"delegated install precheck failed: minimum OpenClaw version constraint is empty",
		)

	openclaw_executable = shutil.which("openclaw")
	if openclaw_executable is None:
		return False, "openclaw_cli_missing", (
			"delegated install precheck failed: OpenClaw CLI was not found in PATH. "
			"Install OpenClaw CLI and retry."
		)

	required_version = _parse_numeric_version(normalized_minimum)
	if required_version is None:
		return False, "openclaw_cli_minimum_constraint_invalid", (
			"delegated install precheck failed: minimum OpenClaw version has invalid format "
			f"'{normalized_minimum}'."
		)

	try:
		version_result = _RUN_SUBPROCESS(
			[openclaw_executable, "--version"],
			capture_output=True,
			text=True,
		)
	except OSError as error:
		return (
			False,
			"openclaw_cli_version_probe_failed",
			f"delegated install precheck failed: unable to execute openclaw --version: {error}",
		)

	if version_result.returncode != 0:
		stderr = version_result.stderr.strip()
		stderr_suffix = f" ({stderr})" if stderr else ""
		return False, "openclaw_cli_version_probe_failed", (
			"delegated install precheck failed: openclaw --version returned non-zero "
			f"exit code{stderr_suffix}"
		)

	current_version = _parse_node_version_output(version_result.stdout or "")
	if current_version is None:
		return False, "openclaw_cli_version_parse_failed", (
			"delegated install precheck failed: unable to parse OpenClaw CLI version from "
			f"output '{(version_result.stdout or '').strip()}'"
		)

	if _compare_versions(current_version, required_version) < 0:
		current_label = ".".join(str(part) for part in current_version)
		return False, "openclaw_cli_version_unsupported", (
			"delegated install precheck failed: "
			f"OpenClaw CLI version {current_label} is below required >= {normalized_minimum}. "
			"Upgrade OpenClaw CLI and retry."
		)

	current_label = ".".join(str(part) for part in current_version)
	return True, "openclaw_cli_precheck_ok", (
		"delegated install precheck passed: "
		f"OpenClaw CLI version {current_label} satisfies >= {normalized_minimum}"
	)


def detect_openclaw_run_backend() -> tuple[bool, str, str, str | None, list[str] | None]:
	"""Detect supported OpenClaw run adapter backend from CLI availability/version."""
	openclaw_executable = shutil.which("openclaw")
	if openclaw_executable is None:
		return (
			False,
			"openclaw_adapter_cli_missing",
			"OpenClaw adapter precheck failed: OpenClaw CLI not found in PATH.",
			None,
			None,
		)

	try:
		version_result = _RUN_SUBPROCESS(
			[openclaw_executable, "--version"],
			capture_output=True,
			text=True,
		)
	except OSError as error:
		return (
			False,
			"openclaw_adapter_version_probe_failed",
			f"OpenClaw adapter precheck failed: unable to execute openclaw --version: {error}",
			None,
			None,
		)

	if version_result.returncode != 0:
		stderr = version_result.stderr.strip()
		stderr_suffix = f" ({stderr})" if stderr else ""
		return (
			False,
			"openclaw_adapter_version_probe_failed",
			"OpenClaw adapter precheck failed: openclaw --version returned non-zero "
			f"exit code{stderr_suffix}",
			None,
			None,
		)

	current_version = _parse_node_version_output(version_result.stdout or "")
	if current_version is None:
		return (
			False,
			"openclaw_adapter_version_parse_failed",
			"OpenClaw adapter precheck failed: unable to parse OpenClaw CLI version from "
			f"output '{(version_result.stdout or '').strip()}'",
			None,
			None,
		)

	version_label = ".".join(str(part) for part in current_version)
	if _compare_versions(current_version, (0, 3, 0)) >= 0:
		return (
			True,
			"openclaw_adapter_backend_native_skills_run",
			f"OpenClaw adapter selected backend native-skills-run for CLI version {version_label}.",
			"native-skills-run",
			["openclaw", "skills", "run", "."],
		)

	if _compare_versions(current_version, (0, 2, 0)) >= 0:
		return (
			True,
			"openclaw_adapter_backend_legacy_run",
			f"OpenClaw adapter selected backend legacy-run for CLI version {version_label}.",
			"legacy-run",
			["openclaw", "run", "."],
		)

	return (
		False,
		"openclaw_adapter_version_unsupported",
		"OpenClaw adapter precheck failed: "
		f"CLI version {version_label} is unsupported (requires >= 0.2.0).",
		None,
		None,
	)
