"""Configuration management for SIP."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """SIP configuration."""

    github_token: str
    openrouter_api_key: str
    default_repository: str = "happyherp/self-dev"
    llm_model: str = "anthropic/claude-3.5-sonnet"
    max_file_size: int = 100000  # 100KB
    max_files_per_pr: int = 10
    max_retry_attempts: int = 5

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        return cls(
            github_token=github_token,
            openrouter_api_key=openrouter_api_key,
            default_repository=os.getenv("DEFAULT_REPOSITORY", "happyherp/self-dev"),
            llm_model=os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet"),
            max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", "5")),
        )
