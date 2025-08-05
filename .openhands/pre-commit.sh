#!/bin/bash
# Pre-commit hook for OpenHands
# This script is called by the git pre-commit hook installed by OpenHands

set -e

echo "🔍 Running OpenHands pre-commit checks..."

# Run the CI pipeline to ensure code quality
make ci_for-developers

echo "✅ Pre-commit checks passed!"