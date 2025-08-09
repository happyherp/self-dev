#!/usr/bin/env python
"""Integration tests for SIP."""

import os
from unittest.mock import Mock, patch

import pytest

from sip.config import Config
from sip.github_client import GitHubClient
from sip.issue_processor import IssueProcessor
from sip.llm_client import LLMClient
from sip.models import AnalysisResult, CodeChange, GitHubIssue, ProcessingResult, PullRequest
from sip.test_runner import SipTestResult, SipTestRunner


def create_test_issue(number=1, title="Test Issue", body="Test body"):
    """Helper to create a test GitHubIssue with all required fields."""
    return GitHubIssue(
        number=number,
        title=title,
        body=body,
        author="test_user",
        labels=["bug"],
        state="open",
        html_url=f"https://github.com/test/repo/issues/{number}",
        repository="test/repo",
    )


class TestConfigIntegration:
    """Test configuration integration."""

    def test_config_from_env_missing_github_token(self):
        """Test config fails without GitHub token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AGENT_GITHUB_TOKEN"):
                Config.from_env()

    def test_config_from_env_missing_openrouter_key(self):
        """Test config fails without OpenRouter key."""
        with patch.dict(os.environ, {"AGENT_GITHUB_TOKEN": "test"}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                Config.from_env()

    def test_config_from_env_success(self):
        """Test config creation with environment variables."""
        env = {
            "AGENT_GITHUB_TOKEN": "gh_test_token",
            "OPENROUTER_API_KEY": "or_test_key",
            "DEFAULT_REPOSITORY": "test/repo",
            "LLM_MODEL": "test/model",
            "MAX_RETRY_ATTEMPTS": "3",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config.from_env()
            assert config.github_token == "gh_test_token"
            assert config.openrouter_api_key == "or_test_key"
            assert config.default_repository == "test/repo"
            assert config.llm_model == "test/model"
            assert config.max_retry_attempts == 3

    def test_config_start_work_comment_template(self):
        """Test config has start work comment template."""
        config = Config(github_token="test", openrouter_api_key="test")
        assert hasattr(config, "start_work_comment_template")
        assert "SIP" in config.start_work_comment_template
        assert "started working" in config.start_work_comment_template


class TestGitHubClientIntegration:
    """Test GitHub client integration."""

    def test_github_client_initialization(self):
        """Test GitHub client can be initialized."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        client = GitHubClient(config)
        assert client.config == config
        assert client.github is not None

    def test_github_client_get_issue(self):
        """Test GitHub client can fetch issues."""
        config = Config(github_token="test", openrouter_api_key="test")
        client = GitHubClient(config)

        # Mock the PyGithub objects
        mock_user = Mock()
        mock_user.login = "test_user"

        mock_label = Mock()
        mock_label.name = "bug"

        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test body"
        mock_issue.state = "open"
        mock_issue.user = mock_user
        mock_issue.labels = [mock_label]
        mock_issue.html_url = "https://github.com/test/repo/issues/1"

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        client.github.get_repo = Mock(return_value=mock_repo)

        issue = client.get_issue("test/repo", 1)
        assert issue.number == 1
        assert issue.title == "Test Issue"
        assert issue.body == "Test body"
        assert issue.author == "test_user"
        assert issue.labels == ["bug"]
        assert issue.state == "open"

    def test_github_client_create_comment(self):
        """Test GitHub client can create comments."""
        config = Config(github_token="test", openrouter_api_key="test")
        client = GitHubClient(config)

        # Mock the issue
        mock_issue = Mock()
        mock_issue.create_comment = Mock()

        with patch.object(client, "get_github_issue", return_value=mock_issue):
            client.create_comment("test/repo", 1, "Test comment")

        mock_issue.create_comment.assert_called_once_with("Test comment")


class TestLLMClientIntegration:
    """Test LLM client integration."""

    def test_llm_client_initialization(self):
        """Test LLM client can be initialized."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        client = LLMClient(config)
        assert client.config == config
        assert client.model is not None
        assert client.analysis_agent is not None
        assert client.solution_agent is not None

    def test_llm_client_analyze_goal(self):
        """Test LLM client can analyze goals."""
        config = Config(github_token="test", openrouter_api_key="test")
        client = LLMClient(config)

        # Mock the PydanticAI agent
        mock_analysis = AnalysisResult(
            summary="Test summary",
            problem_type="bug",
            suggested_approach="Fix the bug",
            files_to_modify=["test.py"],
            confidence=0.8,
        )

        # Mock the run_sync method to return a mock result
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.data = mock_analysis
        client.analysis_agent.run_sync = Mock(return_value=mock_result)

        from sip.core import Goal

        goal = Goal(description="Fix the bug in test.py", context="Test context")
        analysis = client.analyze_goal(goal, "repo context")

        assert analysis.files_to_modify == ["test.py"]
        assert analysis.suggested_approach == "Fix the bug"
        assert analysis.confidence == 0.8


class TestTestRunnerIntegration:
    """Test test runner integration."""

    def test_test_runner_success(self):
        """Test test runner with successful command."""
        runner = SipTestRunner(["echo", "success"])
        result = runner.run_tests()

        assert result.success is True
        assert "success" in result.output
        assert result.return_code == 0

    def test_test_runner_failure(self):
        """Test test runner with failing command."""
        runner = SipTestRunner(["false"])  # Command that always fails
        result = runner.run_tests()

        assert result.success is False
        assert result.return_code == 1

    def test_test_runner_format_failure(self):
        """Test test runner failure formatting."""
        runner = SipTestRunner()
        result = SipTestResult(success=False, output="Test failed", error_output="Error details", return_code=1)

        formatted = runner.format_test_failure(result)
        assert "TESTS FAILED" in formatted
        assert "return code: 1" in formatted
        assert "Test failed" in formatted
        assert "Error details" in formatted


class TestIssueProcessorIntegration:
    """Test issue processor integration."""

    def test_issue_processor_initialization(self):
        """Test issue processor can be initialized."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        processor = IssueProcessor(config)

        assert processor.config == config
        # IssueProcessor handles GitHub issue processing directly
        assert isinstance(processor.github, GitHubClient)
        assert isinstance(processor.llm, LLMClient)
        # Test runner is now part of the core CodeEditor
        assert hasattr(processor, "code_editor")

    def test_issue_processor_creates_start_comment(self):
        """Test issue processor creates a start comment."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        processor = IssueProcessor(config)

        # Mock the GitHub client
        mock_issue = create_test_issue()
        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor.github, "create_comment") as mock_create_comment,
            patch.object(processor, "_fetch_github_repo", return_value={}),
            patch.object(processor.code_editor, "process_goal") as mock_process_goal,
            patch.object(processor, "_changeset_to_github_pr", return_value="http://test.pr"),
        ):
            # Mock the changeset
            from sip.core import ChangeSet

            mock_changeset = ChangeSet(summary="Test", description="Test", files=[])
            mock_process_goal.return_value = mock_changeset

            processor.process_issue("test/repo", 1, "main")

            # Verify that create_comment was called
            mock_create_comment.assert_called_once()
            args = mock_create_comment.call_args[0]
            assert args[0] == "test/repo"
            assert args[1] == 1
            assert "SIP" in args[2]  # Comment should contain SIP


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""

    def test_full_workflow_mock(self):
        """Test full workflow with mocked dependencies."""
        config = Config(
            github_token="test_token",
            openrouter_api_key="test_key",
            max_retry_attempts=1,  # Limit retries for testing
        )
        processor = IssueProcessor(config)

        # Mock all external dependencies
        mock_issue = create_test_issue(title="Test Issue", body="Fix this bug")

        with (
            patch.object(processor, "process_issue") as mock_process_issue,
        ):
            # Mock successful processing result
            mock_result = ProcessingResult(
                success=True,
                issue=mock_issue,
                analysis=AnalysisResult(
                    summary="Test issue analysis",
                    problem_type="bug",
                    suggested_approach="Fix the bug by updating test.py",
                    files_to_modify=["test.py"],
                    confidence=0.8,
                ),
                pull_request=PullRequest(
                    title="Fix: Test Issue",
                    body="This fixes the test issue",
                    branch_name="sip/issue-1-test",
                    changes=[
                        CodeChange(
                            file_path="test.py",
                            change_type="modify",
                            content="print('fixed')",
                            description="Fix the bug",
                        )
                    ],
                ),
            )
            mock_process_issue.return_value = mock_result

            result = processor.process_issue("test/repo", 1, "main")

            assert result.success is True
            assert result.issue == mock_issue
            assert result.pull_request is not None

    def test_workflow_with_failure(self):
        """Test workflow with failure."""
        config = Config(github_token="test_token", openrouter_api_key="test_key", max_retry_attempts=1)
        processor = IssueProcessor(config)

        mock_issue = create_test_issue(title="Test Issue", body="Fix this bug")

        with (
            patch.object(processor, "process_issue") as mock_process_issue,
        ):
            # Mock failed processing result
            mock_result = ProcessingResult(success=False, issue=mock_issue, error_message="Failed to process issue")
            mock_process_issue.return_value = mock_result

            result = processor.process_issue("test/repo", 1, "main")

            assert result.success is False
            assert result.error_message == "Failed to process issue"