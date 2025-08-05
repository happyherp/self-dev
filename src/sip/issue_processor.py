"""
Issue processor - Handles GitHub issue processing workflow.

This module processes GitHub issues by converting them to goals,
using the core code editor, and creating pull requests.
"""

import logging

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

    def process_issue(self, repo: str, issue_number: int, branch: str = "main") -> ProcessingResult:
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
            branch: Branch to analyze and create PR from (defaults to "main")

        Returns:
            ProcessingResult with GitHub-specific information
        """
        try:
            self.logger.info(f"Processing GitHub issue #{issue_number} in {repo}")

            # 1. Fetch GitHub issue and convert to Goal
            github_issue = self.github.get_issue(repo, issue_number)
            goal = self._issue_to_goal(github_issue)
            self.logger.info(f"Converted issue to goal: {goal.description[:100]}...")

            # 2. Fetch GitHub repository and convert to Repo
            github_repo = self._fetch_github_repo(repo, branch)
            core_repo = self._github_to_repo(repo, github_repo)
            self.logger.info(f"Loaded repository with {len(core_repo.files)} files")

            # 3. Core processing (platform-agnostic)
            changeset = self.code_editor.process_goal(goal, core_repo)
            self.logger.info(f"Generated changeset with {len(changeset.files)} file changes")

            # 4. Convert changeset to GitHub PR
            pr_url = self._changeset_to_github_pr(repo, changeset, issue_number, branch)
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
                base_branch=branch,
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
        # Get list of files and then fetch their content
        files = {}
        file_paths = self.github.list_repository_files(repo, ref=branch)

        for file_path in file_paths:
            try:
                content = self.github.get_file_content(repo, file_path, ref=branch)
                files[file_path] = content
            except Exception as e:
                self.logger.warning(f"Could not fetch {file_path}: {e}")
                continue

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

    def _changeset_to_github_pr(self, repo: str, changeset: ChangeSet, issue_number: int, base_branch: str = "main") -> str:
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
