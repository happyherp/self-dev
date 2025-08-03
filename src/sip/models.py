"""Data models for SIP."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GitHubIssue(BaseModel):
    """Represents a GitHub issue."""

    number: int
    title: str
    body: str
    author: str
    labels: list[str]
    state: str
    html_url: str
    repository: str


class AnalysisResult(BaseModel):
    """Result of AI analysis of an issue."""

    summary: str = Field(description="Brief summary of the issue")
    problem_type: str = Field(description="Type: bug|feature|documentation|enhancement|other")
    suggested_approach: str = Field(description="Detailed approach to solve the issue")
    files_to_modify: list[str] = Field(description="List of files that need modification")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0")

    @field_validator("problem_type")
    @classmethod
    def validate_problem_type(cls, v: str) -> str:
        allowed_types = {"bug", "feature", "documentation", "enhancement", "other"}
        if v not in allowed_types:
            raise ValueError(f"problem_type must be one of {allowed_types}")
        return v


class CodeChange(BaseModel):
    """Represents a code change to be made."""

    file_path: str = Field(description="Path to the file to be changed")
    change_type: Literal["create", "modify", "delete"] = Field(description="Type of change: create, modify, or delete")
    content: str = Field(description="Complete new content of the file (for create/modify)")
    description: str = Field(description="Brief description of what this change does")


class PullRequest(BaseModel):
    """Represents a pull request to be created."""

    title: str = Field(description="Pull request title")
    body: str = Field(description="Pull request description")
    branch_name: str = Field(description="Branch name for the pull request")
    changes: list[CodeChange] = Field(description="List of code changes to make")
    base_branch: str = Field(default="main", description="Base branch for the pull request")


class ProcessingResult(BaseModel):
    """Result of processing an issue."""

    issue: GitHubIssue | None = Field(default=None, description="The processed issue")
    analysis: AnalysisResult | None = Field(default=None, description="Analysis results")
    pull_request: PullRequest | None = Field(default=None, description="Generated pull request")
    success: bool = Field(description="Whether processing was successful")
    error_message: str | None = Field(default=None, description="Error message if processing failed")


class LiveSessionState(BaseModel):
    """State data for live programming session."""
    
    modifications: list[dict] = Field(default=[], description="History of modifications made")
    current_version: int = Field(default=1, description="Current version of the program")
    backup_path: str | None = Field(default=None, description="Path to current backup")
    last_meta_request: str | None = Field(default=None, description="Last meta-programming request")
    pending_changes: PullRequest | None = Field(default=None, description="Pending changes to apply")
    session_start_time: float = Field(description="Session start timestamp")
