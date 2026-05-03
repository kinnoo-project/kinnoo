# Brainstorming: Rust MCP Server Support in Kinnoo

**Date:** 2026-05-03

---

## Prompt

> I want to brainstorm using kinnoo to support an MCP server developed with Rust. See issue #7 (https://github.com/kinnoo-project/kinnoo/issues/7) for details - see issue description and comments. As a Rust, Unix and MCP server expert, and with a deep knowledge of the kinnoo codebase, give your assessment on the feasibility and practicality of supporting this, and an implementation (feature) roadmap. Also highlight a few "gotchas" I might encounter and things to consider while developing and testing Rust agent support in kinnoo.

---

## Response

Assessment: supporting Rust MCP servers in Kinnoo is feasible and practical, but it should be treated as first-class compiled-agent support rather than a small template tweak.

**Current state:**
- Kinnoo already has useful primitives: `runtime.type` supports `one-shot`, `mcp-server`, and `daemon`; `run` has long-running process handling, daemon state files, logs, stop/attach helpers, readiness probes, service checks, env var handling, and package/install/signing flows.
- Rust is not currently a supported runtime language. `runtime.language` is limited to Python and Node-compatible languages in `src/kinnoo/schema.py`, `src/kinnoo/init_command.py`, and runtime checks in `src/kinnoo/run_command.py`.
- `kinnoo inspect` currently requires `requirements.txt` for directory targets, which is Python-centric and would need to become runtime-aware.
- `kinnoo pack` currently requires `requirements.txt` for non-Node runtimes, so adding `rust` without changing pack/install behavior would create awkward false requirements.
- Existing `runtime.run_command` looks tempting as a workaround, but `kinnoo run` still rejects unsupported languages before process launch, so a clean Rust implementation requires schema/runtime changes.

**Feasibility:**
- High for local development support: scaffold Rust project, validate Cargo metadata, build, run, stop/log daemon.
- Medium for portable install/distribution: Rust binaries are OS/architecture/libc-specific, so Kinnoo must model platform-specific artifacts instead of assuming one `.kno` works everywhere.
- Medium-high for MCP support specifically: Kinnoo can supervise an MCP server process, but if the MCP transport is `stdio`, stdout becomes protocol-critical and Kinnoo must avoid corrupting the JSON-RPC stream.

**Practicality:**
- For the MCP server author, Kinnoo is useful if it gives repeatable scaffolding, preflight checks, manifest validation, packaging, signing, install instructions, and daemon control.
- It becomes burdensome if Kinnoo forces a non-idiomatic Rust layout. The Rust project should remain a normal Cargo project; Kinnoo should layer metadata and lifecycle commands around it.
- For end users, Kinnoo is most valuable if it distributes a prebuilt, signed binary and avoids requiring users to install Rust/Cargo.

**Recommended manifest direction:**

Keep `entrypoint` as the executable path used at runtime. Add first-class Rust/build metadata rather than overloading Python/Node fields.

Example target shape:

```yaml
name: mcp-os
version: 0.1.0
description: Local OS MCP server
entrypoint: bin/mcp-os
runtime:
  language: rust
  version: ">=1.75"
  type: mcp-server
  transport: stdio
  shutdown_timeout_seconds: 5
build:
  system: cargo
  command: cargo build --release
  artifact: target/release/mcp-os
  target_triple: x86_64-unknown-linux-gnu
artifacts:
  platforms:
    - os: linux
      arch: x86_64
      libc: glibc
      path: bin/mcp-os
permissions:
  filesystem_scope: read-only
  shell: false
  network: false
env_vars: []
dependencies: []
inputs:
  type: json
outputs:
  type: json
```

**Important distinction:**
- In development, `kinnoo run` may execute `cargo run` or build then execute `target/release/<binary>`.
- In distribution, `entrypoint` should point to a bundled executable, ideally under `bin/`, not deep inside `target/release/`.

---

## Roadmap

### 1. Define the Rust compatibility contract
- Decide whether Rust support is for:
  - local source projects only,
  - prebuilt binary packages only,
  - or both.
- Decide MCP transport support:
  - `stdio` for normal MCP host integration,
  - TCP/HTTP/SSE for daemon-style local service,
  - Unix socket if you want Unix-native local daemons later.
- Define whether `runtime.type: mcp-server` and `runtime.type: daemon` are separate modes or whether Rust MCP daemon uses both concepts through fields like `runtime.transport`.

### 2. Update `kinnoo.yaml` schema
- Add `rust` to supported runtime languages.
- Add optional `build` metadata:
  - build system, command, artifact path, target triple, release/debug profile.
- Add optional platform artifact metadata.
- Make Python-only files like `requirements.txt` conditional on `runtime.language == python`.
- Make Node-only package-manager checks conditional on Node-compatible runtimes.
- Document Rust examples in `docs/kinnoo-yaml-spec.md`.

### 3. Add Rust scaffolding to `kinnoo init`
- Support a command shape like:
  - `kinnoo init mcp-server --language rust my-rust-mcp`
  - or `kinnoo init rust-mcp-server my-rust-mcp`.
- Generate:
  - `Cargo.toml`
  - `src/main.rs`
  - `kinnoo.yaml`
  - `README.md`
  - `.gitignore`
  - optional `tests/` or MCP smoke-test notes.
- Keep the project as a normal Cargo binary crate so Rust developers can still use `cargo build`, `cargo test`, and `cargo run` directly.

### 4. Make `inspect` runtime-aware
- For Rust projects, inspect should verify:
  - `kinnoo.yaml` validity,
  - Cargo manifest exists,
  - `cargo`/`rustc` availability for source projects,
  - build artifact path if declared,
  - platform metadata if binary distribution is declared,
  - permissions/env var declarations.
- Avoid building by default during `inspect`; building has side effects and can be slow.
- Add an explicit build/check mode later, such as `kinnoo inspect --build-check` or reuse `kinnoo check`.

### 5. Add Rust preflight support
- For source/dev mode:
  - check `cargo` is on PATH,
  - check Rust version satisfies `runtime.version`,
  - optionally run `cargo metadata` or `cargo check`.
- For binary/distribution mode:
  - check the entrypoint exists,
  - check executable bit on Unix,
  - check platform compatibility,
  - fail clearly if a Linux binary is installed on macOS/Windows or wrong architecture.

### 6. Add Rust run support
- Development mode:
  - run `cargo run` or `cargo build --release` then execute artifact.
- Distribution mode:
  - execute `entrypoint` directly.
- For `runtime.type: daemon`, reuse existing daemon launch/state/log/stop flow.
- For `runtime.type: mcp-server`, be careful with stdio:
  - stdout must be reserved for MCP JSON-RPC messages,
  - Kinnoo diagnostics should go to stderr,
  - logs should not be interleaved into stdout.

### 7. Harden pack/install for compiled artifacts
- Build before packaging only when explicitly requested, e.g. `kinnoo pack --build`.
- Package the final binary under a stable path like `bin/mcp-os`.
- Exclude bulky build directories like `target/` by default.
- Preserve/restore executable permissions on install, or explicitly `chmod +x` after extraction on Unix.
- Record platform metadata in the package.
- Recommend signing Rust MCP server packages with Kinnoo's existing signing flow.

### 8. Add MCP-specific tests
- Unit tests:
  - validator accepts Rust manifest,
  - rejects invalid build/artifact fields,
  - Rust projects do not require `requirements.txt`.
- Init tests:
  - Rust MCP scaffold contains `Cargo.toml`, `src/main.rs`, and valid `kinnoo.yaml`.
- Inspect/preflight tests:
  - use fake `cargo` where possible to avoid requiring Rust in every CI environment.
- Integration tests:
  - if Rust is installed, build and run a tiny MCP stdio server.
- Protocol smoke test:
  - send MCP `initialize` and `tools/list` messages over stdio and assert valid JSON-RPC responses.

---

## Answers to Issue #7 Questions

### `kinnoo init`
It should scaffold a normal Cargo binary project plus Kinnoo metadata.

Recommended layout:
```text
my-rust-mcp/
├── Cargo.toml
├── src/
│   └── main.rs
├── kinnoo.yaml
├── README.md
├── .gitignore
└── tests/
```

The template should be intentionally minimal. Avoid locking into one Rust MCP SDK until the ecosystem stabilizes; document how to swap SDKs.

### `kinnoo inspect` and `kinnoo run`
- `inspect` should validate metadata and report Rust build readiness, not necessarily build.
- `run` should either:
  - build then execute the binary,
  - run `cargo run`,
  - or execute a packaged binary depending on manifest/build mode.
- For daemon mode, existing daemon process management can be reused after Rust process args are generated.

### `entrypoint`
- For packaged installs: `entrypoint: bin/<binary-name>` is best.
- For local dev: either use `entrypoint: target/release/<binary-name>` after build, or use `build.artifact` plus `runtime.run_command`/build metadata to resolve it.
- Avoid using `src/main.rs` as the entrypoint because Kinnoo runs executables/scripts, not source files.

### Development/testing value
- Useful if Kinnoo remains a wrapper around normal Cargo workflows.
- Burdensome if Rust developers must reshape their project away from Cargo conventions.
- Best approach: make Kinnoo additive—manifest, checks, packaging, daemon supervision—not a replacement for Cargo.

### Install/run value for others
- Yes, strongly, if Kinnoo packages signed prebuilt binaries with platform metadata.
- Less useful if users must install Rust and compile locally.
- The strongest user experience is: `kinnoo install mcp-os` followed by `kinnoo run`/daemon start, with no Rust toolchain required.

---

## Gotchas

- **MCP stdio is fragile:** stdout is the protocol channel. Any Kinnoo banner, readiness message, log line, or debug print on stdout can break MCP clients. Send Kinnoo diagnostics to stderr for stdio MCP mode.
- **"Daemon" and "MCP stdio server" are not always the same thing.** A stdio MCP server is usually launched by a host process and lives as long as that session; a daemon usually listens on a socket/port or exposes another transport.
- **Rust binaries are platform-specific.** You need OS, architecture, and sometimes libc metadata: Linux glibc vs musl matters.
- **Cargo build output under `target/` is large.** Kinnoo should not package the entire `target/` directory by accident.
- **Unix executable bits may be lost or mishandled in zip archives.** Install should ensure packaged binaries are executable.
- **Long-running Rust processes should handle SIGTERM gracefully;** Kinnoo already escalates to SIGKILL, but the Rust server should flush state and close resources on termination.
- **Readiness for stdio MCP is different from TCP readiness.** A good readiness check is an actual MCP `initialize` handshake, not just "process started."
- **Rust logs should go to stderr, not stdout, for stdio MCP.**
- **Cross-compilation and reproducible builds can become complex quickly.** Start with local-platform builds, then add multi-platform release packaging later.
- **Security model matters more for native binaries.** Signed archives, checksums, publisher identity, and strict install mode should be part of the recommended Rust MCP workflow.
- **If the MCP server touches OS resources, model permissions explicitly in `kinnoo.yaml`;** do not hide powerful filesystem/shell access behind a generic binary.

---

## Recommended First Implementation Slice

1. Add `runtime.language: rust` to the schema.
2. Make `inspect`, `preflight`, `pack`, and `run` stop assuming non-Node means Python.
3. Add minimal Rust MCP scaffold to `kinnoo init`.
4. Support local `cargo run`/`cargo build --release`.
5. Add binary entrypoint execution.
6. Add tests with a fake `cargo` plus optional real Rust integration.
7. Defer multi-platform binary registry distribution until the local Rust workflow is solid.
