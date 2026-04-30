# Task 382 Notes - Create integrity.py module and embed SHA-256 manifest in .kno archives

## What was implemented
- Added integrity API module at <redacted-path>
- Implemented compute_integrity_manifest(directory) -> dict:
  - Recursively scans files.
  - Excludes META-INF/ entries.
  - Records sha256 and size for each file using POSIX-style relative paths.
- Implemented verify_integrity_manifest(directory, manifest) -> list[str]:
  - Validates manifest structure.
  - Detects missing files, size mismatches, hash mismatches, and extra files not listed.
- Updated pack flow in <redacted-path>
  - Computes an archive-level integrity manifest after all content entries are written.
  - Appends META-INF/integrity.json as the final archive entry.

## Why this design
- Appending integrity.json last avoids self-referential hashing and guarantees all non-META-INF archive entries are covered.
- Hashing archive entry payloads directly avoids drift between source directory shape and packaged archive shape.

## Targeted tests added/run
- Added tests/test_feature_86.py::test_feature86_group1.
- Test coverage includes:
  - kinnoo pack emits META-INF/integrity.json.
  - Manifest includes core archive entries and excludes META-INF/*.
  - Public integrity API recomputes and verifies the extracted archive cleanly.

## Teaching notes
- Integrity manifests are a practical way to detect tampering: SHA-256 gives collision-resistant file fingerprints suitable for distribution integrity checks.
- A useful packaging pattern is:
  1) write payload files,
  2) compute integrity over immutable payload set,
  3) write metadata as final artifact.
- Returning a list of mismatches (instead of bool) improves operator debuggability and supports richer diagnostics later.
