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

echo ""
echo "🎉 SIP development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "  • Run 'make qa' to auto-fix any style issues"
echo "  • Run 'make ci' before committing (now automated via pre-commit hook)"
echo "  • Set environment variables for integration tests:"
echo "    export AGENT_GITHUB_TOKEN='your_token'"
echo "    export OPENROUTER_API_KEY='your_key'"
echo ""
echo "🔧 Available commands:"
echo "  • make qa      - Auto-fix style and run type checking"
echo "  • make ci      - Run full CI pipeline"
echo "  • make test    - Run tests with custom arguments"
echo "  • make help    - Show all available make targets"