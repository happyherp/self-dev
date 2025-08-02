"""GitHub API client for SIP."""

import base64
from typing import Any

import httpx

from .config import Config
from .models import CodeChange, GitHubIssue, PullRequest


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.Client(
            headers={
                "Authorization": f"token {config.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "SIP-Bot/1.0",
            }
        )

    def get_issue(self, repo: str, issue_number: int) -> GitHubIssue:
        """Fetch an issue from GitHub."""
        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        return GitHubIssue(
            number=data["number"],
            title=data["title"],
            body=data["body"] or "",
            author=data["user"]["login"],
            labels=[label["name"] for label in data["labels"]],
            state=data["state"],
            html_url=data["html_url"],
            repository=repo,
        )

    def get_file_content(self, repo: str, path: str, ref: str = "main") -> str:
        """Get file content from repository."""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        params = {"ref": ref}
        response = self.client.get(url, params=params)

        if response.status_code == 404:
            return ""  # File doesn't exist

        response.raise_for_status()
        data = response.json()

        if data["encoding"] == "base64":
            return base64.b64decode(data["content"]).decode("utf-8")
        else:
            return str(data["content"])

    def create_branch(self, repo: str, branch_name: str, base_branch: str = "main") -> None:
        """Create a new branch."""
        # Get the SHA of the base branch
        url = f"https://api.github.com/repos/{repo}/git/refs/heads/{base_branch}"
        response = self.client.get(url)
        response.raise_for_status()
        base_sha = response.json()["object"]["sha"]

        # Create new branch
        url = f"https://api.github.com/repos/{repo}/git/refs"
        data = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
        response = self.client.post(url, json=data)
        response.raise_for_status()

    def commit_changes(self, repo: str, branch: str, changes: list[CodeChange], message: str) -> None:
        """Commit changes to a branch."""
        for change in changes:
            if change.change_type == "create" or change.change_type == "modify":
                self._update_file(repo, change.file_path, change.content, message, branch)
            elif change.change_type == "delete":
                self._delete_file(repo, change.file_path, message, branch)

    def _update_file(self, repo: str, path: str, content: str, message: str, branch: str) -> None:
        """Update or create a file."""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"

        # Try to get existing file to get its SHA
        try:
            response = self.client.get(url, params={"ref": branch})
            if response.status_code == 200:
                existing_sha = response.json()["sha"]
            else:
                existing_sha = None
        except Exception:
            existing_sha = None

        # Prepare the update
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        data = {"message": message, "content": encoded_content, "branch": branch}

        if existing_sha:
            data["sha"] = existing_sha

        response = self.client.put(url, json=data)
        response.raise_for_status()

    def _delete_file(self, repo: str, path: str, message: str, branch: str) -> None:
        """Delete a file."""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"

        # Get file SHA
        response = self.client.get(url, params={"ref": branch})
        response.raise_for_status()
        file_sha = response.json()["sha"]

        # Delete file
        data = {"message": message, "sha": file_sha, "branch": branch}
        response = self.client.request("DELETE", url, json=data)
        response.raise_for_status()

    def create_pull_request(self, repo: str, pr: PullRequest) -> str:
        """Create a pull request and return its URL."""
        url = f"https://api.github.com/repos/{repo}/pulls"
        data = {"title": pr.title, "body": pr.body, "head": pr.branch_name, "base": pr.base_branch}

        response = self.client.post(url, json=data)
        response.raise_for_status()

        return str(response.json()["html_url"])

    def list_repository_files(self, repo: str, path: str = "", ref: str = "main") -> list[str]:
        """List files in repository directory."""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        params = {"ref": ref}
        response = self.client.get(url, params=params)

        if response.status_code == 404:
            return []

        response.raise_for_status()
        data = response.json()

        files = []
        for item in data:
            if item["type"] == "file":
                files.append(item["path"])
            elif item["type"] == "dir":
                # Recursively get files from subdirectories
                subfiles = self.list_repository_files(repo, item["path"], ref)
                files.extend(subfiles)

        return files

    def get_repository(self, repo: str) -> dict[str, Any]:
        """Get repository information from GitHub."""
        url = f"https://api.github.com/repos/{repo}"
        response = self.client.get(url)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data
