#!/bin/bash
# OpenHands Development Environment Setup for SIP
# This script sets up the development environment and installs pre-commit hooks

set -e  # Exit on any error

echo "🚀 Setting up SIP development environment for OpenHands..."

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

echo "📦 Installing dependencies with uv..."
uv sync --extra test

# Install pre-commit hooks using make target
make install-pre-commit-hooks

# Verify installation
echo "🧪 Verifying installation..."
if uv run python -c "import sip; print('✅ SIP package importable')"; then
    echo "✅ Package installation verified"
else
    echo "❌ Package installation failed"
    exit 1
fi

# Check if make ci works
echo "🔍 Testing make ci..."
if make ci; then
    echo "✅ All quality checks passed!"
else
    echo "⚠️  Some quality checks failed. Run 'make qa' to auto-fix issues."
fi

echo "🎉 SIP development environment setup complete!"