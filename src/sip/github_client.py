"""GitHub API client for SIP."""

from typing import Any

from github import Auth, Github
from github.GithubException import UnknownObjectException

from .config import Config
from .models import CodeChange, GitHubIssue, PullRequest


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, config: Config):
        self.config = config
        auth = Auth.Token(config.github_token)
        self.github = Github(auth=auth)

    def get_issue(self, repo: str, issue_number: int) -> GitHubIssue:
        """Fetch an issue from GitHub."""
        repository = self.github.get_repo(repo)
        issue = repository.get_issue(issue_number)

        return GitHubIssue(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            author=issue.user.login,
            labels=[label.name for label in issue.labels],
            state=issue.state,
            html_url=issue.html_url,
            repository=repo,
        )

    def get_file_content(self, repo: str, path: str, ref: str = "main") -> str:
        """Get file content from repository."""
        try:
            repository = self.github.get_repo(repo)
            file_content = repository.get_contents(path, ref=ref)

            if isinstance(file_content, list):
                # This is a directory, not a file
                return ""

            return file_content.decoded_content.decode("utf-8")
        except UnknownObjectException:
            return ""  # File doesn't exist

    def create_branch(self, repo: str, branch_name: str, base_branch: str = "main") -> None:
        """Create a new branch."""
        repository = self.github.get_repo(repo)
        base_ref = repository.get_git_ref(f"heads/{base_branch}")
        repository.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)

    def commit_changes(self, repo: str, branch: str, changes: list[CodeChange], message: str) -> None:
        """Commit changes to a branch."""
        repository = self.github.get_repo(repo)

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
        repository = self.github.get_repo(repo)
        pull_request = repository.create_pull(title=pr.title, body=pr.body, head=pr.branch_name, base=pr.base_branch)
        return pull_request.html_url

    def list_repository_files(self, repo: str, path: str = "", ref: str = "main") -> list[str]:
        """List files in repository directory."""
        try:
            repository = self.github.get_repo(repo)
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
        repository = self.github.get_repo(repo)
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
