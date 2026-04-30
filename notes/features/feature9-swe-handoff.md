# Feature 86 — SWE Handoff: Embedded Integrity Manifest

## Context
Create a system to embed tamper-detection metadata in `.kno` archives. During `kinnoo pack`, a JSON file (`META-INF/integrity.json`) listing every file's SHA-256 hash and size is added to the archive. This is the foundation for features 87 (signature) and 88 (install-time verification).

## Files to Create
- `src/kinnoo/integrity.py` — New module with:
  - `compute_integrity_manifest(directory: Path) -> dict` — walks directory, computes SHA-256 + size for each file
  - `verify_integrity_manifest(directory: Path, manifest: dict) -> list[str]` — returns list of mismatched files (empty = pass)
  - Manifest format: `{"version": 1, "files": {"path/to/file": {"sha256": "abc...", "size": 1234}, ...}}`

## Files to Modify
- `src/kinnoo/pack_command.py` (~500 lines) — After archiving all files into the `.kno` zip, call `compute_integrity_manifest()` on the archive contents and add `META-INF/integrity.json` as the final entry. The META-INF/ directory itself should be excluded from the manifest.

## Implementation Notes
- `META-INF/integrity.json` must be the **last** file added to the archive so it covers all other files
- Use `hashlib.sha256` for hashing — no external dependencies
- Manifest should be pretty-printed JSON (indent=2) for human readability in `kinnoo inspect`
- Exclude `META-INF/` directory from the manifest hash list (integrity.json cannot hash itself)
- File paths in the manifest should use forward slashes (POSIX-style) regardless of OS

## Testing
- Test `compute_integrity_manifest()` against a known directory
- Test `verify_integrity_manifest()` with matching and mismatched files
- Test that `kinnoo pack` produces a `.kno` containing `META-INF/integrity.json`
- Test that the manifest contains correct hashes for all archived files
- Existing pack tests must continue to pass

## Dependencies
- None — this is the first feature in Phase 8

## Acceptance Criteria Summary
1. `kinnoo pack` produces `META-INF/integrity.json` inside the `.kno`
2. Manifest contains SHA-256 + size for every file (excluding META-INF/)
3. `compute_integrity_manifest()` and `verify_integrity_manifest()` are public API
4. Existing tests pass
