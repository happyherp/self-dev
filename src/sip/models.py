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


# Core models - Platform-agnostic representations


class Goal(BaseModel):
    """Platform-agnostic representation of what needs to be accomplished."""

    description: str = Field(description="What to accomplish")
    context: str = Field(default="", description="Additional context about the codebase")
    priority: str = Field(default="normal", description="Priority: low, normal, high")
    tags: list[str] = Field(default_factory=list, description="Optional categorization")


class FileContent(BaseModel):
    """Represents a file in the repository."""

    path: str = Field(description="File path relative to repository root")
    content: str = Field(description="Complete file content")
    exists: bool = Field(default=True, description="Whether the file currently exists")


class ChangeSet(BaseModel):
    """Platform-agnostic representation of changes to make."""

    summary: str = Field(description="Brief summary of changes")
    description: str = Field(description="Detailed description of changes")
    files: list[FileContent] = Field(description="Complete file contents after changes")
    branch_name: str = Field(default="", description="Suggested branch name")
    test_command: str | None = Field(default=None, description="How to test these changes")


class Repo(BaseModel):
    """Abstract repository representation."""

    name: str = Field(description="Repository name or identifier")
    files: dict[str, str] = Field(description="File path to content mapping")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional repo info")


class CoreAnalysisResult(BaseModel):
    """Result of core analysis - platform-agnostic version of AnalysisResult."""

    summary: str = Field(description="Brief summary of the goal")
    problem_type: str = Field(description="Type: bug|feature|documentation|enhancement|other")
    suggested_approach: str = Field(description="Detailed approach to solve the goal")
    files_to_modify: list[str] = Field(description="List of files that need modification")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0")
