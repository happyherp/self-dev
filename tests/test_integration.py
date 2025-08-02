#!/usr/bin/env python
"""Integration tests for SIP."""

import os
from unittest.mock import Mock, patch

import pytest

from sip.config import Config
from sip.github_client import GitHubClient
from sip.issue_processor import IssueProcessor
from sip.llm_client import LLMClient
from sip.models import AnalysisResult, CodeChange, GitHubIssue, PullRequest
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
        assert client.client is not None

    def test_llm_client_analyze_issue(self):
        """Test LLM client can analyze issues."""
        config = Config(github_token="test", openrouter_api_key="test")
        client = LLMClient(config)

        # Mock the instructor client
        mock_analysis = AnalysisResult(
            summary="Test summary",
            problem_type="bug",
            suggested_approach="Fix the bug",
            files_to_modify=["test.py"],
            confidence=0.8,
        )
        client.client.chat.completions.create = Mock(return_value=mock_analysis)

        issue = create_test_issue()
        analysis = client.analyze_issue(issue, "repo context")

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
        assert isinstance(processor.github, GitHubClient)
        assert isinstance(processor.llm, LLMClient)
        assert isinstance(processor.test_runner, SipTestRunner)

    def test_get_repository_context(self):
        """Test repository context gathering."""
        config = Config(github_token="test", openrouter_api_key="test")
        processor = IssueProcessor(config)

        # Mock the GitHub client methods
        with (
            patch.object(processor.github, "get_file_content") as mock_get_file,
            patch.object(processor.github, "list_repository_files") as mock_list_files,
        ):
            mock_get_file.side_effect = lambda repo, path: f"Content of {path}" if path == "README.md" else None
            mock_list_files.return_value = ["README.md", "src/main.py", "tests/test.py"]

            context = processor._get_repository_context("test/repo")

            assert "Repository: test/repo" in context
            assert "Content of README.md" in context
            assert "src/main.py" in context

    def test_get_relevant_files(self):
        """Test relevant file content gathering."""
        config = Config(github_token="test", openrouter_api_key="test")
        processor = IssueProcessor(config)

        with patch.object(processor.github, "get_file_content") as mock_get_file:
            mock_get_file.side_effect = lambda repo, path: f"Content of {path}"

            files = processor._get_relevant_files("test/repo", ["file1.py", "file2.py"])

            assert len(files) == 2
            assert files["file1.py"] == "Content of file1.py"
            assert files["file2.py"] == "Content of file2.py"


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
        mock_analysis = AnalysisResult(
            summary="Test issue analysis",
            problem_type="bug",
            suggested_approach="Fix the bug by updating test.py",
            files_to_modify=["test.py"],
            confidence=0.8,
        )
        mock_pull_request = PullRequest(
            title="Fix: Test Issue",
            body="This fixes the test issue",
            branch_name="sip/issue-1-test",
            changes=[
                CodeChange(
                    file_path="test.py", change_type="modify", content="print('fixed')", description="Fix the bug"
                )
            ],
        )

        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor, "_get_repository_context", return_value="repo context"),
            patch.object(processor.llm, "analyze_issue", return_value=mock_analysis),
            patch.object(processor, "_get_relevant_files", return_value={"test.py": "print('old')"}),
            patch.object(processor.llm, "generate_solution", return_value=mock_pull_request),
            patch.object(processor, "_test_solution_in_temp_repo") as mock_test,
            patch.object(processor.github, "create_branch"),
            patch.object(processor.github, "commit_changes"),
            patch.object(processor.github, "create_pull_request", return_value="https://github.com/test/repo/pull/1"),
        ):
            # Mock successful test
            mock_test.return_value = SipTestResult(
                success=True, output="All tests passed", error_output="", return_code=0
            )

            result = processor.process_issue("test/repo", 1)

            assert result.success is True
            assert result.issue == mock_issue
            assert result.analysis == mock_analysis
            assert result.pull_request == mock_pull_request

    def test_workflow_with_test_failure_and_retry(self):
        """Test workflow with test failure and successful retry."""
        config = Config(github_token="test_token", openrouter_api_key="test_key", max_retry_attempts=2)
        processor = IssueProcessor(config)

        mock_issue = create_test_issue(title="Test Issue", body="Fix this bug")
        mock_analysis = AnalysisResult(
            summary="Test issue analysis",
            problem_type="bug",
            suggested_approach="Fix the bug",
            files_to_modify=["test.py"],
            confidence=0.8,
        )

        # First attempt fails, second succeeds
        failing_pr = PullRequest(
            title="Fix: Test Issue (broken)",
            body="This is broken",
            branch_name="sip/issue-1-test",
            changes=[
                CodeChange(
                    file_path="test.py", change_type="modify", content="print('broken')", description="Broken fix"
                )
            ],
        )

        working_pr = PullRequest(
            title="Fix: Test Issue (working)",
            body="This works",
            branch_name="sip/issue-1-test",
            changes=[
                CodeChange(
                    file_path="test.py", change_type="modify", content="print('working')", description="Working fix"
                )
            ],
        )

        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor, "_get_repository_context", return_value="repo context"),
            patch.object(processor.llm, "analyze_issue", return_value=mock_analysis),
            patch.object(processor, "_get_relevant_files", return_value={"test.py": "print('old')"}),
            patch.object(processor.llm, "generate_solution", side_effect=[failing_pr, working_pr]),
            patch.object(processor, "_test_solution_in_temp_repo") as mock_test,
            patch.object(processor.github, "create_branch"),
            patch.object(processor.github, "commit_changes"),
            patch.object(processor.github, "create_pull_request", return_value="https://github.com/test/repo/pull/1"),
        ):
            # First test fails, second succeeds
            mock_test.side_effect = [
                SipTestResult(success=False, output="", error_output="Tests failed", return_code=1),
                SipTestResult(success=True, output="All tests passed", error_output="", return_code=0),
            ]

            result = processor.process_issue("test/repo", 1)

            assert result.success is True
            assert result.pull_request == working_pr
            assert mock_test.call_count == 2  # Called twice due to retry

    def test_workflow_with_recoverable_errors_and_retry(self):
        """Test workflow with recoverable errors that count towards retry limit."""
        config = Config(github_token="test_token", openrouter_api_key="test_key", max_retry_attempts=3)
        processor = IssueProcessor(config)

        mock_issue = create_test_issue(title="Test Issue", body="Fix this bug")
        mock_analysis = AnalysisResult(
            summary="Test issue analysis",
            problem_type="bug",
            suggested_approach="Fix the bug",
            files_to_modify=["test.py"],
            confidence=0.8,
        )

        working_pr = PullRequest(
            title="Fix: Test Issue (working)",
            body="This works",
            branch_name="sip/issue-1-test",
            changes=[
                CodeChange(
                    file_path="test.py", change_type="modify", content="print('working')", description="Working fix"
                )
            ],
        )

        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor, "_get_repository_context", return_value="repo context"),
            patch.object(processor.llm, "analyze_issue", return_value=mock_analysis),
            patch.object(processor, "_get_relevant_files", return_value={"test.py": "print('old')"}),
            patch.object(processor.llm, "generate_solution") as mock_generate,
            patch.object(processor, "_test_solution_in_temp_repo") as mock_test,
            patch.object(processor.github, "create_branch"),
            patch.object(processor.github, "commit_changes"),
            patch.object(processor.github, "create_pull_request", return_value="https://github.com/test/repo/pull/1"),
        ):
            # First two attempts fail with recoverable errors, third succeeds
            mock_generate.side_effect = [
                Exception("Network timeout"),  # Recoverable error
                Exception("Rate limit exceeded"),  # Recoverable error  
                working_pr,  # Success
            ]
            mock_test.return_value = SipTestResult(success=True, output="All tests passed", error_output="", return_code=0)

            result = processor.process_issue("test/repo", 1)

            assert result.success is True
            assert result.pull_request == working_pr
            assert mock_generate.call_count == 3  # Called three times due to retries

    def test_workflow_with_unrecoverable_error_no_retry(self):
        """Test workflow with unrecoverable error that doesn't retry."""
        config = Config(github_token="test_token", openrouter_api_key="test_key", max_retry_attempts=3)
        processor = IssueProcessor(config)

        mock_issue = create_test_issue(title="Test Issue", body="Fix this bug")
        mock_analysis = AnalysisResult(
            summary="Test issue analysis",
            problem_type="bug",
            suggested_approach="Fix the bug",
            files_to_modify=["test.py"],
            confidence=0.8,
        )

        with (
            patch.object(processor.github, "get_issue", return_value=mock_issue),
            patch.object(processor, "_get_repository_context", return_value="repo context"),
            patch.object(processor.llm, "analyze_issue", return_value=mock_analysis),
            patch.object(processor, "_get_relevant_files", return_value={"test.py": "print('old')"}),
            patch.object(processor.llm, "generate_solution") as mock_generate,
        ):
            # First attempt fails with unrecoverable error
            mock_generate.side_effect = Exception("401 Unauthorized")  # Unrecoverable error

            result = processor.process_issue("test/repo", 1)

            assert result.success is False
            assert "Unrecoverable error: 401 Unauthorized" in result.error_message
            assert mock_generate.call_count == 1  # Called only once, no retries

    def test_is_unrecoverable_error_classification(self):
        """Test the error classification logic."""
        config = Config(github_token="test_token", openrouter_api_key="test_key")
        processor = IssueProcessor(config)

        # Test unrecoverable errors
        assert processor._is_unrecoverable_error(Exception("401 Unauthorized")) is True
        assert processor._is_unrecoverable_error(Exception("403 Forbidden")) is True
        assert processor._is_unrecoverable_error(Exception("404 Not Found")) is True
        assert processor._is_unrecoverable_error(Exception("Invalid API key")) is True
        assert processor._is_unrecoverable_error(Exception("Invalid model specified")) is True
        assert processor._is_unrecoverable_error(ValueError("Missing required config")) is True

        # Test recoverable errors
        assert processor._is_unrecoverable_error(Exception("Network timeout")) is False
        assert processor._is_unrecoverable_error(Exception("Rate limit exceeded")) is False
        assert processor._is_unrecoverable_error(Exception("Temporary server error")) is False
        assert processor._is_unrecoverable_error(ValueError("No changes generated")) is False
