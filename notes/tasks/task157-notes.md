# Task401 Notes

## Summary
- Added expected output snippets to:
  - `docs/getting-started.md`
  - `docs/registry-guide.md`
- Added README cross-references to both guides.

## Why
- Task401 covers feature14 AC4/AC5: expected output examples and README discoverability links.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature95_group2"`
- Result: 1 passed.

## Teaching Notes
- Include expected output snippets as examples, not strict guarantees, because message wording can evolve.
- Keep output examples high-signal (success markers and key lines), avoiding environment-specific noise.
- Cross-link guides from README so new users can progress from overview to execution paths quickly.
