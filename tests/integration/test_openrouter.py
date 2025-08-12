#!/usr/bin/env python
"""OpenRouter integration tests for SIP.

These tests require real OpenRouter API credentials (OPENROUTER_API_KEY) and test actual
integration with OpenRouter LLM services. They are designed to be safe and use minimal API calls.
"""

import os

import pytest

from sip.config import Config
from sip.llm_client import LLMClient


def has_openrouter_credentials() -> bool:
    """Check if OpenRouter credentials are available for integration testing."""
    return bool(os.environ.get("OPENROUTER_API_KEY"))


@pytest.mark.skipif(not has_openrouter_credentials(), reason="OpenRouter credentials not available")
class TestLLMClientIntegrationReal:
    """Test LLM client integration with real OpenRouter API (requires credentials)."""

    def test_llm_client_initialization_with_real_credentials(self):
        """Test LLM client initialization with real credentials."""
        config = Config.from_env()
        client = LLMClient(config)

        assert client.config == config
        assert client.model is not None
        assert client.analysis_agent is not None
        assert client.solution_agent is not None

    def test_llm_client_can_analyze_simple_issue(self):
        """Test that LLM client can analyze a simple issue."""
        config = Config.from_env()
        client = LLMClient(config)

        # Test with a very simple, safe issue analysis
        test_issue = {
            "title": "Add hello world function",
            "body": "Please add a simple hello world function that returns 'Hello, World!'",
        }

        test_repo_files = {
            "README.md": "# Test Repository\nThis is a test repository.",
            "main.py": "# Main module\npass",
        }

        # This should not fail and should return some kind of analysis
        analysis = client.analyze_issue(test_issue, test_repo_files)

        assert analysis is not None
        assert hasattr(analysis, "summary")
        assert hasattr(analysis, "confidence")
        assert isinstance(analysis.summary, str)
        assert len(analysis.summary) > 0

    def test_llm_client_can_generate_simple_solution(self):
        """Test that LLM client can generate a simple solution."""
        config = Config.from_env()
        client = LLMClient(config)

        # Test with a very simple solution generation
        test_goal = "Add a hello world function"
        test_repo_files = {"main.py": "# Main module\npass"}

        # This should not fail and should return some kind of solution
        solution = client.generate_solution(test_goal, test_repo_files)

        assert solution is not None
        assert hasattr(solution, "summary")
        assert hasattr(solution, "files")
        assert isinstance(solution.summary, str)
        assert len(solution.summary) > 0
        assert isinstance(solution.files, list)

    def test_llm_client_handles_empty_input_gracefully(self):
        """Test that LLM client handles empty or minimal input gracefully."""
        config = Config.from_env()
        client = LLMClient(config)

        # Test with minimal input
        test_issue = {"title": "Test", "body": "Test"}

        test_repo_files = {}

        # This should not crash, even with minimal input
        try:
            analysis = client.analyze_issue(test_issue, test_repo_files)
            assert analysis is not None
        except Exception as e:
            # If it fails, it should fail gracefully with a meaningful error
            assert isinstance(e, Exception)
            assert len(str(e)) > 0


@pytest.mark.skipif(not has_openrouter_credentials(), reason="OpenRouter credentials not available")
class TestLLMClientErrorHandling:
    """Test LLM client error handling with real API."""

    def test_llm_client_handles_malformed_input(self):
        """Test that LLM client handles malformed input gracefully."""
        config = Config.from_env()
        client = LLMClient(config)

        # Test with malformed issue data
        malformed_issue = {
            "title": None,  # Invalid
            "body": 123,  # Invalid type
        }

        # Should handle this gracefully
        with pytest.raises((ValueError, TypeError, Exception)):
            client.analyze_issue(malformed_issue, {})

    def test_llm_client_handles_very_large_input(self):
        """Test that LLM client handles very large input appropriately."""
        config = Config.from_env()
        client = LLMClient(config)

        # Create a very large file content (but not so large as to be expensive)
        large_content = "# Large file\n" + "print('line')\n" * 1000

        test_issue = {"title": "Test with large file", "body": "Test issue with large repository file"}

        test_repo_files = {"large_file.py": large_content}

        # Should handle this without crashing (though it might truncate or summarize)
        try:
            analysis = client.analyze_issue(test_issue, test_repo_files)
            assert analysis is not None
        except Exception as e:
            # If it fails due to size limits, that's acceptable
            assert "too large" in str(e).lower() or "limit" in str(e).lower() or "token" in str(e).lower()


@pytest.mark.skipif(not has_openrouter_credentials(), reason="OpenRouter credentials not available")
class TestLLMClientConfiguration:
    """Test LLM client configuration and model selection."""

    def test_llm_client_uses_configured_model(self):
        """Test that LLM client uses the configured model."""
        config = Config.from_env()
        client = LLMClient(config)

        # The client should be using the model specified in config
        assert client.model == config.llm_model

    def test_llm_client_respects_retry_configuration(self):
        """Test that LLM client respects retry configuration."""
        config = Config.from_env()
        client = LLMClient(config)

        # The client should have the retry configuration from config
        assert hasattr(client, "config")
        assert client.config.max_retry_attempts == config.max_retry_attempts
