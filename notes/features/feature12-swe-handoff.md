# Feature 92 — SWE Handoff: kinnoo.yaml Specification Document

## Context
Create a comprehensive specification document for the kinnoo.yaml manifest format. This is the primary reference for agent developers.

## Files to Create
- `docs/kinnoo-yaml-spec.md`

## Content Structure
1. **Overview** — What kinnoo.yaml is, where it lives, when it's validated
2. **Required fields** — name, version, framework, entrypoint
3. **Optional fields** — description, author, license, dependencies, env_vars, etc.
4. **Framework-specific fields** — Fields unique to chatgpt, openai, gemini, claude, generic
5. **Field reference table** — name, type, required/optional, default, description, validation
6. **Validation rules** — name format (lowercase, hyphens), version format (semver), etc.
7. **Examples** — Complete kinnoo.yaml for each supported framework
8. **Version history** — Manifest format changelog

## Implementation Notes
- Reference `src/kinnoo/validator.py` for the actual validation logic and field definitions
- Cross-reference from README.md: add a link in the "Documentation" section
- Include both minimal and full examples
- Document which fields are used by which commands (pack, install, run, publish)

## Dependencies
- None

## Acceptance Criteria Summary
1. docs/kinnoo-yaml-spec.md exists with all fields documented
2. Examples for each framework
3. Cross-referenced from README.md
