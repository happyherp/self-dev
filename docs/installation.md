# Installation

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Modern Python package manager

### Installing uv

```sh
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation

SIP is currently in development and not yet published to PyPI. Install from source:

1. **Clone the repository**:
   ```sh
   git clone https://github.com/happyherp/self-dev.git
   cd self-dev
   ```

2. **Install SIP and dependencies**:
   ```sh
   uv sync
   ```

3. **Install with development dependencies**:
   ```sh
   uv sync --extra test
   ```

## Environment Setup

SIP requires API keys to function:

1. **GitHub Token**: Create a personal access token with minimal required permissions
   - 📋 **[Complete Setup Guide](./github-token-setup.md)** - Follow this for secure token creation
   - 🔗 Quick link: https://github.com/settings/tokens
2. **OpenRouter API Key**: Get an API key from https://openrouter.ai/

### For Local Development

Set these as environment variables:

```sh
export AGENT_GITHUB_TOKEN="your_github_token_here"
export OPENROUTER_API_KEY="your_openrouter_key_here"
```

Or create a `.env` file in the project root:

```
AGENT_GITHUB_TOKEN=your_github_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

### For GitHub Actions (Repository Setup)

**Required**: For SIP to work automatically on GitHub issues, you must add repository secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following repository secrets:
   - `AGENT_GITHUB_TOKEN`: Your GitHub token (see [GitHub Token Setup Guide](./github-token-setup.md))
   - `OPENROUTER_API_KEY`: Your OpenRouter API key

**Without these secrets, the GitHub Actions workflow will fail.**

## Verification

### Basic Installation
Verify the installation by running:

```sh
uv run sip --help
```

You should see the SIP command-line interface help message.

### GitHub Integration
To verify your GitHub token works correctly:

```sh
# Set your token (see GitHub Token Setup guide)
export AGENT_GITHUB_TOKEN="your_token_here"

# Test GitHub access
uv run python -c "
import os
from src.sip.github_client import GitHubClient
from src.sip.config import Config

config = Config.from_env()
client = GitHubClient(config.github_token)
print('✅ GitHub token works!')
"
```

### Integration Tests
To run the full integration test suite (requires GitHub token):

```sh
# Ensure AGENT_GITHUB_TOKEN is set
export AGENT_GITHUB_TOKEN="your_token_here"

# Run integration tests
uv run python -m pytest tests/test_integration.py -v
```

**Note**: Integration tests will be skipped in CI if `AGENT_GITHUB_TOKEN` is not available.
