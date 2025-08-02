# Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to ensure code quality and consistency. Pre-commit hooks run automatically before each commit to catch issues early.

## Setup

Install pre-commit hooks after setting up the development environment:

```bash
# Install dependencies
uv sync --extra test

# Install pre-commit hooks
make pre-commit-install
```

## Hooks Configured

### General File Checks

- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with a newline
- **check-yaml**: Validate YAML syntax (including GitHub Actions)
- **check-json**: Validate JSON syntax
- **check-toml**: Validate TOML syntax
- **check-merge-conflict**: Detect merge conflict markers
- **check-case-conflict**: Detect case conflicts
- **check-added-large-files**: Prevent large files (>500KB)

### Python-specific Checks

- **check-ast**: Validate Python syntax
- **check-builtin-literals**: Require literal syntax when initializing empty or zero Python builtin types
- **check-docstring-first**: Ensure docstrings come first
- **debug-statements**: Detect debug statements
- **name-tests-test**: Ensure test files follow naming conventions

### Code Quality

- **ruff**: Python linting and auto-fixing
- **ruff-format**: Python code formatting
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning

### CI/CD and Configuration

- **actionlint**: GitHub Actions workflow validation
- **markdownlint**: Markdown formatting and style
- **shellcheck**: Shell script linting (when present)
- **hadolint**: Dockerfile linting (when present)

## Usage

### Automatic (Recommended)

Pre-commit hooks run automatically on `git commit`. If any hook fails, the commit is aborted and you need to fix the issues.

### Manual

Run hooks manually on all files:

```bash
make pre-commit-run
```

Run hooks on specific files:

```bash
uv run --extra test pre-commit run --files src/sip/cli.py
```

### Updating Hooks

Update to the latest versions of hooks:

```bash
make pre-commit-update
```

## Configuration Files

- **`.pre-commit-config.yaml`**: Main pre-commit configuration
- **`.markdownlint.json`**: Markdown linting rules
- **`.markdownlintignore`**: Files to ignore for markdown linting
- **`pyproject.toml`**: Contains configuration for ruff, mypy, and bandit

## Bypassing Hooks

In rare cases, you can bypass pre-commit hooks:

```bash
git commit --no-verify -m "Emergency fix"
```

**Note**: This should only be used in emergencies as it bypasses all quality checks.
