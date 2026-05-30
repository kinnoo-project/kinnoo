# Feature 20 SWE Handoff - Refactor kinnoo init for Git-Repo Compatibility

## Goal
Refactor `kinnoo init` so it works seamlessly inside an existing git repository, following the standard developer flow of: (1) create/clone repo, (2) run `kinnoo init` to scaffold agent code inside.

## Scope Boundaries
- Only modify init scaffolding behavior; do not change `kinnoo run`, `kinnoo pack`, or other commands.
- Keep all existing framework/language combinations working.
- OpenClaw framework may need special handling due to its unique directory structure.
- Do NOT break backward compatibility for the case where agent-dir does not yet exist.

## Ordered Tasks
1. task178: Allow existing directory and "." target support.
2. task179: Skip .gitignore creation.
3. task180: Rename README.md to README.kinnoo.md.
4. task181: Move entrypoint to src/ subdirectory.
5. task182: Don't override existing directories.
6. task183: Intelligently merge dependency files.

## Key Design Constraints
- `init_agent()` currently raises `FileExistsError` if agent_dir exists — change to allow existing dirs.
- When agent_name is ".", resolve to current directory and init in-place (don't create a subdirectory).
- The `.gitignore` templates defined in init_command.py should remain in code (they may be useful elsewhere) but should NOT be written during init.
- README.kinnoo.md should contain the same content that was previously in README.md.
- The `src/` directory is for the entrypoint only; tool/prompt/eval/test/data dirs remain at agent root.
- The manifest `entrypoint` field must reflect the new `src/` path (e.g., `src/main.py`).
- For dependency merging: only append lines that are not already present in requirements.txt.
- For package.json merging: use JSON parse/merge for the `dependencies` object.

## Important Implementation Notes
- The `init_agent()` function in `src/kinnoo/init_command.py` is the main target.
- The CLI dispatch in `src/kinnoo/cli.py` (around line 995-1070) handles arg parsing.
- The NAME_PATTERN regex validation in cli.py may need updating to accept "." as valid.
- Go scaffolding uses subprocess calls to `go mod init` — the cwd should still be agent_dir.
- For Go, `main.go` should move to `src/main.go` but `go.mod` stays at agent root.
- Tests are in `tests/client_cli_init/`.

## Review Expectations
For each task:
- Update task status to in-progress before implementation.
- Implement code + associated tests.
- Run `python3 -m pytest tests --testmon` for validation.
- Update task status to needs-review once green.
- Add concise teaching notes to notes/tasks/taskXXX-notes.md.
