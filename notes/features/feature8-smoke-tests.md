# Feature 54 Smoke Tests - Agent Cards, Manifest Modal, and Copy Flow

## Goal
Validate card metadata rendering, modal behavior, detail-fetch rendering, and install-command copy flow.

## Manual smoke checklist

### 1) Card metadata fields
1. Open /registry My Agents and Search views.
2. Inspect any rendered card.

Pass when:
- Card shows Tenant, Name, Version, Author, Framework, Size, Description.

### 2) Name click -> modal open
1. Click agent Name on a card.

Pass when:
- Modal opens and displays manifest/detail context for selected agent.

### 3) Modal close behavior
1. Click X close control in modal.
2. Re-open modal and close again.

Pass when:
- Modal closes reliably and dashboard state remains intact.

### 4) Detail endpoint rendering
1. Open browser network/devtools while opening modal.

Pass when:
- Request is sent to /api/agents/{tenant_slug}/{agent_slug}.
- Modal content reflects returned metadata/version data.

### 5) Install command block in search modal
1. Open modal from a Search result card.
2. Inspect modal footer/terminal section.

Pass when:
- Terminal-like install command block is present with deterministic command text.

### 6) Copy button behavior
1. Click copy button for install command.

Pass when:
- Visible success feedback appears and copy action completes.

### 7) Automated test run
1. Run agent card/modal tests.

Pass when:
- Tests pass for field rendering, modal open/close, detail rendering, and copy flow.

## Sign-off
- [ ] All required card fields shown
- [ ] Name opens modal
- [ ] X closes modal reliably
- [ ] Detail endpoint used and rendered
- [ ] Search modal install command shown
- [ ] Copy action feedback visible
- [ ] Agent card/modal tests passing
