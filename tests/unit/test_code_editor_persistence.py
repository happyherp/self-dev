#!/usr/bin/env python
"""Tests for CodeEditor persistent temporary directory functionality."""

from unittest.mock import Mock, patch

import pytest

from sip.code_editor import CodeEditor
from sip.models import ChangeSet, FileContent, Repo
from sip.test_runner import SipTestResult


class TestCodeEditorPersistence:
    """Test CodeEditor persistent temporary directory functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_test_runner = Mock()
        self.code_editor = CodeEditor(llm_client=self.mock_llm, test_runner=self.mock_test_runner, max_retry_attempts=2)

    def teardown_method(self):
        """Clean up after each test."""
        # Ensure cleanup happens
        self.code_editor._cleanup_temp_dir()

    def test_temp_dir_initialization(self):
        """Test that temporary directory is properly initialized."""
        repo = Repo(
            name="test-repo",
            files={
                "main.py": "def main():\n    print('hello')\n",
                "utils.py": "def helper():\n    return True\n",
                "subdir/module.py": "class TestClass:\n    pass\n",
            },
        )

        # Initialize temp directory
        self.code_editor._initialize_temp_dir(repo)

        # Verify state
        assert self.code_editor._temp_dir is not None
        assert self.code_editor._temp_dir.exists()
        assert self.code_editor._is_temp_dir_initialized is True
        assert self.code_editor._current_repo_name == "test-repo"
        assert len(self.code_editor._current_repo_state) == 3

        # Verify files exist on filesystem
        main_file = self.code_editor._temp_dir / "main.py"
        utils_file = self.code_editor._temp_dir / "utils.py"
        module_file = self.code_editor._temp_dir / "subdir" / "module.py"

        assert main_file.exists()
        assert utils_file.exists()
        assert module_file.exists()

        # Verify file contents
        assert main_file.read_text() == "def main():\n    print('hello')\n"
        assert utils_file.read_text() == "def helper():\n    return True\n"
        assert module_file.read_text() == "class TestClass:\n    pass\n"

    def test_temp_dir_cleanup(self):
        """Test that temporary directory is properly cleaned up."""
        repo = Repo(name="test-repo", files={"test.py": "# test"})

        # Initialize and get temp dir path
        self.code_editor._initialize_temp_dir(repo)
        temp_dir_path = self.code_editor._temp_dir

        assert temp_dir_path.exists()

        # Cleanup
        self.code_editor._cleanup_temp_dir()

        # Verify cleanup
        assert not temp_dir_path.exists()
        assert self.code_editor._temp_dir is None
        assert self.code_editor._is_temp_dir_initialized is False
        assert self.code_editor._current_repo_state == {}
        assert self.code_editor._current_repo_name == ""

    def test_ensure_temp_dir_ready_first_time(self):
        """Test ensuring temp directory is ready when not initialized."""
        repo = Repo(name="test-repo", files={"main.py": "print('hello')"})

        # Should initialize on first call
        self.code_editor._ensure_temp_dir_ready(repo)

        assert self.code_editor._temp_dir is not None
        assert self.code_editor._temp_dir.exists()
        assert self.code_editor._is_temp_dir_initialized is True

        # Verify file exists
        main_file = self.code_editor._temp_dir / "main.py"
        assert main_file.exists()
        assert main_file.read_text() == "print('hello')"

    def test_ensure_temp_dir_ready_different_repo(self):
        """Test ensuring temp directory is ready when switching repositories."""
        repo1 = Repo(name="repo1", files={"file1.py": "# repo1"})
        repo2 = Repo(name="repo2", files={"file2.py": "# repo2"})

        # Initialize with first repo
        self.code_editor._ensure_temp_dir_ready(repo1)
        first_temp_dir = self.code_editor._temp_dir

        # Switch to second repo
        self.code_editor._ensure_temp_dir_ready(repo2)
        second_temp_dir = self.code_editor._temp_dir

        # Should have created new temp directory
        assert second_temp_dir != first_temp_dir
        assert not first_temp_dir.exists()  # Old one should be cleaned up
        assert second_temp_dir.exists()

        # Verify correct files exist
        assert not (second_temp_dir / "file1.py").exists()
        assert (second_temp_dir / "file2.py").exists()
        assert (second_temp_dir / "file2.py").read_text() == "# repo2"

    def test_sync_repo_changes_new_files(self):
        """Test synchronizing new files to temp directory."""
        initial_repo = Repo(name="test-repo", files={"main.py": "print('hello')"})
        updated_repo = Repo(
            name="test-repo",
            files={
                "main.py": "print('hello')",
                "new_file.py": "def new_function():\n    pass\n",
                "subdir/another.py": "# another file",
            },
        )

        # Initialize with initial repo
        self.code_editor._initialize_temp_dir(initial_repo)
        temp_dir = self.code_editor._temp_dir

        # Sync changes
        self.code_editor._sync_repo_changes(updated_repo)

        # Verify new files exist
        assert (temp_dir / "main.py").exists()
        assert (temp_dir / "new_file.py").exists()
        assert (temp_dir / "subdir" / "another.py").exists()

        # Verify content
        assert (temp_dir / "new_file.py").read_text() == "def new_function():\n    pass\n"
        assert (temp_dir / "subdir" / "another.py").read_text() == "# another file"

    def test_sync_repo_changes_modified_files(self):
        """Test synchronizing modified files to temp directory."""
        initial_repo = Repo(
            name="test-repo", files={"main.py": "print('hello')", "utils.py": "def helper(): return False"}
        )
        updated_repo = Repo(
            name="test-repo",
            files={
                "main.py": "print('hello world')",  # Modified
                "utils.py": "def helper(): return True",  # Modified
            },
        )

        # Initialize with initial repo
        self.code_editor._initialize_temp_dir(initial_repo)
        temp_dir = self.code_editor._temp_dir

        # Verify initial content
        assert (temp_dir / "main.py").read_text() == "print('hello')"
        assert (temp_dir / "utils.py").read_text() == "def helper(): return False"

        # Sync changes
        self.code_editor._sync_repo_changes(updated_repo)

        # Verify updated content
        assert (temp_dir / "main.py").read_text() == "print('hello world')"
        assert (temp_dir / "utils.py").read_text() == "def helper(): return True"

    def test_sync_repo_changes_deleted_files(self):
        """Test synchronizing deleted files from temp directory."""
        initial_repo = Repo(
            name="test-repo",
            files={
                "main.py": "print('hello')",
                "to_delete.py": "# will be deleted",
                "subdir/also_delete.py": "# also deleted",
            },
        )
        updated_repo = Repo(
            name="test-repo",
            files={"main.py": "print('hello')"},  # Other files removed
        )

        # Initialize with initial repo
        self.code_editor._initialize_temp_dir(initial_repo)
        temp_dir = self.code_editor._temp_dir

        # Verify initial files exist
        assert (temp_dir / "main.py").exists()
        assert (temp_dir / "to_delete.py").exists()
        assert (temp_dir / "subdir" / "also_delete.py").exists()

        # Sync changes
        self.code_editor._sync_repo_changes(updated_repo)

        # Verify deleted files are gone
        assert (temp_dir / "main.py").exists()
        assert not (temp_dir / "to_delete.py").exists()
        assert not (temp_dir / "subdir" / "also_delete.py").exists()

    def test_update_temp_dir_with_changeset(self):
        """Test applying changeset to temp directory."""
        repo = Repo(
            name="test-repo",
            files={"main.py": "def main():\n    print('hello')\n", "utils.py": "def helper():\n    return False\n"},
        )

        changeset = ChangeSet(
            summary="Update functions",
            description="Update main and helper functions",
            files=[
                FileContent(path="main.py", content="def main():\n    print('hello world')\n"),
                FileContent(path="utils.py", content="def helper():\n    return True\n"),
                FileContent(path="new_module.py", content="class NewClass:\n    pass\n", exists=False),
            ],
        )

        # Initialize temp directory
        self.code_editor._initialize_temp_dir(repo)
        temp_dir = self.code_editor._temp_dir

        # Apply changeset
        self.code_editor._update_temp_dir(changeset)

        # Verify changes applied
        assert (temp_dir / "main.py").read_text() == "def main():\n    print('hello world')\n"
        assert (temp_dir / "utils.py").read_text() == "def helper():\n    return True\n"
        assert (temp_dir / "new_module.py").read_text() == "class NewClass:\n    pass\n"

    def test_update_temp_dir_no_unnecessary_writes(self):
        """Test that update_temp_dir only writes files that actually changed."""
        repo = Repo(name="test-repo", files={"unchanged.py": "# unchanged content"})

        changeset = ChangeSet(
            summary="No real changes",
            description="File content is the same",
            files=[
                FileContent(path="unchanged.py", content="# unchanged content")  # Same content
            ],
        )

        # Initialize temp directory
        self.code_editor._initialize_temp_dir(repo)
        temp_dir = self.code_editor._temp_dir
        unchanged_file = temp_dir / "unchanged.py"

        # Get initial modification time
        initial_mtime = unchanged_file.stat().st_mtime

        # Apply changeset (should not write since content is same)
        self.code_editor._update_temp_dir(changeset)

        # Verify file was not rewritten (modification time unchanged)
        final_mtime = unchanged_file.stat().st_mtime
        assert final_mtime == initial_mtime

    def test_test_changes_in_temp_repo_integration(self):
        """Test the full integration of testing changes in persistent temp repo."""
        repo = Repo(
            name="test-repo",
            files={
                "main.py": "def main():\n    return 'hello'\n",
                "test_main.py": "from main import main\n\ndef test_main():\n    assert main() == 'hello'\n",
            },
        )

        changeset = ChangeSet(
            summary="Update main function",
            description="Change return value",
            files=[FileContent(path="main.py", content="def main():\n    return 'hello world'\n")],
        )

        # Mock successful test result
        mock_test_result = SipTestResult(success=True, output="All tests passed", error_output="", return_code=0)
        self.mock_test_runner.run_tests.return_value = mock_test_result

        # Test the changes
        result = self.code_editor._test_changes_in_temp_repo(repo, changeset)

        # Verify test was called with correct directory
        assert self.mock_test_runner.run_tests.called
        call_args = self.mock_test_runner.run_tests.call_args
        assert call_args[1]["cwd"] == str(self.code_editor._temp_dir)

        # Verify result
        assert result.success is True
        assert result.output == "All tests passed"

        # Verify temp directory contains updated files
        temp_dir = self.code_editor._temp_dir
        assert (temp_dir / "main.py").read_text() == "def main():\n    return 'hello world'\n"
        assert (temp_dir / "test_main.py").exists()

    def test_multiple_test_runs_reuse_directory(self):
        """Test that multiple test runs reuse the same temporary directory."""
        repo = Repo(name="test-repo", files={"main.py": "def main(): pass"})

        changeset1 = ChangeSet(
            summary="First change",
            description="First change",
            files=[FileContent(path="main.py", content="def main(): return 1")],
        )

        changeset2 = ChangeSet(
            summary="Second change",
            description="Second change",
            files=[FileContent(path="main.py", content="def main(): return 2")],
        )

        # Mock successful test results
        mock_test_result = SipTestResult(success=True, output="OK", error_output="", return_code=0)
        self.mock_test_runner.run_tests.return_value = mock_test_result

        # First test run
        self.code_editor._test_changes_in_temp_repo(repo, changeset1)
        first_temp_dir = self.code_editor._temp_dir

        # Second test run
        self.code_editor._test_changes_in_temp_repo(repo, changeset2)
        second_temp_dir = self.code_editor._temp_dir

        # Should reuse the same directory
        assert first_temp_dir == second_temp_dir
        assert first_temp_dir.exists()

        # Verify final content is from second changeset
        assert (second_temp_dir / "main.py").read_text() == "def main(): return 2"

        # Verify test runner was called twice with same directory
        assert self.mock_test_runner.run_tests.call_count == 2
        for call in self.mock_test_runner.run_tests.call_args_list:
            assert call[1]["cwd"] == str(first_temp_dir)

    def test_temp_dir_survives_failed_tests(self):
        """Test that temp directory persists even when tests fail."""
        repo = Repo(name="test-repo", files={"main.py": "def main(): pass"})

        changeset = ChangeSet(
            summary="Failing change",
            description="This will fail tests",
            files=[FileContent(path="main.py", content="def main(): raise Exception('fail')")],
        )

        # Mock failed test result
        mock_test_result = SipTestResult(success=False, output="", error_output="Test failed", return_code=1)
        self.mock_test_runner.run_tests.return_value = mock_test_result

        # Test the changes (should not raise exception)
        result = self.code_editor._test_changes_in_temp_repo(repo, changeset)

        # Verify test failed but temp directory still exists
        assert result.success is False
        assert self.code_editor._temp_dir is not None
        assert self.code_editor._temp_dir.exists()

        # Verify file was still updated
        assert (self.code_editor._temp_dir / "main.py").read_text() == "def main(): raise Exception('fail')"

    def test_destructor_cleanup(self):
        """Test that __del__ properly cleans up temp directory."""
        repo = Repo(name="test-repo", files={"test.py": "# test"})

        # Initialize temp directory
        self.code_editor._initialize_temp_dir(repo)
        temp_dir_path = self.code_editor._temp_dir

        assert temp_dir_path.exists()

        # Simulate destructor call
        self.code_editor.__del__()

        # Verify cleanup
        assert not temp_dir_path.exists()

    def test_error_handling_in_initialization(self):
        """Test error handling during temp directory initialization."""
        repo = Repo(name="test-repo", files={"test.py": "# test"})

        # Mock tempfile.mkdtemp to raise an exception
        with pytest.raises(OSError):
            with patch("tempfile.mkdtemp", side_effect=OSError("Permission denied")):
                self.code_editor._initialize_temp_dir(repo)

        # Verify state is clean after failed initialization
        assert self.code_editor._temp_dir is None
        assert self.code_editor._is_temp_dir_initialized is False
        assert self.code_editor._current_repo_state == {}

    def test_temp_dir_prefix(self):
        """Test that temp directory uses correct prefix."""
        repo = Repo(name="test-repo", files={"test.py": "# test"})

        self.code_editor._initialize_temp_dir(repo)

        # Verify temp directory name has correct prefix
        assert self.code_editor._temp_dir.name.startswith("sip_code_editor_")

    def test_concurrent_editor_instances(self):
        """Test that multiple CodeEditor instances have separate temp directories."""
        repo = Repo(name="test-repo", files={"test.py": "# test"})

        # Create second editor instance
        mock_llm2 = Mock()
        mock_test_runner2 = Mock()
        code_editor2 = CodeEditor(llm_client=mock_llm2, test_runner=mock_test_runner2)

        try:
            # Initialize both editors
            self.code_editor._initialize_temp_dir(repo)
            code_editor2._initialize_temp_dir(repo)

            # Verify they have different temp directories
            assert self.code_editor._temp_dir != code_editor2._temp_dir
            assert self.code_editor._temp_dir.exists()
            assert code_editor2._temp_dir.exists()

            # Verify both directories contain the same files but are separate
            assert (self.code_editor._temp_dir / "test.py").exists()
            assert (code_editor2._temp_dir / "test.py").exists()

        finally:
            # Clean up second editor
            code_editor2._cleanup_temp_dir()
