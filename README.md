# SIP - Self-Improving Program

A GitHub-native autonomous development system that processes issues via AI, creates code changes, and submits pull requests.

## Overview

SIP (Self-Improving Program) is an AI-powered system that:

1. **Monitors GitHub Issues**: Automatically detects new issues in repositories
2. **Analyzes with AI**: Uses OpenRouter/Claude to understand the issue and codebase
3. **Generates Solutions**: Creates code changes to address the issue
4. **Submits Pull Requests**: Opens PRs with the proposed changes for human review

**Core Mission**: Enable AI to develop software autonomously through GitHub-native workflows, with simplicity and comprehensive testing supporting reliable self-development.

## Features

- 🤖 **AI-Powered Analysis**: Uses Claude 3.5 Sonnet via OpenRouter for intelligent code analysis
- 🔄 **Automated Workflow**: GitHub Actions integration for seamless issue processing
- 🛡️ **Human Review**: All changes require human approval before merging
- 📁 **Context-Aware**: Loads and analyzes the entire codebase for informed decisions
- 🎯 **Focused Changes**: Makes minimal, targeted modifications to address issues

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/happyherp/self-dev.git
   cd self-dev
   ```

2. **Install SIP**:
   ```bash
   uv pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   export AGENT_GITHUB_TOKEN="your_github_token"
   export OPENROUTER_API_KEY="your_openrouter_key"
   ```

4. **Process an issue**:
   ```bash
   sip process-issue 123
   ```

### Development

```bash
# Install with test dependencies
uv pip install -e ".[test]"

# Run tests
make test

# Run quality checks
make qa

# Run full CI pipeline (required before committing)
make ci
```

#### OpenHands Development Automation

For OpenHands users, automated development tools are available:

```bash
# Set up development environment with pre-commit hooks
./.openhands/setup.sh
```

This installs a pre-commit hook that automatically runs `make ci` before every commit, ensuring code quality standards are maintained. See [`.openhands/README.md`](.openhands/README.md) for details.

## Documentation

- [Installation Guide](docs/installation.md)
- [GitHub Token Setup](docs/github-token-setup.md) - **Required for GitHub integration**
- [Usage Instructions](docs/usage.md)
- [Project Overview](PROJECT.md)
- [Original Idea](idea.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
