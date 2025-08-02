"""LLM client for OpenRouter integration."""

import instructor
from openai import OpenAI

from .config import Config
from .models import AnalysisResult, GitHubIssue, PullRequest


class LLMClient:
    """Client for interacting with LLMs via OpenRouter."""

    def __init__(self, config: Config):
        self.config = config
        # Create OpenAI client configured for OpenRouter
        openai_client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/happyherp/self-dev",
                "X-Title": "SIP - Self-Improving Program",
            }
        )
        # Patch with instructor for structured outputs
        self.client = instructor.from_openai(openai_client)

    def analyze_issue(self, issue: GitHubIssue, repository_context: str) -> AnalysisResult:
        """Analyze a GitHub issue and determine how to address it."""

        prompt = f"""You are SIP (Self-Improving Program), an AI that analyzes GitHub issues and creates solutions.

ISSUE TO ANALYZE:
Title: {issue.title}
Body: {issue.body}
Author: {issue.author}
Labels: {", ".join(issue.labels)}
Repository: {issue.repository}

REPOSITORY CONTEXT:
{repository_context}

Please analyze this issue and provide:
1. A brief summary of the problem
2. The type of problem (bug, feature, documentation, enhancement, or other)
3. Your suggested approach to solve it
4. List of files that likely need to be modified
5. Your confidence level (0.0 to 1.0)"""

        return self.client.chat.completions.create(
            model=self.config.llm_model,
            response_model=AnalysisResult,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4000,
        )

    def generate_solution(
        self,
        issue: GitHubIssue,
        analysis: AnalysisResult,
        file_contents: dict[str, str],
        previous_attempt: str | None = None,
        test_failure: str | None = None,
    ) -> PullRequest:
        """Generate a complete solution for the issue."""

        files_context = ""
        for file_path, content in file_contents.items():
            files_context += f"\n--- {file_path} ---\n{content}\n"

        retry_context = ""
        if previous_attempt and test_failure:
            retry_context = f"""
PREVIOUS ATTEMPT FAILED:
The previous solution failed tests. Here was the previous attempt:
{previous_attempt}

TEST FAILURE:
{test_failure}

Please fix the issues and provide a corrected solution.
"""

        prompt = f"""You are SIP (Self-Improving Program). Generate a complete solution for this GitHub issue.

ISSUE:
Title: {issue.title}
Body: {issue.body}

ANALYSIS:
{analysis.suggested_approach}

CURRENT FILES:
{files_context}

{retry_context}

Generate a complete solution including:
1. A descriptive pull request title
2. A detailed pull request body explaining the changes
3. A unique branch name (use format: sip/issue-{issue.number}-description)
4. All necessary code changes

For each code change, specify:
- file_path: The path to the file
- change_type: "create", "modify", or "delete"
- content: The complete new content of the file (for create/modify)
- description: Brief description of what this change does

IMPORTANT:
- Provide complete file content, not just diffs
- Ensure all changes are consistent and work together
- Follow the existing code style and patterns
- Include proper error handling and logging
- Add tests if appropriate"""

        return self.client.chat.completions.create(
            model=self.config.llm_model,
            response_model=PullRequest,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=8000,
        )
