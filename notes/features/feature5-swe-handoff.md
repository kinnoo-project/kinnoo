# Feature 51 SWE Handoff - Landing Page Content, Terminal Preview, and Feature Grid

## Goal
Implement the public landing page at / according to Sub-phase 2 in notes/phases/phase5-planning.md.

## Scope
- Parent feature: feature5
- Tasks: task112, task113, task114, task115
- Related tests: test432, test433, test434, test435, test436
- Dependency context: feature4 (global theme/layout)

## Required copy (must match exactly)
### Hero Title
Package, publish, share your AI agents with the world

### Sub-headline
Take any AI agent — a LangGraph chatbot, a PydanticAI workflow, an OpenClaw daemon — and give it a portable, version-controlled, signed package that anyone can install and run

### Feature cards
1. Header: Supports common AI agent frameworks
   Subtext: Initialize, import or install AI agents developed with LangChain, LangGraph, PydanticAI, OpenAI Agents SDK, OpenClaw and more.
2. Header: One-command packaging
   Subtext: Bundle your agent, its dependencies, assets, and state into a single portable .kno archive — ready to share or publish.
3. Header: Discover and install from a registry
   Subtext: Publish agents to a hosted registry where others can search, inspect, and install them with kinnoo install — like npm, but for agents.
4. Header: Built to run real-world agents
   Subtext: kinnoo handles environment setup, dependency isolation, and runtime wiring for Python and Node.js agents, including one-shot and long-running daemon-based agents.
5. Header: Security built-in
   Subtext: Signed archives, permission declarations, static security sweeps, dependency audits, preflight checks, runtime monitoring, and a kill switch — trust what you run.
6. Header: Inspect before you run
   Subtext: Review any agent's manifest, dependencies, environment variables, permissions, and services before installation — no surprises.

## Task-by-task implementation guidance

### task112 - Hero section and responsive structure
Files:
- <redacted-path>)/page.tsx

Implement:
1. Build page sections in order: Hero -> Terminal Preview -> Features grid.
2. Use one h1 only.
3. Keep layout responsive at 375px, 768px, 1280px.
4. Use theme classes established in Sub-phase 1.

Done when:
- Hero title/sub-headline exact copy is visible and readable on mobile/desktop.

### task113 - Terminal Preview with copy button
Files:
- <redacted-path>
- <redacted-path>)/page.tsx

Implement:
1. Terminal-style block with command text: pip install kinnoo.
2. Copy button using navigator.clipboard.writeText.
3. Show short feedback state after copy (example: Copied!).
4. Ensure keyboard focus and visible focus ring.

Done when:
- Copy button works and feedback resets cleanly.

### task114 - Features section
Files:
- <redacted-path>
- <redacted-path>)/page.tsx

Implement:
1. Create typed array of six cards and map to UI.
2. Use exact copy for each card.
3. Add subtle hover affordance (border/background/elevation).
4. Prevent overflow on small screens.

Done when:
- Six cards render with exact heading/subtext and responsive wrapping.

### task115 - Automated tests
Files:
- <redacted-path>
- <redacted-path>

Implement:
1. Add tests for hero title/sub-headline exact text.
2. Add tests for terminal command and copy button.
3. Add tests for all six feature cards.
4. Add assertions for accessible controls where applicable.

Done when:
- test432-test436 scenarios pass.

## Notes for SWE Agent
- Keep component boundaries clean: page composition in route file, reusable blocks in components/blocks.
- Do not alter auth flow logic in this feature; login behavior is feature6.
- Do not change planning copy punctuation or dashes.
