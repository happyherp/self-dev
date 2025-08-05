#!/usr/bin/env python3
"""Security check script for the SIP project."""

import ast
import os


def check_file(filepath: str) -> None:
    """Check a Python file for common security issues."""
    with open(filepath) as f:
        try:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                # Check for eval/exec usage
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec"]:
                        print(f"⚠️ Found {node.func.id} in {filepath}")
                # Check for subprocess with shell=True
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["run", "call", "check_call"]:
                        for keyword in node.keywords:
                            if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                                if keyword.value.value is True:
                                    print(f"⚠️ Found subprocess with shell=True in {filepath}")
        except SyntaxError:
            pass


def main() -> None:
    """Run security checks on all Python files in src/."""
    for root, _dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                check_file(os.path.join(root, file))

    print("✅ Security check completed")


if __name__ == "__main__":
    main()
