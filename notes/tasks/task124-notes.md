# Task302 Notes - Reusable AgentCard Component

## What I implemented
- Added reusable `AgentCard` component in `web/components/blocks/AgentCard.tsx`.
- `AgentCard` renders required fields with stable labels:
  - Tenant, Name, Version, Author, Framework, Size, Description
- Name is rendered as an interactive button that invokes `onNameClick(agent)`.
- Integrated card rendering into both My Agents and Search result sections through `RegistryTabs`.
- Wired click callback in registry route (`onAgentNameClick`) as the modal trigger hook point for follow-up tasks.

## Why this design
- The reusable card encapsulates metadata display concerns, which reduces duplication across My Agents and Search views.
- Keeping click behavior callback-based allows modal behavior to be added without modifying card internals.
- Explicit field labels make component-level testing deterministic.

## Teaching notes
- This is a component contract pattern: pass data + callbacks, avoid embedding parent behavior directly in the child.
- In interview settings, this demonstrates separation of presentation (`AgentCard`) from orchestration (`RegistryPage`).

## Tests run
Command:
```bash
cd web && npm run test -- agent-card-modal.test.tsx -t "renders required metadata fields and clickable name"
```

Result:
```text
1 passed
```
