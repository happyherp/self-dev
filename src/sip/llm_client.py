"""LLM client for OpenRouter integration."""

import json

import requests

from .config import Config
from .models import AnalysisResult, CodeChange, GitHubIssue, PullRequest


class LLMClient:
    """Client for interacting with LLMs via OpenRouter."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/happyherp/self-dev",
                "X-Title": "SIP - Self-Improving Program",
            }
        )

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
2. The type of problem (bug, feature, documentation, etc.)
3. Your suggested approach to solve it
4. List of files that likely need to be modified
5. Your confidence level (0.0 to 1.0)

Respond in JSON format:
{{
    "summary": "Brief summary of the issue",
    "problem_type": "bug|feature|documentation|enhancement|other",
    "suggested_approach": "Detailed approach to solve the issue",
    "files_to_modify": ["file1.py", "file2.py"],
    "confidence": 0.85
}}"""

        response = self._call_llm(prompt)

        try:
            data = json.loads(response)
            return AnalysisResult(
                summary=data["summary"],
                problem_type=data["problem_type"],
                suggested_approach=data["suggested_approach"],
                files_to_modify=data["files_to_modify"],
                confidence=data["confidence"],
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails
            return AnalysisResult(
                summary=f"Failed to parse analysis: {str(e)}",
                problem_type="other",
                suggested_approach="Manual review required",
                files_to_modify=[],
                confidence=0.0,
            )

    def generate_solution(
        self, issue: GitHubIssue, analysis: AnalysisResult, file_contents: dict[str, str]
    ) -> PullRequest:
        """Generate a complete solution for the issue."""

        files_context = ""
        for file_path, content in file_contents.items():
            files_context += f"\n--- {file_path} ---\n{content}\n"

        prompt = f"""You are SIP (Self-Improving Program). Generate a complete solution for this GitHub issue.

ISSUE:
Title: {issue.title}
Body: {issue.body}

ANALYSIS:
{analysis.suggested_approach}

CURRENT FILES:
{files_context}

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

Respond in JSON format:
{{
    "title": "Fix: Brief description of the fix",
    "body": "Detailed explanation of changes made...",
    "branch_name": "sip/issue-{issue.number}-short-description",
    "changes": [
        {{
            "file_path": "path/to/file.py",
            "change_type": "modify",
            "content": "complete file content here...",
            "description": "What this change does"
        }}
    ]
}}

IMPORTANT:
- Provide complete file content, not just diffs
- Ensure all changes are consistent and work together
- Follow the existing code style and patterns
- Include proper error handling and logging
- Add tests if appropriate"""

        response = self._call_llm(prompt)

        try:
            data = json.loads(response)
            changes = [
                CodeChange(
                    file_path=change["file_path"],
                    change_type=change["change_type"],
                    content=change["content"],
                    description=change["description"],
                )
                for change in data["changes"]
            ]

            return PullRequest(title=data["title"], body=data["body"], branch_name=data["branch_name"], changes=changes)
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails
            return PullRequest(
                title=f"SIP: Address issue #{issue.number}",
                body=f"Automated attempt to address: {issue.title}\n\nError generating solution: {str(e)}",
                branch_name=f"sip/issue-{issue.number}-auto",
                changes=[],
            )

    def _call_llm(self, prompt: str) -> str:
        """Make a call to the LLM via OpenRouter."""
        url = "https://openrouter.ai/api/v1/chat/completions"

        data = {
            "model": self.config.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for consistent, focused responses
            "max_tokens": 4000,
        }

        response = self.session.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        return str(result["choices"][0]["message"]["content"])
