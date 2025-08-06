"""
Code Editor - Core code manipulation engine.

This module contains the CodeEditor class which handles the core logic for:
1. Analyzing goals against repositories
2. Generating code changes
3. Testing changes in isolation
4. Retry logic for failed attempts

It has no knowledge of GitHub, issues, PRs, or any platform-specific concepts.
"""

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import CoreAnalysisResult
from .test_runner import SipTestResult, SipTestRunner

if TYPE_CHECKING:
    from .models import ChangeSet, Goal, Repo


class CodeEditor:
    """
    Core code manipulation engine - platform-agnostic.

    This class contains the core logic for:
    1. Analyzing goals against repositories
    2. Generating code changes
    3. Testing changes in isolation
    4. Retry logic for failed attempts

    It has no knowledge of GitHub, issues, PRs, or any platform-specific concepts.
    """

    def __init__(self, llm_client: Any, test_runner: SipTestRunner | None = None, max_retry_attempts: int = 3):
        """
        Initialize the code editor.

        Args:
            llm_client: LLM client for AI operations (must have analyze_goal and generate_solution methods)
            test_runner: Optional test runner for validating changes
            max_retry_attempts: Maximum number of retry attempts for failed solutions
        """
        self.llm_client = llm_client
        self.test_runner = test_runner or SipTestRunner()
        self.max_retry_attempts = max_retry_attempts
        self.logger = logging.getLogger(__name__)

        # Persistent temporary directory state
        self._temp_dir: Path | None = None
        self._current_repo_state: dict[str, str] = {}
        self._is_temp_dir_initialized: bool = False
        self._current_repo_name: str = ""

    def process_goal(self, goal: "Goal", repo: "Repo") -> "ChangeSet":
        """
        Process a goal against a repository to generate changes.

        This is the main entry point for the core engine. It:
        1. Analyzes the goal against the repository
        2. Generates changes with retry logic
        3. Tests changes if test runner is available
        4. Returns a complete changeset

        Args:
            goal: What needs to be accomplished
            repo: Repository to work with

        Returns:
            ChangeSet with all necessary changes

        Raises:
            Exception: If unable to generate a valid solution after all retries
        """
        self.logger.info(f"Processing goal: {goal.description[:100]}...")

        # 1. Analyze the goal against the repository
        analysis = self._analyze_goal(goal, repo)
        self.logger.info(f"Analysis complete. Confidence: {analysis.confidence}")

        # 2. Skip if confidence is too low
        if analysis.confidence < 0.3:
            raise ValueError(f"Confidence too low: {analysis.confidence}")

        # 3. Generate solution with retry logic
        changeset = None
        previous_attempt = None
        last_error = None

        for attempt in range(self.max_retry_attempts):
            self.logger.info(f"Generating solution (attempt {attempt + 1}/{self.max_retry_attempts})...")

            try:
                # Generate the changes
                changeset = self._generate_changes(goal, repo, analysis, previous_attempt, last_error)

                if not changeset or not changeset.files:
                    raise ValueError("No changes generated")

                # Test the solution if test runner is available
                if self.test_runner:
                    test_result = self._test_changes_in_temp_repo(repo, changeset)

                    if test_result.success:
                        self.logger.info("✅ Tests passed! Solution validated.")
                        break
                    else:
                        # Test failure - prepare for retry
                        error_msg = f"Tests failed: {self.test_runner.format_test_failure(test_result)}"
                        raise TestFailureError(error_msg)
                else:
                    # No testing - accept the solution
                    self.logger.info("No test runner configured, accepting solution without testing.")
                    break

            except Exception as e:
                self.logger.warning(f"❌ Attempt {attempt + 1} failed: {str(e)}")

                # Prepare context for next attempt
                if changeset:
                    previous_attempt = self._format_attempt_for_retry(changeset)

                last_error = str(e)

                if attempt == self.max_retry_attempts - 1:
                    raise Exception(
                        f"Failed to generate valid solution after {self.max_retry_attempts} attempts. "
                        f"Last error: {last_error}"
                    ) from e

        if changeset is None:
            raise Exception("Failed to generate a valid solution")

        return changeset

    def _analyze_goal(self, goal: "Goal", repo: "Repo") -> CoreAnalysisResult:
        """Analyze what needs to be done to accomplish the goal."""
        # Format repository context for analysis
        repo_context = self._format_repo_context(repo)

        analysis = self.llm_client.analyze_goal(goal, repo_context)

        # Convert to core analysis result if needed
        if hasattr(analysis, "model_dump"):
            # It's a Pydantic model, convert to our core format
            return CoreAnalysisResult(**analysis.model_dump())
        else:
            # Assume it's already in the right format
            return analysis  # type: ignore[no-any-return]

    def _generate_changes(
        self,
        goal: "Goal",
        repo: "Repo",
        analysis: CoreAnalysisResult,
        previous_attempt: str | None = None,
        last_error: str | None = None,
    ) -> "ChangeSet":
        """Generate the actual code changes."""
        # Get relevant file contents
        file_contents = self._get_relevant_files(repo, analysis.files_to_modify)

        changeset = self.llm_client.generate_solution(goal, analysis, file_contents, previous_attempt, last_error)

        # Convert to core changeset if needed
        if hasattr(changeset, "model_dump"):
            # Convert from platform-specific format to core format
            changeset_data = changeset.model_dump()

            # Convert changes to FileContent objects
            files = []
            if "changes" in changeset_data:
                for change in changeset_data["changes"]:
                    from .models import FileContent

                    files.append(
                        FileContent(
                            path=change["file_path"],
                            content=change["content"],
                            exists=change.get("change_type") != "create",
                        )
                    )

            from .models import ChangeSet

            return ChangeSet(
                summary=changeset_data.get("title", "Generated changes"),
                description=changeset_data.get("body", "AI-generated solution"),
                files=files,
                branch_name=changeset_data.get("branch_name", ""),
            )
        else:
            # Assume it's already in the right format
            return changeset  # type: ignore[no-any-return]

    def _test_changes_in_temp_repo(self, repo: "Repo", changeset: "ChangeSet") -> SipTestResult:
        """Test the changes in the persistent temporary repository."""
        try:
            # Ensure temporary directory is ready and synchronized
            self._ensure_temp_dir_ready(repo)

            # Apply the changes to the persistent temporary directory
            self._update_temp_dir(changeset)

            # Run tests in the persistent temporary directory
            return self.test_runner.run_tests(cwd=str(self._temp_dir))

        except Exception as e:
            return SipTestResult(
                success=False,
                output="",
                error_output=f"Error setting up test environment: {e}",
                return_code=-1,
            )

    def _format_repo_context(self, repo: "Repo") -> str:
        """Format repository information for LLM consumption."""
        context = f"Repository: {repo.name}\n\n"

        # Add metadata if available
        if repo.metadata:
            context += "Metadata:\n"
            for key, value in repo.metadata.items():
                context += f"  {key}: {value}\n"
            context += "\n"

        # Add file structure
        context += "Files:\n"
        for file_path in sorted(repo.files.keys()):
            content_length = len(repo.files[file_path])
            context += f"  {file_path} ({content_length} chars)\n"

        return context

    def _get_relevant_files(self, repo: "Repo", file_paths: list[str]) -> dict[str, str]:
        """Get content of relevant files for the goal."""
        file_contents = {}

        for file_path in file_paths:
            if file_path in repo.files:
                content = repo.files[file_path]
                # Limit file size to prevent token overflow
                max_size = 50000  # 50KB
                if len(content) <= max_size:
                    file_contents[file_path] = content
                else:
                    # Truncate large files
                    file_contents[file_path] = content[:max_size] + "\n... (truncated)"
                    self.logger.warning(f"File {file_path} truncated due to size")
            else:
                # File doesn't exist - will be created
                file_contents[file_path] = ""

        return file_contents

    def _format_attempt_for_retry(self, changeset: "ChangeSet") -> str:
        """Format a failed attempt for retry context."""
        attempt_info = {
            "summary": changeset.summary,
            "description": changeset.description,
            "files_changed": len(changeset.files),
            "file_paths": [f.path for f in changeset.files],
        }

        # Include truncated content for context
        for file_change in changeset.files[:3]:  # Only first 3 files
            content_preview = file_change.content[:500]
            if len(file_change.content) > 500:
                content_preview += "..."
            attempt_info[f"content_preview_{file_change.path}"] = content_preview

        return json.dumps(attempt_info, indent=2)

    def _initialize_temp_dir(self, repo: "Repo") -> None:
        """Initialize the persistent temporary directory with repository content."""
        try:
            # Create temporary directory
            self._temp_dir = Path(tempfile.mkdtemp(prefix="sip_code_editor_"))
            self.logger.debug(f"Created temporary directory: {self._temp_dir}")

            # Copy repository files to temp directory
            for file_path, content in repo.files.items():
                full_path = self._temp_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            # Update state tracking
            self._current_repo_state = repo.files.copy()
            self._current_repo_name = repo.name
            self._is_temp_dir_initialized = True

            self.logger.info(f"Initialized temporary directory with {len(repo.files)} files")

        except Exception as e:
            self.logger.error(f"Failed to initialize temporary directory: {e}")
            self._cleanup_temp_dir()
            raise

    def _ensure_temp_dir_ready(self, repo: "Repo") -> None:
        """Ensure the temporary directory exists and is synchronized with the repository."""
        # Check if we need to initialize or reinitialize
        needs_init = (
            not self._is_temp_dir_initialized
            or self._temp_dir is None
            or not self._temp_dir.exists()
            or self._current_repo_name != repo.name
        )

        if needs_init:
            self._cleanup_temp_dir()
            self._initialize_temp_dir(repo)
            return

        # Synchronize any changes in repository state
        self._sync_repo_changes(repo)

    def _sync_repo_changes(self, repo: "Repo") -> None:
        """Synchronize repository changes to the temporary directory."""
        if not self._temp_dir or not self._temp_dir.exists():
            raise RuntimeError("Temporary directory not initialized")

        changes_made = 0

        # Update or create files that have changed
        for file_path, content in repo.files.items():
            if file_path not in self._current_repo_state or self._current_repo_state[file_path] != content:
                full_path = self._temp_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                changes_made += 1

        # Remove files that no longer exist in the repository
        for file_path in self._current_repo_state:
            if file_path not in repo.files:
                full_path = self._temp_dir / file_path
                if full_path.exists():
                    full_path.unlink()
                    changes_made += 1

        # Update state tracking
        self._current_repo_state = repo.files.copy()

        if changes_made > 0:
            self.logger.debug(f"Synchronized {changes_made} file changes to temporary directory")

    def _update_temp_dir(self, changeset: "ChangeSet") -> None:
        """Apply changeset to the persistent temporary directory."""
        if not self._temp_dir or not self._temp_dir.exists():
            raise RuntimeError("Temporary directory not initialized")

        changes_applied = 0

        for file_change in changeset.files:
            full_path = self._temp_dir / file_change.path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Only write if content has actually changed
            current_content = ""
            if full_path.exists():
                current_content = full_path.read_text()

            if current_content != file_change.content:
                full_path.write_text(file_change.content)
                changes_applied += 1

        if changes_applied > 0:
            self.logger.debug(f"Applied {changes_applied} changes to temporary directory")

    def _cleanup_temp_dir(self) -> None:
        """Clean up the persistent temporary directory."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                self.logger.debug(f"Cleaned up temporary directory: {self._temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temporary directory {self._temp_dir}: {e}")

        # Reset state
        self._temp_dir = None
        self._current_repo_state = {}
        self._is_temp_dir_initialized = False
        self._current_repo_name = ""

    def __del__(self) -> None:
        """Cleanup temporary directory when the CodeEditor instance is destroyed."""
        self._cleanup_temp_dir()


class TestFailureError(Exception):
    """Exception raised when tests fail during solution validation."""

    pass
