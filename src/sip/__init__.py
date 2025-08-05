"""Top-level package for SIP."""

import importlib.metadata

__author__ = """Audrey M. Roy Greenfeld"""
__email__ = "happyherp@users.noreply.github.com"

try:
    __version__ = importlib.metadata.version("sip")
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

# Export main classes for easy importing
from .core import ChangeSet, CodeEditor, Goal, Repo
from .issue_processor import IssueProcessor
from .local_file_processor import LocalFileProcessor

__all__ = [
    "CodeEditor",
    "Goal",
    "Repo",
    "ChangeSet",
    "IssueProcessor",
    "LocalFileProcessor",
]
