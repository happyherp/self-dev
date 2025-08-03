"""Tests for meta processor functionality."""

from unittest.mock import Mock, patch

import pytest

from sip.config import Config
from sip.meta_processor import MetaProcessor
from sip.models import ProcessingResult, PullRequest


class TestMetaProcessor:
    """Test MetaProcessor class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Mock(spec=Config)
        config.default_repository = "test/repo"
        return config
    
    @pytest.fixture
    def processor(self, mock_config):
        """Create a meta processor with mocked dependencies."""
        with patch('sip.meta_processor.IssueProcessor'):
            processor = MetaProcessor(mock_config)
            return processor
    
    def test_enhance_meta_request(self, processor):
        """Test enhancement of meta requests."""
        request = "add logging to the CLI"
        repository = "test/repo"
        
        enhanced = processor.enhance_meta_request(request, repository)
        
        assert "META-PROGRAMMING REQUEST" in enhanced
        assert request in enhanced
        assert repository in enhanced
        assert "live CLI session" in enhanced
    
    def test_process_meta_request_success(self, processor):
        """Test successful meta request processing."""
        # Mock successful processing
        mock_pr = PullRequest(
            title="Test PR",
            body="Test body",
            branch_name="test-branch",
            changes=[]
        )
        
        mock_result = ProcessingResult(
            success=True,
            pull_request=mock_pr
        )
        
        processor.issue_processor.process_issue_with_data.return_value = mock_result
        
        result = processor.process_meta_request("add feature", "test/repo")
        
        assert result.success is True
        assert result.pull_request is not None
        assert "Live Meta:" in result.pull_request.title
        assert "live-meta-" in result.pull_request.branch_name
    
    def test_process_meta_request_failure(self, processor):
        """Test failed meta request processing."""
        # Mock failed processing
        mock_result = ProcessingResult(
            success=False,
            error_message="Test error"
        )
        
        processor.issue_processor.process_issue_with_data.return_value = mock_result
        
        result = processor.process_meta_request("invalid request", "test/repo")
        
        assert result.success is False
        assert "Test error" in result.error_message
    
    def test_process_meta_request_exception(self, processor):
        """Test meta request processing with exception."""
        # Mock exception during processing
        processor.issue_processor.process_issue_with_data.side_effect = Exception("Test exception")
        
        result = processor.process_meta_request("request", "test/repo")
        
        assert result.success is False
        assert "Meta processing failed" in result.error_message
        assert "Test exception" in result.error_message
