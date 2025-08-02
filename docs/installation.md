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

1. **GitHub Token**: Create a personal access token at https://github.com/settings/tokens
2. **OpenRouter API Key**: Get an API key from https://openrouter.ai/

### For Local Development

Set these as environment variables:

```sh
export GITHUB_TOKEN="your_github_token_here"
export OPENROUTER_API_KEY="your_openrouter_key_here"
```

Or create a `.env` file in the project root:

```
GITHUB_TOKEN=your_github_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

### For GitHub Actions (Repository Setup)

**Required**: For SIP to work automatically on GitHub issues, you must add repository secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following repository secrets:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
   - Note: `GITHUB_TOKEN` is automatically provided by GitHub Actions

**Without these secrets, the GitHub Actions workflow will fail.**

## Verification

Verify the installation by running:

```sh
uv run sip --help
```

You should see the SIP command-line interface help message.
