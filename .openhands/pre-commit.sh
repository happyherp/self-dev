#!/bin/bash
# SIP Pre-commit Quality Checks for OpenHands
# This script is a thin wrapper around the make target

set -e  # Exit on any error

# Change to project root if not already there
if [[ -f "pyproject.toml" ]]; then
    PROJECT_ROOT="$(pwd)"
else
    # Try to find project root
    PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
    cd "$PROJECT_ROOT"
fi

# Verify we're in the right place
if [[ ! -f "pyproject.toml" ]] || [[ ! -f "Makefile" ]]; then
    echo "❌ Error: Cannot find SIP project files (pyproject.toml, Makefile)"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "📁 Working in: $PROJECT_ROOT"

# Call the make target that does the actual work
make run-pre-commit-checks