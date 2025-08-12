#!/usr/bin/env python
"""End-to-end integration tests for SIP.

These tests require both GitHub and OpenRouter API credentials and test the complete
workflow from issue processing to PR creation. They are designed to be safe and
clean up after themselves.
"""

import os
import time

import pytest

from sip.config import Config
from sip.issue_processor import IssueProcessor


def has_github_credentials() -> bool:
    """Check if GitHub credentials are available for integration testing."""
    return bool(os.environ.get("AGENT_GITHUB_TOKEN"))


def has_openrouter_credentials() -> bool:
    """Check if OpenRouter credentials are available for integration testing."""
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def has_all_credentials() -> bool:
    """Check if all required credentials are available for end-to-end testing."""
    return has_github_credentials() and has_openrouter_credentials()


@pytest.mark.skipif(not has_all_credentials(), reason="Both GitHub and OpenRouter credentials required")
class TestEndToEndIntegrationReal:
    """Test end-to-end integration with real services (requires all credentials).

    These tests use real APIs but are designed to be safe and clean up after themselves.
    """

    def test_config_loads_from_environment(self):
        """Test that config can be loaded from real environment variables."""
        config = Config.from_env()

        assert config.github_token.startswith(("ghp_", "github_pat_"))
        assert len(config.openrouter_api_key) > 10
        assert config.default_repository
        assert "/" in config.default_repository  # Should be in format "owner/repo"

    def test_issue_processor_initialization_with_real_credentials(self):
        """Test issue processor initialization with real credentials."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        assert processor.config == config
        assert processor.github is not None
        assert processor.llm is not None
        assert processor.code_editor is not None

    def test_issue_processor_can_fetch_real_repository_info(self):
        """Test that issue processor can fetch real repository information."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Test fetching repository info (safe read operation)
        repo_info = processor._fetch_github_repo(config.default_repository)

        assert isinstance(repo_info, dict)
        assert len(repo_info) > 0

    @pytest.mark.slow
    def test_issue_processor_can_analyze_simple_mock_issue(self):
        """Test that issue processor can analyze a simple mock issue.

        This test uses real LLM but mocks the GitHub issue to avoid
        creating real issues or PRs.
        """
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Create a simple mock issue for testing
        from unittest.mock import Mock

        mock_issue = Mock()
        mock_issue.number = 999999  # Use a number that's unlikely to exist
        mock_issue.title = "Add hello world function"
        mock_issue.body = "Please add a simple hello world function that returns 'Hello, World!'"
        mock_issue.state = "open"
        mock_issue.html_url = "https://github.com/test/test/issues/999999"

        # Mock the GitHub operations to avoid creating real branches/PRs
        from unittest.mock import patch

        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor.github, "create_comment") as mock_create_comment,
            patch.object(processor, "_changeset_to_github_pr", return_value="http://test.pr"),
        ):
            # This should work with real LLM but mocked GitHub operations
            result = processor.process_issue(config.default_repository, 999999, "main")

            assert result is not None
            assert hasattr(result, "success")

            # Should have attempted to create a start comment
            mock_create_comment.assert_called_once()


@pytest.mark.skipif(not has_all_credentials(), reason="Both GitHub and OpenRouter credentials required")
class TestEndToEndWorkflowComponents:
    """Test individual components of the end-to-end workflow with real services."""

    def test_github_and_llm_integration(self):
        """Test that GitHub client and LLM client can work together."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Test that we can fetch repository info and analyze it with LLM
        repo_files = processor._fetch_github_repo(config.default_repository)

        # Create a simple test issue for LLM analysis
        test_issue = {"title": "Test integration", "body": "This is a test issue for integration testing"}

        # This should work - LLM analyzing real repository files
        analysis = processor.llm.analyze_issue(test_issue, repo_files)

        assert analysis is not None
        assert hasattr(analysis, "summary")
        assert isinstance(analysis.summary, str)
        assert len(analysis.summary) > 0

    def test_code_editor_with_real_llm(self):
        """Test that code editor works with real LLM."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Test code editor with a simple goal
        test_goal = "Add a hello world function to main.py"
        test_repo_files = {"main.py": "# Main module\npass", "README.md": "# Test Repository"}

        # This should work - code editor using real LLM
        changeset = processor.code_editor.process_goal(test_goal, test_repo_files)

        assert changeset is not None
        assert hasattr(changeset, "summary")
        assert hasattr(changeset, "files")
        assert isinstance(changeset.summary, str)
        assert len(changeset.summary) > 0


@pytest.mark.skipif(not has_all_credentials(), reason="Both GitHub and OpenRouter credentials required")
class TestEndToEndErrorHandling:
    """Test end-to-end error handling with real services."""

    def test_issue_processor_handles_nonexistent_issue(self):
        """Test that issue processor handles nonexistent issues gracefully."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Test with an issue number that definitely doesn't exist
        nonexistent_issue = 999999999

        with pytest.raises((ValueError, RuntimeError, Exception)):
            processor.process_issue(config.default_repository, nonexistent_issue, "main")

    def test_issue_processor_handles_invalid_repository(self):
        """Test that issue processor handles invalid repositories gracefully."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Test with a repository that doesn't exist
        invalid_repo = "nonexistent-user-12345/nonexistent-repo-67890"

        with pytest.raises((ValueError, RuntimeError, Exception)):
            processor.process_issue(invalid_repo, 1, "main")


@pytest.mark.skipif(not has_all_credentials(), reason="Both GitHub and OpenRouter credentials required")
class TestEndToEndPerformance:
    """Test end-to-end performance characteristics with real services."""

    @pytest.mark.slow
    def test_issue_processing_completes_in_reasonable_time(self):
        """Test that issue processing completes in reasonable time."""
        config = Config.from_env()
        processor = IssueProcessor(config)

        # Create a simple mock issue
        from unittest.mock import Mock, patch

        mock_issue = Mock()
        mock_issue.number = 999999
        mock_issue.title = "Simple test"
        mock_issue.body = "Simple test issue"
        mock_issue.state = "open"
        mock_issue.html_url = "https://github.com/test/test/issues/999999"

        start_time = time.time()

        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor.github, "create_comment"),
            patch.object(processor, "_changeset_to_github_pr", return_value="http://test.pr"),
        ):
            processor.process_issue(config.default_repository, 999999, "main")

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete within a reasonable time (adjust as needed)
        assert processing_time < 60  # 60 seconds max for simple issue
