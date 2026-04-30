# Task304 Notes - Install Command Block and Copy Flow

## What I implemented
- Added deterministic install command helper in `web/lib/install-command.ts`:
  - `kinnoo install {tenant_slug}/{agent_slug}@{version}`
- Extended `AgentManifestModal` to render install command block for Search-context selections only.
- Added copy-to-clipboard action with transient `Copied!` feedback.
- Updated registry selection wiring to track modal source (`my-agents` vs `search`) so install block only appears for search results.
- Added task126 test451 coverage in `web/__tests__/agent-card-modal.test.tsx`.

## Why this design
- Source-aware modal rendering prevents install command controls from appearing in contexts where they are not requested.
- Command generation is centralized and deterministic to reduce test flakiness and avoid duplicated formatting logic.
- Copy feedback is brief and explicit, improving UX while remaining testable.

## Teaching notes
- This is a useful example of “contextual UI features”: same modal component, different capabilities based on invocation context.
- In interview settings, deterministic string builders are a strong pattern for reliability and reproducibility.

## Tests run
Command:
```bash
cd web && npm run test -- agent-card-modal.test.tsx -t "install command in search modal and copy feedback"
```

Result:
```text
1 passed, 3 skipped
```
