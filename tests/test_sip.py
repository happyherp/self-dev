#!/usr/bin/env python
"""Tests for SIP."""

import re
from pathlib import Path

import tomllib

from sip import __version__
from sip.config import Config
from sip.test_runner import SipTestResult, SipTestRunner


def test_version():
    """Test version consistency between pyproject.toml and package."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    pyproject_version = pyproject_data["project"]["version"]

    assert __version__ == pyproject_version
    assert re.match(r"^\d+\.\d+\.\d+$", __version__) is not None


def test_config_creation():
    """Test config creation with defaults."""
    config = Config(github_token="test_token", openrouter_api_key="test_key")
    assert config.github_token == "test_token"
    assert config.openrouter_api_key == "test_key"
    assert config.max_retry_attempts == 5
    assert config.llm_model == "anthropic/claude-sonnet-4"


def test_test_runner_initialization():
    """Test test runner can be initialized."""
    runner = SipTestRunner()
    assert runner.test_command == ["make", "ci"]


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
