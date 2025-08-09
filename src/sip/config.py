"""Configuration management for SIP."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """SIP configuration."""

    github_token: str
    openrouter_api_key: str
    default_repository: str = "happyherp/self-dev"
    llm_model: str = "anthropic/claude-sonnet-4"
    max_file_size: int = 100000  # 100KB
    max_files_per_pr: int = 10
    max_retry_attempts: int = 5
    start_work_comment_template: str = (
        "🤖 **SIP (Self-Improving Program) has started working on this issue!**\n\n"
        "I'm analyzing the requirements and will create a pull request with the solution soon. "
        "You can track the progress here."
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        github_token = os.getenv("AGENT_GITHUB_TOKEN")
        if not github_token:
            raise ValueError("AGENT_GITHUB_TOKEN environment variable is required")

        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        # Get default values from dataclass fields
        fields = cls.__dataclass_fields__

        return cls(
            github_token=github_token,
            openrouter_api_key=openrouter_api_key,
            default_repository=os.getenv("DEFAULT_REPOSITORY", str(fields["default_repository"].default)),
            llm_model=os.getenv("LLM_MODEL", str(fields["llm_model"].default)),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", str(fields["max_file_size"].default))),
            max_files_per_pr=int(os.getenv("MAX_FILES_PER_PR", str(fields["max_files_per_pr"].default))),
            max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", str(fields["max_retry_attempts"].default))),
            start_work_comment_template=os.getenv(
                "START_WORK_COMMENT_TEMPLATE", str(fields["start_work_comment_template"].default)
            ),
        )