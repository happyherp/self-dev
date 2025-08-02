# SIP - Self-Improving Program

## Overview

SIP is a minimal, GitHub-native autonomous development system that primarily operates on **this repository** (`happyherp/self-dev`). Create a GitHub issue, and AI automatically analyzes the codebase, makes changes, and submits a pull request.

The system is designed to improve itself by working on its own issues, but can also be configured to work on other repositories.

## Design Principles

### Simplicity First
When faced with choices like "support A or B or both", we choose **one option** unless supporting both genuinely reduces complexity. Supporting multiple approaches typically adds maintenance burden, documentation overhead, and user confusion.

### GitHub-Native
Built specifically for GitHub workflows - issues, pull requests, and Actions integration.

### AI-Powered
Leverages modern LLMs for intelligent code analysis and generation.

### Human-in-the-Loop
All changes require human review and approval before merging.

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
export GITHUB_TOKEN="your_token"
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
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
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