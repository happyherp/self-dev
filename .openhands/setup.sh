#!/bin/bash
# OpenHands Development Environment Setup for SIP
# This script sets up the development environment and installs pre-commit hooks

set -e  # Exit on any error

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]] || [[ ! -f "Makefile" ]]; then
    echo "❌ Error: This script must be run from the SIP project root directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Use the make target for complete setup
make setup-openhands