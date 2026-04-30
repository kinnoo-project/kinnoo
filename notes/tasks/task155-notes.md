# Task399 Notes

## Summary
- Completed feature13 AC4/AC5 by:
  - ensuring auth flow coverage in `docs/security-model.md` (registration, login, JWT issuance, token refresh note, logout)
  - adding README cross-reference to `docs/security-model.md`

## Why
- Task399 focuses on authentication-flow communication quality and discoverability from the project entrypoint docs.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature94_group2"`
- Result: 1 passed.

## Teaching Notes
- For security documentation, be explicit when a capability is intentionally absent (for example, no dedicated JWT refresh endpoint) rather than silently omitting it.
- README cross-links should point to deeper operational docs so new developers can move from overview to implementation details quickly.
