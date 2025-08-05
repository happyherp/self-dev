# SIP Repository Instructions for OpenHands

This file is auto-generated from multiple source files. Do not edit directly.
Run 'make generate-openhands-repo' to regenerate.

---

# SIP - Self-Improving Program

A GitHub-native autonomous development system that processes issues via AI, creates code changes, and submits pull requests.

## Overview

SIP (Self-Improving Program) is an AI-powered autonomous development system that:

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

### Local Development Mode

For local development and testing, you can use the `process-local` command to work with local files without GitHub integration:

1. **Create a goal file** describing what you want to accomplish:
   ```bash
   echo "Add a new function to calculate fibonacci numbers" > goal.md
   ```

2. **Process the goal against a local repository**:
   ```bash
   # Preview changes (default behavior)
   sip process-local goal.md /path/to/your/repo
   
   # Apply changes to local files
   sip process-local goal.md /path/to/your/repo --apply
   ```

**Benefits of Local Mode:**
- 🚀 **Faster iteration**: No GitHub API calls or network dependencies
- 🔧 **Development testing**: Test SIP's AI capabilities on local codebases
- 📝 **Flexible goals**: Work with any text file describing your objectives
- 🎯 **Precise control**: Preview changes before applying them

**Requirements for Local Mode:**
- Only requires `OPENROUTER_API_KEY` (no GitHub token needed)
- Goal file can be any text file describing the desired changes
- Repository directory must exist and contain the code to modify

### Development

```bash
# Install with test dependencies
uv pip install -e ".[test]"

# Install pre-commit hooks (recommended for all developers)
make install-pre-commit-hooks

# Run full CI pipeline (required before committing)
make ci_for-developers
```

#### Pre-commit Hooks

We strongly recommend installing pre-commit hooks that automatically run `make ci` before every commit:

```bash
# Install pre-commit hooks (for all developers)
make install-pre-commit-hooks

# Manually run pre-commit checks
make run-pre-commit-checks
```

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

---

# SIP - Self-Improving Program

## Overview

SIP is a minimal, GitHub-native autonomous development system that primarily operates on **this repository** (`happyherp/self-dev`). Create a GitHub issue, and AI automatically analyzes the codebase, makes changes, and submits a pull request.

The system is designed to improve itself by working on its own issues, but can also be configured to work on other repositories.

## Design Principles

### AI-Driven Software Development
This project is fundamentally about enabling AI to develop software autonomously. Everything else serves this primary goal.

### Simplicity
Makes it easier for AI to understand, modify, and extend the codebase. Ensures consistent runtime conditions between AI sandbox, CI tests, and human development environments - essential for reliable self-development.

### Test-Driven Development
Automatic tests are critical since we rely on them far more than traditional projects. We develop test-first when possible and prioritize integration and end-to-end tests, even when they're challenging to implement.

### GitHub-Native
Built specifically for GitHub workflows - issues, pull requests, and Actions integration provide the natural interface for AI-driven development.

### Minimal Human Oversight
Currently humans gate merges to main, but the long-term goal is full autonomy. We minimize human intervention points to eventually achieve complete AI-driven development cycles.

### Fail-Fast Error Handling
**CRITICAL ANTIPATTERN TO AVOID**: Never swallow errors and return fake/default data. This masks real issues and makes debugging impossible.

❌ **BAD - Swallowing errors:**
```python
try:
    data = json.loads(response)
    return data["result"]
except Exception:
    return "default_value"  # Hides the real problem!
```

✅ **GOOD - Fail fast with clear errors:**
```python
try:
    data = json.loads(response)
    return data["result"]
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON response: {e}\nRaw: {response}")
except KeyError as e:
    raise ValueError(f"Missing field {e} in response: {response}")
```

This is especially critical for a self-improving system that needs to diagnose and fix its own issues. Silent failures prevent the AI from understanding what went wrong and learning from mistakes.

## How It Works

```
GitHub Issue → GitHub Actions → AI Analysis → Code Changes → Pull Request → Human Review
```

1. **Create Issue**: Describe what you want built/fixed
2. **AI Processes**: Loads full codebase context + issue into LLM
3. **AI Acts**: Returns EDIT (modify files) or SUBMIT (create PR) actions
4. **Auto-Execute**: Changes applied, PR created
5. **CI/CD**: Tests run, human reviews and merges

## Architecture

### Core Components
- **CLI Tool**: `python -m sip process-issue <number>`
- **GitHub Actions**: Triggers AI on issue creation
- **OpenRouter LLM**: Cost-effective AI processing
- **GitHub API**: All operations through GitHub

### Project Structure
```
sip/
├── cli.py                 # Command-line interface
├── issue_processor.py     # Main orchestrator
├── codebase_loader.py     # Load full repo context
├── llm_client.py         # OpenRouter integration
├── action_executor.py     # Execute EDIT/SUBMIT actions
├── github_client.py      # GitHub API wrapper
└── config.py             # Configuration

.github/workflows/
└── process-issue.yml      # Auto-trigger on issue creation
```

## AI Actions

The AI can perform two actions:

### EDIT Action
```json
{
  "action": "EDIT",
  "files": [
    {
      "path": "src/main.py",
      "content": "import os\n# new code here..."
    }
  ]
}
```

### SUBMIT Action
```json
{
  "action": "SUBMIT",
  "branch": "feature/fix-bug-123",
  "title": "Fix critical bug in main module",
  "description": "Detailed description of changes made"
}
```

## Setup

### Prerequisites
- OpenRouter API key
- GitHub token with repo access

### Installation
```bash
# Clone and install
git clone https://github.com/happyherp/self-dev.git
cd self-dev
uv pip install -e .

# Configure (defaults to this repository)
export AGENT_GITHUB_TOKEN="your_token"
export OPENROUTER_API_KEY="your_key"

# Optional: Override to work on different repository
export GITHUB_REPO="other-owner/other-repo"

# Test manually on this repository
python -m sip process-issue 1
```

### GitHub Actions Setup
```yaml
# .github/workflows/process-issue.yml
name: Process Issue with AI
on:
  issues:
    types: [opened]

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install SIP
        run: uv pip install -e .
      - name: Process Issue
        run: python -m sip process-issue ${{ github.event.issue.number }}
        env:
          AGENT_GITHUB_TOKEN: ${{ secrets.AGENT_GITHUB_TOKEN }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Design Principles

- **GitHub-Native**: Uses Issues, PRs, Actions as the complete interface
- **Minimal Setup**: No external servers or complex orchestration
- **Context-Rich**: AI gets full codebase context for intelligent decisions
- **Cost-Conscious**: OpenRouter for affordable LLM access
- **Autonomous**: Runs hands-off after initial setup
- **Test-Driven**: Comprehensive testing with CI/CD validation

## Current Status

**Status**: 📋 Planning Phase - Architecture Defined

**Next Steps**:
1. Generate cookiecutter-pypackage structure
2. Implement core components
3. Add comprehensive tests
4. Set up GitHub Actions workflow
5. Deploy and test end-to-end

## Example Workflow

1. **Create Issue**: "Add user authentication to the web app"
2. **AI Analysis**: Loads all project files, understands current architecture
3. **AI Decision**: Returns EDIT actions to modify auth files + SUBMIT for PR
4. **Execution**: Files updated, branch created, PR submitted
5. **CI/CD**: Tests pass, awaits human review
6. **Human Review**: Developer reviews and merges PR
7. **Result**: Feature implemented with AI assistance

## Vision

A self-improving program that gets better by working on its own issues in the `happyherp/self-dev` repository, creating a feedback loop of continuous autonomous development. The AI learns about its own codebase and can implement new features, fix bugs, and improve itself based on GitHub issues created by users or the system itself.