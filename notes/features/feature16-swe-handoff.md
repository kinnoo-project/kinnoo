# Feature 99 — SWE Handoff: PyPI Publishing Configuration

## Context
Configure the project for PyPI publishing with trusted publisher (OIDC).

## Files to Modify
- `pyproject.toml` — Validate and complete metadata
- `src/kinnoo/__init__.py` — Ensure `__version__` is defined

## Files to Create
- `.github/workflows/pypi-publish.yml` — Publish on release tag

## pyproject.toml Metadata Checklist
- `name`: "kinnoo"
- `version`: synced with `__version__`
- `description`: One-line project description
- `authors`: Jerry's info
- `license`: MIT
- `classifiers`: Development Status, License, Python versions, Topic
- `project-urls`: Homepage, Documentation, Repository, Issues
- `requires-python`: ">=3.11"

## Workflow: pypi-publish.yml
- Trigger: release published (tag v*)
- Steps: checkout → setup Python → build wheel + sdist → publish to PyPI (trusted publisher)
- Uses `pypa/gh-action-pypi-publish@release/v1` with OIDC

## Implementation Notes
- Trusted publisher: requires manual setup on PyPI (add GitHub as trusted publisher for kinnoo package)
- Version should be sourced from a single location
- Test with `pip install dist/kinnoo-*.whl` before publishing
- Consider: `pip install kinnoo` should only install client deps (not server deps)

## Dependencies
- None

## Acceptance Criteria Summary
1. pyproject.toml has complete metadata
2. `pip install` from built wheel works
3. GitHub Actions publishes on release tag
4. Uses trusted publisher (OIDC)
