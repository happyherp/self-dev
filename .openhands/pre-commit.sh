#!/bin/bash
# SIP Pre-commit Quality Checks
# This script runs all quality checks before allowing a commit

set -e  # Exit on any error

echo "🔍 Running SIP pre-commit quality checks..."

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

# Check if there are any staged changes
if ! git diff --cached --quiet; then
    echo "📝 Found staged changes, running quality checks..."
else
    echo "⚠️  No staged changes found. Make sure to 'git add' your changes first."
    exit 1
fi

# Run the full CI pipeline
echo "🚀 Running 'make ci'..."
if make ci; then
    echo "✅ All quality checks passed!"
    echo "🎉 Ready to commit!"
else
    echo ""
    echo "❌ Quality checks failed!"
    echo ""
    echo "🔧 To fix issues automatically, run:"
    echo "   make qa"
    echo ""
    echo "📋 Then review changes and commit again."
    echo ""
    echo "💡 Common fixes:"
    echo "   • Linting errors: 'make lint-fix' or 'make qa' auto-fixes most issues"
    echo "   • Format issues: 'make format'"
    echo "   • Import sorting: 'uv run ruff check --select I --fix .'"
    echo "   • Type errors: Check mypy output and fix type annotations"
    echo ""
    exit 1
fi

echo ""
echo "✨ Pre-commit checks completed successfully!"