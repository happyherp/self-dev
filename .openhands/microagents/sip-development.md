---
name: SIP Development Workflow
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - "sip"
  - "self-dev"
  - "development workflow"
  - "make ci"
  - "pre-commit"
  - "quality checks"
---

# SIP Development Workflow Microagent

This microagent provides context and automation for the SIP (Self-Improving Program) development workflow.

## Project Overview

SIP is an AI-powered GitHub-native autonomous development system that processes issues, analyzes codebases, and creates pull requests automatically. The project uses modern Python tooling with comprehensive quality checks.

## Development Stack

- **Package Manager**: `uv` (modern Python package manager)
- **Linting & Formatting**: `ruff`
- **Type Checking**: `mypy`
- **Testing**: `pytest` with coverage
- **Build System**: `pyproject.toml` with uv

## Critical Development Rules

### Always Run CI Before Committing
**MANDATORY**: Run `make ci` before any commit or push. This runs:
1. Linting with ruff (`make lint`)
2. Format checking (`make format-check`)
3. Type checking with mypy (`make typecheck`)
4. Unit tests with coverage (`make test-unit`)

### Quality Targets Available
- `make qa` - Auto-fix style, sort imports, format code, run type checking
- `make ci` - Full CI pipeline (must pass before committing)
- `make test-unit` - Run unit tests with coverage
- `make test-integration` - Run integration tests (requires API tokens)
- `make security` - Run security checks

### Environment Setup
Required environment variables for full functionality:
- `AGENT_GITHUB_TOKEN` - GitHub API access
- `OPENROUTER_API_KEY` - AI model access

## Workflow Commands

### Development Setup
```bash
# Install with test dependencies
uv sync --extra test

# Run quality fixes
make qa

# Run full CI checks
make ci
```

### Pre-Commit Workflow
```bash
# Before any commit:
make ci

# If CI passes, then commit:
git add .
git commit --author="openhands <openhands@all-hands.dev>" -m "Your commit message"
```

### Testing
```bash
# Unit tests only
make test-unit

# Integration tests (requires secrets)
make test-integration

# All tests across Python versions
make test-all
```

## File Structure Context

- `src/sip/` - Main package code
- `tests/` - Test files
- `Makefile` - Development automation
- `pyproject.toml` - Project configuration
- `.github/workflows/` - CI/CD automation

## Common Issues & Solutions

### CI Failures
1. **Linting errors**: Run `make lint-fix` or `make qa` to auto-fix most issues
2. **Type errors**: Check `mypy` output and fix type annotations
3. **Test failures**: Run `make test-unit` locally to debug
4. **Format issues**: Run `make format` to fix formatting

### Integration Test Issues
- Ensure `AGENT_GITHUB_TOKEN` and `OPENROUTER_API_KEY` are set
- Use `make test-integration-optional` for graceful skipping when secrets missing

## Automation Available

The project includes:
- `.openhands/setup.sh` - Development environment setup
- `.openhands/pre-commit.sh` - Pre-commit quality checks
- GitHub Actions for automated CI/CD

## Best Practices

1. **Always run `make ci` before committing**
2. Use `make qa` to auto-fix style issues
3. Write tests for new functionality
4. Keep commits focused and atomic
5. Use descriptive commit messages
6. Set git author to `"openhands <openhands@all-hands.dev>"` for OpenHands commits

## Error Handling Philosophy

**CRITICAL**: Never swallow errors and return fake/default data. This project follows fail-fast error handling:

❌ **BAD**:
```python
try:
    result = risky_operation()
    return result
except Exception:
    return "default"  # Hides real problems!
```

✅ **GOOD**:
```python
try:
    result = risky_operation()
    return result
except SpecificError as e:
    raise ValueError(f"Operation failed: {e}")
```

This is essential for a self-improving system that needs to diagnose and fix its own issues.