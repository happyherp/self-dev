"""Data models for SIP."""

from dataclasses import dataclass


@dataclass
class GitHubIssue:
    """Represents a GitHub issue."""

    number: int
    title: str
    body: str
    author: str
    labels: list[str]
    state: str
    html_url: str
    repository: str


@dataclass
class AnalysisResult:
    """Result of AI analysis of an issue."""

    summary: str
    problem_type: str
    suggested_approach: str
    files_to_modify: list[str]
    confidence: float


@dataclass
class CodeChange:
    """Represents a code change to be made."""

    file_path: str
    change_type: str  # 'create', 'modify', 'delete'
    content: str
    description: str


@dataclass
class PullRequest:
    """Represents a pull request to be created."""

    title: str
    body: str
    branch_name: str
    changes: list[CodeChange]
    base_branch: str = "main"


@dataclass
class ProcessingResult:
    """Result of processing an issue."""

    issue: GitHubIssue | None
    analysis: AnalysisResult | None
    pull_request: PullRequest | None
    success: bool
    error_message: str | None = None
