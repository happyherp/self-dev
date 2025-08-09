"""GitHub API client for SIP."""

from typing import Any

from github import Auth, Github
from github.GithubException import GithubException, RateLimitExceededException, UnknownObjectException
from github.Issue import Issue
from github.PullRequest import PullRequest as GithubPullRequest
from github.Repository import Repository

from .config import Config
from .models import CodeChange, GitHubIssue, PullRequest


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, config: Config):
        self.config = config
        auth = Auth.Token(config.github_token)
        # Enable per_page optimization for better performance
        self.github = Github(auth=auth, per_page=100)
        self._repo_cache: dict[str, Repository] = {}

    def _get_repository(self, repo: str) -> Repository:
        """Get repository with caching."""
        if repo not in self._repo_cache:
            self._repo_cache[repo] = self.github.get_repo(repo)
        return self._repo_cache[repo]

    # Direct PyGithub object access methods
    def get_github_issue(self, repo: str, issue_number: int) -> Issue:
        """Get PyGithub Issue object directly."""
        repository = self._get_repository(repo)
        return repository.get_issue(issue_number)

    def get_github_repository(self, repo: str) -> Repository:
        """Get PyGithub Repository object directly."""
        return self._get_repository(repo)

    def get_github_pull_request(self, repo: str, pr_number: int) -> GithubPullRequest:
        """Get PyGithub PullRequest object directly."""
        repository = self._get_repository(repo)
        return repository.get_pull(pr_number)

    # Convenience methods that work with PyGithub objects
    def issue_from_github_issue(self, github_issue: Issue, repo: str) -> GitHubIssue:
        """Convert PyGithub Issue to our GitHubIssue model."""
        return GitHubIssue(
            number=github_issue.number,
            title=github_issue.title,
            body=github_issue.body or "",
            author=github_issue.user.login,
            labels=[label.name for label in github_issue.labels],
            state=github_issue.state,
            html_url=github_issue.html_url,
            repository=repo,
        )

    def get_issue(self, repo: str, issue_number: int) -> GitHubIssue:
        """Fetch an issue from GitHub."""
        github_issue = self.get_github_issue(repo, issue_number)
        return self.issue_from_github_issue(github_issue, repo)

    def create_comment(self, repo: str, issue_number: int, body: str) -> None:
        """Create a comment on a GitHub issue.
        
        Args:
            repo: Repository name in format "owner/repo"
            issue_number: Issue number to comment on
            body: Comment text
        """
        try:
            github_issue = self.get_github_issue(repo, issue_number)
            github_issue.create_comment(body)
        except Exception as e:
            # Log the error but don't fail the entire operation
            print(f"Warning: Failed to create comment on issue #{issue_number}: {e}")

    def get_file_content(self, repo: str, path: str, ref: str = "main") -> str:
        """Get file content from repository."""
        try:
            repository = self._get_repository(repo)
            file_content = repository.get_contents(path, ref=ref)

            if isinstance(file_content, list):
                # This is a directory, not a file
                return ""

            return file_content.decoded_content.decode("utf-8")
        except UnknownObjectException:
            return ""  # File doesn't exist

    def create_branch(self, repo: str, branch_name: str, base_branch: str = "main") -> None:
        """Create a new branch."""
        repository = self._get_repository(repo)
        base_ref = repository.get_git_ref(f"heads/{base_branch}")
        repository.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)

    def commit_changes(self, repo: str, branch: str, changes: list[CodeChange], message: str) -> None:
        """Commit changes to a branch."""
        repository = self._get_repository(repo)

        for change in changes:
            if change.change_type == "create" or change.change_type == "modify":
                self._update_file(repository, change.file_path, change.content, message, branch)
            elif change.change_type == "delete":
                self._delete_file(repository, change.file_path, message, branch)

    def _update_file(self, repository: Any, path: str, content: str, message: str, branch: str) -> None:
        """Update or create a file."""
        try:
            # Try to get existing file
            existing_file = repository.get_contents(path, ref=branch)
            if isinstance(existing_file, list):
                # This shouldn't happen for a file, but handle it
                raise UnknownObjectException(404, "File not found", None)

            # Update existing file
            repository.update_file(path=path, message=message, content=content, sha=existing_file.sha, branch=branch)
        except UnknownObjectException:
            # File doesn't exist, create it
            repository.create_file(path=path, message=message, content=content, branch=branch)

    def _delete_file(self, repository: Any, path: str, message: str, branch: str) -> None:
        """Delete a file."""
        existing_file = repository.get_contents(path, ref=branch)
        if isinstance(existing_file, list):
            raise ValueError(f"Cannot delete directory: {path}")

        repository.delete_file(path=path, message=message, sha=existing_file.sha, branch=branch)

    def create_pull_request(self, repo: str, pr: PullRequest) -> str:
        """Create a pull request and return its URL."""
        repository = self._get_repository(repo)
        pull_request = repository.create_pull(title=pr.title, body=pr.body, head=pr.branch_name, base=pr.base_branch)
        return pull_request.html_url

    def list_repository_files(self, repo: str, path: str = "", ref: str = "main") -> list[str]:
        """List files in repository directory."""
        try:
            repository = self._get_repository(repo)
            contents = repository.get_contents(path, ref=ref)

            if not isinstance(contents, list):
                # Single file
                return [contents.path] if contents.type == "file" else []

            files = []
            for item in contents:
                if item.type == "file":
                    files.append(item.path)
                elif item.type == "dir":
                    # Recursively get files from subdirectories
                    subfiles = self.list_repository_files(repo, item.path, ref)
                    files.extend(subfiles)

            return files
        except UnknownObjectException:
            return []

    def get_repository(self, repo: str) -> dict[str, Any]:
        """Get repository information from GitHub."""
        repository = self._get_repository(repo)
        return {
            "id": repository.id,
            "name": repository.name,
            "full_name": repository.full_name,
            "description": repository.description,
            "html_url": repository.html_url,
            "clone_url": repository.clone_url,
            "ssh_url": repository.ssh_url,
            "default_branch": repository.default_branch,
            "language": repository.language,
            "size": repository.size,
            "stargazers_count": repository.stargazers_count,
            "watchers_count": repository.watchers_count,
            "forks_count": repository.forks_count,
            "open_issues_count": repository.open_issues_count,
            "created_at": repository.created_at.isoformat() if repository.created_at else None,
            "updated_at": repository.updated_at.isoformat() if repository.updated_at else None,
            "pushed_at": repository.pushed_at.isoformat() if repository.pushed_at else None,
        }

    def get_rate_limit_info(self) -> dict[str, Any]:
        """Get current rate limit information."""
        rate_limit = self.github.get_rate_limit()
        # Access rate limit attributes safely
        core_limit = getattr(rate_limit, "core", None)
        search_limit = getattr(rate_limit, "search", None)

        result = {}
        if core_limit:
            result["core"] = {
                "limit": getattr(core_limit, "limit", 0),
                "remaining": getattr(core_limit, "remaining", 0),
                "reset": getattr(core_limit, "reset", None),
            }
        if search_limit:
            result["search"] = {
                "limit": getattr(search_limit, "limit", 0),
                "remaining": getattr(search_limit, "remaining", 0),
                "reset": getattr(search_limit, "reset", None),
            }
        return result

    def handle_github_exception(self, e: GithubException) -> str:
        """Convert GitHub exceptions to user-friendly error messages."""
        if isinstance(e, RateLimitExceededException):
            headers = getattr(e, "headers", {}) or {}
            return f"GitHub API rate limit exceeded. Reset time: {headers.get('X-RateLimit-Reset', 'unknown')}"
        elif isinstance(e, UnknownObjectException):
            data = getattr(e, "data", {})
            if isinstance(data, dict):
                return f"GitHub resource not found: {data.get('message', 'Unknown error')}"
            else:
                return f"GitHub resource not found: {data or 'Unknown error'}"
        else:
            data = getattr(e, "data", {})
            if isinstance(data, dict):
                return f"GitHub API error: {data.get('message', str(e))}"
            else:
                return f"GitHub API error: {data or str(e)}"

    def get_multiple_file_contents(self, repo: str, file_paths: list[str], ref: str = "main") -> dict[str, str]:
        """Get content of multiple files efficiently."""
        repository = self._get_repository(repo)
        contents = {}

        for file_path in file_paths:
            try:
                file_content = repository.get_contents(file_path, ref=ref)
                if not isinstance(file_content, list):
                    contents[file_path] = file_content.decoded_content.decode("utf-8")
            except UnknownObjectException:
                # File doesn't exist, skip it
                continue
            except Exception as e:
                # Log warning but continue with other files
                print(f"Warning: Could not fetch {file_path}: {e}")
                continue

        return contents