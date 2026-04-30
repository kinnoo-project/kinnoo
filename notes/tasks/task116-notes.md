# Task 294 Notes - Login card UI and required fields (2026-03-24)

## Summary
- Implemented centered dark-theme login card in web/app/(public)/login/page.tsx.
- Added required controls:
  - Username (E-mail) input
  - Password input
  - Login button
  - Forgot your password? link to /forgot-password
- Added task-associated test file web/__tests__/login-page.test.tsx with field/link rendering checks.

## Teaching Notes
- UI-first task slicing helps isolate structure from behavior: this task delivers accessible form scaffolding before adding validation/network complexity.
- Label-first form testing is resilient and accessibility-aligned compared to placeholder-only selectors.
- For AI interview prep: this mirrors progressive capability rollout in agents, where interface contracts are validated before executing side-effecting actions.

## Targeted Test Runs
- Vitest (task-associated):
  - cd web && npx vitest run __tests__/login-page.test.tsx --environment jsdom -t "required fields and forgot-password link"
  - Result: 1 passed
- Build/type check:
  - cd web && npm run build
  - Result: success
- Manifest validation:
  - python scripts/validate_project_manifests.py
  - Result: validation passed
