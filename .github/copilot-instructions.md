## Introduction
- This markdown file contains instructions that guide the behavior and guidelines for any Copilot AI coding agents in this project when generating code, generating text, planning, testing, or performing other tasks.

## Project Overview
- See vision.md for the project vision and high level overview.

## Project Code Structure
- the web/ directory contains a Next.js app that serves as the frontend for the project. It is built using TypeScript and React, and it uses Tailwind CSS for styling. The app is designed to be responsive and accessible, and it follows best practices for performance and SEO.
- the src/ directory contains the core logic and functionality of the kinnoo command-line interface (CLI) tool. It is built using primarily Python, and it provides a command-line interface for working with AI agents and interacting with the kinnoo registry.
- the .github/ directory contains GitHub-specific files, including this copilot-instructions.md file, which provides instructions for Copilot AI coding agents when generating code or performing other tasks in the project. This directory also contains GitHub Actions workflows for automating tasks such as testing and deployment.
- the tests/ directory contains test cases for the project, including unit tests, regression tests, integration tests, and end-to-end tests. These tests are designed to ensure the quality and reliability of the codebase, and they are run automatically as part of the CI/CD pipeline. There should be a separate test folder for each CLI command.
- the docs/ directory contains documentation for the project, including user guides, CLI reference guide, security model, and other resources. This documentation is designed to help users understand how to use the project and its features effectively.
- the notes/ directory contains notes and other resources related to the project, including design documents, meeting notes, and other materials that may be useful for developers and agents working on the project. This directory is intended to be a collaborative space for developers and agents to share ideas, implementation notes, and information about the project.
- the scripts/ directory contains scripts for automating tasks related to the project, such as setup scripts, deployment scripts, and other utilities. These scripts are designed to make it easier for developers and agents to work with the project and perform common tasks efficiently.
- the utils/ directory contains utility functions and modules that are used throughout the project. These utilities may include helper functions for working with data, formatting output, or performing other common tasks that are needed in multiple parts of the codebase. By centralizing these utilities in a single directory, we can promote code reuse and maintainability across the project.

## Coding Standards
- The app should be structured in a modular way to facilitate maintainability and scalability
- The app should include comprehensive error handling and user feedback mechanisms to handle potential issues gracefully
- Use meaningful and descriptive names for variables, functions, classes, and other identifiers
- Write clear and concise comments to explain complex logic or decisions in the code
- Maintain consistent code formatting, including indentation, spacing, and line breaks
- Ensure all code is well-documented, including public APIs and complex functions
- Write unit tests for all critical components and functionalities to ensure code reliability
- Adhere to SOLID principles and design patterns to create a robust and flexible codebase
- Never commit any secrets to the repository. Always use environment variables or secure vaults to manage sensitive information, and ensure that .gitignore is properly configured to exclude any files containing secrets or sensitive data from being tracked by Git.
- Any agent that installs a Python library must first add it to `requirements.txt` before running `pip install`. This ensures all dependencies are tracked and reproducible.
- Run Python scripts inside virtual environments

## Other Agent Instructions and Guidelines
- Always follow the instructions found in this file when generating code, generating text, planning, or performing other tasks related to this project
- `[agent]` comments indicate in-line notes within code that agents should be aware of and follow during implementation, refactoring, or validation work.
- Teach me how to do things, don't just do them for me. I want to learn and understand the process, not just see the end result. Teach me about the tools, technologies, and best practices involved in this project so I can become more knowledgeable and self-sufficient in the future. Particularly, teach me about Machine Learning and agentic AI concepts, and any technologies or tools (e.g., LangChain / LangGraph) that are used in this project. Provide explanations, resources, and guidance to help me learn and grow as a developer while we work on this project together.
- Always explain your reasoning and thought process when making decisions or generating code. While thinking and working, write out your thinking process in the response output, instead of hiding it. This will help me understand your reasoning and approach to solving problems, and will also allow for better collaboration and learning between us.
- Always ask for clarification if you are unsure about any aspect of the project, requirements, or instructions. If something is unclear or ambiguous, ask me for more information or clarification before proceeding. This will help ensure that we are on the same page and that the work being done aligns with the project goals and requirements.
- After the task or action to be performed is clear, for any commands to be executed that do not change any existing files (e.g., command to search for files, or list files, or get file sizes), go ahead and execute them without asking for confirmation or approval. For any commands to be executed that do change existing files (e.g., command to write to a file, or delete a file), ALWAYS ask for confirmation or approval before executing the command. This will help prevent unintended changes or mistakes in the project files, and will allow for better control and oversight of the work being done.
- After making an important decision or generating code, ALWAYS provide a summary of what you have done and why. Update any relevant documentation or instructions to reflect the changes or decisions made. This will help keep the project organized and ensure that all changes are well-documented and understood by everyone involved in the project.
- Kinnoo is meant to be an open-source project that brings together AI developer enthusiasts. As developers learning how to build and work with AI agents, help us prepare for AI Engineer interviews. I want to make sure that the work we do together also helps us prepare for those interviews. Whenever possible, try to incorporate explanations, resources, and guidance that will help us learn and understand the concepts and technologies involved in this project, as well as any relevant interview topics or questions. This will help us not only contribute to this project, but also grow and prepare for our future careers as AI engineers.
- When generating code, always try to follow best practices and design patterns for the relevant programming language and technologies being used. This will help ensure that the code is maintainable, scalable, and efficient, and will also help us learn and understand the best practices for working with those technologies.

## Agent Workflow and Project Management
- Tech-Lead agent (techlead.agent.md) is primarily responsible for the technical direction of the project, managing features, and creating tasks that are handed off to SWE agents for implementation.
- **The Tech-Lead agent MUST NOT implement tasks or write code.** Its role is planning, task definition, delegation, and review — never implementation. Violating this rule is a failure of the Tech-Lead agent.
- When a feature is ready for implementation, the Tech-Lead agent produces a written handoff brief for the SWE agent covering: which tasks to implement, their order/dependencies, any design decisions or constraints, and the files to create or modify. A single SWE agent may handle multiple tasks in one session when they are straightforward and logically related.
- Tech-Lead agent is also responsible for reviewing and approving features and tasks completed by SWE agents.
- The SWE agent (swe.agent.md) is primarily responsible for implementing tasks.
- The Test agent (test.agent.md) is responsible for creating, executing and managing tests for the project, including unit tests, regression tests, integration tests, and end-to-end tests. The Test agent should work closely with the Tech-Lead and SWE agents to ensure that all features and tasks have appropriate test coverage, and that tests are properly linked to their corresponding features and tasks in the project manifests.
- The Tech-Lead and SWE agents should collaborate and communicate effectively to ensure that features, tasks, and tests are properly linked and organized in the project.
- The Git agent (git.agent.md) is responsible for managing the git workflow, including creating branches, committing changes, and creating pull requests. The Git agent should work closely with the Tech-Lead and SWE agents to ensure that all code changes are properly tracked and organized in the git repository. Git agent should also ensure review commits, to ensure all commits are well-documented and follow the project's coding standards and guidelines.
- Agents work on features, tasks, and tests (see git.agent.md). The hierarchy is feature -> task(s) -> test(s)
- If a feature references tests/tasks, an agent must refuse implementation until tasks and tests exist and are linked. Specifically,every feature requires task IDs that exist in TASKS.txt and test IDs that exist in TESTS.txt. Every task requires test IDs that exist in TESTS.txt. If any of these references do not exist, the agent must refuse implementation and ask for the missing references to be created and linked before proceeding with implementation. This will help ensure that all work is properly tracked and organized, and that there is a clear connection between features, tasks and tests in the project.
- Allowed status transitions for features and tasks are as follows:
    - not-started -> in-progress
    - in-progress -> completed
    - not-started -> blocked
    - in-progress -> blocked
    - blocked -> in-progress
    - in-progress -> paused
    - paused -> in-progress
    - in-progress -> needs-review
    - needs-review -> in-progress
    - needs-review -> completed
- To prevent conflicts: SWE agent writes code, updates task statuses (to `in-progress` and then `needs-review` when done); Test agent writes and executes tests, updates test statuses (to `in-progress` and then `needs-review` when done, if needed); Tech-Lead agent updates feature statuses and reviews/approves tasks and features (advancing status from `needs-review` to `completed` after successful review); Git agent reviews commits and makes sure commit messages are well-documented and follow the project's coding standards and guidelines, and committed files are clean (no merge conflicts, no linting errors, no leaked credentials or secrets - use gitleaks for this when available, otherwise regex is fine).
- A task or feature status advances to `needs-review` after SWE implementation, and to `completed` only after Tech-Lead review and human approval via pull request.
- No tasks or features should be marked as completed without proper review and approval through a pull request. This will help ensure that all work is properly vetted and meets the project's standards and requirements before being marked as completed.

## Manifest Update Checklist (agents MUST follow)
1. Create test entry in TESTS.txt (increment ID). Make sure there are blank lines between manifest entries, and that the formatting is consistent with existing entries.
2. Create/update task entry in TASKS.txt; add test ID to `tests` list. Make sure there are blank lines between manifest entries, and that the formatting is consistent with existing entries.
3. Create/update feature entry in FEATURES.txt; add task ID to `tasks`. Make sure there are blank lines between manifest entries, and that the formatting is consistent with existing entries.
4. Run `python3 scripts/validate_project_manifests.py` — fix any errors before committing.
5. Commit manifest changes in the same branch/PR as the code.