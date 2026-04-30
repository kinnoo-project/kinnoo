# Task275 Notes - Service Dependency Auto-Detection

## What was implemented
- Updated `<redacted-path>`:
  - Added import-based service inference for common dependencies:
    - `ollama` -> `name: ollama`, `type: api`, default endpoint `<redacted-url>`
    - `chromadb` -> `name: chromadb`, `type: vector-db`, default endpoint `<redacted-url>`
    - `pinecone` -> `name: pinecone`, `type: vector-db`
    - `redis` -> `name: redis`, `type: redis`, default endpoint `redis://<redacted-host-port>`
    - `psycopg2`/`asyncpg`/`sqlalchemy` -> `name: postgresql`, `type: postgres`, default endpoint `postgresql://<redacted-host-port>`
    - `pymongo` -> `name: mongodb`, `type: mongodb`, default endpoint `mongodb://<redacted-host-port>`
  - Extended literal endpoint detection to include redis/postgres/mongodb URL schemes and common localhost port hints.
  - Added service name normalization from endpoint signals (for example, `<redacted-host-port>` -> `ollama`).
  - Merged import-derived and literal-derived services deterministically.
- Updated `<redacted-path>`:
  - Expanded service type alias normalization for postgres/mongodb variants.
  - Preserved analyzer-provided service names in generated manifest service entries.

## Tests added
- `tests/test_validator.py::test_analyzer_service_detection` (test396)
- `tests/test_cli_install.py::test_import_service_detection_yaml` (test397)

## Targeted regression run
Command:
```bash
python3 -m pytest tests --testmon -k "test_analyzer_service_detection or test_import_service_detection_yaml"
```
Result:
```text
2 passed, 384 deselected
```

## Manifest validation
Command:
```bash
python3 <redacted-path>
```
Result:
```text
Validation passed: manifests are consistent
```

## Teaching notes
- Why both import and literal detection:
  - Import-only heuristics catch dependencies even when endpoints are configured via env vars or runtime defaults.
  - Literal endpoint parsing catches explicit service URLs even when imports are indirect.
- Why stable service naming matters:
  - Consumer tooling and humans need semantic names (`ollama`, `postgresql`) rather than generic labels (`api`).
  - Stable names reduce manifest churn and make diffs/reviews easier.
- Interview angle (AI infra tooling):
  - This is a practical static-analysis pattern: infer operational dependencies from syntax-level signals, then emit portable deployment metadata with confidence/evidence provenance.
