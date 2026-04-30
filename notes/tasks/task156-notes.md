# Task400 Notes

## Summary
- Created `docs/getting-started.md` with end-to-end onboarding from install to pack.
- Created `docs/registry-guide.md` with invite-only login/publish/search/install workflow.
- Added `tests/test_feature_95.py` with feature14 grouped acceptance tests.

## Why
- Task400 covers feature14 AC1-AC3: complete walkthrough docs and copy-paste command coverage.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature95_group1"`
- Result: 1 passed.

## Teaching Notes
- Keep getting-started docs task-oriented: install, scaffold, run, package, then forward-link to registry workflows.
- Separate local and remote workflows to reduce cognitive load for first-time users.
- Use executable command blocks for every step to keep docs runnable as a checklist.
