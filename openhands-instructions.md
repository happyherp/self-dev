# OpenHands Instructions for SIP Development

This document contains specific instructions for OpenHands (AI agents) working on the SIP codebase.

## Critical Development Rules for AI Agents

### Mandatory Quality Checks
**ALWAYS run `make check-code_for-self` before committing**. This command:
1. Auto-fixes linting and formatting issues
2. Runs the full CI pipeline to ensure quality

Never commit without passing all quality checks. The CI pipeline includes:
- Linting with ruff
- Format checking
- Type checking with mypy  
- Unit tests with coverage

### Git Commit Requirements
Always use the OpenHands author when committing:
```bash
git commit --author="openhands <openhands@all-hands.dev>" -m "Your commit message"
```

### Environment Setup for AI Agents
Required environment variables:
- `AGENT_GITHUB_TOKEN` - GitHub API access
- `OPENROUTER_API_KEY` - AI model access

### Development Workflow Commands

#### Quality Automation
```bash
# Auto-fix issues then run CI (recommended for self-improvement)
make check-code_for-self

# Auto-fix linting and formatting only
make auto-fix

# Manual quality fixes
make qa

# Full CI pipeline (must pass)
make ci
```

#### Testing
```bash
# Unit tests with coverage
make test-unit

# Integration tests (requires API tokens)
make test-integration

# Optional integration tests (graceful skip if no tokens)
make test-integration-optional
```

## Error Handling Philosophy

**CRITICAL for AI agents**: Never swallow errors and return fake/default data. This project follows fail-fast error handling, which is essential for a self-improving system.

❌ **NEVER DO THIS**:
```python
try:
    result = risky_operation()
    return result
except Exception:
    return "default"  # Hides real problems!
```

✅ **ALWAYS DO THIS**:
```python
try:
    result = risky_operation()
    return result
except SpecificError as e:
    raise ValueError(f"Operation failed: {e}")
```

Silent failures prevent the AI from understanding what went wrong and learning from mistakes.

## File Structure for AI Context

- `src/sip/` - Main package code
- `tests/` - Test files  
- `Makefile` - Development automation (use `make check-code_for-self`)
- `pyproject.toml` - Project configuration
- `.github/workflows/` - CI/CD automation
- `.openhands/` - OpenHands configuration and scripts

## Common Issues & AI Solutions

### CI Failures
1. **Linting errors**: Run `make auto-fix` first, then `make ci`
2. **Type errors**: Check mypy output and fix type annotations
3. **Test failures**: Run `make test-unit` locally to debug
4. **Format issues**: Included in `make auto-fix`

### Integration Test Issues
- Ensure environment variables are set
- Integration tests require `AGENT_GITHUB_TOKEN` and `OPENROUTER_API_KEY`

## Best Practices for AI Agents

1. **Always run `make check-code_for-self` before committing**
2. Use descriptive commit messages
3. Keep commits focused and atomic
4. Write tests for new functionality
5. Follow the fail-fast error handling philosophy
6. Use the OpenHands git author for all commits

## Available Automation

- `.openhands/setup.sh` - Development environment setup
- `make check-code_for-self` - Self-improvement quality pipeline
- Pre-commit hooks - Automatic quality checks
- GitHub Actions - Automated CI/CD