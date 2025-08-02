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

2. **Install SIP**:
   ```sh
   uv pip install -e .
   ```

3. **Install with development dependencies**:
   ```sh
   uv pip install -e ".[test]"
   ```

## Environment Setup

SIP requires API keys to function:

1. **GitHub Token**: Create a personal access token at https://github.com/settings/tokens
2. **OpenRouter API Key**: Get an API key from https://openrouter.ai/

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

## Verification

Verify the installation by running:

```sh
sip --help
```

You should see the SIP command-line interface help message.
