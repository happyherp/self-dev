"""Meta-programming processor for live self-modification."""

import logging
from typing import Dict, Any

from .config import Config
from .issue_processor import IssueProcessor
from .models import ProcessingResult, GitHubIssue, PullRequest

logger = logging.getLogger(__name__)


class MetaProcessor:
    """Processes meta-programming requests for live code modification."""
    
    def __init__(self, config: Config):
        self.config = config
        self.issue_processor = IssueProcessor(config)
    
    def enhance_meta_request(self, request: str, repository: str) -> str:
        """Enhance meta request with context for better AI understanding."""
        enhanced = f"""
META-PROGRAMMING REQUEST for live self-modification:

User Request: {request}

Context:
- This is a live CLI session where the user wants to modify the currently running program
- The program is SIP (Self-Improving Program) with CLI and AI capabilities
- The modification should be applied to the current codebase structure
- Focus on making targeted, safe changes that improve the specified functionality
- Repository: {repository}

Please generate specific code changes to implement this request.
"""
        return enhanced
    
    def process_meta_request(self, request: str, repository: str) -> ProcessingResult:
        """Process a meta-programming request and generate code changes."""
        try:
            logger.info(f"Processing meta request: {request}")
            
            # Create a synthetic issue for the meta request
            enhanced_request = self.enhance_meta_request(request, repository)
            
            synthetic_issue = GitHubIssue(
                number=99999,  # Special number for meta requests
                title=f"Meta: {request}",
                body=enhanced_request,
                author="live-session",
                labels=["meta-programming", "live-session"],
                state="open",
                html_url="#meta-request",
                repository=repository
            )
            
            # Process using existing AI pipeline
            result = self.issue_processor.process_issue_with_data(synthetic_issue)
            
            if result.success and result.pull_request:
                # Enhance the pull request title and body for meta context
                pr = result.pull_request
                pr.title = f"Live Meta: {request}"
                pr.body = f"""**Live Meta-Programming Request**

Original Request: {request}

{pr.body}

---
*Generated during live CLI session*"""
                pr.branch_name = f"live-meta-{abs(hash(request)) % 10000}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing meta request: {e}")
            return ProcessingResult(
                success=False,
                error_message=f"Meta processing failed: {str(e)}"
            )
