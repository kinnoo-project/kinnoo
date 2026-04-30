# Task 384 Notes - Add Ed25519 signing to .kno archives via --sign flag

## What was implemented
- Updated src/kinnoo/pack_command.py so `kinnoo pack --sign --signing-key <pem>` now embeds META-INF/signature.json in the archive.
- Signature is generated over the exact raw bytes of META-INF/integrity.json.
- Embedded signature payload includes:
  - version
  - algorithm (ed25519)
  - signature (base64)
  - public_key_fingerprint
  - signed_at (UTC ISO-8601)
- Existing detached signature artifact behavior remains intact for compatibility.

## Why this design
- Signing integrity.json instead of the whole archive avoids circularity and aligns with a layered trust model:
  - integrity.json attests file-level content
  - signature.json attests integrity.json authenticity

## Targeted tests added/run
- Added tests/test_feature_87.py::test_feature87_group1.
- Command: python3 -m pytest tests/test_feature_87.py -k test_feature87_group1 --testmon
- Result: 1 passed, 1 deselected

## Teaching notes
- In cryptographic packaging, keep signed payloads deterministic (stable ordering and formatting) to prevent verification drift.
- Fingerprints are identity hints, not proof by themselves; cryptographic verification must still check signature validity over payload bytes.
