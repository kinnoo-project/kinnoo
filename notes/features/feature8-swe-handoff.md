# Feature 54 SWE Handoff - Agent Cards, Manifest Modal, and Install Command Copy Flow

## Feature context
- Feature ID: feature8
- Scope: Agent card UI + manifest modal + install command copy behavior
- Planning source: notes/phases/phase5-planning.md (Sub-phase 3)
- Tasks: task124, task125, task126, task127
- Tests: test448, test449, test450, test451, test452
- Depends on: feature7

## Product requirements summary
1. Agent cards in both views show required metadata fields.
2. Name is clickable and opens modal.
3. Modal has explicit close X.
4. Modal fetches detail from GET /api/agents/{tenant_slug}/{agent_slug}.
5. Search modal includes terminal-like install command and copy button.
6. Copy action shows visible success feedback.
7. Component tests validate the entire card->modal->copy flow.

## Task handoff

### task124
Goal:
- Build reusable AgentCard component for both My Agents and Search lists.

Files:
- <redacted-path>
- <redacted-path>)/registry/page.tsx

Implementation notes:
1. Render fields: Tenant, Name, Version, Author, Framework, Size, Description.
2. Name click should call handler to open modal context.
3. Keep props typed and stable for tests.

### task125
Goal:
- Build manifest modal and endpoint integration.

Files:
- <redacted-path>
- <redacted-path>
- <redacted-path>)/registry/page.tsx

Implementation notes:
1. Fetch detail from /api/agents/{tenant_slug}/{agent_slug} on open/select.
2. Render manifest metadata safely and show loading/error states.
3. Add explicit X close control and reliable close behavior.

### task126
Goal:
- Add install command terminal block and copy action in search modal context.

Files:
- <redacted-path>
- <redacted-path>

Implementation notes:
1. Keep install command generation deterministic.
2. Add copy button with copied feedback.
3. Preserve keyboard accessibility and focus visibility.

### task127
Goal:
- Add automated tests for card fields, modal interactions, and copy flow.

Files:
- <redacted-path>
- <redacted-path>

Implementation notes:
1. Assert all required fields render in AgentCard.
2. Assert click Name opens modal, X closes modal.
3. Assert detail endpoint data is rendered in modal.
4. Assert install command copy action works with feedback.

## Acceptance criteria mapping
- AC1 -> test448
- AC2 -> test449
- AC3 -> test449
- AC4 -> test450
- AC5 -> test451
- AC6 -> test451
- AC7 -> test452

## SWE pitfalls to avoid
- Do not hardcode manifest details; always use detail endpoint response shape safely.
- Keep modal close behavior robust when loading or error states occur.
- Keep copy behavior deterministic to avoid flaky tests.
