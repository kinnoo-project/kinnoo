# Feature 19 SWE Handoff - Go Agent Support

## Goal
Implement Go language support across init, manifest validation, run, and preflight in five ordered tasks: task173 -> task174 -> task175 -> task176 -> task177.

## Scope Boundaries
- Only implement behavior linked to feature19 AC1-AC12.
- Keep Python behavior unchanged unless required for Go support parity.
- Do not weaken existing validator guarantees.

## Ordered Tasks
1. task173: Go init scaffolding and framework matrix templates.
2. task174: manifest/schema validator support for runtime.language go.
3. task175: go source execution and preflight checks.
4. task176: precompiled Go binary execution and compatibility preflight.
5. task177: docs/help/UX updates and troubleshooting guidance.

## Key Design Constraints
- Default Go entrypoint is main.go for generated source agents.
- Preserve stdout/stderr streaming and exit code semantics in run.
- Preflight diagnostics must clearly report pass/warn/fail and remediation.
- Binary compatibility checks should use executable headers when feasible.
- Keep acceptance criteria traceable to tests test79-test83.

## Review Expectations
For each task:
- Update task status to in-progress before implementation.
- Implement code + associated tests.
- Run only relevant regression tests for the task.
- Update task status to needs-review once green.
- Add concise teaching notes to notes/tasks/taskXXX-notes.md.
