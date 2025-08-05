# OpenHands Automation for SIP Development

This directory contains automation tools to streamline development of the SIP project with OpenHands.

## Files

### `setup.sh`
Development environment setup script that:
- Installs dependencies with `uv`
- Sets up pre-commit hooks
- Verifies the installation
- Provides guidance for next steps

**Usage:**
```bash
./.openhands/setup.sh
```

### `pre-commit.sh`
Pre-commit quality check script that:
- Runs the full `make ci` pipeline
- Prevents commits if quality checks fail
- Provides helpful error messages and fix suggestions

**Automatically triggered by git pre-commit hook after running setup.sh**

### `microagents/sip-development.md`
OpenHands microagent that provides:
- Project context and development workflow
- Quality check requirements
- Common commands and troubleshooting
- Best practices for SIP development

**Automatically activated when working on SIP-related tasks**

## Quick Start

1. **Set up development environment:**
   ```bash
   ./.openhands/setup.sh
   ```

2. **The pre-commit hook will now automatically run `make ci` before every commit**

3. **If quality checks fail, fix them with:**
   ```bash
   make qa  # Auto-fix most issues
   make ci  # Verify all checks pass
   ```

## Workflow

1. Make your changes
2. `git add .` (stage changes)
3. `git commit` (pre-commit hook runs `make ci` automatically)
4. If checks pass → commit succeeds
5. If checks fail → fix issues with `make qa` and try again

## Environment Variables

For full functionality, set these environment variables:
```bash
export AGENT_GITHUB_TOKEN="your_github_token"
export OPENROUTER_API_KEY="your_openrouter_key"
```

## Benefits

- **Consistent Quality**: Ensures `make ci` always runs before commits
- **Fast Feedback**: Catches issues before they reach CI/CD
- **Automated Fixes**: `make qa` auto-fixes most style issues
- **Context Awareness**: Microagent provides project-specific guidance
- **Error Prevention**: Prevents broken commits from entering the repository
