# Feature 53 Smoke Tests - Registry Dashboard Shell and Views

## Goal
Validate Sub-phase 3 dashboard shell, tabs, transitions, and data-state behavior.

## Manual smoke checklist

### 1) Registry route shell
1. Start frontend.
2. Navigate to /registry in authenticated context.
3. Verify secondary nav controls are visible: My Agents, Search, Logout.

Pass when:
- All three controls are present and interactive.

### 2) Default view
1. Load /registry fresh.
2. Verify My Agents view is selected by default.

Pass when:
- My Agents tab is active and corresponding content is visible.

### 3) Search controls
1. Switch to Search.
2. Verify search input appears.
3. Verify Show only my agents checkbox appears and can be toggled.

Pass when:
- Both controls exist and accept input.

### 4) Tab transitions
1. Toggle My Agents -> Search -> My Agents repeatedly.
2. Watch for smooth transition behavior.

Pass when:
- No abrupt layout jumps or broken intermediate states.

### 5) Data loading states
1. Simulate slow API response.
2. Verify loading indicators.
3. Simulate empty result.
4. Simulate API failure.

Pass when:
- Loading, empty, and error states render clearly in both views.

### 6) Proxy route usage
1. Inspect network requests while dashboard loads and while searching.

Pass when:
- My Agents requests target /api/agents and Search requests target /api/search.

### 7) Automated test run
1. Run registry dashboard tests.

Pass when:
- Test suite passes for nav, default view, search controls, tab switching, and data states.

## Sign-off
- [ ] /registry nav complete
- [ ] My Agents default
- [ ] Search controls functional
- [ ] Transition UX acceptable
- [ ] Loading/empty/error states present
- [ ] Proxy endpoints used correctly
- [ ] Dashboard tests passing
