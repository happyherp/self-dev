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


class TestGitHubClientIntegration:
    """Test GitHub client integration."""

    def test_github_client_initialization(self):
        """Test GitHub client can be initialized."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        client = GitHubClient(config)
        assert client.config == config
        assert "Authorization" in client.client.headers
        assert client.client.headers["Authorization"] == "token test_token"

    def test_github_client_get_issue(self):
        """Test GitHub client can fetch issues."""
        config = Config(github_token="test", openrouter_api_key="test")
        client = GitHubClient(config)

        # Mock the client.get method
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 1,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "user": {"login": "test_user"},
            "labels": [{"name": "bug"}],
            "html_url": "https://github.com/test/repo/issues/1",
        }
        mock_response.raise_for_status.return_value = None
        client.client.get = Mock(return_value=mock_response)

        issue = client.get_issue("test/repo", 1)
        assert issue.number == 1
        assert issue.title == "Test Issue"
        assert issue.body == "Test body"


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

            result = processor.process_issue("test/repo", 1)

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

            result = processor.process_issue("test/repo", 1)

            assert result.success is False
            assert result.error_message == "Failed to process issue"
