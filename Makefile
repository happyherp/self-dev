.PHONY: clean clean-build clean-pyc clean-test coverage dist docs help install lint lint/flake8

.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-openhands ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-openhands: ## remove generated OpenHands files
	rm -f .openhands/repo.md

qa: ## fix style, sort imports, check types
	uv run --extra test ruff check . --fix
	uv run --extra test ruff check --select I --fix .
	uv run --extra test ruff format .
	uv run --extra test mypy src/

auto-fix: ## automatically fix all fixable linting and formatting issues
	@echo "🔧 Auto-fixing linting issues..."
	@uv run --extra test ruff check src/ tests/ --fix || true
	@echo "🔧 Auto-fixing import sorting..."
	@uv run --extra test ruff check --select I src/ tests/ --fix || true
	@echo "🔧 Auto-formatting code..."
	@uv run --extra test ruff format src/ tests/
	@echo "✅ Auto-fix complete"

check-code_for-self: ## auto-fix issues then run CI checks (called by test_runner for self-improvement)
	@echo "🔧 Self-check: auto-fixing then validating code..."
	@$(MAKE) auto-fix
	@echo "🔍 Running CI validation..."
	@$(MAKE) ci_for-developers

# Legacy aliases for backwards compatibility  
agent-check-code_for-ai-agents: check-code_for-self ## alias for check-code_for-self (backwards compatibility)
agent-check-code: check-code_for-self ## alias for check-code_for-self (backwards compatibility)

lint: ## check code style with ruff
	uv run ruff check src/ tests/

lint-fix: ## fix linting issues with ruff
	uv run ruff check src/ tests/ --fix

format: ## format code with ruff
	uv run ruff format src/ tests/

format-check: ## check code formatting with ruff
	uv run ruff format --check src/ tests/

typecheck: ## check types with mypy
	uv run mypy src/

test-unit: ## run unit tests with coverage
	uv run python -m pytest tests/ -v --cov=src/sip --cov-report=xml --cov-report=term

security: ## run security checks
	@echo "🔒 Running security checks..."
	@uv run python scripts/security_check.py

ci_for-github-ci-yml: ## run all CI checks (called by .github/workflows/ci.yml)
	@echo "🔍 Running CI pipeline for GitHub CI workflow..."
	@echo "📋 Step 1: Generating OpenHands repo documentation..."
	@$(MAKE) generate-openhands-repo
	@echo "✅ OpenHands repo documentation generated"
	@echo "📋 Step 2: Linting with ruff..."
	@$(MAKE) lint
	@echo "✅ Linting passed"
	@echo "📋 Step 3: Format check with ruff..."
	@$(MAKE) format-check
	@echo "✅ Format check passed"
	@echo "📋 Step 4: Type checking with mypy..."
	@$(MAKE) typecheck
	@echo "✅ Type checking passed"
	@echo "📋 Step 5: Running tests with coverage..."
	@$(MAKE) test-unit
	@echo "✅ All CI checks passed! 🎉"

ci_for-developers: ## run all CI checks locally (called by developers)
	@echo "🔍 Running CI pipeline locally..."
	@echo "📋 Step 1: Generating OpenHands repo documentation..."
	@$(MAKE) generate-openhands-repo
	@echo "✅ OpenHands repo documentation generated"
	@echo "📋 Step 2: Linting with ruff..."
	@$(MAKE) lint
	@echo "✅ Linting passed"
	@echo "📋 Step 3: Format check with ruff..."
	@$(MAKE) format-check
	@echo "✅ Format check passed"
	@echo "📋 Step 4: Type checking with mypy..."
	@$(MAKE) typecheck
	@echo "✅ Type checking passed"
	@echo "📋 Step 5: Running tests with coverage..."
	@$(MAKE) test-unit
	@echo "✅ All CI checks passed! 🎉"

ci_for-setup: ## run all CI checks during setup (called internally by setup targets)
	@echo "🔍 Running CI pipeline for setup verification..."
	@echo "📋 Step 1: Generating OpenHands repo documentation..."
	@$(MAKE) generate-openhands-repo
	@echo "✅ OpenHands repo documentation generated"
	@echo "📋 Step 2: Linting with ruff..."
	@$(MAKE) lint
	@echo "✅ Linting passed"
	@echo "📋 Step 3: Format check with ruff..."
	@$(MAKE) format-check
	@echo "✅ Format check passed"
	@echo "📋 Step 4: Type checking with mypy..."
	@$(MAKE) typecheck
	@echo "✅ Type checking passed"
	@echo "📋 Step 5: Running tests with coverage..."
	@$(MAKE) test-unit
	@echo "✅ All CI checks passed! 🎉"

# Legacy alias for backwards compatibility
ci: ci_for-developers ## alias for ci_for-developers (backwards compatibility)

MAKECMDGOALS ?= .	

test:  ## Run all the tests, but allow for arguments to be passed
	@echo "Running with arg: $(filter-out $@,$(MAKECMDGOALS))"
	pytest $(filter-out $@,$(MAKECMDGOALS))

pdb:  ## Run all the tests, but on failure, drop into the debugger
	@echo "Running with arg: $(filter-out $@,$(MAKECMDGOALS))"
	pytest --pdb --maxfail=10 --pdbcls=IPython.terminal.debugger:TerminalPdb $(filter-out $@,$(MAKECMDGOALS))

test-all: ## run tests on every Python version with uv
	uv run --python=3.10 --extra test pytest
	uv run --python=3.11 --extra test pytest
	uv run --python=3.12 --extra test pytest
	uv run --python=3.13 --extra test pytest

test-integration: ## run integration tests with live API tokens (fails if secrets missing)
	@echo "🧪 Running integration tests with live API tokens..."
	@# Fail if secrets are not available
	@if [ -z "$$AGENT_GITHUB_TOKEN" ] || [ -z "$$OPENROUTER_API_KEY" ]; then \
		echo "❌ Integration tests failed: secrets not available"; \
		echo "Set AGENT_GITHUB_TOKEN and OPENROUTER_API_KEY environment variables to run integration tests"; \
		exit 1; \
	fi
	@echo "Testing CLI help command..."
	@uv run python -m sip --help > /dev/null
	@echo "✅ CLI help works"
	@echo "Testing config loading..."
	@uv run python -c "from sip.config import Config; config = Config.from_env(); print(f'✅ Config loaded for repository: {config.default_repository}')"
	@echo "Testing GitHub API connectivity..."
	@uv run python -c "from sip.github_client import GitHubClient; from sip.config import Config; config = Config.from_env(); client = GitHubClient(config); repo_info = client.get_repository(config.default_repository); print(f'✅ GitHub API connected - Repository: {repo_info[\"full_name\"]}'); print(f'✅ Repository description: {repo_info.get(\"description\", \"No description\")}')";
	@echo "✅ All integration tests passed!"

coverage: ## check code coverage quickly with the default Python
	coverage run --source sip -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/sip.md
	rm -f docs/modules.md
	sphinx-apidoc -o docs/ sip
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.md' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	uv release -t $(UV_PUBLISH_TOKEN)

build: clean ## builds source and wheel package
	rm -rf build dist
	uv build
	ls -l dist

build-check: build ## build package and verify contents
	@echo "🔍 Checking build artifacts..."
	@uv run python scripts/build_check.py

install: clean ## install the package to the active Python's site-packages
	python setup.py install

install-pre-commit-hooks: ## install pre-commit hooks for quality checks
	@mkdir -p .git/hooks
	@echo '#!/bin/bash' > .git/hooks/pre-commit
	@echo 'make run-pre-commit-checks_for-git-hooks' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit

run-pre-commit-checks_for-git-hooks: ## run pre-commit quality checks (called by git pre-commit hooks)
	@git diff --cached --quiet || $(MAKE) ci_for-developers

setup_for-openhands: ## complete OpenHands development environment setup (called by .openhands/setup.sh)
	@echo "🚀 Setting up OpenHands development environment..."
	@uv sync --extra test
	@echo "🔧 Installing pre-commit hooks..."
	@$(MAKE) install-pre-commit-hooks
	@echo "📝 Generating OpenHands repository documentation..."
	@$(MAKE) generate-openhands-repo
	@echo "🎉 OpenHands development environment setup complete!"

generate-openhands-repo: ## generate .openhands/repo.md from source files
	@echo "📝 Generating .openhands/repo.md from source files..."
	@mkdir -p .openhands
	@echo "# SIP Repository Instructions for OpenHands" > .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@echo "This file is auto-generated from multiple source files. Do not edit directly." >> .openhands/repo.md
	@echo "Run 'make generate-openhands-repo' to regenerate." >> .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@echo "---" >> .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@cat README.md >> .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@echo "---" >> .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@cat PROJECT.md >> .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@echo "---" >> .openhands/repo.md
	@echo "" >> .openhands/repo.md
	@cat openhands-instructions.md >> .openhands/repo.md
	@echo "✅ Generated .openhands/repo.md"
