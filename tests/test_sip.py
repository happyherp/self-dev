#!/usr/bin/env python
"""Tests for SIP."""

from sip.config import Config
from sip.models import GitHubIssue, ProcessingResult
from sip.sip import SIP
from sip.test_runner import SipTestResult, SipTestRunner


def test_config_creation():
    """Test config creation with defaults."""
    config = Config(github_token="test_token", openrouter_api_key="test_key")
    assert config.github_token == "test_token"
    assert config.openrouter_api_key == "test_key"
    assert config.max_retry_attempts == 5
    assert config.llm_model == "anthropic/claude-3.5-sonnet"


def test_test_runner_initialization():
    """Test test runner can be initialized."""
    runner = SipTestRunner()
    assert runner.test_command == ["python", "-m", "pytest", "-v"]


def test_test_runner_custom_command():
    """Test test runner with custom command."""
    runner = SipTestRunner(["echo", "test"])
    assert runner.test_command == ["echo", "test"]


def test_test_result_creation():
    """Test test result creation."""
    result = SipTestResult(success=True, output="All tests passed", error_output="", return_code=0)
    assert result.success is True
    assert result.output == "All tests passed"
    assert result.return_code == 0


def test_test_runner_format_failure():
    """Test test runner failure formatting."""
    runner = SipTestRunner()
    result = SipTestResult(success=False, output="Test output", error_output="Error details", return_code=1)

    formatted = runner.format_test_failure(result)
    assert "TESTS FAILED" in formatted
    assert "return code: 1" in formatted
    assert "Test output" in formatted
    assert "Error details" in formatted


def test_sip_initialization():
    """Test SIP initialization."""
    sip = SIP(github_token="test_token")
    assert sip.github_token == "test_token"


def test_sip_process_issue():
    """Test processing an issue."""
    sip = SIP(github_token="test_token")
    issue = GitHubIssue(
        number=1,
        title="Test Issue",
        body="Test body",
        author="test_user",
        labels=["bug"],
        state="open",
        html_url="https://github.com/test/test/issues/1",
        repository="test/test"
    )

    result = sip.process_issue(issue)
    assert isinstance(result, ProcessingResult)
    assert result.success is True
    assert result.issue == issue
    assert result.analysis is not None
    assert result.analysis.confidence > 0
