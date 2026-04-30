# Task 291 Notes - Terminal Preview with copy interaction (2026-03-24)

## Summary
- Added reusable `TerminalPreview` component in `web/components/blocks/TerminalPreview.tsx`.
- Rendered exact command text `pip install kinnoo` with copy button and short copied feedback state.
- Wired component into landing page route composition in `web/app/(public)/page.tsx`.
- Added task-associated test in `web/__tests__/landing-page.test.tsx` for command visibility + copy behavior.

## Teaching Notes
- For interactive UI elements, keep state local and short-lived (e.g., copied feedback timer), which improves component reuse and test isolation.
- Accessibility-first labels (`aria-label`) reduce ambiguity in automation and make behavior easier to verify.
- This maps to AI-agent UX patterns: explicit action affordances + immediate feedback loops improve trust and operator control.

## Targeted Test Runs
- Vitest (task-associated):
  - cd web && npx vitest run __tests__/landing-page.test.tsx --environment jsdom -t "terminal command and supports copy feedback"
  - Result: 1 passed (1 unrelated skipped)
- Build/type check:
  - cd web && npm run build
  - Result: success
- Manifest validation:
  - python scripts/validate_project_manifests.py
  - Result: validation passed
