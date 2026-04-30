# Feature 96 — SWE Handoff: README Rewrite & Supported Agents

## Context
Rewrite README.md for beta release. Create docs/supported-agents.md with framework compatibility.

## Files to Modify
- `README.md` — Complete rewrite for public-facing beta

## Files to Create
- `docs/supported-agents.md` — Framework compatibility matrix

## README Structure
1. **Header** — Project name, tagline, badges (PyPI version, CI status, license)
2. **What is kinnoo?** — 2-3 sentence overview
3. **Quick Start** — 5-command workflow (install → init → run → pack → publish)
4. **Features** — Bullet list of key capabilities
5. **Installation** — pip install instructions
6. **Documentation** — Links to docs/ files
7. **Supported Frameworks** — Brief list, link to supported-agents.md
8. **Contributing** — Link to CONTRIBUTING.md
9. **License** — MIT

## Supported Agents Matrix
| Feature | ChatGPT | OpenAI | Gemini | Claude | Generic |
|---------|---------|--------|--------|--------|---------|
| init scaffold | ✅ | ✅ | ✅ | ✅ | ✅ |
| pack | ✅ | ✅ | ✅ | ✅ | ✅ |
| run | ✅ | ✅ | ✅ | ✅ | ✅ |
| publish | ✅ | ✅ | ✅ | ✅ | ✅ |
| install | ✅ | ✅ | ✅ | ✅ | ✅ |

## Implementation Notes
- Remove all internal development references from README
- No scratch/, notes/, outputs/ references
- Badges: use shields.io for PyPI, CI status from GitHub Actions
- Keep it concise — README should be scannable in 30 seconds

## Dependencies
- feature12 (yaml spec), other feature (unreferenced) (CLI reference) — so we can link to them

## Acceptance Criteria Summary
1. README rewritten for beta: concise, professional
2. docs/supported-agents.md with framework matrix
3. No internal development details
