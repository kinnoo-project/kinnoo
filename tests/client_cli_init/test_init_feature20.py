"""
Tests for feature20: Refactor kinnoo init for git-repo compatibility.
Covers task178-task183 (test84-test89).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_kinnoo_init(args, cwd=None):
    """Run kinnoo init via CLI and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "kinnoo.cli", "init"] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd
    )
    return result.returncode, result.stdout, result.stderr


class TestTask178ExistingDirAndDot:
    """test84: kinnoo init on existing directory and '.' target."""

    def test_init_succeeds_when_dir_already_exists(self, tmp_path):
        """kinnoo init should succeed even if the agent directory already exists."""
        agent_dir = tmp_path / "my-agent"
        agent_dir.mkdir()
        # Create a file to prove we don't destroy existing content
        (agent_dir / "existing-file.txt").write_text("keep me")

        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"Expected success, got stderr: {err}"
        assert "Initialized agent" in out
        # Existing file should still be there
        assert (agent_dir / "existing-file.txt").read_text() == "keep me"
        # Scaffolded files should be created
        assert (agent_dir / "kinnoo.yaml").exists()

    def test_init_dot_works_in_current_directory(self, tmp_path):
        """kinnoo init <framework> . should scaffold in the current directory."""
        code, out, err = run_kinnoo_init(["pydantic-ai", "."], cwd=str(tmp_path))
        assert code == 0, f"Expected success, got stderr: {err}"
        # Files should be in tmp_path directly, not in a subdirectory called "."
        assert (tmp_path / "kinnoo.yaml").exists()
        assert not (tmp_path / "." / "kinnoo.yaml").exists() or (tmp_path / "kinnoo.yaml").exists()

    def test_init_dot_uses_directory_name_in_manifest(self, tmp_path):
        """When using '.', the manifest name should be the directory name."""
        agent_dir = tmp_path / "my-cool-agent"
        agent_dir.mkdir()
        code, out, err = run_kinnoo_init(["pydantic-ai", "."], cwd=str(agent_dir))
        assert code == 0, f"Expected success, got stderr: {err}"
        manifest = (agent_dir / "kinnoo.yaml").read_text()
        assert "my-cool-agent" in manifest


class TestTask179NoGitignore:
    """test85: kinnoo init should NOT create .gitignore."""

    def test_no_gitignore_python(self, tmp_path):
        """Python init should not create .gitignore."""
        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        assert not (tmp_path / "my-agent" / ".gitignore").exists()

    def test_no_gitignore_go(self, tmp_path):
        """Go init should not create .gitignore (if go toolchain available)."""
        import shutil
        if not shutil.which("go"):
            pytest.skip("Go toolchain not available")
        code, out, err = run_kinnoo_init(
            ["no-framework", "--language", "go", "my-go-agent"], cwd=str(tmp_path)
        )
        if code != 0 and "Go toolchain" in err:
            pytest.skip("Go toolchain not available")
        assert code == 0, f"stderr: {err}"
        assert not (tmp_path / "my-go-agent" / ".gitignore").exists()

    def test_no_gitignore_js(self, tmp_path):
        """JS init should not create .gitignore."""
        code, out, err = run_kinnoo_init(
            ["no-framework", "--language", "javascript", "my-js-agent"], cwd=str(tmp_path)
        )
        assert code == 0, f"stderr: {err}"
        assert not (tmp_path / "my-js-agent" / ".gitignore").exists()


class TestTask180ReadmeKinnoo:
    """test86: kinnoo init creates README.kinnoo.md instead of README.md."""

    def test_readme_kinnoo_md_created(self, tmp_path):
        """Init should create README.kinnoo.md, not README.md."""
        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        agent_dir = tmp_path / "my-agent"
        assert (agent_dir / "README.kinnoo.md").exists()
        assert not (agent_dir / "README.md").exists()

    def test_readme_kinnoo_md_has_content(self, tmp_path):
        """README.kinnoo.md should have meaningful content."""
        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        content = (tmp_path / "my-agent" / "README.kinnoo.md").read_text()
        assert "kinnoo" in content.lower() or "agent" in content.lower()


class TestTask181EntrypointInSrc:
    """test87: Entrypoint files should be inside src/ subdirectory."""

    def test_python_entrypoint_in_src(self, tmp_path):
        """Python entrypoint (main.py) should be in src/."""
        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        agent_dir = tmp_path / "my-agent"
        assert (agent_dir / "src" / "main.py").exists()
        assert not (agent_dir / "main.py").exists()

    def test_js_entrypoint_in_src(self, tmp_path):
        """JS entrypoint (index.js) should be in src/."""
        code, out, err = run_kinnoo_init(
            ["no-framework", "--language", "javascript", "my-js-agent"], cwd=str(tmp_path)
        )
        assert code == 0, f"stderr: {err}"
        agent_dir = tmp_path / "my-js-agent"
        assert (agent_dir / "src" / "index.js").exists()
        assert not (agent_dir / "index.js").exists()

    def test_manifest_entrypoint_has_src_prefix(self, tmp_path):
        """kinnoo.yaml entrypoint field should reference src/ path."""
        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        manifest = (tmp_path / "my-agent" / "kinnoo.yaml").read_text()
        assert "src/main.py" in manifest


class TestTask182DontOverrideExistingDirs:
    """test88: Existing directories should not be overwritten."""

    def test_existing_tests_dir_preserved(self, tmp_path):
        """If tests/ already exists with content, it should not be modified."""
        agent_dir = tmp_path / "my-agent"
        agent_dir.mkdir()
        tests_dir = agent_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "my_test.py").write_text("# existing test")

        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        # Existing file still there
        assert (tests_dir / "my_test.py").read_text() == "# existing test"

    def test_existing_data_dir_preserved(self, tmp_path):
        """If data/ already exists with content, it should not be modified."""
        agent_dir = tmp_path / "my-agent"
        agent_dir.mkdir()
        data_dir = agent_dir / "data"
        data_dir.mkdir()
        (data_dir / "sample.csv").write_text("a,b,c")

        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        assert (data_dir / "sample.csv").read_text() == "a,b,c"


class TestTask183MergeDependencies:
    """test89: Dependencies should be merged, not overwritten."""

    def test_requirements_txt_merge(self, tmp_path):
        """Existing requirements.txt should get kinnoo deps appended, not overwritten."""
        agent_dir = tmp_path / "my-agent"
        agent_dir.mkdir()
        existing_reqs = "flask>=2.0\nrequests>=2.28\n"
        (agent_dir / "requirements.txt").write_text(existing_reqs)

        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        reqs = (agent_dir / "requirements.txt").read_text()
        # Existing deps should still be there
        assert "flask>=2.0" in reqs
        assert "requests>=2.28" in reqs
        # Kinnoo/framework deps should be added
        assert "pydantic-ai" in reqs

    def test_requirements_txt_no_duplicates(self, tmp_path):
        """If a dep already exists in requirements.txt, don't duplicate it."""
        agent_dir = tmp_path / "my-agent"
        agent_dir.mkdir()
        existing_reqs = "pydantic-ai>=0.1\nflask>=2.0\n"
        (agent_dir / "requirements.txt").write_text(existing_reqs)

        code, out, err = run_kinnoo_init(["pydantic-ai", "my-agent"], cwd=str(tmp_path))
        assert code == 0, f"stderr: {err}"
        reqs = (agent_dir / "requirements.txt").read_text()
        # Should not have duplicate pydantic-ai lines
        count = reqs.lower().count("pydantic-ai")
        assert count == 1, f"pydantic-ai appeared {count} times"

    def test_package_json_merge(self, tmp_path):
        """Existing package.json should get kinnoo deps merged, not overwritten."""
        agent_dir = tmp_path / "my-agent"
        agent_dir.mkdir()
        existing_pkg = {
            "name": "my-agent",
            "version": "1.0.0",
            "dependencies": {"express": "^4.18.0"},
        }
        (agent_dir / "package.json").write_text(json.dumps(existing_pkg, indent=2))

        code, out, err = run_kinnoo_init(
            ["no-framework", "--language", "javascript", "my-agent"], cwd=str(tmp_path)
        )
        assert code == 0, f"stderr: {err}"
        pkg = json.loads((agent_dir / "package.json").read_text())
        # Existing dep should still be there
        assert "express" in pkg.get("dependencies", {})
