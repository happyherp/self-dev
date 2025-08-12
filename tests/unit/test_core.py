#!/usr/bin/env python
"""Unit tests for core.py - platform-agnostic code manipulation engine."""

from unittest.mock import Mock, patch

import pytest

from sip.core import ChangeSet, CodeEditor, CoreAnalysisResult, FileContent, Goal, Repo


class TestGoal:
    """Test Goal class."""

    def test_goal_creation(self):
        """Test Goal object creation."""
        goal = Goal(
            description="Fix bug in authentication - The login function is not working properly",
            context="Issue #123 with labels: bug, high-priority",
            priority="high",
            tags=["bug", "authentication"],
        )

        assert goal.description == "Fix bug in authentication - The login function is not working properly"
        assert goal.context == "Issue #123 with labels: bug, high-priority"
        assert goal.priority == "high"
        assert goal.tags == ["bug", "authentication"]

    def test_goal_creation_minimal(self):
        """Test Goal creation with minimal required fields."""
        goal = Goal(description="Do something")

        assert goal.description == "Do something"
        assert goal.context == ""
        assert goal.priority == "normal"
        assert goal.tags == []

    def test_goal_str_representation(self):
        """Test Goal string representation."""
        goal = Goal(description="Test description")
        str_repr = str(goal)

        assert "Test description" in str_repr


class TestRepo:
    """Test Repo class."""

    def test_repo_creation(self):
        """Test Repo object creation."""
        files = {"main.py": "print('hello')", "utils.py": "def helper(): pass"}
        metadata = {"language": "python", "framework": "none"}

        repo = Repo(name="test-repo", files=files, metadata=metadata)

        assert repo.name == "test-repo"
        assert repo.files == files
        assert repo.metadata == metadata
        assert len(repo.files) == 2

    def test_repo_creation_minimal(self):
        """Test Repo creation with minimal required fields."""
        files = {"test.py": "# test file"}
        repo = Repo(name="minimal-repo", files=files)

        assert repo.name == "minimal-repo"
        assert repo.files == files
        assert repo.metadata == {}

    def test_repo_empty_files(self):
        """Test Repo with empty files dict."""
        repo = Repo(name="empty-repo", files={})

        assert repo.name == "empty-repo"
        assert repo.files == {}
        assert repo.metadata == {}

    def test_repo_str_representation(self):
        """Test Repo string representation."""
        files = {"file1.py": "code1", "file2.py": "code2"}
        repo = Repo(name="test-repo", files=files)
        str_repr = str(repo)

        assert "test-repo" in str_repr


class TestFileContent:
    """Test FileContent class."""

    def test_file_content_creation(self):
        """Test FileContent object creation."""
        file_content = FileContent(path="main.py", content="def main(): pass", exists=True)

        assert file_content.path == "main.py"
        assert file_content.content == "def main(): pass"
        assert file_content.exists is True

    def test_file_content_creation_minimal(self):
        """Test FileContent creation with minimal required fields."""
        file_content = FileContent(path="test.py", content="# test")

        assert file_content.path == "test.py"
        assert file_content.content == "# test"
        assert file_content.exists is True  # Default value

    def test_file_content_new_file(self):
        """Test FileContent for new file."""
        file_content = FileContent(path="new_file.py", content="# new file", exists=False)

        assert file_content.path == "new_file.py"
        assert file_content.content == "# new file"
        assert file_content.exists is False


class TestChangeSet:
    """Test ChangeSet class."""

    def test_changeset_creation(self):
        """Test ChangeSet object creation."""
        files = [
            FileContent(path="main.py", content="def main(): return True"),
            FileContent(path="new.py", content="# new file", exists=False),
        ]

        changeset = ChangeSet(
            summary="Fix main function and add new file",
            description="Updated main function to return True and added new utility file",
            files=files,
            branch_name="fix-main-function",
            test_command="pytest tests/",
        )

        assert changeset.summary == "Fix main function and add new file"
        assert changeset.description == "Updated main function to return True and added new utility file"
        assert len(changeset.files) == 2
        assert changeset.files[0].path == "main.py"
        assert changeset.files[1].exists is False
        assert changeset.branch_name == "fix-main-function"
        assert changeset.test_command == "pytest tests/"

    def test_changeset_creation_minimal(self):
        """Test ChangeSet creation with minimal required fields."""
        files = [FileContent(path="test.py", content="# test")]
        changeset = ChangeSet(summary="Test change", description="Simple test change", files=files)

        assert changeset.summary == "Test change"
        assert changeset.description == "Simple test change"
        assert len(changeset.files) == 1
        assert changeset.branch_name == ""
        assert changeset.test_command is None

    def test_changeset_empty_files(self):
        """Test ChangeSet with empty files list."""
        changeset = ChangeSet(summary="No changes", description="No files changed", files=[])

        assert changeset.summary == "No changes"
        assert changeset.description == "No files changed"
        assert changeset.files == []

    def test_changeset_str_representation(self):
        """Test ChangeSet string representation."""
        files = [FileContent(path="file1.py", content="code1"), FileContent(path="file2.py", content="code2")]
        changeset = ChangeSet(summary="Test changes", description="Test description", files=files)
        str_repr = str(changeset)

        assert "Test changes" in str_repr


class TestCodeEditor:
    """Test CodeEditor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_test_runner = Mock()
        self.code_editor = CodeEditor(llm_client=self.mock_llm, test_runner=self.mock_test_runner, max_retry_attempts=2)

    def test_code_editor_initialization(self):
        """Test CodeEditor initialization."""
        assert self.code_editor.llm_client == self.mock_llm
        assert self.code_editor.test_runner == self.mock_test_runner
        assert self.code_editor.max_retry_attempts == 2

    def test_code_editor_initialization_defaults(self):
        """Test CodeEditor initialization with defaults."""
        editor = CodeEditor(llm_client=self.mock_llm)

        assert editor.llm_client == self.mock_llm
        assert editor.test_runner is not None  # Should create default SipTestRunner
        assert editor.max_retry_attempts == 3  # Default value

    def test_process_goal_success(self):
        """Test successful goal processing."""
        # Setup
        goal = Goal(description="Fix the authentication bug")
        repo = Repo(name="test-repo", files={"auth.py": "def login(): pass"})

        mock_analysis = CoreAnalysisResult(
            summary="Need to fix login function",
            problem_type="bug",
            suggested_approach="Update the login function",
            files_to_modify=["auth.py"],
            confidence=0.9,
        )

        mock_changeset = ChangeSet(
            summary="Fix login function",
            description="Updated login function to return True",
            files=[FileContent(path="auth.py", content="def login(): return True")],
        )

        # Mock internal methods
        with (
            patch.object(self.code_editor, "_analyze_goal", return_value=mock_analysis),
            patch.object(self.code_editor, "_generate_changes", return_value=mock_changeset),
            patch.object(self.code_editor, "_test_changes_in_temp_repo") as mock_test,
        ):
            # Mock test runner success
            mock_test_result = Mock()
            mock_test_result.success = True
            mock_test_result.output = "All tests passed"
            mock_test.return_value = mock_test_result

            # Execute
            result = self.code_editor.process_goal(goal, repo)

            # Verify
            assert isinstance(result, ChangeSet)
            assert len(result.files) == 1
            assert result.files[0].path == "auth.py"
            assert result.summary == "Fix login function"

    def test_process_goal_low_confidence(self):
        """Test goal processing when analysis confidence is too low."""
        # Setup
        goal = Goal(description="Unclear request")
        repo = Repo(name="test-repo", files={"test.py": "def test(): pass"})

        mock_analysis = CoreAnalysisResult(
            summary="Unclear what to do",
            problem_type="unclear",
            suggested_approach="Need more information",
            files_to_modify=[],
            confidence=0.1,  # Very low confidence
        )

        # Mock internal method
        with patch.object(self.code_editor, "_analyze_goal", return_value=mock_analysis):
            # Execute and expect exception for low confidence
            with pytest.raises(ValueError, match="Confidence too low"):
                self.code_editor.process_goal(goal, repo)
