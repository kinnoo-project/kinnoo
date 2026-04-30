# Task273 Notes - Node.js/TypeScript Import and Run Improvements

## What was implemented
- Updated `src/kinnoo/analyzer.py` for Node/TS-aware inference:
  - Added package.json loading helpers.
  - Added package.json-based entrypoint detection (`main`, then `scripts.start` parsing).
  - Added Node runtime detection in `_detect_runtime` when package.json exists.
  - Added lockfile-based package manager detection with support for `npm`, `yarn`, and `pnpm`.
  - Added optional `engines.node` runtime version inference fallback to `>=20.0.0`.
- Updated `src/kinnoo/run_command.py`:
  - For Node runtime with `.ts`/`.tsx` entrypoints, execute via `npx tsx <entrypoint>`.
  - Keep existing `node <entrypoint>` path for JS entrypoints.
- Updated `src/kinnoo/install_command.py`:
  - Added lockfile-based package-manager inference for installs when `runtime.package_manager` is absent.

## Tests added
- `tests/test_validator.py::test_analyzer_nodejs_detection` (test392)
- `tests/test_cli_install_runnable.py::test_run_typescript_entrypoint` (test393)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_analyzer_nodejs_detection or test_run_typescript_entrypoint"
```
Result:
```text
2 passed, 380 deselected
```

## Manifest validation
Command:
```bash
python3 scripts/validate_project_manifests.py
```
Result:
```text
Validation passed: manifests are consistent
```

## Teaching notes
- Why package.json-first detection matters:
  - JS/TS projects declare execution contracts in package metadata, unlike many Python projects where entrypoint is code-convention driven.
- Why `scripts.start` parsing is heuristic:
  - Start scripts can be arbitrary shell commands. Lightweight token parsing captures common cases (`node`, `tsx`, `ts-node`) without full shell emulation risk.
- Why TypeScript runtime choice (`npx tsx`) is pragmatic:
  - `tsx` is widely used for zero-build execution in dev workflows and avoids requiring precompiled JS output for many agent repos.
- Interview angle (agent platform engineering):
  - Multi-runtime tooling requires separating detection (metadata inference) from execution policy (runtime command resolution), then testing both with deterministic fixtures.
