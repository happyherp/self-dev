"""
Core layer - Platform-agnostic code manipulation engine.

This module provides convenient imports for core functionality.
The main CodeEditor class has been moved to code_editor.py for better organization.
"""

# Import core models from models.py
# Import the main CodeEditor class and exception from code_editor.py
from .code_editor import CodeEditor, TestFailureError
from .models import (
    ChangeSet,
    CoreAnalysisResult,
    FileContent,
    Goal,
    Repo,
)

# Re-export everything for backward compatibility
__all__ = [
    "ChangeSet",
    "CodeEditor",
    "CoreAnalysisResult",
    "FileContent",
    "Goal",
    "Repo",
    "TestFailureError",
]
