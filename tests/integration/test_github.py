#!/usr/bin/env python
"""GitHub integration tests for SIP.

These tests require real GitHub API credentials (AGENT_GITHUB_TOKEN) and test actual
integration with GitHub services. They are designed to be safe and clean up after themselves.
"""

import os
import time

import pytest

from sip.config import Config
from sip.github_client import GitHubClient
from sip.models import CodeChange


def has_github_credentials() -> bool:
    """Check if GitHub credentials are available for integration testing."""
    return bool(os.environ.get("AGENT_GITHUB_TOKEN"))


def get_test_repository() -> str | None:
    """Get the test repository from config, if available."""
    if not has_github_credentials():
        return None
    try:
        config = Config.from_env()
        return config.default_repository
    except Exception:
        return None


@pytest.mark.skipif(not has_github_credentials(), reason="GitHub credentials not available")
class TestGitHubClientIntegrationReal:
    """Test GitHub client integration with real GitHub API (requires credentials)."""

    def test_github_client_can_read_repository_info(self):
        """Test that GitHub client can read repository information."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Test reading repository info (safe read operation)
        repo_info = client.get_repository(config.default_repository)

        assert repo_info["full_name"] == config.default_repository
        assert "html_url" in repo_info
        assert "default_branch" in repo_info

    def test_github_client_can_list_repository_files(self):
        """Test that GitHub client can list repository files."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Test listing files (safe read operation)
        files = client.list_repository_files(config.default_repository)

        assert isinstance(files, list)
        assert len(files) > 0
        # Should contain some expected files
        assert any("README" in f.upper() for f in files)

    def test_github_client_can_read_file_content(self):
        """Test that GitHub client can read file content."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Test reading a file that should exist (safe read operation)
        content = client.get_file_content(config.default_repository, "README.md")

        assert isinstance(content, str)
        assert len(content) > 0

    def test_github_client_rate_limit_info(self):
        """Test that GitHub client can get rate limit info."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Test getting rate limit info (safe read operation)
        rate_limit = client.get_rate_limit_info()

        assert isinstance(rate_limit, dict)
        if "core" in rate_limit:
            assert "limit" in rate_limit["core"]
            assert "remaining" in rate_limit["core"]


@pytest.mark.skipif(not has_github_credentials(), reason="GitHub credentials not available")
class TestGitHubClientGitOperationsReal:
    """Test GitHub client git operations with real GitHub API (requires credentials).

    These tests are more careful - they only test on branches we create and clean up.
    """

    def test_github_client_can_create_and_cleanup_branch(self):
        """Test creating and cleaning up a test branch."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Use a unique test branch name
        test_branch = f"test-branch-{int(time.time())}"

        try:
            # Test creating a branch (write operation, but safe)
            client.create_branch(config.default_repository, test_branch, config.default_branch or "main")

            # Verify the branch was created by trying to get its info
            repo = client.get_github_repository(config.default_repository)
            branch = repo.get_branch(test_branch)
            assert branch.name == test_branch

        finally:
            # Clean up: delete the test branch
            try:
                repo = client.get_github_repository(config.default_repository)
                ref = repo.get_git_ref(f"heads/{test_branch}")
                ref.delete()
            except Exception as e:
                print(f"Warning: Could not clean up test branch {test_branch}: {e}")

    def test_github_client_can_create_file_and_cleanup(self):
        """Test creating a file and cleaning it up."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Use a unique test branch and file
        test_branch = f"test-file-branch-{int(time.time())}"
        test_file = f"test-file-{int(time.time())}.txt"

        try:
            # Create test branch
            client.create_branch(config.default_repository, test_branch, config.default_branch or "main")

            # Test creating a file
            changes = [
                CodeChange(
                    file_path=test_file,
                    change_type="create",
                    content="This is a test file created by integration tests",
                    description="Test file creation",
                )
            ]

            client.commit_changes(config.default_repository, test_branch, changes, "Test commit from integration tests")

            # Verify the file was created
            content = client.get_file_content(config.default_repository, test_file, test_branch)
            assert "test file created by integration tests" in content

        finally:
            # Clean up: delete the test branch (which also removes the file)
            try:
                repo = client.get_github_repository(config.default_repository)
                ref = repo.get_git_ref(f"heads/{test_branch}")
                ref.delete()
            except Exception as e:
                print(f"Warning: Could not clean up test branch {test_branch}: {e}")

    def test_github_client_can_create_comment_on_issue(self):
        """Test creating a comment on an issue (if test issue exists)."""
        config = Config.from_env()
        client = GitHubClient(config)

        # This test is more cautious - it only runs if we can find a test issue
        # We don't want to spam real issues with test comments

        # For now, just test that the method exists and can be called
        # In a real test environment, you might have a dedicated test issue
        assert hasattr(client, "create_comment")

        # TODO: Implement when we have a dedicated test issue or test repository
        pytest.skip("Skipping comment creation test - needs dedicated test issue")


@pytest.mark.skipif(not has_github_credentials(), reason="GitHub credentials not available")
class TestGitHubClientErrorHandling:
    """Test GitHub client error handling with real API."""

    def test_github_client_handles_nonexistent_repository(self):
        """Test that client handles requests to nonexistent repositories gracefully."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Test with a repository that definitely doesn't exist
        nonexistent_repo = "nonexistent-user-12345/nonexistent-repo-67890"

        with pytest.raises((ValueError, RuntimeError, Exception)):  # Should raise some kind of exception
            client.get_repository(nonexistent_repo)

    def test_github_client_handles_nonexistent_file(self):
        """Test that client handles requests to nonexistent files gracefully."""
        config = Config.from_env()
        client = GitHubClient(config)

        # Test with a file that definitely doesn't exist
        nonexistent_file = f"nonexistent-file-{int(time.time())}.xyz"

        with pytest.raises((ValueError, RuntimeError, Exception)):  # Should raise some kind of exception
            client.get_file_content(config.default_repository, nonexistent_file)
