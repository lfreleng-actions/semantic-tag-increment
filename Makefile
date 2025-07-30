# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

.PHONY: help install install-dev test test-verbose lint format clean build \
        coverage coverage-html pre-commit action-test cli-test security-audit \
        docs-build docs-serve release-test all

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install package in production mode
	python -m pip install --upgrade pip
	python -m pip install .

install-dev: ## Install package in development mode with all dependencies
	python -m pip install --upgrade pip
	python -m pip install pdm
	pdm install --dev

# Testing targets
test: ## Run unit tests
	pdm run pytest tests/ -v

test-verbose: ## Run tests with verbose output and coverage
	pdm run pytest tests/ -v --cov=src/semantic_tag_increment --cov-report=term-missing

test-integration: ## Run integration tests only
	pdm run pytest tests/test_integration.py -v -m integration

test-unit: ## Run unit tests only
	pdm run pytest tests/ -v -m "not integration"

test-property: ## Run property-based tests
	pdm run pytest tests/ -v -m property

# Code quality targets
lint: ## Run all linting checks
	pdm run ruff check src/ tests/
	pdm run ruff format --check src/ tests/
	pdm run mypy src/

format: ## Format code with ruff
	pdm run ruff format src/ tests/
	pdm run ruff check --fix src/ tests/

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Coverage targets
coverage: ## Generate coverage report
	pdm run pytest tests/ --cov=src/semantic_tag_increment --cov-report=term --cov-report=xml

coverage-html: ## Generate HTML coverage report
	pdm run pytest tests/ --cov=src/semantic_tag_increment --cov-report=html
	@echo "Coverage report generated in coverage_html_report/"

# CLI testing targets
cli-test: ## Test CLI functionality
	@echo "Testing CLI help commands..."
	pdm run semantic-tag-increment --help
	pdm run semantic-tag-increment increment --help
	pdm run semantic-tag-increment validate --help
	pdm run semantic-tag-increment suggest --help

	@echo "Testing basic increment operations..."
	pdm run semantic-tag-increment increment --tag "1.2.3" --increment "patch" --no-check-conflicts
	pdm run semantic-tag-increment increment --tag "v1.2.3" --increment "minor" --no-check-conflicts
	pdm run semantic-tag-increment increment --tag "1.2.3" --increment "major" --no-check-conflicts
	pdm run semantic-tag-increment increment --tag "1.2.3" --increment "prerelease" --no-check-conflicts

	@echo "Testing validation..."
	pdm run semantic-tag-increment validate --tag "1.2.3"
	pdm run semantic-tag-increment validate --tag "v1.2.3-alpha.1+build.123"

	@echo "Testing complex versions..."
	pdm run semantic-tag-increment validate --tag "1.2.3----RC-SNAPSHOT.12.9.1--.12+788"
	pdm run semantic-tag-increment increment --tag "1.0.0-alpha.1" --increment "prerelease" --no-check-conflicts

action-test: ## Test GitHub Action functionality
	@echo "Testing action with temporary files..."
	@echo "This requires the action to be available in the current directory"

# Security targets
security-audit: ## Run security audit
	pdm run ruff check --select=S src/ tests/
	@echo "Security audit complete using Ruff's security checks"

# Build targets
build: ## Build package
	pdm build

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage_html_report/
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Documentation targets (placeholder for future)
docs-build: ## Build documentation
	@echo "Documentation build not yet implemented"

docs-serve: ## Serve documentation locally
	@echo "Documentation serve not yet implemented"

# Release testing
release-test: ## Test release process
	pdm build
	python -m twine check dist/*
	@echo "Release test complete. Ready for PyPI upload."

# Comprehensive target
all: clean install-dev lint test coverage cli-test ## Run all checks and tests

# Development workflow
dev-setup: install-dev pre-commit ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make help' to see available commands"

# Quick checks for CI
ci-test: lint test coverage ## Run CI-appropriate tests
	@echo "CI tests complete"

# Performance testing
perf-test: ## Run performance tests
	@echo "Running performance tests..."
	@pdm run python -c "\
import time; \
from semantic_tag_increment.parser import SemanticVersion; \
from semantic_tag_increment.incrementer import VersionIncrementer; \
start = time.time(); \
[SemanticVersion.parse('1.2.3-alpha.1+build.123') for i in range(1000)]; \
parse_time = time.time() - start; \
print(f'Parse 1000 versions: {parse_time:.3f}s'); \
incrementer = VersionIncrementer(); \
version = SemanticVersion.parse('1.2.3'); \
start = time.time(); \
[incrementer.increment(version, incrementer.determine_increment_type('patch')) for i in range(1000)]; \
increment_time = time.time() - start; \
print(f'Increment 1000 versions: {increment_time:.3f}s'); \
"

# Example usage target
examples: ## Run example commands
	@echo "=== Semantic Tag Increment Examples ==="
	@echo ""
	@echo "1. Basic patch increment:"
	pdm run semantic-tag-increment increment --tag "v1.2.3" --increment "patch" --no-check-conflicts
	@echo ""
	@echo "2. Prerelease increment:"
	pdm run semantic-tag-increment increment --tag "1.2.3" --increment "prerelease" --prerelease-type "alpha" --no-check-conflicts
	@echo ""
	@echo "3. Complex version validation:"
	pdm run semantic-tag-increment validate --tag "1.2.3----RC-SNAPSHOT.12.9.1--.12+788"
	@echo ""
	@echo "4. Version suggestions:"
	pdm run semantic-tag-increment suggest --tag "1.2.3" --increment "prerelease"

# Debugging target
debug-info: ## Show debug information
	@echo "=== Debug Information ==="
	@echo "Python version:"
	python --version
	@echo ""
	@echo "PDM version:"
	pdm --version || echo "PDM not installed"
	@echo ""
	@echo "Package location:"
	python -c "import semantic_tag_increment; print(semantic_tag_increment.__file__)" 2>/dev/null || echo "Package not installed"
	@echo ""
	@echo "Dependencies:"
	pdm list || pip list | grep -E "(typer|semantic)"
