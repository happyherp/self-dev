#!/usr/bin/env python
"""Tests for SIP CLI."""

import os
from unittest.mock import Mock, patch

from click.testing import CliRunner

from sip.cli import main
from sip.models import AnalysisResult, GitHubIssue, ProcessingResult


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


class TestCLI:
    """Test CLI functionality."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "SIP" in result.output
        assert "process-issue" in result.output

    def test_cli_missing_env_vars(self):
        """Test CLI fails gracefully without environment variables."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(main, ["process-issue", "1", "--repo", "test/repo"])

            assert result.exit_code != 0
            assert "AGENT_GITHUB_TOKEN" in result.output or "environment variable" in result.output

    def test_cli_missing_arguments(self):
        """Test CLI requires issue argument."""
        runner = CliRunner()

        # Missing issue number
        result = runner.invoke(main, ["process-issue"])
        assert result.exit_code != 0

    @patch("sip.cli.IssueProcessor")
    def test_cli_successful_processing(self, mock_processor_class):
        """Test CLI with successful issue processing."""
        # Mock the processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        # Mock successful result
        mock_issue = create_test_issue()
        mock_analysis = AnalysisResult(
            summary="Test analysis",
            problem_type="bug",
            suggested_approach="Fix it",
            files_to_modify=["test.py"],
            confidence=0.8,
        )
        mock_result = ProcessingResult(issue=mock_issue, analysis=mock_analysis, pull_request=None, success=True)
        mock_processor.process_issue.return_value = mock_result

        runner = CliRunner()

        with patch.dict(os.environ, {"AGENT_GITHUB_TOKEN": "test_token", "OPENROUTER_API_KEY": "test_key"}):
            result = runner.invoke(main, ["process-issue", "1", "--repo", "test/repo"])

            assert result.exit_code == 0
            assert "✅ Successfully processed issue #1" in result.output
            # The CLI should call process_issue with repo, issue_number, and branch
            # The branch will be the current git branch or "main" as fallback
            args, kwargs = mock_processor.process_issue.call_args
            assert args[0] == "test/repo"
            assert args[1] == 1
            assert len(args) == 3  # Should have 3 arguments including branch

    @patch("sip.cli.IssueProcessor")
    def test_cli_failed_processing(self, mock_processor_class):
        """Test CLI with failed issue processing."""
        # Mock the processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        # Mock failed result
        mock_result = ProcessingResult(
            issue=None, analysis=None, pull_request=None, success=False, error_message="Something went wrong"
        )
        mock_processor.process_issue.return_value = mock_result

        runner = CliRunner()

        with patch.dict(os.environ, {"AGENT_GITHUB_TOKEN": "test_token", "OPENROUTER_API_KEY": "test_key"}):
            result = runner.invoke(main, ["process-issue", "1", "--repo", "test/repo"])

            assert result.exit_code == 1
            assert "❌ Failed to process issue #1" in result.output
            assert "Something went wrong" in result.output

    @patch("sip.cli.IssueProcessor")
    def test_cli_exception_handling(self, mock_processor_class):
        """Test CLI handles exceptions gracefully."""
        # Mock the processor to raise an exception
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.process_issue.side_effect = Exception("Unexpected error")

        runner = CliRunner()

        with patch.dict(os.environ, {"AGENT_GITHUB_TOKEN": "test_token", "OPENROUTER_API_KEY": "test_key"}):
            result = runner.invoke(main, ["process-issue", "1", "--repo", "test/repo"])

            assert result.exit_code == 1
            assert "💥 Fatal error: Unexpected error" in result.output

    @patch("sip.cli.IssueProcessor")
    def test_cli_with_custom_config(self, mock_processor_class):
        """Test CLI with custom configuration via environment variables."""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        mock_result = ProcessingResult(
            issue=create_test_issue(1, "Test", "Body"), analysis=None, pull_request=None, success=True
        )
        mock_processor.process_issue.return_value = mock_result

        runner = CliRunner()

        custom_env = {
            "AGENT_GITHUB_TOKEN": "custom_token",
            "OPENROUTER_API_KEY": "custom_key",
            "DEFAULT_REPOSITORY": "custom/repo",
            "LLM_MODEL": "custom/model",
            "MAX_RETRY_ATTEMPTS": "3",
        }

        with patch.dict(os.environ, custom_env):
            result = runner.invoke(main, ["process-issue", "1", "--repo", "test/repo"])

            assert result.exit_code == 0

            # Verify the processor was created with the right config
            mock_processor_class.assert_called_once()
            config = mock_processor_class.call_args[0][0]
            assert config.github_token == "custom_token"
            assert config.openrouter_api_key == "custom_key"
            assert config.default_repository == "custom/repo"
            assert config.llm_model == "custom/model"
            assert config.max_retry_attempts == 3
