# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Added Feature68 reference GitHub Actions workflow at `.github/workflows/kinnoo-publish.yml` covering install, preflight, pack, and remote publish stages.
- Added Feature69 standardized test contract documentation for `kinnoo.tests.yaml` and `kinnoo test` execution modes.
- Added Feature70 landing-page and README messaging updates for OpenClaw bridge, ClawHub mirror attribution, and Phase 6 command matrix coverage.

### Changed
- Added CI environment/secrets contract documentation for `KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, `KINNOO_TENANT_SLUG`, and strict-mode compatibility control.
- Added docs consistency references for strict mode (`--strict`), lockfile freeze mode (`--frozen`), `kinnoo diff`, `kinnoo uninstall`, and framework import adapters (`kinnoo import --from ...`).
- Deprecated OpenClaw bridge-era feature metadata (feature62-feature67) in favor of Phase 7 wrapper features (feature76-feature84) and added migration command guidance in README/help surfaces.
- Deprecated legacy CLI import regression tests that no longer match wrapper-era OpenClaw import behavior:
  - `tests/test_cli_import.py::test_feature36_openclaw_detection_weighted_confidence_output`
  - `tests/test_cli_import.py::test_feature36_infers_runtime_skills_state_dirs`
  - `tests/test_cli_import.py::test_feature36_manifest_valid_or_todo_guidance`
  - `tests/test_cli_import.py::test_feature62_import_openclaw_manifest_migration_guidance`
- Bumped project version from `0.29.0` to `0.30.0` after Phase 7 final review closure.

## [v0.30.0] - 2026-03-30
### Added
- Implemented Feature66 OpenClaw run adapter v1 for `type: openclaw-skill` manifests behind explicit compatibility gating.
- Added backend selection diagnostics for OpenClaw adapter routing:
  - `openclaw_adapter_backend_native_skills_run` for OpenClaw CLI >= 0.3.0 (`openclaw skills run .`)
  - `openclaw_adapter_backend_legacy_run` for OpenClaw CLI >= 0.2.0 and < 0.3.0 (`openclaw run .`)

### Changed
- Added deterministic adapter failure categories with actionable remediation:
  - `openclaw_adapter_cli_missing`
  - `openclaw_adapter_version_unsupported`
  - `openclaw_adapter_runtime_nonzero_exit`
- Added explicit experimental compatibility gate for adapter behavior:
  - `kinnoo run <agent-dir> <input> --experimental-openclaw-adapter`

### Notes
- Adapter compatibility is intentionally explicit: kinnoo does not silently switch incompatible execution strategies.
- `kinnoo run --preflight` remains a readiness path and does not require adapter enablement.

## [v0.29.0] - 2026-03-26
### Added
- Added CLI auth commands:
  - `kinnoo login` for interactive and non-interactive registry token issuance and local auth-state persistence.
  - `kinnoo logout` for clearing persisted registry auth state.

### Changed
- Updated stale test assertions to match current frontend and integration behavior:
  - Sub-phase 4 integration assertions now validate SSR auth-me contract via dynamic backend base URL usage.
  - Hardening suite now validates security-header implementation in web/proxy.ts.
  - Web frontend setup route-content assertion now matches current landing-page content.
  - Frontend unit tests now match current classes/responsive layout and the two-step login CSRF + POST request flow.
- Added argon2-cffi to root requirements.txt to ensure password rehash paths and auth regression tests run in a fresh root environment.
- Bumped project version from v0.28.0 to v0.29.0.
- Documented auth-state precedence and post-logout behavior for publish/registry flows in README.

## [v0.28.0] - 2026-03-24
### Added
- Better support for openclaw agents
- Improved kinnoo import
- UX improvements

### Changed
- Added --full, --update, --raw flags to kinnoo inspect


## [v0.27.0] - 2026-03-20
### Added
- Completed Feature30 "Registry Web UI" Tech Lead review and merge-readiness approval cycle.
- Added authenticated web UI routes and templates for login, listing, search, and per-agent profile/download flows aligned with session-first policy.

### Changed
- Finalized web-session browsing guard behavior so unauthenticated requests to browsing pages redirect to `/login`.
- Preserved download architecture where UI-triggered downloads redirect to presigned object-storage URLs instead of proxying archive bytes through the server.
- Applied targeted MCP runtime startup-path remediation to address delayed stream output in the feature23 regression path.

### Quality
- Feature30 AC coverage validated across mapped tests `test343`-`test346`.
- Targeted MCP regression fix verification passed:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr -q`
  - Result: `1 passed`
- Manifest validation gate passed:
  - `python3 src/validate_project_manifests.py`
  - Result: `Validation passed: manifests are consistent`
- Security and repository hygiene checks reported no hardcoded real secrets and no git-tracked files over 10 MB.
- Merge commit: TBD (populate after merge to `phase3/main`).


## [v0.26.0] - 2026-03-20
### Added
- Completed Feature29 "Remote Registry Server" remediation cycle and approval readiness review for merge.
- Added FastAPI auth token route wiring (`POST /api/auth/token`) so auth issuance is part of the live API surface and covered by route-level controls.
- Added AC7-compliant structured error envelope behavior across feature29 server routes.

### Changed
- Updated feature29 endpoint error responses to consistently expose structured error fields (`error.code`, `error.message`, `error.request_id`).
- Expanded `GET /api/agents` response metadata to include AC4-required list fields (name/description/author/archive size) in addition to tenant/version context.
- Confirmed rate-limiting path coverage for auth and publish endpoint flows in remediation test coverage.

### Quality
- Focused remediation verification passed (`5 passed`):
  - `python3 -m pytest server/tests/test_auth_route.py server/tests/test_publish.py::test_publish_endpoint server/tests/test_agents_routes.py::test_list_and_detail server/tests/test_download.py::test_download_presigned server/tests/test_search.py::test_search_endpoint`
- Required review command executed:
  - `python3 -m pytest --testmon`
  - Result: `348 passed, 1 skipped`
- Manifest validation gate passed:
  - `python3 src/validate_project_manifests.py`
  - Result: `Validation passed: manifests are consistent`
- Security and repository hygiene checks reported no hardcoded real secrets and no git-tracked files over 10 MB.
- Merge commit: TBD (populate after merge to `phase3/main`).


## [v0.25.0] - 2026-03-20
### Added
- Completed Feature28 "Registry Backend Abstraction & Remote Client" implementation review and merge readiness approval.
- Added formal Tech Lead review evidence for feature28 covering backend abstraction, remote client behavior, config/env precedence, and remote error UX contracts.

### Changed
- Integrated deterministic backend-selection behavior across CLI registry operations (`publish`, `install`, `list`, `search`) for `--local`, `--remote`, and auto/config-driven modes.
- Standardized remote client error taxonomy for 401/403/404/409/429/5xx and network-failure paths with actionable user-facing guidance.

### Quality
- Feature28 acceptance criteria gate validated across `test327`-`test331` mapped checks.
- Required review command executed:
  - `python3 -m pytest --testmon`
  - Result: `69 passed, 1 skipped, 24 deselected`
- Security review evidence (server scope): credential/token/private-key pattern scan reported no hardcoded real secrets or leaked private keys.
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.24.0] - 2026-03-19
### Added
- Completed Feature43 "Auth, User & Tenant Management" endpoint requirements for AC4 and AC5.
- Added explicit API handlers in server endpoint layer for:
  - `POST /api/auth/token` (credential exchange -> JWT)
  - `POST /api/admin/users` (admin-only user creation)
  - `POST /api/admin/tenants` (admin-only tenant creation)

### Changed
- Enforced endpoint-boundary authorization for admin management operations using `registry:admin` scope checks.
- Standardized endpoint error behavior for malformed payloads and invalid credential/authorization flows (401/403/400/409 paths as applicable).

### Quality
- Focused remediation verification for AC4/AC5 endpoint behavior passed:
  - `python3 -m pytest server/tests/test_jwt_auth.py::test_jwt_lifecycle server/tests/test_tenant_model.py::test_tenant_slug_management`
  - Result: `2 passed`
- Required review command executed for feature review gate:
  - `python3 -m pytest --testmon`
  - Result: `5 passed`
- Security review evidence (server scope): broad sensitive-string scan and high-signal credential-pattern scan reported no leaked real credentials/private keys.
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.23.0] - 2026-03-20
### Added
- Implemented Feature41 "Runtime Defense-in-Depth (Behavioral Monitoring + Dynamic Enforcement)" with baseline runtime telemetry event capture for process, network, and filesystem activity.
- Added deterministic policy-violation handling with structured reason codes, warning mode, and hard kill-switch termination for high-risk violations.
- Added `kinnoo run --dry-run` predictive execution trace mode that reports expected actions without launching the agent entrypoint.

### Changed
- Added runtime resource-control enforcement options for wall-clock timeout, CPU cap, and memory cap where supported, with explicit degraded-mode messaging on unsupported platforms.
- Integrated runtime monitor policy summaries with feature39 permission declarations for both Python and Node execution paths.
- Added graceful telemetry-limited degradation signaling (`reason_code=telemetry_limited_backend`) when low-level telemetry capabilities are unavailable.

### Quality
- Feature41 acceptance criteria gate validated across `test322`-`test326`.
- Required review command executed: `python3 -m pytest --testmon` (result: `collected 0 items` due no-change selection state).
- Full regression evidence in testmon workflow: `python3 -m pytest --testmon-noselect` (result: `330 passed, 1 skipped`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.22.0] - 2026-03-19
### Added
- Implemented Feature40 "Archive Signing & Publisher Verification" with Ed25519 key generation (`kinnoo keygen`) and signed archive packaging support (`kinnoo pack --sign`).
- Added install-time detached-signature verification for signed archives, including explicit block behavior and remediation guidance for invalid signatures.
- Added registry publisher public-key association path to support verified distribution workflows.

### Changed
- Added explicit unsigned publisher trust-gate handling during install, including confirmation and non-interactive override policy via `--allow-unverified-publisher`.
- Updated regression and compatibility test expectations for non-interactive unsigned install flows to preserve backward-compatible automation behavior with explicit trust override.

### Quality
- Feature40 acceptance criteria gate validated across `test317`-`test321`.
- SWE remediation verified for prior feature40 trust-gate regressions:
  - `python3 -m pytest --testmon`
  - Result: `15 passed, 63 deselected`
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.21.0] - 2026-03-19
### Changed
- Applied SWE regression remediation for permission-model compatibility paths referenced in feature review notes, including validator compatibility and regression-gate stabilization.
- Hardened sandbox backend deterministic failure-shape behavior for feature39 run enforcement paths.

### Quality
- Focused remediation verification passed:
  - `python3 -m pytest tests/test_validator.py::test_feature26_permissions_schema_validation tests/test_regression_v1.py::test_feature26_framework_template_regression_gate tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 tests/test_cli.py::test_feature39_sandbox_backend_failure_shapes -q`
  - Result: `4 passed`
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.20.0] - 2026-03-19
### Added
- Implemented Feature38 "JS/TS Static Security Sweep" with cross-language static scanning support for `.js`, `.mjs`, `.ts`, and `.json` artifacts.
- Added risky JS/TS execution primitive detection (`eval`, `Function` constructor, and child-process execution patterns) with deterministic file/line finding evidence.
- Added dangerous OpenClaw JSON configuration checks for high-risk settings with targeted warning diagnostics.

### Changed
- Extended pack-time warning-first security checks to include memory snapshot candidate credential-risk scanning before archive completion.
- Preserved and regression-validated no-secret-value reporting contract across mixed Python and JS/TS sweep findings.

### Quality
- Feature38 acceptance criteria gate validated across `test307`-`test311`.
- Full regression executed for review cycle: `314 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.19.0] - 2026-03-19
### Added
- Implemented Feature37 "Node.js Dependency Audit & Lifecycle Script Controls" with install-time Node audit visibility and deterministic severity summary reporting (`critical/high/moderate/low`).
- Added machine-readable Node install trace output capturing lifecycle-script detection, severity counts, and policy decisions.

### Changed
- Enforced default install blocking when Node audit reports critical vulnerabilities, with explicit operator override via `--allow-vulnerable`.
- Added lifecycle-script policy controls for Node installs with warning-first behavior and `--ignore-scripts` enforcement.
- Preserved runtime isolation so feature37 controls remain Node-only and do not alter Python install workflows.

### Quality
- Feature37 acceptance criteria gate validated across `test302`-`test306`.
- SWE remediation applied for feature37 test-contract mismatch (AC1 summary validation now explicitly opts into AC2 override semantics).
- Focused verification after remediation: `2 passed` (`python3 -m pytest tests/test_cli_install.py::test_feature37_node_audit_severity_summary tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q`).
- Full regression after remediation: `309 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.18.0] - 2026-03-19
### Added
- Implemented Feature36 "OpenClaw Import Detection & Manifest Inference" with weighted strong/medium OpenClaw evidence detection surfaced through analyzer confidence metadata.
- Added OpenClaw import inference for runtime hints (`language: nodejs`, `type: daemon`, package manager), detected `skills` paths, and candidate mutable `state_dirs`.
- Added identity artifact detection signals for `SOUL.md`, `AGENTS.md`, and optional `USER.md` to improve OpenClaw import diagnostics.

### Changed
- Extended `kinnoo import` output to report framework confidence metadata and actionable unresolved-field TODO guidance when manifest inference remains partial.
- Preserved warning-first onboarding behavior for ambiguous detections while keeping operator-confirmed import flow.

### Quality
- Feature36 acceptance criteria gate validated across `test297`-`test301`.
- Full regression executed for review cycle: `304 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.17.0] - 2026-03-19
### Added
- Implemented Feature35 "Mutable State Directories in Pack/Install" with first-class `state_dirs` snapshot semantics for mutable runtime state.
- Added structured `state_dirs` entry support (`path`, optional `exclude`) with validator checks for safe relative paths and traversal-resistant exclude patterns.
- Added install-time state restore controls with warning-first default behavior and explicit overwrite flag support via `--state-overwrite`.

### Changed
- Extended pack flow to archive mutable state snapshots under deterministic `state_snapshots/<declared-state-dir>/...` paths while preserving immutable `assets` behavior.
- Added exclusion-aware snapshot collection so targeted noisy/sensitive state files can be omitted without dropping core warm-start state.
- Updated documentation in `README.md` and `docs/manifest-schema-reference.md` to distinguish mutable `state_dirs` from immutable `assets`, including restore and compatibility guidance.

### Quality
- Feature35 acceptance criteria gate validated across `test292`-`test296`.
- Full regression executed for review cycle: `296 passed, 1 failed, 1 skipped` (`python3 -m pytest`), with failure isolated to legacy MCP stream regression gate.
- Focused re-run of failing regression path: `2 passed` (`python3 -m pytest tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.16.0] - 2026-03-18
### Added
- Implemented Feature33 "Manifest Schema Extensions for OpenClaw/JS Agents" with optional schema fields: `runtime.package_manager`, `channels`, `skills`, and `state_dirs`.
- Added framework-targeted validation path for `framework: openclaw` with explicit diagnostics and required-field guidance.
- Added manifest documentation examples for OpenClaw daemon and generic Node.js one-shot workflows.

### Changed
- Extended validator path-safety checks for `skills` and `state_dirs` entries (relative-only, no parent traversal).
- Preserved non-openclaw compatibility: new fields are optional/non-breaking for existing manifests.

### Quality
- Feature33 acceptance criteria gate validated across `test282`-`test286`.
- Full regression suite validation after review: `285 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.15.0] - 2026-03-18
### Added
- Implemented Feature32 "Daemon Runtime Type + Process Controls" with first-class `runtime.type: daemon` manifest support.
- Added daemon lifecycle operator commands in CLI: `kinnoo stop`, `kinnoo attach`, and `kinnoo logs`.
- Added daemon supervisor state persistence (`daemon-state.json`) and execution log persistence (`daemon.log`) under the runtime workspace.

### Changed
- Extended runtime execution flow to support detached daemon launch semantics while preserving one-shot behavior for existing runtime types.
- Added daemon lifecycle preflight classification and operator guidance for `not-running`, `unhealthy`, and `healthy` states.

### Quality
- Feature32 acceptance criteria gate validated across `test276`-`test281`.
- Full regression suite validation after review: `280 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.14.0] - 2026-03-17
### Added
- Implemented Feature42 "JSON Input/Output Types for Agent Interop" with first-class manifest contract support for `inputs.type: json` and `outputs.type: json`.
- Added structured run input modes for JSON payload delivery:
  - inline payloads via `--json-input`
  - file-backed payloads via `--json-file`
- Added one-shot runtime output contract enforcement for `outputs.type: json`, including deterministic parse diagnostics for invalid JSON stdout.
- Added inspect/preflight/help visibility for JSON contract expectations, including operator guidance for structured input and output validation behavior.

### Changed
- Extended validator I/O type guidance to include `json` as an allowed manifest type while preserving rejection behavior for unsupported values.
- Documented the Feature42 JSON contract in `README.md` and `docs/manifest-schema-reference.md` with additive compatibility guidance for existing text workflows.

### Quality
- Feature42 focused gate passed (`7 passed`) across validator, run JSON modes, output contract enforcement, docs coverage, and regression gate assertions.
- Full-suite regression after Feature42 implementation: `273 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.13.0] - 2026-03-17
### Added
- Implemented Feature31 "Node.js Runtime Support (Foundation)" for first-class `runtime.language: nodejs` execution and install workflows.
- Added node runtime execution path in `kinnoo run` with parity for input forwarding, stdout/stderr streaming, and exit-code propagation.
- Added node install dependency resolution support using `npm` (default) and `pnpm` (optional via `runtime.package_manager`).
- Added pack/install safeguards for node agents: exclude `node_modules`, preserve `package.json` and lockfiles for reproducible installs.
- Added node preflight readiness checks for runtime version constraints and package-manager availability.

### Changed
- Hardened subprocess test isolation around node version/tool probes to prevent monkeypatch cross-effects in feature31 tests.
- Improved permission-path handling in run command to produce deterministic permission-denied behavior under restricted directory access.

### Quality
- Feature31 blocker tests from Tech Lead Review 1 now pass (`5 passed`):
  - `tests/test_cli.py::test_run_permission_error`
  - `tests/test_install.py::test_feature31_node_dependency_install_npm_and_pnpm`
  - `tests/test_pack.py::test_feature31_pack_node_modules_excluded_lockfiles_preserved`
  - `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`
  - `tests/test_regression_v1.py::test_feature20_does_not_regress_v2_behavior`
- Full suite validation after fixes: `266 passed, 1 skipped` (`python3 -m pytest`).
- Merge commit: TBD (populate after merge to `phase4/main`).


## [v0.12.1] - 2026-03-16
### Added
- Implemented Feature19 "kinnoo import - Analyzer-backed onboarding wizard" for in-place project onboarding.
- Added `kinnoo import [path]` flow (default `.`) that analyzes existing projects and generates `kinnoo.yaml` without scaffold-copy behavior.
- Added confirm-first import wizard behavior with analyzer-driven defaults, conditional follow-up prompts, and confidence-aware warning display.
- Added optional entrypoint bridge generation path (`kinnoo_wrapper.py`) for legacy scripts that do not meet one-shot CLI contract expectations.

### Changed
- Added collision preflight and explicit override support via `kinnoo import [path] --force`.
- Improved non-interactive import safety by defaulting EOF prompts in automation contexts while preserving Ctrl+C interruption handling.
- Refined prompt minimization logic to avoid unnecessary prompts when inferred list fields are intentionally empty (for example `services: []`).

### Quality
- Feature19 focused import suite passes: `11 passed` (`tests/test_cli_import.py`).
- Full regression suite passes after remediation: `259 passed, 1 skipped`.


## [v0.12.0] - 2026-03-16
### Added
- Implemented Feature25 "Service Health Checks - Runtime Preflight" with HTTP, TCP, and process probes integrated into `kinnoo run` and `--preflight` flows.
- Added interactive/non-interactive health-check decision behavior so failed checks can warn-and-proceed in interactive mode and fail-fast in non-interactive mode.
- Implemented Feature26 "MCP Server Packages & Client Templates" with first-party filesystem and GitHub MCP server package fixtures and `mcp-client` init template support.
- Added concrete MCP client template handshake demonstration using JSON-RPC over stdio (`initialize` and `tools/list`) plus workflow guidance in generated README.

### Changed
- Extended filesystem MCP runtime enforcement coverage to validate `tools/call` handler-path permission behavior (read-only blocking, allowlist sandbox checks).
- Updated manifest/review governance state for feature26 to review-ready alignment.

### Quality
- Feature25 and Feature26 follow-up validation completed with full regression pass: `238 passed, 1 skipped`.


## [v0.11.0] - 2026-03-16
### Added
- Implemented Feature24 "Service Declarations - Manifest Schema" with optional `services` manifest support.
- Added canonical service type taxonomy support: `mcp-server`, `vector-db`, `database`, `api`, `local-process`.
- Added backward-compatible service type aliases: `postgres`, `redis`, `http-api`, `process`.
- Added inspect output support for declared services, including service names, types, and health-check configuration fields.

### Changed
- Extended validator checks for `services` objects:
  - required fields (`name`, `type`)
  - allowed-value validation for service types and health-check methods
  - method-specific health-check field requirements (`port`, `url`, `process_name`)
  - duplicate service-name rejection
- Enforced that `health_check.method` is required whenever `health_check` is declared.
- Updated feature24 acceptance criteria text to align canonical values and compatibility alias policy.

### Quality
- Feature24 focused AC/reconciliation suite passed: `7 passed`.
- Full regression suite passed after feature24 updates: `222 passed, 1 skipped`.


## [v0.10.0] - 2026-03-16
### Added
- Implemented Feature23 "MCP Server Runtime Type - Schema & Lifecycle".
- Added `mcp-server` as a supported `runtime.type` value alongside `one-shot`.
- Added dedicated supervisor lifecycle support for MCP server execution in `kinnoo run`, including readiness gating and long-running process management.
- Added readiness strategies for explicit `runtime.readiness_probe` modes (`tcp`, `stdout`) with fallback to `runtime.port` TCP probing or immediate-ready when no probe config is provided.

### Changed
- Extended `kinnoo run` runtime branching to treat `mcp-server` agents as long-running services rather than one-shot executions.
- Added graceful Ctrl+C handling for MCP server mode: SIGTERM-first shutdown with timeout-based SIGKILL escalation for unresponsive processes.
- Extended run trace logging for MCP server sessions to include lifecycle metadata (`start_timestamp`, `stop_timestamp`, `server_exit_code`, `server_exit_signal`, `shutdown_sigterm_sent`, `shutdown_sigkill_sent`).

### Quality
- Added and validated feature23 coverage tests (`test214` through `test221`) across validator support, readiness behavior, streaming, shutdown semantics, trace metadata, fallback behavior, and one-shot regression protection.
- Executed full regression suite after feature23 integration: `215 passed, 1 skipped`.


## [v0.9.0] - 2026-03-16
### Added
- Implemented Feature22 "Asset Bundling" with manifest-level `assets` support (`paths`, `bundle`, `max_bundle_size_mb`).
- Added recursive asset inclusion during `kinnoo pack` for declared files/directories when bundling is enabled.
- Added install-time extraction support so bundled assets are restored to their original relative paths.
- Added inspect visibility for declared asset paths and asset size details.

### Security
- Added path-traversal protection for declared asset paths during packing.
- Added non-blocking asset credential risk sweep with filename-pattern warnings and size-limited UTF-8 text pattern scanning.
- Expanded filename warning coverage to align with feature22 examples, including `.key`, `*.p12`, and `*.pfx`.

### Changed
- `kinnoo pack` now honors `assets.bundle: false` as an explicit opt-out while keeping manifest declarations intact.
- Archive large-size warnings now support per-agent override via `assets.max_bundle_size_mb`.

### Quality
- Feature22-focused validation and regression suites passed across validator, pack, install extract, inspect, and regression gate coverage.


## [v0.8.0] - 2026-03-15
### Added
- Implemented Feature20 "Flexible Runtime Inputs" for `kinnoo run`.
- Added support for no-input execution when manifests declare `inputs.required: false`.
- Added pass-through invocation mode via `--` with verbatim argv forwarding to the agent entrypoint.
- Added explicit protection so required input cannot be bypassed by pass-through arguments.

### Changed
- Updated run CLI usage/help messaging to document all three supported invocation modes (single input, no-input, pass-through).
- Extended feature20 test coverage with focused assertions for required-input enforcement and usage guidance output.

### Quality
- Feature20 follow-up regression checks passed, including required-input/pass-through compatibility paths.


## [v0.7.0] - 2026-03-13
### Added
- Completed Phase 2 feature delivery and validation across runtime safety, trust, archive integrity, and packaging UX.
- Finalized input safety guard coverage in `kinnoo run`, including type-aware detection, interactive warn-and-confirm flow, and CI-friendly bypass controls.
- Finalized archive size reporting and visibility across `kinnoo pack`, `kinnoo inspect`, and `kinnoo list`.

### Changed
- Consolidated and stabilized registry/archive publish-install flows introduced in Phase 2, including local archive-first packaging and remote-mode abstractions.
- Improved install and pack test stability for non-interactive trust confirmation and archive destination handling.

### Quality
- Phase 2 closeout validation completed:
  - Manifest validation: `python3 src/validate_project_manifests.py` passed
  - Full test suite: `158 passed, 1 skipped`


## [v0.6.0] - 2026-03-13
### Added
- Implemented Feature18 "Input Safety Guard" with pre-entrypoint input threat detection in `kinnoo run`.
- Added pluggable guard architecture via `InputGuard` protocol and `get_default_guard()` factory for future ML-based guard replacement.
- Added V1 `RegexInputGuard` coverage for SQL injection, shell command injection, path traversal, SSRF, XSS, and template injection patterns.
- Added type-aware guard checks for input types (`text`, `string`, `file_path`, `url`, `id`) and aggregated multi-parameter checking via `check_inputs()`.
- Added `--no-guard` override for trusted CI/automation workflows.

### Changed
- `kinnoo run` now warns on flagged input and prompts `Proceed anyway? [y/N]` in interactive mode.
- Non-interactive execution now fails closed on flagged input unless `--no-guard` is provided.
- Added focused regression coverage in `tests/test_input_guard.py`, `tests/test_input_guard_integration.py`, and docs contract coverage in `tests/test_docs.py` for feature18 behavior.

### Quality
- TechLead pre-merge validation passed:
  - Feature18-focused suite: `16 passed`
  - Full repository suite: `156 passed, 1 skipped`


## [v0.5.0] - 2026-03-12
### Added
- Implemented Feature17 "Pack Size Reporting & Warnings" across pack/inspect/list workflows.
- Added pack-time archive size output: `[kinnoo pack] Archive size: <human-readable>`.
- Added large-archive warning for artifacts exceeding 100 MB: `Warning: archive is large (X MB). Consider whether all dependencies are necessary.`
- Added archive size visibility in `kinnoo inspect <archive.kno>` and list outputs (`kinnoo list`, `kinnoo list --local`, `kinnoo list --remote`).
- Added focused regression coverage in `tests/test_pack_size_reporting.py` and docs contract coverage in `tests/test_docs.py` for feature17 behavior.

### Changed
- Stabilized install tests to explicitly handle trust-confirmation behavior in non-interactive flows (`--yes` where prompt behavior is not under test).
- Stabilized pack tests around canonical archive backend destination semantics using isolated `KINNOO_ARCHIVE_ROOT` test paths.

### Quality
- Full repository validation now passes after stabilization: `140 passed, 1 skipped`.


## [v0.4.0] - 2026-03-11
### Added
- Implemented Feature16 "Archive Integrity (Checksums)" across pack/install/inspect/publish workflows.
- Added checksum sidecar generation during pack using sibling `.kno.sha256` files with stable `<sha256>  <archive-filename>` format.
- Added install-time checksum verification for file-path installs when sidecar exists, with explicit archive integrity failure behavior on mismatch.
- Added install warning-only fallback when checksum sidecar is missing: `No checksum file found — archive integrity not verified`.
- Added archive checksum visibility in `kinnoo inspect` and checksum sidecar propagation in `kinnoo publish` when source sidecar is present.

### Security
- Strengthened artifact provenance and tamper detection by validating archive digests before extraction side effects.


## [v0.3.0] - 2026-03-11
### Added
- Implemented Feature15 "Trust Baseline" across install, run, inspect, and pack flows.
- Added install-time trust summary with confirmation prompt and `--yes`/`-y` automation bypass.
- Added unverified-source warning path when installing raw `.kno` archives without sidecar checksum files.
- Added UTC JSON run trace logging at `~/.kinnoo/logs/run.<TIMESTAMP>.log` with safe fields only (`timestamp`, `agent_name`, `agent-version`, `runtime_type`, `exit_code`).
- Added heuristic env-var exposure sweep integrated into `kinnoo inspect` and non-blocking warnings in `kinnoo pack`.

### Security
- Reinforced the project-wide invariant that secret/env var values are never emitted in trust-related output or logs; only names may be shown.


## [v0.2.0] - 2026-03-05
### Changed
- Refactored `pack` and `publish` flows in Feature13 to use the registry abstraction and source-mode path consistently.
- Improved packaging/publishing reliability through shared backend handling and updated test coverage.

### Deprecated
- Feature12 legacy registry path/tests were deprecated and documented to prevent accidental re-enable.


## [v0.1.1] - 2026-03-05
### Added
- Implemented `kinnoo pack` command for packaging projects.
- Enhanced `kinnoo install` with improved functionality and support for packaged projects.

## [v0.1.0] - 2026-02-25
### Added
- Initial release.
- Implemented all MVP features:
  - `kinnoo init` for project initialization.
  - `kinnoo run` for running projects.
  - `kinnoo install` for installing dependencies.
