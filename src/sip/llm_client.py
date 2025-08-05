"""LLM client for OpenRouter integration."""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from .config import Config
from .core import Goal
from .models import AnalysisResult, PullRequest


class LLMClient:
    """Client for interacting with LLMs via OpenRouter."""

    def __init__(self, config: Config):
        self.config = config
        # Create OpenAI model configured for OpenRouter
        import os

        # Set the API key as environment variable for PydanticAI
        os.environ["OPENROUTER_API_KEY"] = config.openrouter_api_key

        self.model = OpenAIModel(
            model_name=config.llm_model,
            provider="openrouter",
        )

        # Create agents for different tasks
        self.analysis_agent = Agent(
            model=self.model,
            output_type=AnalysisResult,
            system_prompt="""You are SIP (Self-Improving Program), an AI that analyzes GitHub issues.

Analyze the provided GitHub issue and provide:
1. A brief summary of the problem
2. The type of problem (bug, feature, documentation, enhancement, or other)
3. Your suggested approach to solve it
4. List of files that likely need to be modified
5. Your confidence level (0.0 to 1.0)

Be precise and focused in your analysis.""",
        )

        self.solution_agent = Agent(
            model=self.model,
            output_type=PullRequest,
            system_prompt="""You are SIP (Self-Improving Program). Generate complete solutions for GitHub issues.

Generate a complete solution including:
1. A descriptive pull request title
2. A detailed pull request body explaining the changes
3. A unique branch name (use format: sip/issue-{issue_number}-description)
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
- Add tests if appropriate""",
        )

    def analyze_goal(self, goal: Goal, repository_context: str) -> AnalysisResult:
        """Analyze a goal and determine how to address it."""
        prompt = f"""GOAL TO ANALYZE:
Description: {goal.description}
Context: {goal.context}
Priority: {goal.priority}
Tags: {", ".join(goal.tags)}

REPOSITORY CONTEXT:
{repository_context}"""

        result = self.analysis_agent.run_sync(prompt)
        return result.data

    def generate_solution(
        self,
        goal: Goal,
        analysis: AnalysisResult,
        file_contents: dict[str, str],
        previous_attempt: str | None = None,
        last_error: str | None = None,
    ) -> PullRequest:
        """Generate a complete solution for the goal."""
        files_context = ""
        for file_path, content in file_contents.items():
            files_context += f"\n--- {file_path} ---\n{content}\n"

        retry_context = ""
        if previous_attempt and last_error:
            retry_context = f"""
PREVIOUS ATTEMPT FAILED:
The previous solution failed tests. Here was the previous attempt:
{previous_attempt}

TEST FAILURE:
{last_error}

Please fix the issues and provide a corrected solution.
"""

        # Extract a title from the goal description for issue number context
        goal_title = goal.description.split("\n")[0][:100]

        prompt = f"""GOAL:
Description: {goal.description}
Context: {goal.context}
Title: {goal_title}

ANALYSIS:
{analysis.suggested_approach}

CURRENT FILES:
{files_context}

{retry_context}"""

        result = self.solution_agent.run_sync(prompt)
        return result.data
