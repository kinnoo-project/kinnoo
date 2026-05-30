# kinnoo import — current functionality and gap analysis

Date: 2026-05-29
Author: GitHub Copilot agent (per @jerryschen31's request)

---

## Original prompt

> Assess the current functionality of `kinnoo import` and give me a comprehensive review of its functionality for all supported agent frameworks and languages.
> Then, assess the current gaps in `kinnoo import` functionality, given that the goal of kinnoo import is to make it as seamless as possible for a developer to make the developer's agent codebase compatible with kinnoo - so that the developer can subsequently run `kinnoo pack` and `kinnoo publish` to publish his or her agent to the kinnoo registry, without any issues. I believe the primary artifact that should be created when a developer runs `kinnoo import` is that a proper kinnoo.yaml should be written, and a proper requirements.txt (for Python), package.json (for TS/JS), or go.mod (for Go) should be written that allows another developer to seamlessly install and run the agent after it has been published to the registry. All other considerations of kinnoo import I believe are secondary - but feel free to push back if my understanding is off or if I am missing something, based on your knowledge of agentic AI development and your knowledge of this codebase. Write this prompt and your complete response as a new note to notes/20260529-kinnoo-import-gaps.md . Break down the gaps in kinnoo import into distinct features that can be implemented and tested by coding agents. Again, the goal is a powerful, easy-to-use kinnoo import that allow agent developers to make their agent codebase completely kinnoo-compatible. If this is not feasible or realistic given the wide range of frameworks and tools used to build agents as well as the variety of ways in which developers organize their codebase, then I need to know this as well. Perhaps full kinnoo import functionality is just not realistic, and I need to focus on specific types of agents for kinnoo import.

---

## TL;DR

- Today, `kinnoo import` is fundamentally a **Python-first** tool with **partial Node.js (JS/TS) support** and **zero Go support**, even though `kinnoo init`, the schema, `pack`, `install`, and `run` all officially support Go (`runtime.language: go`) per `src/kinnoo/schema.py:100`, `src/kinnoo/init_command.py:91`, and `src/kinnoo/run_command.py:426+`.
- The single artifact `kinnoo import` reliably (re-)generates is `kinnoo.yaml`. It will additionally **auto-generate `requirements.txt`** for Python projects when missing, but it will **never generate `package.json`** for Node/TS projects and **never generate `go.mod`** for Go projects. This is the most important concrete gap relative to your stated success criterion.
- Framework-aware adapters exist for **only three frameworks**: `langchain`, `langgraph`, `openai` (Python only), plus a separate code path for `openclaw` workspaces. Vision-promised frameworks **CrewAI, smolagents, PydanticAI** have no adapter; **AutoGen, LlamaIndex, Haystack, AG2, DSPy, Mastra, Vercel AI SDK, Google ADK, Semantic Kernel** are not detected at all.
- Your mental model — "the primary artifact is a correct `kinnoo.yaml` plus a correct dependency manifest for the language" — is **correct and well-aligned with what `pack`/`install` actually require downstream**. The biggest delta between vision and implementation is around the dependency manifest for non-Python languages and around framework breadth.
- Full universal "import any agent codebase" is **not realistic**, but a **significantly more powerful, opinionated `kinnoo import`** that covers Python + Node/TS + Go and the top ~5 frameworks per language is realistic and is the right next investment. Recommendations and a feature breakdown follow.

---

## Response Summary

Current functionality summary:

- kinnoo import is Python-first, with partial Node/TS detection (entrypoint + deps from package.json) and no Go detection at all — even though the schema, init, pack, install, and run all support Go.
- It reliably writes kinnoo.yaml, and conditionally writes requirements.txt for Python (via analyzer-inferred deps → uv export → empty fallback).
- It never writes package.json for Node/TS (which pack then hard-rejects) and never writes go.mod.
- Framework adapters: only langchain, langgraph, openai (Python), plus a separate openclaw workspace path. Vision-promised CrewAI / smolagents / PydanticAI have no adapter.
- Validation of your assumption: Your model — primary artifact = correct kinnoo.yaml + correct dependency manifest per language — is correct and matches exactly what pack/install/run enforce downstream (citations to pack_command.py:716/783, run_command.py:426, install_command.py:818 are in the note).

Gap breakdown — 20 distinct, independently implementable+testable features in 4 tiers:

- Tier 1 (close the dependency-manifest contract): A) Node/TS package.json synthesis, B) Go detector + go.mod, C) Node lockfiles, D) go.sum
- Tier 2 (language fidelity): E) TS-specific runtime, F) Python [project.scripts], G) monorepo handling
- Tier 3 (framework breadth): H) PydanticAI, I) CrewAI, J) smolagents, K/L) AutoGen/LlamaIndex (optional), M) Node-side adapters
- Tier 4 (UX/robustness): N) --yes/--dry-run, O) richer GitHub URL support, P) schema-driven manifest emission, Q) dependency-confidence reporting, R) .env parsing, S) Compose detection, T) (language × framework) regression matrix

On feasibility: Universal "import any agent repo" is not realistic — too much heterogeneity in monorepos, custom build systems, notebook-based agents, web-only agents, etc. But "for the agent shapes kinnoo intends to support (CLI-runnable, in Python/TS/Go, with the top ~5 frameworks per language), produce a working manifest with at most a couple confirmations" is realistic. I recommend committing to and documenting an explicit support matrix, and falling back to best-effort + explicit TODO guidance outside it. Concrete ordered roadmap is at the bottom of the note.

---

## 1. Current functionality of `kinnoo import`

### 1.1 CLI surface (`src/kinnoo/cli.py:909-945`)

```
kinnoo import [target] [import_path] [--force] [--from {langchain,langgraph,openai,openclaw}]
```

- `target`: optional. A local directory path (defaults to CWD) **or** a GitHub HTTPS URL of the form `https://github.com/<owner>/<repo>(.git)?`. SSH URLs, GitLab, Bitbucket, tarball URLs, and arbitrary git remotes are not supported.
- `import_path`: only valid when `target` is a GitHub URL — destination directory for the `git clone --depth 1` (`src/kinnoo/import_command.py:109-129`).
- `--force`: overwrite an existing `kinnoo.yaml`.
- `--from`: explicitly select a framework adapter. Restricted to `langchain | langgraph | openai | openclaw`.

### 1.2 High-level flow (`import_agent`, `src/kinnoo/import_command.py:1042-1321`)

1. Resolve target path (or `git clone --depth 1` from a GitHub URL).
2. Detect collisions with an existing `kinnoo.yaml` (abort unless `--force`).
3. If the directory looks like an OpenClaw workspace, run a separate OpenClaw-specific path (preflight, copy into `~/.openclaw/workspace-*`, register).
4. Run `analyze_project()` (`src/kinnoo/analyzer.py`) → an `AnalysisReport` with inferred fields and per-field confidence.
5. Optionally apply a framework adapter (`--from`) that overrides analyzer output if its coverage score clears a per-framework minimum.
6. Show detected values and analyzer warnings; prompt the user for confirmation; conditionally prompt for runtime, framework, services, permissions, and entrypoint wrapper generation.
7. Build manifest text via `_build_manifest_from_analysis` (lines 637-788).
8. Validate the manifest in-memory; if invalid, abort before any writes (lines 1270-1278).
9. Write `kinnoo.yaml`. For Python projects only, optionally generate `requirements.txt` (lines 856-899).
10. Run final manifest validation against the on-disk file and print TODO guidance for low-confidence fields.
11. On any error, roll back partial artifacts (`kinnoo.yaml`, generated wrapper, generated `requirements.txt`).

### 1.3 What the analyzer detects (`src/kinnoo/analyzer.py`)

Per-language detection coverage:

| Detector                | Python                                                                | Node.js / TS                                                                  | Go     |
| ----------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------ |
| Source-file walk        | Yes (`_iter_python_files*`)                                           | Yes (`_iter_node_files_with_depth`, `.js .mjs .cjs .ts .tsx`)                 | **No** |
| Entrypoint detection    | AST-based (`if __name__ == "__main__"`, class entrypoints, scoring)   | `package.json` `main`, `scripts.start`, then file heuristics                  | **No** |
| Runtime version         | `pyproject.toml` `requires-python` or `>=3.10` default                | `package.json` `engines.node` or `>=20.0.0` default                           | **No** |
| Package manager         | n/a                                                                   | `_detect_node_package_manager` (npm/pnpm/yarn lockfiles)                      | **No** |
| Dependency parsing      | `requirements.txt`, `pyproject.toml` (PEP 621 + Poetry)               | `package.json` `dependencies/devDependencies/peerDependencies/optional`       | **No** |
| Import-graph fallback   | Yes (`_collect_import_names` + `IMPORT_TO_PACKAGE` map)               | Markers via `_collect_node_module_markers` (limited)                          | **No** |
| Framework patterns (Py) | `langchain*`, `langgraph`, `pydantic_ai`, `openai`, `agents`          | n/a                                                                           | n/a    |
| Framework patterns (JS) | n/a                                                                   | `@langchain/core`, `@langchain/openai`, `langchain`, `@langchain/langgraph`, `@openai/agents`, `openai` | n/a |
| Env-var detection       | AST-based `os.environ.get`/`os.getenv`                                | Heuristic (limited)                                                           | **No** |
| Service detection       | URLs + connection strings (postgres, redis, mongodb, http, mcp, etc.) | Same heuristic on text                                                        | **No** |
| OpenClaw weighted score | n/a                                                                   | Yes (signals: deps, README, layout, skills, memory, identity)                 | n/a    |

### 1.4 What the framework adapters add (`src/kinnoo/framework_adapters/*`)

Three adapters: `langchain_adapter.py`, `langgraph_adapter.py`, `openai_adapter.py`. Each returns an `AdapterResult` with coverage score, inferred overrides, confidence overrides, warnings, and unresolved-TODO guidance. `_apply_framework_adapter` falls back to plain analyzer output when coverage is below a per-adapter minimum.

Wrapper templates exist for **only two** frameworks and **only Python**: `langchain_wrapper.py.j2`, `openai_agents_wrapper.py.j2`.

### 1.5 Artifacts produced by `kinnoo import` today

| Artifact                  | Python                                                       | Node.js / TS                            | Go     |
| ------------------------- | ------------------------------------------------------------ | --------------------------------------- | ------ |
| `kinnoo.yaml`             | Yes                                                          | Yes (with `runtime.language: nodejs`)   | **No** (analyzer never assigns `go`) |
| `requirements.txt`        | Yes — from analyzer-inferred deps, falls back to `uv export`, falls back to empty file | n/a                                     | n/a    |
| `package.json`            | n/a                                                          | **No** — requires the user already has one. `pack` will hard-fail (`pack_command.py:783`) if it's missing | n/a |
| `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` | n/a                                  | **No**                                  | n/a    |
| `go.mod`                  | n/a                                                          | n/a                                     | **No** |
| `go.sum`                  | n/a                                                          | n/a                                     | **No** |
| Entrypoint wrapper script | Optional, Python-only (`_generate_entrypoint_wrapper`, class-wrapper for langchain/openai) | **No** | **No** |
| OpenClaw registration     | n/a                                                          | Yes (copies into `~/.openclaw/workspace-*` and registers via `openclaw` CLI) | n/a |

---

## 2. Validation of your assumption

Your stated success criterion is: after `kinnoo import`, a developer should be able to `kinnoo pack && kinnoo publish` and another developer should be able to `kinnoo install && kinnoo run`. The downstream commands tell us exactly what artifacts must exist:

- `pack_command.py:716-718` — Python runtimes hard-require a non-missing `requirements.txt`.
- `pack_command.py:783-787` — Node.js runtimes hard-require `package.json`.
- `run_command.py:426-478` — Go runtimes warn loudly and fail when dependencies are declared but `go.mod` is missing.
- `install_command.py:818-861` — Node.js install path requires `package.json` in the extracted agent.

So the artifacts you named — `kinnoo.yaml` + `requirements.txt` | `package.json` | `go.mod` — are **exactly** the dependency contract that `pack`/`install`/`run` enforce. **Your mental model is correct.** Everything else (wrappers, services, env vars, framework field, model field) is a quality-of-life or compatibility enhancement, not a hard prerequisite for a successful publish-install-run round trip.

One small refinement: for Node.js, `pack` and `install` work better when a **lockfile** is present (reproducibility), and for Go, an installed agent that depends on external modules also wants `go.sum`. These are secondary but worth keeping on the radar.

---

## 3. Gaps, broken down into implementable features

I've ordered features by how much they move the needle on your stated goal. Each is scoped so a coding agent can pick it up, implement it, and write tests against the existing `tests/client_cli_import/` suite.

### Tier 1 — Close the dependency-manifest contract (directly blocks `pack`/`install`)

#### Feature A: `kinnoo import` auto-generates `package.json` for Node/TS projects

- **Why:** Today `pack` will reject any imported Node/TS project that doesn't already have `package.json`. The analyzer correctly identifies Node/TS projects and infers a runtime, but does nothing to author the manifest.
- **What:** When `runtime.language` resolves to `nodejs`/`javascript`/`typescript` and `package.json` is absent, synthesize a minimal `package.json` with `name`, `version`, `main` (= manifest entrypoint), `scripts.start`, `engines.node` (from inferred runtime), `type` (module/commonjs based on detected `import`/`require` usage), and `dependencies` populated from imports detected via `_collect_node_module_markers`. Use `npm pkg set`/`npm init -y` first if `npm` is available, then patch — analogous to how Python uses `uv export`.
- **Tests to add:** new fixture under `tests/client_cli_import/` for (i) bare TS file with no `package.json`, (ii) JS with `package.json` already present (must not overwrite), (iii) TS project where `tsconfig.json` exists and `runtime.typescript=true` is set.
- **Risk:** medium — overwriting a partial `package.json` is sensitive; gate behind the same `--force` rule used for `kinnoo.yaml`.

#### Feature B: First-class Go support in the analyzer + `kinnoo import` writes `go.mod`

- **Why:** Schema, `init`, `pack`, and `run` all support Go, but `import` never identifies Go projects. A user who runs `kinnoo import` on a Go agent currently gets either a Python or Node manifest depending on what other files happen to be in the tree.
- **What:**
  1. Add a Go detector to `src/kinnoo/analyzer.py`: walk `*.go` files (skip `vendor/`, `testdata/`, `.git`), prefer `main.go` or files with `package main` + `func main()` for entrypoint, infer `runtime.language: go` and `runtime.version` from existing `go.mod`'s `go` directive, and parse `require` blocks for dependencies.
  2. Teach `_build_manifest_from_analysis` to emit a Go manifest stanza.
  3. Add `_ensure_import_go_mod_file` analogous to `_ensure_import_requirements_file` that runs `go mod init <module-name>` and `go mod tidy` when Go is on PATH; otherwise writes a minimal `go.mod` skeleton with a TODO and clear guidance, mirroring the empty-`requirements.txt` fallback.
- **Tests:** new `tests/client_cli_import/test_cli_import_go.py` covering: project with existing `go.mod`, project without `go.mod` and `go` on PATH, project without `go.mod` and `go` missing, multi-package layouts.

#### Feature C: Generate/refresh Node lockfiles when missing for reproducible installs

- **Why:** `kinnoo install` for Node uses `npm ci`-style flows where lockfiles materially affect reproducibility. A published agent without a lockfile is more likely to break for end users.
- **What:** After Feature A, if no lockfile is present and the chosen package manager is on PATH, run `npm install --package-lock-only` / `pnpm install --lockfile-only` / `yarn install --mode=update-lockfile`. Otherwise emit a clear TODO.

#### Feature D: Generate `go.sum` when Go is on PATH

- **Why:** Symmetric to Feature C; required for `go build` reproducibility for the end user.
- **What:** After Feature B, if `go.mod` was generated and `go` is on PATH, run `go mod tidy`. Otherwise emit guidance.

### Tier 2 — Broaden language-aware manifest fidelity

#### Feature E: TypeScript-specific runtime fidelity

- **Why:** The schema accepts `typescript` as a `runtime.language`, but the analyzer collapses TS to `nodejs`. Without a TS-aware path, transpile/build steps (`tsc`, `tsup`, `vite`) get lost; `kinnoo run` then fails because no built JS exists.
- **What:** When `tsconfig.json` is present, set `runtime.language: typescript`, infer `runtime.build_command` (e.g., `npm run build` if `scripts.build` exists, else `tsc`), and ensure the manifest entrypoint points to either a TS source the runtime can execute (with `tsx`/`ts-node` declared as a dependency) or to the compiled JS output as configured by `tsconfig.outDir`.

#### Feature F: Honor Python project layouts beyond flat `run.py`

- **Why:** Real Python agent codebases use `src/<pkg>/__main__.py`, Hatch layouts, console-scripts entry points, or `python -m mypkg`. The current entrypoint scoring favors top-level files and gracefully degrades to wrappers, but it doesn't actually surface "the package's `[project.scripts]` entry" as the entrypoint — which is the most common case for installable Python agents.
- **What:** Extend `_detect_entrypoint` and `_build_manifest_from_analysis` to recognize `[project.scripts]` (PEP 621) and `[tool.poetry.scripts]`, and synthesize a `runtime.run_command` (e.g., `python -m mypkg`) plus an importable entrypoint when no script-style entrypoint exists.

#### Feature G: Multi-language repos and monorepos

- **Why:** Many agent repos contain both a Python service and a TS client. Today the analyzer picks one language and silently ignores the other, which is a frequent source of surprise.
- **What:** Detect multiple languages, fail clearly with a `--subdir <path>` remediation hint, and document the convention. Don't try to import multiple agents in one run.

### Tier 3 — Broaden framework coverage (vision-aligned)

#### Feature H: PydanticAI adapter

- **Why:** Already detected by the analyzer (`pydantic_ai`) but no adapter writes a high-quality manifest. Vision document calls this out by name.
- **What:** New `framework_adapters/pydantic_ai_adapter.py`. Coverage signals: presence of `pydantic_ai.Agent` instantiations, `agent.run_sync(...)` patterns. Wrapper template that bridges `agent.run_sync(input)` to the kinnoo one-shot CLI contract (stdin/argv → stdout).

#### Feature I: CrewAI adapter

- **Why:** Vision-listed; large user base. Not detected today.
- **What:** Detect via `crewai` import or `crewai.Crew`/`@crew`/`@agent`/`@task` decorators; adapter sets framework, infers entrypoint to the file containing `Crew(...)` or `crew.kickoff()`; wrapper template invokes `Crew.kickoff(inputs={...})` with parsed CLI input.

#### Feature J: smolagents adapter

- **Why:** Vision-listed.
- **What:** Detect via `smolagents` import (`CodeAgent`, `ToolCallingAgent`); adapter; wrapper template that calls `agent.run(prompt)`.

#### Feature K: AutoGen / AG2 adapter (optional, evaluate demand)

- **Why:** Big in research/agentic-workflow space, not in the vision list. Evaluate before committing.
- **What:** Detect `autogen`, `autogen_agentchat`, `ag2`. Lower priority.

#### Feature L: LlamaIndex agent adapter (optional)

- **Why:** Common in RAG-style agents.
- **What:** Detect `llama_index.core.agent` + `AgentRunner`/`ReActAgent`.

#### Feature M: Node-side adapters (LangChain JS, LangGraph JS, Mastra, Vercel AI SDK)

- **Why:** Right now Node frameworks are only loosely detected via dependency strings; there is no adapter producing high-coverage hints, no Node wrapper template, and no class-based wrapper synthesis. The OpenAI Agents SDK now ships in JS too.
- **What:** Add `framework_adapters/langchain_node_adapter.py`, `langgraph_node_adapter.py`, `mastra_adapter.py`, `vercel_ai_adapter.py` with parallel structure to the Python ones. Add `wrapper_templates/*.{js,ts}.j2`.

### Tier 4 — UX, robustness, and parity polish

#### Feature N: Non-interactive mode (`--yes` / `--non-interactive`)

- **Why:** `PromptSession` already handles non-TTY EOF gracefully, but there is no explicit `--yes` flag, which makes scripted onboarding (CI, Copilot agents, dev-container post-create) brittle. Today users have to pipe `yes` or close stdin.
- **What:** Add an explicit flag that takes all defaults, and a `--dry-run` flag that prints the would-be `kinnoo.yaml` without writing.

#### Feature O: GitHub URL support beyond `github.com/owner/repo`

- **Why:** The regex (`_GITHUB_URL_RE`, line 86-89) rejects `https://github.com/owner/repo/tree/<branch>/<subdir>`, SSH `git@github.com:owner/repo.git`, GitLab/Bitbucket, and arbitrary git URLs. This blocks the very common "import the agent that lives inside a sub-folder of a monorepo" workflow.
- **What:** Accept `tree/<ref>/<path>` URLs and translate them into clone + `--subdir`; accept SSH; gracefully reject hosts we don't recognize with a clear message.

#### Feature P: Stable, schema-driven manifest emission

- **Why:** `_build_manifest_from_analysis` builds YAML by string concatenation and `manifest_lines.insert(...)` magic offsets. This is fragile — a future schema change to put e.g. `runtime.package_manager` somewhere else is a one-line edit in the schema but a multi-line surgery in `import_command.py`, and bugs here silently produce invalid manifests.
- **What:** Build a Python dict, pass it through `validate_manifest_data`, and dump with `yaml.safe_dump(..., sort_keys=False)` so the manifest is always schema-shaped by construction. Snapshot tests for every framework.

#### Feature Q: Dependency-confidence reporting

- **Why:** Today the user gets a flat list of inferred dependencies with no indication of which were found in `requirements.txt` vs. inferred from `import` statements vs. inferred via `uv export`. For a non-Python user, the gap is even bigger.
- **What:** Surface a per-dependency provenance ("from pyproject", "from imports") and ask before adding inference-only deps to `requirements.txt`/`package.json`/`go.mod`. This is the difference between "kinnoo import is magic" and "kinnoo import is trustworthy".

#### Feature R: Detect and migrate `.env` / `.env.example` to `env_vars`

- **Why:** Almost every real agent codebase has a `.env.example`. The analyzer currently only finds env vars by scanning Python AST for `os.environ.get`/`os.getenv`. Many TS/JS/Go agents go undetected.
- **What:** Parse `.env*` files (excluding `.env` itself by default for safety) and seed `env_vars` from their keys.

#### Feature S: Detect Dockerfile / `compose.yaml` and surface them as `services` candidates

- **Why:** A surprising number of agent projects bundle Postgres/Redis/Qdrant via Docker Compose. Today these services don't get into `kinnoo.yaml` at all unless their connection string appears in source.
- **What:** Light parser for `docker-compose.yml`/`compose.yaml` `services:` keys → suggested manifest `services` entries (gated by user confirmation).

#### Feature T: First-class regression suite per `(language × framework)` matrix

- **Why:** Today `tests/client_cli_import/` is comprehensive for Python + LangChain/LangGraph/OpenAI/OpenClaw, but adding Go or CrewAI without explicit fixtures will silently regress. The repo already has `tests/client_cli_init/test_init_go_feature19.py` (Go init) — `import` deserves equivalent coverage.
- **What:** Build a parameterized fixture matrix `(python|nodejs|typescript|go) × (no-framework|langchain|langgraph|openai|crewai|smolagents|pydantic-ai|openclaw)` with synthetic minimal projects and assert the produced manifest validates and the produced dependency manifest is `pack`-acceptable.

---

## 4. Is "universal kinnoo import" realistic?

**Short answer: no, and that's fine.** Here's the nuance:

- "Universal" in the sense of "import any random agent repo and produce a working kinnoo manifest with zero further edits" is **not realistic** because:
  - Agent codebases are too heterogeneous: monorepos, multi-language, custom build systems, custom CLI argument parsers, custom prompt-loading conventions, and home-grown agent loops that look nothing like a framework's idioms.
  - The kinnoo manifest hard-encodes a CLI-runnable contract (one-shot stdin/argv → stdout, daemon, or mcp-server). Many agents are written as Jupyter notebooks, FastAPI services with bespoke routers, Discord bots, Slack apps, or web UIs that don't fit any of those modes without a wrapper.
  - "Configuration via `.env` plus arbitrary YAML/TOML files plus prompts inlined in code" is the modal pattern, and there is no general-purpose extractor for prompt assets.

- "Universal" in the sense of "for the agent shapes kinnoo intends to support — CLI-runnable, framework-aligned, in Python/TS/Go — `kinnoo import` should produce a working manifest plus dependency file with at most a couple of confirmation prompts" is **realistic**, and the gap analysis above gets you most of the way there.

- The pragmatic recommendation: **commit to a supported matrix** and document it in `vision.md` and `README.md`. A reasonable v1 matrix:

  | Language   | Frameworks supported by `kinnoo import` (high-coverage adapters)            |
  | ---------- | --------------------------------------------------------------------------- |
  | Python     | langchain, langgraph, openai-agents, pydantic-ai, crewai, smolagents, "no-framework" |
  | TypeScript | langchain (JS), langgraph (JS), openai-agents (JS), mastra, vercel-ai, "no-framework" |
  | JavaScript | same as TS but without TS-specific build hints                              |
  | Go         | "no-framework", openai (raw SDK), mcp-server, mcp-client                    |

  Outside that matrix, `kinnoo import` should still produce a best-effort `kinnoo.yaml` with explicit warnings + a clear TODO list — exactly the "fallback to generic analyzer output" behavior that already exists. This keeps "kinnoo import works on my repo" honest and avoids overpromising.

- The single largest user-visible win is **Tier 1 (A–D)**. Without those, kinnoo's "publish a Node or Go agent" promise is silently broken at the import boundary. Tier 2 and Tier 3 are the difference between a usable tool and a delightful one. Tier 4 is the difference between a delightful tool and one that survives breadth.

---

## 5. Concrete next steps I'd recommend, in order

1. **Tier 1, Feature A** — Node/TS `package.json` synthesis. Highest immediate ROI.
2. **Tier 1, Feature B** — Go detector + `go.mod` synthesis. Closes the language gap that the schema already promises.
3. **Tier 4, Feature P** — Schema-driven manifest emission. Makes everything that follows safer to build.
4. **Tier 4, Feature N** — `--yes`/`--dry-run`. Unblocks scripted onboarding and CI smoke tests for the rest of the work.
5. **Tier 3, Features H–J** — PydanticAI, CrewAI, smolagents adapters (Python). Vision-aligned framework breadth.
6. **Tier 2, Feature E** — TypeScript runtime fidelity.
7. **Tier 3, Feature M** — Node-side adapters.
8. **Tier 1, Features C and D** — lockfiles + `go.sum`.
9. **Tier 4, Features O, Q, R, S, T** — UX, trust, and regression coverage.

Each of these is independently mergeable and testable; none of them require a rewrite of `import_command.py`.
