# Task395 Notes

## Summary
- Added explicit manifest-format history and compatibility notes to `docs/kinnoo-yaml-spec.md`.
- Verified that spec cross-references remain present from `README.md` and CLI help (`src/kinnoo/cli.py`).
- Completed repository housekeeping requested by operator:
  - moved `docs/iac-operator-runbook.md` to `notes/iac-operator-runbook.md`
  - moved `docs/operator-launch-week-timeline.md` to `notes/operator-launch-week-timeline.md`
  - ignored `.wrangler` artifacts in `.gitignore`

## Why
- Task395 covers feature12 AC4/AC5: version/backward-compatibility notes + cross-references.
- The docs move and ignore rule prevent future accidental inclusion of personal/operator notes and build artifacts in task commits.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature92_group1 or test_feature92_group2"`
- Result: 2 passed.

## Teaching Notes
- For documentation tasks with acceptance criteria, model tests around stable anchors (sections and links) rather than full text snapshots.
- Put operational runbooks in `notes/` when they are personal/operator-facing, and keep `docs/` focused on developer-facing material.
- Add ignore rules early for generated artifacts (`.open-next`, `.wrangler`) to keep task commits minimal and reviewable.
