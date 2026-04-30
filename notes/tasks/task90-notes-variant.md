# Task117 Notes - RegexInputGuard pattern library

## Scope implemented
- Replaced the task89 placeholder guard with a full regex-based `RegexInputGuard` implementation.
- Added comprehensive threat pattern coverage across six categories:
  - SQL injection
  - shell injection
  - path traversal
  - SSRF
  - XSS
  - template injection
- Added type-aware filtering by `input_type` (`text`, `string`, `file_path`, `url`, `id`) with unknown types defaulting to full scan.
- Implemented multi-input aggregation via `check_inputs(...)` with per-warning `param_name` attribution.

## Implementation details
- Updated `<redacted-path>` to add:
  - `PATTERNS: dict[str, list[tuple[str, str]]]` mapping categories to `(regex, human description)` tuples.
  - `TYPE_FILTER` mapping input types to applicable categories.
  - `RegexInputGuard.check(...)`:
    - applies `re.IGNORECASE`
    - scans only applicable categories for the input type
    - returns one warning per category (break on first match to avoid warning floods)
  - `RegexInputGuard.check_inputs(...)`:
    - checks each `(param_name, value, input_type)` tuple
    - aggregates warnings and stamps each warning with the originating `param_name`

## Tests implemented (task90)
- Added these tests in `tests/test_input_guard.py`:
  - `test_sql_injection_patterns_detected` (test151)
  - `test_shell_injection_patterns_detected` (test152)
  - `test_path_traversal_patterns_detected` (test153)
  - `test_ssrf_patterns_detected` (test154)
  - `test_xss_patterns_detected` (test155)
  - `test_template_injection_patterns_detected` (test156)
  - `test_safe_inputs_pass_clean` (test157)
  - `test_type_aware_filtering` (test158)
  - `test_check_inputs_multi_value_aggregation` (test159)

## Validation results
- `python3 -m pytest tests/test_input_guard.py -q` -> `11 passed`
- `python3 -m pytest -q` -> `151 passed, 1 skipped`

## Design choices and rationale
- Pattern matching is intentionally category-oriented rather than payload-oriented:
  - this keeps output readable and actionable for users (`[CATEGORY] description`),
  - and prevents duplicate/noisy warnings for one malicious input.
- Type-aware filtering helps reduce false positives in future parameterized input mode.
  - Example: SQL patterns are intentionally skipped for `file_path` checks.
- Guard remains pluggable through the existing Protocol/factory contract from task89.

## Teaching notes
- Regex guards are best treated as a high-recall baseline layer, not a perfect classifier. In real systems, combine them with contextual policy checks and allowlist validation for defense-in-depth.
- Type-aware scanning is an important practical anti-false-positive technique: narrowing hypothesis space by data type often improves both precision and usability.
- The current `Protocol + factory` shape is the right seam for incremental ML adoption:
  - V1 (current): deterministic regex heuristics for explainability and control.
  - V2+: replace factory output with an ML scoring guard (or hybrid guard) while preserving the same `InputGuardResult` contract for CLI integration.
