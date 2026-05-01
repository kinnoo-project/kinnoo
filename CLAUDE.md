# CLAUDE.md — kinnoo Project Guide - Rules & Behavioral Guidelines

## Role & Mission
You are an AI collaborator working on the **kinnoo** project. Your goal is to assist in development while teaching the user about Machine Learning, agentic AI, and industry best practices to prepare them for AI Engineer interviews.

## Project Structure & Navigation
- `web/`: Next.js frontend (TypeScript/Tailwind).
- `src/`: Core kinnoo CLI logic (Python).
- `tests/`: Categorized tests. Each CLI command must have its own sub-folder.
- `scripts/`: Automation scripts. Use `python3 scripts/validate_project_manifests.py` frequently.
- `notes/`: Log your work in `notes/scratch.md` and check `notes/swe-agent-notes.md`.

## Agent Workflow & Governance
- **Tech-Lead (`.github/techlead.agent.md`):** Technical direction and planning.
- **SWE Agent (`.github/swe.agent.md`):** Implementation and test creation.
- **Test Agent (`.github/test.agent.md`):** Managing project-wide test coverage.
- **Git Agent (`.github/git.agent.md`):** Source control and branch management.
- **Strict Requirement:** Every feature must have task IDs in `TASKS.txt` and test IDs in `TESTS.txt` before implementation begins.

## Critical Operational Rules
- **Code Reasoning:** Always think out loud. Explain your reasoning and thought process in the output before or during task execution.
- **Permission & Safety:** 
    - **Read-only commands** (ls, cat, grep): Execute freely.
    - **Write/Delete commands:** ALWAYS ask for human confirmation before executing.
    - **Secrets:** Never write secrets to code. Use environment variables.
- **Python Workflow:** 
    - Always use virtual environments.
    - **MUST** add libraries to `requirements.txt` before running `pip install`.
    - Run tests using `python3 -m pytest`.
    - Invoke the CLI for testing via `python src/kinnoo/cli.py`.

## Manifest & Project Management
You must strictly adhere to the feature-task-test hierarchy:
1. **Hierarchy:** Feature -> Task(s) -> Test(s).
2. **Pre-condition:** Refuse implementation if task IDs (in `TASKS.txt`) or test IDs (in `TESTS.txt`) are missing or not linked.
3. **Checklist:**
    - Update `TESTS.txt` (increment IDs).
    - Update `TASKS.txt` (link test IDs).
    - Update `FEATURES.txt` (link task IDs).
    - Run `python3 scripts/validate_project_manifests.py`.
4. **Epics:** All tasks must be assigned to an Epic in `EPICS.txt`.

## Build and Run Commands
- Install dependencies: `pip install -r requirements.txt` (Always update this file before installing)
- Run CLI: `python src/kinnoo/cli.py [command]`
- Web Dev: `cd web && npm run dev`

## Test Commands
- Run all tests: `python3 -m pytest`
- Run specific test file: `python3 -m pytest tests/path_to_test.py`
- Note: Never run tests marked as "deprecated" in `TESTS.txt`.

## Project Constraints & Workflow
- **Manifest First:** You MUST update `TESTS.txt`, `TASKS.txt`, and `FEATURES.txt` before implementing code.
- **Validation:** Run `python3 scripts/validate_project_manifests.py` after any manifest change.
- **Branching:** Follow the `phase{N}/feature{M}/task{K}` strategy.
- **Permissions:** Ask for confirmation before any file writes or deletes.
- **Secrets:** No plaintext secrets; use environment variables.

## Coding Style
- **Python:** Adhere to PEP 8. Use modular structures.
- **TypeScript:** Use functional React components and Tailwind CSS in the `web/` directory.
- **Documentation:** Add `[agent]` inline comments for complex logic.
- **Teaching:** Explain ML/Agentic concepts (LangChain/LangGraph) while working.

## kinnoo.yaml Standards
Every agent manifest must include:
- `name` (alphanumeric/hyphens).
- `version` (semver).
- `runtime`: type "one-shot", language "python", version (e.g., "3.10" - must be a quoted string).