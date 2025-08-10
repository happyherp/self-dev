"""
Unit tests for LocalFileProcessor.

Tests local file processing functionality including file loading,
goal processing, and change application.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from src.sip.core import ChangeSet, FileContent, Goal, Repo
from src.sip.local_file_processor import LocalFileProcessor


class TestLocalFileProcessor:
    """Test cases for LocalFileProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.processor = LocalFileProcessor(self.mock_llm)

    def test_initialization(self):
        """Test LocalFileProcessor initialization."""
        assert self.processor.code_editor is not None
        assert self.processor.logger is not None

    def test_load_goal_from_file_simple(self):
        """Test loading a simple goal from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Fix the login bug")
            goal_file = f.name

        try:
            goal = self.processor._load_goal_from_file(goal_file)

            assert isinstance(goal, Goal)
            assert goal.description == "Fix the login bug"
            assert goal.context == f"Local goal file: {goal_file}"
            assert goal.priority == "normal"
            assert "local" in goal.tags
        finally:
            os.unlink(goal_file)

    def test_load_goal_from_file_with_title_and_description(self):
        """Test loading goal with title and description separated by double newline."""
        content = "Fix Login Bug\n\nThe login function currently returns False when it should return True"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            goal_file = f.name

        try:
            goal = self.processor._load_goal_from_file(goal_file)

            assert "Fix Login Bug" in goal.description
            assert "login function" in goal.description
            assert goal.description == content
        finally:
            os.unlink(goal_file)

    def test_load_goal_from_file_not_found(self):
        """Test loading goal from non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.processor._load_goal_from_file("/nonexistent/file.txt")

    def test_load_local_repo_simple(self):
        """Test loading a simple local repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            with open(os.path.join(temp_dir, "main.py"), "w") as f:
                f.write("def main():\n    print('Hello, World!')")

            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write("# Test Project\n\nThis is a test project.")

            repo = self.processor._load_local_repo(temp_dir)

            assert isinstance(repo, Repo)
            assert repo.name == os.path.basename(temp_dir)
            assert len(repo.files) == 2
            assert "main.py" in repo.files
            assert "README.md" in repo.files
            assert "def main():" in repo.files["main.py"]
            assert "# Test Project" in repo.files["README.md"]
            assert repo.metadata["platform"] == "local"
            assert repo.metadata["repository"] == temp_dir

    def test_load_local_repo_with_subdirectories(self):
        """Test loading repository with subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory structure
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir)

            with open(os.path.join(src_dir, "app.py"), "w") as f:
                f.write("from .utils import helper")

            with open(os.path.join(temp_dir, "config.json"), "w") as f:
                f.write('{"debug": true}')

            repo = self.processor._load_local_repo(temp_dir)

            assert len(repo.files) == 2
            assert "src/app.py" in repo.files or "src\\app.py" in repo.files  # Handle Windows paths
            assert "config.json" in repo.files

    def test_load_local_repo_skips_hidden_files(self):
        """Test that hidden files and directories are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create visible file
            with open(os.path.join(temp_dir, "visible.py"), "w") as f:
                f.write("print('visible')")

            # Create hidden file
            with open(os.path.join(temp_dir, ".hidden"), "w") as f:
                f.write("hidden content")

            # Create hidden directory
            hidden_dir = os.path.join(temp_dir, ".git")
            os.makedirs(hidden_dir)
            with open(os.path.join(hidden_dir, "config"), "w") as f:
                f.write("git config")

            repo = self.processor._load_local_repo(temp_dir)

            assert len(repo.files) == 1
            assert "visible.py" in repo.files
            assert ".hidden" not in repo.files
            assert ".git/config" not in repo.files

    def test_load_local_repo_skips_build_directories(self):
        """Test that common build/cache directories are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source file
            with open(os.path.join(temp_dir, "main.py"), "w") as f:
                f.write("print('main')")

            # Create build directories
            for build_dir in ["__pycache__", "node_modules", "dist", "build"]:
                dir_path = os.path.join(temp_dir, build_dir)
                os.makedirs(dir_path)
                with open(os.path.join(dir_path, "file.txt"), "w") as f:
                    f.write("build file")

            repo = self.processor._load_local_repo(temp_dir)

            assert len(repo.files) == 1
            assert "main.py" in repo.files
            for build_dir in ["__pycache__", "node_modules", "dist", "build"]:
                assert not any(build_dir in path for path in repo.files.keys())

    @patch("filetype.guess")
    @patch("os.path.getsize")
    @patch("builtins.open")
    def test_is_text_file_with_filetype(self, mock_open, mock_getsize, mock_filetype):
        """Test text file detection using filetype library."""
        # Test text file (filetype returns None for text files)
        mock_filetype.return_value = None
        mock_getsize.return_value = 100
        mock_open.return_value.__enter__.return_value.read.return_value = b"Hello world"
        assert self.processor._is_text_file("/path/to/file.txt") is True

        # Test binary file detected by filetype
        mock_filetype.return_value = Mock(extension="jpg", mime="image/jpeg")
        assert self.processor._is_text_file("/path/to/image.jpg") is False

    @patch("filetype.guess")
    @patch("os.path.getsize")
    def test_is_text_file_empty_file(self, mock_getsize, mock_filetype):
        """Test empty file detection."""
        mock_filetype.return_value = None
        mock_getsize.return_value = 0
        assert self.processor._is_text_file("/path/to/empty.txt") is True

    @patch("filetype.guess")
    @patch("os.path.getsize")
    @patch("builtins.open")
    def test_is_text_file_binary_content(self, mock_open, mock_getsize, mock_filetype):
        """Test binary content detection."""
        mock_filetype.return_value = None
        mock_getsize.return_value = 100
        # File with null bytes (binary)
        mock_open.return_value.__enter__.return_value.read.return_value = b"Hello\x00world"
        assert self.processor._is_text_file("/path/to/unknown") is False

    @patch("filetype.guess")
    @patch("os.path.getsize")
    @patch("builtins.open")
    def test_is_text_file_unicode_decode_error(self, mock_open, mock_getsize, mock_filetype):
        """Test handling of unicode decode errors."""
        mock_filetype.return_value = None
        mock_getsize.return_value = 100
        # Mock file content that can't be decoded as UTF-8
        mock_open.return_value.__enter__.return_value.read.return_value = b"\xff\xfe\x00\x00"
        assert self.processor._is_text_file("/path/to/unknown") is False

    @patch("filetype.guess")
    def test_is_text_file_fallback_on_error(self, mock_filetype):
        """Test fallback when file operations fail."""
        mock_filetype.side_effect = OSError("File not found")
        assert self.processor._is_text_file("/path/to/nonexistent") is False

    def test_load_local_repo_handles_unreadable_files(self):
        """Test that unreadable files are skipped gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create readable file
            with open(os.path.join(temp_dir, "readable.txt"), "w") as f:
                f.write("readable content")

            # Create a file that will cause UnicodeDecodeError when read as text
            with open(os.path.join(temp_dir, "binary.bin"), "wb") as f:
                f.write(b"\x00\x01\x02\x03\xff\xfe")  # Invalid UTF-8 sequence

            # The binary file should be detected as non-text and skipped
            repo = self.processor._load_local_repo(temp_dir)

            # Should only include the readable file
            assert len(repo.files) == 1
            assert "readable.txt" in repo.files
            assert "binary.bin" not in repo.files

    def test_process_goal_file(self):
        """Test processing a goal file against a local repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create goal file
            goal_file = os.path.join(temp_dir, "goal.txt")
            with open(goal_file, "w") as f:
                f.write("Fix the main function")

            # Create repo directory
            repo_dir = os.path.join(temp_dir, "repo")
            os.makedirs(repo_dir)
            with open(os.path.join(repo_dir, "main.py"), "w") as f:
                f.write("def main():\n    return False")

            # Mock code editor
            mock_changeset = ChangeSet(
                summary="Fix main function",
                description="Changed return value to True",
                files=[FileContent(path="main.py", content="def main():\n    return True")],
            )

            with patch.object(self.processor.code_editor, "process_goal", return_value=mock_changeset):
                result = self.processor.process_goal_file(goal_file, repo_dir)

            assert isinstance(result, ChangeSet)
            assert result.summary == "Fix main function"
            assert len(result.files) == 1

    def test_apply_changeset_locally(self):
        """Test applying a changeset to local files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create changeset
            changeset = ChangeSet(
                summary="Update files",
                description="Updated main.py and added config.json",
                files=[
                    FileContent(path="main.py", content="def main():\n    print('Updated!')"),
                    FileContent(path="config/settings.json", content='{"updated": true}'),
                ],
            )

            # Apply changeset
            self.processor.apply_changeset_locally(temp_dir, changeset)

            # Verify files were created/updated
            main_path = os.path.join(temp_dir, "main.py")
            config_path = os.path.join(temp_dir, "config", "settings.json")

            assert os.path.exists(main_path)
            assert os.path.exists(config_path)

            with open(main_path) as f:
                assert "Updated!" in f.read()

            with open(config_path) as f:
                assert '"updated": true' in f.read()

    def test_apply_changeset_creates_directories(self):
        """Test that applying changeset creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            changeset = ChangeSet(
                summary="Create nested file",
                description="Create file in nested directory",
                files=[FileContent(path="deep/nested/directory/file.txt", content="nested content")],
            )

            self.processor.apply_changeset_locally(temp_dir, changeset)

            file_path = os.path.join(temp_dir, "deep", "nested", "directory", "file.txt")
            assert os.path.exists(file_path)

            with open(file_path) as f:
                assert f.read() == "nested content"

    def test_empty_repository(self):
        """Test loading an empty repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.processor._load_local_repo(temp_dir)

            assert isinstance(repo, Repo)
            assert len(repo.files) == 0
            assert repo.name == os.path.basename(temp_dir)

    def test_repository_with_only_binary_files(self):
        """Test repository containing only binary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create binary file
            with open(os.path.join(temp_dir, "image.png"), "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n")  # PNG header

            repo = self.processor._load_local_repo(temp_dir)

            # Should be empty since no text files
            assert len(repo.files) == 0

    def test_process_goal_file_integration(self):
        """Integration test for the complete goal file processing workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup goal file
            goal_file = os.path.join(temp_dir, "goal.txt")
            with open(goal_file, "w") as f:
                f.write("Add error handling to the calculator")

            # Setup repo
            repo_dir = os.path.join(temp_dir, "calculator")
            os.makedirs(repo_dir)
            with open(os.path.join(repo_dir, "calc.py"), "w") as f:
                f.write("def add(a, b):\n    return a + b")

            # Mock the code editor to return a realistic changeset
            mock_changeset = ChangeSet(
                summary="Add error handling",
                description="Added type checking and error handling to calculator functions",
                files=[
                    FileContent(
                        path="calc.py",
                        content=(
                            "def add(a, b):\n"
                            "    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n"
                            "        raise TypeError('Arguments must be numbers')\n"
                            "    return a + b"
                        ),
                    )
                ],
            )

            with patch.object(self.processor.code_editor, "process_goal", return_value=mock_changeset):
                # Process goal
                changeset = self.processor.process_goal_file(goal_file, repo_dir)

                # Apply changes
                self.processor.apply_changeset_locally(repo_dir, changeset)

                # Verify the result
                calc_path = os.path.join(repo_dir, "calc.py")
                with open(calc_path) as f:
                    content = f.read()
                    assert "TypeError" in content
                    assert "isinstance" in content
