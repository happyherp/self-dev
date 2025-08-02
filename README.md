# SIP - Self-Improving Program

A GitHub-native autonomous development system that processes issues via AI, creates code changes, and submits pull requests.

## Overview

SIP (Self-Improving Program) is an AI-powered system that:

1. **Monitors GitHub Issues**: Automatically detects new issues in repositories
2. **Analyzes with AI**: Uses OpenRouter/Claude to understand the issue and codebase
3. **Generates Solutions**: Creates code changes to address the issue
4. **Submits Pull Requests**: Opens PRs with the proposed changes for human review

## Features

- 🤖 **AI-Powered Analysis**: Uses Claude 3.5 Sonnet via OpenRouter for intelligent code analysis
- 🔄 **Automated Workflow**: GitHub Actions integration for seamless issue processing
- 🛡️ **Human Review**: All changes require human approval before merging
- 📁 **Context-Aware**: Loads and analyzes the entire codebase for informed decisions
- 🎯 **Focused Changes**: Makes minimal, targeted modifications to address issues

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/happyherp/self-dev.git
   cd self-dev
   ```

2. **Install SIP**:
   
   **With uv (recommended)**:
   ```bash
   uv pip install -e .
   ```
   
   **With pip**:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   export GITHUB_TOKEN="your_github_token"
   export OPENROUTER_API_KEY="your_openrouter_key"
   ```

4. **Process an issue**:
   ```bash
   sip process-issue 123
   ```

### Development

For development work, we recommend using `uv` as the project includes `uv`-based development tools:

```bash
# Install with test dependencies
uv pip install -e ".[test]"

# Run tests
make test

# Run quality checks
make qa
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Instructions](docs/usage.md)
- [Project Overview](PROJECT.md)
- [Original Idea](idea.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
