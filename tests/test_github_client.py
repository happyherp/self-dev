"""Tests for GitHubClient."""

from unittest.mock import Mock, patch

from github.GithubException import GithubException

from sip.config import Config
from sip.github_client import GitHubClient


class TestGitHubClient:
    """Test GitHubClient functionality."""

    def test_create_comment_success(self):
        """Test successful comment creation."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        client = GitHubClient(config)

        # Mock the GitHub issue
        mock_issue = Mock()
        mock_issue.create_comment = Mock()

        with patch.object(client, "get_github_issue", return_value=mock_issue):
            client.create_comment("test/repo", 1, "Test comment")

        mock_issue.create_comment.assert_called_once_with("Test comment")

    def test_create_comment_github_exception(self):
        """Test comment creation with GitHub exception."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        client = GitHubClient(config)

        # Mock the GitHub issue to raise an exception
        mock_issue = Mock()
        mock_issue.create_comment.side_effect = GithubException(404, "Not found", {})

        with patch.object(client, "get_github_issue", return_value=mock_issue):
            with patch("builtins.print") as mock_print:
                # This should not raise an exception, just print a warning
                client.create_comment("test/repo", 1, "Test comment")

        # Verify that the warning was printed
        mock_print.assert_called_once()
        assert "Warning: Failed to create comment" in str(mock_print.call_args)

    def test_create_comment_handles_various_exceptions(self):
        """Test comment creation handles different types of exceptions."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        client = GitHubClient(config)

        # Test with general exception during comment creation
        mock_issue = Mock()
        mock_issue.create_comment.side_effect = Exception("Network error")

        with patch.object(client, "get_github_issue", return_value=mock_issue):
            with patch("builtins.print") as mock_print:
                client.create_comment("test/repo", 1, "Test comment")

        # Verify that the warning was printed
        mock_print.assert_called_once()
        assert "Warning: Failed to create comment" in str(mock_print.call_args)