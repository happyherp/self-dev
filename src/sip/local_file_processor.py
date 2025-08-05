"""
Local file processor - Handles local file processing without any platform.

This module processes local files and directories using the core engine.
"""

import logging
import os
from typing import Any

import filetype  # type: ignore

from .core import ChangeSet, CodeEditor, Goal, Repo


class LocalFileProcessor:
    """
    Processes local files without any platform dependencies.

    This demonstrates how the same core engine can work with local files
    instead of GitHub repositories.
    """

    def __init__(self, llm_client: Any) -> None:
        """Initialize with LLM client."""
        self.code_editor = CodeEditor(llm_client)
        self.logger = logging.getLogger(__name__)

    def process_goal_file(self, goal_file: str, repo_dir: str) -> ChangeSet:
        """
        Process a goal file against a local repository.

        Args:
            goal_file: Path to file containing the goal description
            repo_dir: Path to local repository directory

        Returns:
            ChangeSet with the proposed changes
        """
        # 1. Load goal from file
        goal = self._load_goal_from_file(goal_file)
        self.logger.info(f"Loaded goal: {goal.description[:100]}...")

        # 2. Load local repository
        repo = self._load_local_repo(repo_dir)
        self.logger.info(f"Loaded local repository with {len(repo.files)} files")

        # 3. Process using core engine
        changeset = self.code_editor.process_goal(goal, repo)
        self.logger.info(f"Generated changeset with {len(changeset.files)} file changes")

        return changeset

    def apply_changeset_locally(self, repo_dir: str, changeset: ChangeSet) -> None:
        """
        Apply a changeset to local files.

        Args:
            repo_dir: Path to local repository directory
            changeset: ChangeSet to apply
        """
        self.logger.info(f"Applying changeset to {repo_dir}")

        for file_change in changeset.files:
            file_path = os.path.join(repo_dir, file_change.path)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write the file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_change.content)

            self.logger.info(f"Applied changes to {file_change.path}")

        self.logger.info("✅ All changes applied successfully")

    def _load_goal_from_file(self, goal_file: str) -> Goal:
        """Load goal from a text file."""
        with open(goal_file, encoding="utf-8") as f:
            content = f.read().strip()

        # Split into title and description if there's a double newline
        parts = content.split("\n\n", 1)
        if len(parts) == 2:
            title, description = parts
            full_description = f"{title}\n\n{description}"
        else:
            full_description = content

        return Goal(
            description=full_description,
            context=f"Local goal file: {goal_file}",
            priority="normal",
            tags=["local"],
        )

    def _load_local_repo(self, repo_dir: str) -> Repo:
        """Load files from a local repository directory."""
        files = {}

        # Walk through the directory and load text files
        for root, dirs, filenames in os.walk(repo_dir):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in {"__pycache__", "node_modules", "dist", "build"}
            ]

            for filename in filenames:
                # Skip hidden files and binary files
                if filename.startswith("."):
                    continue

                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, repo_dir)

                # Only process text files
                if self._is_text_file(file_path):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            files[relative_path] = f.read()
                    except (UnicodeDecodeError, PermissionError):
                        # Skip files that can't be read as text
                        continue

        return Repo(
            name=os.path.basename(os.path.abspath(repo_dir)),
            files=files,
            metadata={
                "repository": repo_dir,
                "platform": "local",
            },
        )

    def _is_text_file(self, file_path: str) -> bool:
        """Check if a file is a text file using filetype detection."""
        try:
            # If filetype detects a binary format, it's not a text file
            kind = filetype.guess(file_path)
            if kind is not None:
                return False

            # If filetype returns None, it's likely a text file
            # But let's do a quick check for null bytes to be sure
            if os.path.getsize(file_path) == 0:
                return True  # Empty files are text

            with open(file_path, "rb") as f:
                # Check first 8KB for null bytes (binary indicator)
                sample = f.read(8192)
                return b"\x00" not in sample

        except (OSError, PermissionError):
            # If we can't access the file, assume it's not a text file
            return False
