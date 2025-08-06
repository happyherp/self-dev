"""
Issue processor - Handles GitHub issue processing workflow.

This module processes GitHub issues by converting them to goals,
using the core code editor, and creating pull requests.
"""

import logging
from typing import Any

from .config import Config
from .core import ChangeSet, CodeEditor, Goal, Repo
from .github_client import GitHubClient
from .llm_client import LLMClient
from .models import GitHubIssue, ProcessingResult


class IssueProcessor:
    """
    Processes GitHub issues end-to-end.

    This class:
    1. Converts GitHub Issues to Goals
    2. Converts GitHub repositories to Repos
    3. Uses the core CodeEditor for processing
    4. Converts ChangeSets back to GitHub PRs
    """

    def __init__(self, config: Config):
        """Initialize with GitHub and LLM clients."""
        self.config = config
        self.github = GitHubClient(config)
        self.llm = LLMClient(config)

        # Create core code editor with LLM client
        self.code_editor = CodeEditor(llm_client=self.llm, max_retry_attempts=config.max_retry_attempts)

        self.logger = logging.getLogger(__name__)

    def process_issue(self, repo: str, issue_number: int, branch: str | None = None) -> ProcessingResult:
        """
        Process a GitHub issue end-to-end.

        This method orchestrates the workflow:
        1. GitHub Issue -> Goal
        2. GitHub Repository -> Repo
        3. Core processing (Goal + Repo -> ChangeSet)
        4. ChangeSet -> GitHub PR

        Args:
            repo: Repository name in format "owner/repo"
            issue_number: GitHub issue number
            branch: Branch to analyze and create PR from (defaults to current git branch)

        Returns:
            ProcessingResult with GitHub-specific information
        """
        try:
            # Determine target branch
            if not branch:
                import subprocess

                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
                    )
                    target_branch = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    target_branch = "main"  # Fallback if git command fails
            else:
                target_branch = branch

            self.logger.info(f"Processing GitHub issue #{issue_number} in {repo} (branch: {target_branch})")

            # 1. Fetch GitHub issue and convert to Goal
            github_issue = self.github.get_issue(repo, issue_number)
            goal = self._issue_to_goal(github_issue)
            self.logger.info(f"Converted issue to goal: {goal.description[:100]}...")

            # 2. Fetch GitHub repository and convert to Repo
            github_repo = self._fetch_github_repo(repo, target_branch)
            core_repo = self._github_to_repo(repo, github_repo)
            self.logger.info(f"Loaded repository with {len(core_repo.files)} files")

            # 3. Core processing (platform-agnostic)
            changeset = self.code_editor.process_goal(goal, core_repo)
            self.logger.info(f"Generated changeset with {len(changeset.files)} file changes")

            # 4. Convert changeset to GitHub PR
            pr_url = self._changeset_to_github_pr(repo, changeset, issue_number, target_branch)
            self.logger.info(f"Created GitHub PR: {pr_url}")

            # 5. Convert back to GitHub-specific result format
            # Create a PullRequest object for compatibility
            from .models import CodeChange, PullRequest

            # Convert changeset files to CodeChange objects
            code_changes = []
            for file_change in changeset.files:
                code_changes.append(
                    CodeChange(
                        file_path=file_change.path,
                        change_type="create" if not file_change.exists else "modify",
                        content=file_change.content,
                        description=f"Update {file_change.path}",
                    )
                )

            mock_pr = PullRequest(
                title=changeset.summary,
                body=f"{changeset.description}\n\nCloses #{issue_number}",
                branch_name=changeset.branch_name or f"sip/issue-{issue_number}",
                changes=code_changes,
                base_branch=branch or "main",
            )

            return ProcessingResult(
                success=True,
                pull_request=mock_pr,
                error_message=None,
            )

        except Exception as e:
            self.logger.error(f"Failed to process issue #{issue_number}: {str(e)}")
            return ProcessingResult(
                success=False,
                pull_request=None,
                error_message=str(e),
            )

    def _issue_to_goal(self, issue: GitHubIssue) -> Goal:
        """Convert a GitHub issue to a core Goal."""
        # Combine title and body for full context
        description = f"{issue.title}\n\n{issue.body}" if issue.body else issue.title

        return Goal(
            description=description,
            context=f"Repository: {issue.repository}",
            priority="high" if "urgent" in issue.labels else "normal",
            tags=issue.labels,
        )

    def _fetch_github_repo(self, repo: str, branch: str = "main") -> dict[str, str]:
        """Fetch repository files from GitHub."""
        # Get list of files and then fetch their content efficiently
        file_paths = self.github.list_repository_files(repo, ref=branch)

        # Use the optimized method to fetch multiple files
        files = self.github.get_multiple_file_contents(repo, file_paths, ref=branch)

        self.logger.info(f"Successfully fetched {len(files)} files from {repo}")
        return files

    def _github_to_repo(self, repo_name: str, github_files: dict[str, str]) -> Repo:
        """Convert GitHub repository data to core Repo."""
        return Repo(
            name=repo_name,
            files=github_files,
            metadata={
                "repository": repo_name,
                "platform": "github",
            },
        )

    def _changeset_to_github_pr(
        self, repo: str, changeset: ChangeSet, issue_number: int, base_branch: str = "main"
    ) -> str:
        """Convert a ChangeSet to a GitHub pull request and return the PR URL."""
        from .models import CodeChange, PullRequest

        # Convert changeset files to CodeChange objects
        code_changes = []
        for file_change in changeset.files:
            code_changes.append(
                CodeChange(
                    file_path=file_change.path,
                    change_type="create" if not file_change.exists else "modify",
                    content=file_change.content,
                    description=f"Update {file_change.path}",
                )
            )

        # Generate branch name if not provided
        branch_name = changeset.branch_name or f"sip/issue-{issue_number}"

        # Create PullRequest object
        pr = PullRequest(
            title=changeset.summary,
            body=f"{changeset.description}\n\nCloses #{issue_number}",
            branch_name=branch_name,
            changes=code_changes,
            base_branch=base_branch,
        )

        # First create the branch and commit changes
        self.github.create_branch(repo, branch_name, base_branch)
        self.github.commit_changes(repo, branch_name, code_changes, changeset.summary)

        # Then create the pull request
        pr_url = self.github.create_pull_request(repo, pr)

        return pr_url

    def process_github_issue_directly(
        self, repo: str, github_issue: Any, branch: str | None = None
    ) -> ProcessingResult:
        """
        Process a PyGithub Issue object directly.

        This is a convenience method for users who already have PyGithub Issue objects
        and want to avoid the conversion overhead.

        Args:
            repo: Repository name in format "owner/repo"
            github_issue: PyGithub Issue object
            branch: Branch to analyze and create PR from (defaults to current git branch)

        Returns:
            ProcessingResult with GitHub-specific information
        """
        # Convert PyGithub Issue to our GitHubIssue model
        issue = self.github.issue_from_github_issue(github_issue, repo)

        # Use the regular processing workflow
        return self.process_issue(repo, issue.number, branch)
