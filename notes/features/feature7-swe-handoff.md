# Feature 53 SWE Handoff - Authenticated Registry Dashboard Shell, Tabs, and Data Views

## Feature context
- Feature ID: feature7
- Scope: Sub-phase 3 registry dashboard shell and tabbed views at /registry
- Planning source: notes/phases/phase5-planning.md (Sub-phase 3)
- Tasks: task120, task121, task122, task123
- Tests: test443, test444, test445, test446, test447
- Depends on: feature6

## Product requirements summary
1. Build authenticated dashboard route /registry.
2. Add secondary nav with My Agents, Search, Logout.
3. My Agents view is default.
4. Search view has text input + Show only my agents checkbox.
5. Use framer-motion for transitions between My Agents and Search.
6. Use existing API paths via proxy: /api/agents and /api/search.
7. Provide loading, empty, and error states.

## Task handoff

### task120
Goal:
- Build dashboard shell and secondary nav controls.

Files:
- web/app/(auth)/registry/page.tsx
- web/components/blocks/RegistryNav.tsx

Implementation notes:
1. Render nav controls clearly and keep selected-state styling obvious.
2. Default active tab on initial render must be My Agents.
3. Keep keyboard access (tab/focus) intact.

### task121
Goal:
- Implement tab state and framer-motion transitions between My Agents and Search.

Files:
- web/app/(auth)/registry/page.tsx
- web/components/blocks/RegistryTabs.tsx

Implementation notes:
1. View switching should not flash or lose state unexpectedly.
2. Add search input + Show only my agents checkbox in Search view.
3. Keep transition code small and testable.

### task122
Goal:
- Integrate data fetching from existing backend proxy routes.

Files:
- web/lib/registry-client.ts
- web/app/(auth)/registry/page.tsx

Implementation notes:
1. My Agents calls /api/agents.
2. Search calls /api/search with query/filter params.
3. Requests should remain session-cookie compatible.
4. Render explicit loading, empty, and error states in both views.

### task123
Goal:
- Add automated tests for shell/tabs/search controls/data states.

Files:
- web/__tests__/registry-dashboard.test.tsx
- web/package.json

Implementation notes:
1. Cover nav control rendering and default My Agents selection.
2. Cover Search controls and tab switching.
3. Cover loading/empty/error behaviors with mocked client calls.

## Acceptance criteria mapping
- AC1 -> test443
- AC2 -> test444
- AC3 -> test445
- AC4 -> test446
- AC5 -> test447
- AC6 -> test447
- AC7 -> test446

## SWE pitfalls to avoid
- Do not invent new backend endpoints for this feature.
- Do not move auth/session logic to localStorage/sessionStorage.
- Keep framer-motion transitions lightweight and deterministic for tests.
