# Task 287 Notes - MainLayout header and root layout wiring (2026-03-24)

## Summary
- Implemented web/components/blocks/MainLayout.tsx with:
  - Hamburger menu trigger (Lucide icon)
  - Radix Dialog sheet containing GitHub, Docs, Report an Issue links
  - Ghost-style Login and Sign Up buttons using Radix Slot
  - Glassmorphism header style and card/border token usage from themeConfig
- Wired MainLayout into web/app/layout.tsx so all routes render under the shared header.
- Added task-associated integration tests in web/__tests__/layout.test.tsx for test429 and test430.

## Teaching Notes
- This layout approach mirrors agent-system composition patterns: a shared shell (MainLayout) centralizes cross-cutting concerns (navigation, auth entry points) while route pages stay focused on task-specific content.
- Accessibility and testability reinforce each other: explicit aria labels and Radix semantics made interaction tests straightforward and stable.
- Small test-isolation bugs (DOM leakage across tests) are common in UI suites; explicit cleanup is a reliable fix and a good interview talking point about deterministic test environments.

## Targeted Test Runs
- Vitest (task-associated):
  - cd web && npx vitest run __tests__/layout.test.tsx --environment jsdom
  - Result: 2 passed
- Build/type check:
  - cd web && npm run build
  - Result: success
- Manifest validation:
  - python scripts/validate_project_manifests.py
  - Result: validation passed
